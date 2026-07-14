from __future__ import annotations

import inspect
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.minimal_realization_role_succession import cli
from src.minimal_realization_role_succession.protocol import RESULT_PATH_REF
from src.minimal_realization_role_succession.seal import (
    SealError,
    build_outcome_seal,
    write_canonical_json_once,
)


ROOT = Path(__file__).resolve().parents[2]


class OutcomeFreeCommandTests(unittest.TestCase):
    def test_parser_has_no_production_overrides(self) -> None:
        parser = cli.build_parser()
        run = parser.parse_args(["run-development"])
        self.assertIs(run.func, cli.command_run)
        with self.assertRaises(SystemExit):
            parser.parse_args(["run-development", "--candidate", "1"])
        with self.assertRaises(SystemExit):
            parser.parse_args(["run-development", "--output", "/tmp/result.json"])
        with self.assertRaises(SystemExit):
            parser.parse_args(["run-development", "--workers", "2"])

    def test_evaluator_import_occurs_after_open_manifest_gate(self) -> None:
        source = inspect.getsource(cli.command_run)
        self.assertLess(source.index("load_open_manifest"), source.index("from .runner import"))
        self.assertLess(source.index("load_open_manifest"), source.index("evaluate_candidate_exact_orbit"))

    def test_seal_builder_does_not_import_or_call_dynamics(self) -> None:
        source = inspect.getsource(build_outcome_seal)
        self.assertNotIn("evaluate_candidate", source)
        self.assertNotIn("run_development", source)
        self.assertNotIn("assess_layer", source)
        self.assertNotIn("step(", source)

    def test_atomic_json_writer_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "artifact.json"
            write_canonical_json_once(path, {"status": "synthetic"})
            self.assertEqual(path.read_text(encoding="ascii"), '{"status":"synthetic"}\n')
            with self.assertRaisesRegex(SealError, "overwrite"):
                write_canonical_json_once(path, {"status": "replacement"})

    def test_registered_result_path_is_fixed(self) -> None:
        self.assertEqual(
            RESULT_PATH_REF,
            "output/minimal_realization/MIR-ROLE-SUCCESSION-001/role_succession_results.json",
        )

    def test_open_rejects_descendant_head_after_freeze_tag(self) -> None:
        tagged = "a" * 40
        descendant = "b" * 40
        git_results = [
            subprocess.CompletedProcess([], 0, stdout=b"tag\n", stderr=b""),
            subprocess.CompletedProcess(
                [], 0, stdout=(tagged + "\n").encode("ascii"), stderr=b""
            ),
        ]
        with mock.patch.object(cli, "_git", side_effect=git_results), mock.patch.object(
            cli, "_git_head", return_value=descendant
        ):
            with self.assertRaisesRegex(cli.CommandError, "does not select current HEAD"):
                cli._require_freeze_tag_at_head(ROOT)

    def test_open_rejects_lightweight_freeze_tag(self) -> None:
        lightweight = subprocess.CompletedProcess(
            [], 0, stdout=b"commit\n", stderr=b""
        )
        with mock.patch.object(cli, "_git", return_value=lightweight):
            with self.assertRaisesRegex(cli.CommandError, "annotated freeze tag"):
                cli._freeze_tag_commit(ROOT)

    def test_outcome_free_design_audit_reads_no_result(self) -> None:
        source = inspect.getsource(cli.audit_outcome_free_design)
        self.assertNotIn("RESULT_PATH_REF", source)
        self.assertNotIn("load_open_manifest", source)

    def _provenance_patches(self):
        preregistration = "a" * 40
        opening = "b" * 40
        result = "c" * 40
        manifest = {"preregistration_commit": preregistration}
        return preregistration, opening, result, manifest

    def test_result_commit_provenance_accepts_exact_three_commit_chain(self) -> None:
        preregistration, opening, result, manifest = self._provenance_patches()
        with mock.patch.object(cli, "_require_clean_worktree"), mock.patch.object(
            cli, "_require_committed_bytes"
        ), mock.patch.object(cli, "_git_head", return_value=result), mock.patch.object(
            cli, "_commit_parent", side_effect=[opening, preregistration]
        ), mock.patch.object(
            cli,
            "_commit_changes",
            side_effect=[{cli.RESULT_PATH_REF}, {cli.OPEN_MANIFEST_REF}],
        ), mock.patch.object(
            cli, "_commit_has_path", return_value=False
        ), mock.patch.object(
            cli, "_freeze_tag_commit", return_value=preregistration
        ), mock.patch.object(
            cli, "_verify_seal_committed"
        ), mock.patch.object(
            cli, "_require_outcome_seal_introduced"
        ):
            cli._verify_result_commit_provenance(ROOT, manifest)

    def test_result_commit_provenance_rejects_extra_result_change(self) -> None:
        _, opening, result, manifest = self._provenance_patches()
        with mock.patch.object(cli, "_require_clean_worktree"), mock.patch.object(
            cli, "_require_committed_bytes"
        ), mock.patch.object(cli, "_git_head", return_value=result), mock.patch.object(
            cli, "_commit_parent", return_value=opening
        ), mock.patch.object(
            cli, "_commit_changes", return_value={cli.RESULT_PATH_REF, "extra.txt"}
        ):
            with self.assertRaisesRegex(cli.CommandError, "besides the result"):
                cli._verify_result_commit_provenance(ROOT, manifest)

    def test_result_commit_provenance_rejects_result_in_opening(self) -> None:
        _, opening, result, manifest = self._provenance_patches()
        with mock.patch.object(cli, "_require_clean_worktree"), mock.patch.object(
            cli, "_require_committed_bytes"
        ), mock.patch.object(cli, "_git_head", return_value=result), mock.patch.object(
            cli, "_commit_parent", return_value=opening
        ), mock.patch.object(
            cli, "_commit_changes", return_value={cli.RESULT_PATH_REF}
        ), mock.patch.object(
            cli, "_commit_has_path", return_value=True
        ):
            with self.assertRaisesRegex(cli.CommandError, "already existed"):
                cli._verify_result_commit_provenance(ROOT, manifest)

    def test_result_commit_provenance_rejects_open_manifest_in_freeze(self) -> None:
        preregistration, opening, result, manifest = self._provenance_patches()
        with mock.patch.object(cli, "_require_clean_worktree"), mock.patch.object(
            cli, "_require_committed_bytes"
        ), mock.patch.object(cli, "_git_head", return_value=result), mock.patch.object(
            cli, "_commit_parent", return_value=opening
        ), mock.patch.object(
            cli, "_commit_changes", return_value={cli.RESULT_PATH_REF}
        ), mock.patch.object(
            cli, "_commit_has_path", side_effect=[False, True]
        ):
            with self.assertRaisesRegex(cli.CommandError, "freeze commit"):
                cli._verify_result_commit_provenance(ROOT, manifest)

    def test_result_commit_provenance_rejects_wrong_opening_or_tag(self) -> None:
        preregistration, opening, result, manifest = self._provenance_patches()
        base_patches = (
            mock.patch.object(cli, "_require_clean_worktree"),
            mock.patch.object(cli, "_require_committed_bytes"),
            mock.patch.object(cli, "_git_head", return_value=result),
            mock.patch.object(cli, "_commit_has_path", return_value=False),
        )
        with base_patches[0], base_patches[1], base_patches[2], base_patches[3], mock.patch.object(
            cli, "_commit_parent", side_effect=[opening, preregistration]
        ), mock.patch.object(
            cli,
            "_commit_changes",
            side_effect=[{cli.RESULT_PATH_REF}, {cli.OPEN_MANIFEST_REF, "extra.txt"}],
        ):
            with self.assertRaisesRegex(cli.CommandError, "besides the open manifest"):
                cli._verify_result_commit_provenance(ROOT, manifest)

        with mock.patch.object(cli, "_require_clean_worktree"), mock.patch.object(
            cli, "_require_committed_bytes"
        ), mock.patch.object(cli, "_git_head", return_value=result), mock.patch.object(
            cli, "_commit_parent", side_effect=[opening, "d" * 40]
        ), mock.patch.object(
            cli,
            "_commit_changes",
            side_effect=[{cli.RESULT_PATH_REF}, {cli.OPEN_MANIFEST_REF}],
        ), mock.patch.object(
            cli, "_commit_has_path", return_value=False
        ):
            with self.assertRaisesRegex(cli.CommandError, "direct child"):
                cli._verify_result_commit_provenance(ROOT, manifest)

        with mock.patch.object(cli, "_require_clean_worktree"), mock.patch.object(
            cli, "_require_committed_bytes"
        ), mock.patch.object(cli, "_git_head", return_value=result), mock.patch.object(
            cli, "_commit_parent", side_effect=[opening, preregistration]
        ), mock.patch.object(
            cli,
            "_commit_changes",
            side_effect=[{cli.RESULT_PATH_REF}, {cli.OPEN_MANIFEST_REF}],
        ), mock.patch.object(
            cli, "_commit_has_path", return_value=False
        ), mock.patch.object(
            cli, "_freeze_tag_commit", return_value="e" * 40
        ):
            with self.assertRaisesRegex(cli.CommandError, "freeze tag"):
                cli._verify_result_commit_provenance(ROOT, manifest)

    def test_freeze_commit_must_introduce_outcome_seal(self) -> None:
        freeze = "a" * 40
        parent = "b" * 40
        added = subprocess.CompletedProcess(
            [],
            0,
            stdout=f"A\t{cli.OUTCOME_SEAL_REF}\n".encode("utf-8"),
            stderr=b"",
        )
        with mock.patch.object(cli, "_commit_parent", return_value=parent), mock.patch.object(
            cli, "_commit_has_path", side_effect=[False, True]
        ), mock.patch.object(cli, "_git", return_value=added):
            cli._require_outcome_seal_introduced(ROOT, freeze)

        modified = subprocess.CompletedProcess(
            [],
            0,
            stdout=f"M\t{cli.OUTCOME_SEAL_REF}\n".encode("utf-8"),
            stderr=b"",
        )
        with mock.patch.object(cli, "_commit_parent", return_value=parent), mock.patch.object(
            cli, "_commit_has_path", return_value=False
        ), mock.patch.object(cli, "_git", return_value=modified):
            with self.assertRaisesRegex(cli.CommandError, "commit that added"):
                cli._require_outcome_seal_introduced(ROOT, freeze)

        with mock.patch.object(cli, "_commit_parent", return_value=parent), mock.patch.object(
            cli, "_commit_has_path", return_value=True
        ):
            with self.assertRaisesRegex(cli.CommandError, "already existed"):
                cli._require_outcome_seal_introduced(ROOT, freeze)


if __name__ == "__main__":
    unittest.main()
