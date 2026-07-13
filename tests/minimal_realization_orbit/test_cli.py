import contextlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.minimal_realization_orbit import cli
from src.minimal_realization_orbit.runner import (
    OPEN_SEAL_REF,
    OUTCOME_SEAL_REF,
    CANDIDATE_MANIFEST_REF,
    PARENT_BOUNDED_RESULT_REF,
    OrbitLedgerError,
    canonical_json,
    expected_candidate_rows,
    load_canonical_json,
    read_candidate_snapshot,
)


ROOT = Path(__file__).resolve().parents[2]


class ProtocolAuditTests(unittest.TestCase):
    def test_registered_protocol_and_schema_audit(self) -> None:
        cli._audit_protocol(ROOT)

    def test_archival_tag_identifies_frozen_parent(self) -> None:
        cli._verify_archival_identity(ROOT)

    def test_every_sealed_implementation_file_exists(self) -> None:
        for relative in cli.IMPLEMENTATION_FILES:
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file())

    def test_transitive_parent_imports_are_frozen(self) -> None:
        self.assertIn("src/minimal_realization/__init__.py", cli.FROZEN_DEPENDENCIES)
        self.assertIn("src/minimal_realization/search.py", cli.FROZEN_DEPENDENCIES)
        cli._verify_frozen_dependencies_against_parent(ROOT)

    def test_claim_limit_mutation_fails_exact_protocol_audit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = ROOT / cli.SPEC_DIR_REF
            destination = root / cli.SPEC_DIR_REF
            destination.parent.mkdir(parents=True)
            shutil.copytree(source, destination)
            protocol_path = root / cli.PROTOCOL_REF
            protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
            protocol["claim_limits"] = []
            protocol_path.write_text(json.dumps(protocol), encoding="utf-8")
            with self.assertRaises(OrbitLedgerError):
                cli._audit_protocol(root)

    def test_parent_preflight_visits_all_candidates_before_return(self) -> None:
        candidates = read_candidate_snapshot(ROOT / CANDIDATE_MANIFEST_REF)
        parent = load_canonical_json(ROOT / PARENT_BOUNDED_RESULT_REF)
        calls: list[tuple[str, ...]] = []
        with mock.patch.object(
            cli,
            "reproduce_parent_H16",
            side_effect=lambda rows, _record: calls.append(rows),
        ):
            cli._preflight_parent_H16(candidates, parent)
        self.assertEqual(calls, list(expected_candidate_rows()[1:]))


