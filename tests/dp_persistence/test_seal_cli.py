from __future__ import annotations

import argparse
import contextlib
import io
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from src.dp_persistence import cli
from src.dp_persistence.cli import CommandError
from src.dp_persistence.protocol import (
    ALL_PROTECTED_PATHS,
    CALIBRATION_OPEN_MANIFEST_REF,
    CONTRACT_REF,
    FREEZE_TAG,
    OUTCOME_SEAL_REF,
    SOURCE_DIR_REF,
    SPEC_DIR_REF,
    STRUCTURAL_AUDIT_ANSWERS_REF,
    SUPERSEDED_SEAL_REF,
    TEST_DIR_REF,
)
from src.dp_persistence.seal import SealError, build_outcome_seal, verify_outcome_seal, write_outcome_seal


ROOT = Path(__file__).resolve().parents[2]
GIT_ENV = {
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "test@example.invalid",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "test@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
}
STAGE_NAMES = ("calibration", "development", "confirmation")


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, env={**os.environ, **GIT_ENV}
    )
    return result.stdout.decode()


def copy_protocol_tree(destination: Path) -> None:
    ignore = shutil.ignore_patterns("__pycache__", ".*")
    for relative in (SPEC_DIR_REF, SOURCE_DIR_REF, TEST_DIR_REF):
        shutil.copytree(ROOT / relative, destination / relative, ignore=ignore)
    (destination / CONTRACT_REF).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / CONTRACT_REF, destination / CONTRACT_REF)


class ParserTests(unittest.TestCase):
    def test_commands_and_no_overrides(self) -> None:
        parser = cli.build_parser()
        quiet = contextlib.redirect_stderr(io.StringIO())
        quiet.__enter__()
        self.addCleanup(quiet.__exit__, None, None, None)
        for stage in STAGE_NAMES:
            for verb in ("open", "run"):
                parser.parse_args([f"{verb}-{stage}"])
                for flag in ("--workers", "--grid", "--runs", "--output"):
                    with self.assertRaises(SystemExit):
                        parser.parse_args([f"{verb}-{stage}", flag, "2"])
        for name in ("audit", "freeze-seal", "verify-seal"):
            parser.parse_args([name])
        with self.assertRaises(SystemExit):
            parser.parse_args(["structural-audit"])


def registered_snapshot() -> dict[str, bytes | None]:
    """Bytes of every protected path in the real repository (None if absent)."""

    paths = ALL_PROTECTED_PATHS + (SUPERSEDED_SEAL_REF,)
    return {
        relative: (ROOT / relative).read_bytes() if (ROOT / relative).is_file() else None
        for relative in paths
    }


class RegisteredPathTests(unittest.TestCase):
    """Registered artifacts appear over the protocol's life; tests never write one."""

    def test_existing_registered_artifacts_are_tracked(self) -> None:
        for relative, data in registered_snapshot().items():
            if data is None:
                continue
            tracked = subprocess.run(
                ["git", "ls-files", "--error-unmatch", relative], cwd=ROOT, capture_output=True
            )
            self.assertEqual(tracked.returncode, 0, f"untracked registered artifact {relative}")

    def test_structural_audit_refuses_registered_paths(self) -> None:
        before = registered_snapshot()
        for relative in (STRUCTURAL_AUDIT_ANSWERS_REF, OUTCOME_SEAL_REF, "experiments/dp_persistence/x.json"):
            existed = (ROOT / relative).exists()
            with self.assertRaises(CommandError):
                cli.command_structural_audit(argparse.Namespace(output=str(ROOT / relative)))
            self.assertEqual((ROOT / relative).exists(), existed)
        self.assertEqual(registered_snapshot(), before)

    def test_structural_audit_writes_only_its_temporary_output(self) -> None:
        before = registered_snapshot()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "answers.json"
            self.assertEqual(cli.command_structural_audit(argparse.Namespace(output=str(output))), 0)
            self.assertTrue(output.is_file())
        self.assertEqual(registered_snapshot(), before)

    def test_audit_passes(self) -> None:
        for note in cli.audit_outcome_free_design():
            self.assertTrue(note.startswith("registered artifact present: "), note)