class CommandSurfaceTests(unittest.TestCase):
    def test_run_surface_has_no_candidate_layer_or_output_override(self) -> None:
        args = cli.build_parser().parse_args(
            ["run-exact-orbit", "--open-seal", OPEN_SEAL_REF]
        )
        self.assertEqual(
            set(vars(args)),
            {"command", "open_seal", "func"},
        )

    def test_unregistered_resource_override_is_rejected(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                cli.build_parser().parse_args(
                    [
                        "run-exact-orbit",
                        "--open-seal",
                        OPEN_SEAL_REF,
                        "--max-layers",
                        "64",
                    ]
                )

    def test_outcome_seal_path_is_fixed(self) -> None:
        registered = cli._require_registered(
            ROOT / OUTCOME_SEAL_REF,
            OUTCOME_SEAL_REF,
            "test outcome seal",
        )
        self.assertEqual(registered, ROOT / OUTCOME_SEAL_REF)
        with self.assertRaises(OrbitLedgerError):
            cli._require_registered(
                ROOT / "alternate.json",
                OUTCOME_SEAL_REF,
                "test outcome seal",
            )


class FilesystemGuardTests(unittest.TestCase):
    def test_symbolic_link_component_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            directory_path = Path(directory)
            target = directory_path / "target"
            target.mkdir()
            link = directory_path / "link"
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaises(OrbitLedgerError):
                cli._require_no_symlink_components(
                    ROOT,
                    link / "record.json",
                    "synthetic linked record",
                )

    def test_strict_json_loader_rejects_duplicate_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"a":1,"a":2}\n', encoding="utf-8")
            with self.assertRaises(OrbitLedgerError):
                cli._load_strict_json(path)

    def test_canonical_writer_is_no_clobber(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "record.json"
            cli._write_new_canonical(path, {"status": "sealed"})
            self.assertEqual(
                path.read_text(encoding="utf-8"),
                canonical_json({"status": "sealed"}) + "\n",
            )
            with self.assertRaises(OrbitLedgerError):
                cli._write_new_canonical(path, {"status": "changed"})


class HistoryGuardTests(unittest.TestCase):
    def _git(self, root: Path, *arguments: str) -> None:
        subprocess.run(
            ["git", *arguments],
            cwd=root,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def test_precommit_verification_stage_and_result_commit_are_both_valid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._git(root, "init")
            self._git(root, "config", "user.name", "Exact Orbit Test")
            self._git(root, "config", "user.email", "exact-orbit@example.invalid")
            (root / "preregistered.txt").write_text("sealed\n", encoding="utf-8")
            self._git(root, "add", "preregistered.txt")
            self._git(root, "commit", "-m", "preregister")
            preregistration = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()

            open_path = root / OPEN_SEAL_REF
            open_path.parent.mkdir(parents=True)
            open_path.write_text("{}\n", encoding="utf-8")
            self._git(root, "add", OPEN_SEAL_REF)
            self._git(root, "commit", "-m", "open")
            cli._require_opening_history(root, preregistration, allow_result=False)
            cli._require_opening_history(root, preregistration, allow_result=True)

            result_path = root / cli.RESULT_PATH
            result_path.parent.mkdir(parents=True)
            result_path.write_text("{}\n", encoding="utf-8")
            self._git(root, "add", cli.RESULT_PATH.as_posix())
            self._git(root, "commit", "-m", "result")
            cli._require_opening_history(root, preregistration, allow_result=True)

            (root / "sitecustomize.py").write_text("raise RuntimeError\n", encoding="utf-8")
            self._git(root, "add", "sitecustomize.py")
            self._git(root, "commit", "-m", "unregistered executable")
            with self.assertRaises(OrbitLedgerError):
                cli._require_opening_history(root, preregistration, allow_result=True)

    def test_post_result_merge_commit_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._git(root, "init")
            self._git(root, "config", "user.name", "Exact Orbit Test")
            self._git(root, "config", "user.email", "exact-orbit@example.invalid")
            (root / "preregistered.txt").write_text("sealed\n", encoding="utf-8")
            self._git(root, "add", "preregistered.txt")
            self._git(root, "commit", "-m", "preregister")
            preregistration = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()

            open_path = root / OPEN_SEAL_REF
            open_path.parent.mkdir(parents=True)
            open_path.write_text("{}\n", encoding="utf-8")
            self._git(root, "add", OPEN_SEAL_REF)
            self._git(root, "commit", "-m", "open")
            result_path = root / cli.RESULT_PATH
            result_path.parent.mkdir(parents=True)
            result_path.write_text("{}\n", encoding="utf-8")
            self._git(root, "add", cli.RESULT_PATH.as_posix())
            self._git(root, "commit", "-m", "result")
            main_branch = subprocess.check_output(
                ["git", "branch", "--show-current"], cwd=root, text=True
            ).strip()

            self._git(root, "checkout", "-b", "documentation-side")
            (root / "README.md").write_text("side\n", encoding="utf-8")
            self._git(root, "add", "README.md")
            self._git(root, "commit", "-m", "side docs")
            self._git(root, "checkout", main_branch)
            (root / "SESSION_HANDOFF.md").write_text("main\n", encoding="utf-8")
            self._git(root, "add", "SESSION_HANDOFF.md")
            self._git(root, "commit", "-m", "main docs")
            self._git(root, "merge", "--no-ff", "documentation-side", "-m", "merge docs")

            with self.assertRaises(OrbitLedgerError):
                cli._require_opening_history(root, preregistration, allow_result=True)


if __name__ == "__main__":
    unittest.main()