class GatedRepositoryTests(unittest.TestCase):
    """Every gate is exercised in a disposable git repository."""

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name).resolve()
        copy_protocol_tree(self.root)
        git(self.root, "init", "-q", "-b", "main")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "protocol")

    def tearDown(self) -> None:
        self.directory.cleanup()

    def assert_all_refuse(self, fragment: str | None = None) -> None:
        for stage in STAGE_NAMES:
            for action in (cli.gate_open, cli.gate_run):
                with self.assertRaises((CommandError, SealError)) as raised:
                    action(self.root, stage)
                if fragment is not None:
                    self.assertIn(fragment, str(raised.exception))
        for relative in ALL_PROTECTED_PATHS:
            if relative != OUTCOME_SEAL_REF:
                self.assertFalse((self.root / relative).exists(), relative)

    def seal_and_commit(self) -> None:
        write_outcome_seal(self.root, self.root / OUTCOME_SEAL_REF)
        git(self.root, "add", OUTCOME_SEAL_REF)
        git(self.root, "commit", "-q", "-m", "seal")

    def test_refuses_without_seal(self) -> None:
        self.assert_all_refuse("outcome seal is missing")

    def test_refuses_with_uncommitted_seal(self) -> None:
        write_outcome_seal(self.root, self.root / OUTCOME_SEAL_REF)
        self.assert_all_refuse("bytes must equal the current commit")

    def test_refuses_without_tag(self) -> None:
        self.seal_and_commit()
        self.assert_all_refuse("annotated freeze tag is missing")

    def test_refuses_lightweight_tag(self) -> None:
        self.seal_and_commit()
        git(self.root, "tag", FREEZE_TAG)
        self.assert_all_refuse("annotated freeze tag is missing")

    def test_refuses_tag_off_the_seal_commit(self) -> None:
        self.seal_and_commit()
        git(self.root, "tag", "-a", FREEZE_TAG, "-m", "freeze", "HEAD^")
        self.assert_all_refuse("does not select the commit that added the outcome seal")

    def test_refuses_dirty_tree(self) -> None:
        self.seal_and_commit()
        git(self.root, "tag", "-a", FREEZE_TAG, "-m", "freeze")
        (self.root / "scratch.txt").write_text("x")
        self.assert_all_refuse("worktree must be clean")

    def test_refuses_tampered_source(self) -> None:
        self.seal_and_commit()
        git(self.root, "tag", "-a", FREEZE_TAG, "-m", "freeze")
        path = self.root / SOURCE_DIR_REF / "rng.py"
        path.write_text(path.read_text() + "\n# tampered\n")
        self.assert_all_refuse("hash mismatch")

    def test_full_gate_sequence_without_running(self) -> None:
        self.seal_and_commit()
        git(self.root, "tag", "-a", FREEZE_TAG, "-m", "freeze")
        # Sealed, tagged, clean: every run still refuses without its manifest.
        for stage in STAGE_NAMES:
            with self.assertRaises(CommandError) as raised:
                cli.gate_run(self.root, stage)
            self.assertIn("open manifest is missing", str(raised.exception))
        # Development and confirmation cannot open before calibration and Stage A.
        for stage in ("development", "confirmation"):
            with self.assertRaises(CommandError):
                cli.gate_open(self.root, stage)
        # Calibration can open; its manifest must be committed alone before a run.
        path = cli.open_stage("calibration", self.root)
        self.assertEqual(path, self.root / CALIBRATION_OPEN_MANIFEST_REF)
        with self.assertRaises(CommandError):
            cli.gate_run(self.root, "calibration")
        git(self.root, "add", CALIBRATION_OPEN_MANIFEST_REF)
        git(self.root, "commit", "-q", "-m", "open calibration")
        manifest = cli.gate_run(self.root, "calibration")
        self.assertEqual(manifest["stage"], "calibration")
        # run-development still refuses: no committed calibration result.
        with self.assertRaises(CommandError):
            cli.gate_run(self.root, "development")
        with self.assertRaises(CommandError):
            cli.open_stage("calibration", self.root)


class SealContentTests(unittest.TestCase):
    def test_seal_round_trip_and_tamper_detection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            copy_protocol_tree(root)
            seal = build_outcome_seal(root)
            self.assertFalse(seal["run_command_enabled"])
            self.assertIn(f"{SOURCE_DIR_REF}/l0_engine.py", seal["source_files"])
            self.assertIn(f"{SPEC_DIR_REF}/minimal_law.json", seal["spec_files"])
            write_outcome_seal(root, root / OUTCOME_SEAL_REF)
            verify_outcome_seal(root / OUTCOME_SEAL_REF, root=root)
            with self.assertRaises(Exception):
                write_outcome_seal(root, root / OUTCOME_SEAL_REF)
            (root / SPEC_DIR_REF / "extra.json").write_text("{}")
            with self.assertRaises(SealError):
                verify_outcome_seal(root / OUTCOME_SEAL_REF, root=root)


if __name__ == "__main__":
    unittest.main()
