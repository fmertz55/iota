from __future__ import annotations

import copy
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import src.minimal_realization.runner as runner_module
from src.minimal_realization.detector import DetectorResult
from src.minimal_realization.cli import (
    DEVELOPMENT_OPEN_REF,
    RESULT_PATH,
    _require_opening_history,
)
from src.minimal_realization.manifest import compile_candidates
from src.minimal_realization.runner import (
    DevelopmentRunError,
    build_result_ledger,
    evaluate_candidate,
    _exact_translation_evaluator,
    run_bounded_development_search,
    validate_result_ledger,
    write_result_ledger,
)
from src.minimal_realization.spec import SpecError, canonical_json


ROOT = Path(__file__).resolve().parents[2]
SPEC_DIR = ROOT / "specs/icp_minimal_realization/v0.2-draft"


def passing(origin: int, t_proto: int) -> DetectorResult:
    return DetectorResult(
        True,
        t_proto,
        (origin + 1) % 64,
        (origin + 2) % 64,
        0,
        1,
    )


def censored() -> DetectorResult:
    return DetectorResult(False, None, None, None, None, None)


def git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


class DevelopmentRunnerTests(unittest.TestCase):
    """Orchestration tests use synthetic outcomes and never run registered dynamics."""

    def setUp(self) -> None:
        self.candidates = compile_candidates(SPEC_DIR)

    def test_shell_complete_stop_and_all_co_best_winners(self) -> None:
        calls: list[tuple[tuple[str, ...], int]] = []
        co_best_rows = {("00", "01"), ("00", "10")}

        def fake_evaluator(rows: tuple[str, ...], origin: int) -> DetectorResult:
            calls.append((rows, origin))
            if rows in co_best_rows:
                return passing(origin, 3)
            if len(rows) == 2:
                return passing(origin, 4)
            return censored()

        search = run_bounded_development_search(self.candidates, fake_evaluator)
        self.assertEqual(search["evaluated_shells"], [1, 2])
        self.assertEqual(search["first_passing_shell"], 2)
        self.assertEqual(search["stopping_reason"], "first_shell_with_pass_by_H16_completed")
        expected_winners = [
            candidate["candidate_id"]
            for candidate in self.candidates
            if tuple(law["signature"] for law in candidate["laws"]) in co_best_rows
        ]
        self.assertEqual(search["bounded_winner_candidate_ids"], expected_winners)
        self.assertEqual(len(search["candidate_results"]), 16)
        self.assertEqual(len(calls), (4 + 6) * 48)
        self.assertEqual({origin for _, origin in calls}, set(range(48)))
        self.assertFalse(any(origin >= 48 for _, origin in calls))
        later = [
            result
            for result in search["candidate_results"]
            if result["atomic_n_l"] > 2
        ]
        self.assertTrue(later)
        self.assertTrue(
            all(
                result["evaluation_status"]
                == "not_evaluated_after_first_passing_shell"
                for result in later
            )
        )

    def test_high_level_search_api_requires_explicit_evaluator(self) -> None:
        with self.assertRaises(TypeError):
            run_bounded_development_search(self.candidates)  # type: ignore[call-arg]

    def test_opening_history_allows_only_open_then_result_then_records(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            git(root, "init", "-q")
            git(root, "config", "user.name", "Test")
            git(root, "config", "user.email", "test@example.invalid")
            (root / "README.md").write_text("pre\n", encoding="utf-8")
            git(root, "add", "README.md")
            git(root, "commit", "-q", "-m", "preregister")
            preregistration = git(root, "rev-parse", "HEAD")

            open_path = root / DEVELOPMENT_OPEN_REF
            open_path.parent.mkdir(parents=True)
            open_path.write_text("{}\n", encoding="utf-8")
            git(root, "add", DEVELOPMENT_OPEN_REF)
            git(root, "commit", "-q", "-m", "open")
            _require_opening_history(
                root,
                preregistration,
                allow_committed_result=False,
            )

            result_path = root / RESULT_PATH
            result_path.parent.mkdir(parents=True)
            result_path.write_text("{}\n", encoding="utf-8")
            git(root, "add", RESULT_PATH.as_posix())
            git(root, "commit", "-q", "-m", "result")
            _require_opening_history(
                root,
                preregistration,
                allow_committed_result=True,
            )

            (root / "README.md").write_text("post\n", encoding="utf-8")
            git(root, "add", "README.md")
            git(root, "commit", "-q", "-m", "record")
            _require_opening_history(
                root,
                preregistration,
                allow_committed_result=True,
            )

    def test_opening_history_rejects_transient_code_injection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            git(root, "init", "-q")
            git(root, "config", "user.name", "Test")
            git(root, "config", "user.email", "test@example.invalid")
            (root / "README.md").write_text("pre\n", encoding="utf-8")
            git(root, "add", "README.md")
            git(root, "commit", "-q", "-m", "preregister")
            preregistration = git(root, "rev-parse", "HEAD")

            open_path = root / DEVELOPMENT_OPEN_REF
            open_path.parent.mkdir(parents=True)
            open_path.write_text("{}\n", encoding="utf-8")
            git(root, "add", DEVELOPMENT_OPEN_REF)
            git(root, "commit", "-q", "-m", "open")
            (root / "sitecustomize.py").write_text("raise SystemExit\n", encoding="utf-8")
            git(root, "add", "sitecustomize.py")
            git(root, "commit", "-q", "-m", "inject")
            git(root, "rm", "-q", "sitecustomize.py")
            git(root, "commit", "-q", "-m", "remove")

            with self.assertRaisesRegex(SpecError, "second post-preregistration"):
                _require_opening_history(
                    root,
                    preregistration,
                    allow_committed_result=True,
                )

    def test_detector_result_equivariance_mismatch_is_fatal(self) -> None:
        candidate = next(item for item in self.candidates if len(item["laws"]) == 1)

        def mismatched(rows: tuple[str, ...], origin: int) -> DetectorResult:
            del rows
            if origin == 47:
                return DetectorResult(True, 3, 0, 1, 0, 1)
            return passing(origin, 3)

        with self.assertRaisesRegex(DevelopmentRunError, "not exactly equivariant"):
            evaluate_candidate(candidate, mismatched)

    def test_production_evaluator_rejects_trajectory_mismatch_without_dynamics(self) -> None:
        reference = tuple(0 for _ in range(19))
        baseline = tuple(0 for _ in range(19))
        mismatched_seeded = tuple([0] * 18 + [1])
        with patch.object(
            runner_module,
            "_reference_trajectories",
            return_value=(reference, baseline),
        ):
            with patch.object(
                runner_module,
                "run_trajectory",
                return_value=mismatched_seeded,
            ):
                with self.assertRaisesRegex(DevelopmentRunError, "trajectory violates"):
                    _exact_translation_evaluator(("01",), 1)

    def _all_censored_ledger(self, open_path: Path) -> dict[str, object]:
        open_path.write_text("{}\n", encoding="utf-8")
        open_seal = {
            "parent_outcome_seal": {"path": "parent.json", "sha256": "0" * 64},
            "candidate_manifest": {"path": "candidates.jsonl", "sha256": "1" * 64},
        }
        return build_result_ledger(
            root=ROOT,
            open_seal_path=open_path,
            open_seal=open_seal,
            candidates=self.candidates,
            evaluator=lambda rows, origin: censored(),
        )

    def test_ledger_rejects_partial_or_held_out_translation_allocation(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            ledger = self._all_censored_ledger(Path(temporary) / "open.json")
        validate_result_ledger(ledger, self.candidates)

        partial = copy.deepcopy(ledger)
        evaluated = partial["candidate_results"][1]
        evaluated["translations_evaluated"] = 47
        with self.assertRaisesRegex(DevelopmentRunError, "partial"):
            validate_result_ledger(partial, self.candidates)

        held_out = copy.deepcopy(ledger)
        evaluated = held_out["candidate_results"][1]
        evaluated["translations"][-1]["translation_offset"] = 48
        with self.assertRaises(DevelopmentRunError):
            validate_result_ledger(held_out, self.candidates)

    def test_ledger_rejects_incomplete_or_malformed_shell_allocation(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            ledger = self._all_censored_ledger(Path(temporary) / "open.json")

        skipped = copy.deepcopy(ledger)
        candidate = next(
            result for result in skipped["candidate_results"] if result["atomic_n_l"] == 1
        )
        candidate.update(
            evaluation_status="not_evaluated_after_first_passing_shell",
            pass_by_H16=None,
            t_proto=None,
            translation_equivariance_exact=None,
            translations_evaluated=0,
            translations=[],
        )
        with self.assertRaisesRegex(DevelopmentRunError, "evaluated shell"):
            validate_result_ledger(skipped, self.candidates)

        malformed_sizes = copy.deepcopy(ledger)
        candidate = next(
            result
            for result in malformed_sizes["candidate_results"]
            if result["atomic_n_l"] == 1
        )
        candidate["atomic_n_l"] = 2
        with self.assertRaisesRegex(
            DevelopmentRunError,
            "canonical manifest order|shell sizes",
        ):
            validate_result_ledger(malformed_sizes, self.candidates)

    def test_ledger_candidate_bindings_must_match_canonical_manifest(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            ledger = self._all_censored_ledger(Path(temporary) / "open.json")

        forged_id = copy.deepcopy(ledger)
        forged_id["candidate_results"][1]["candidate_id"] = "FORGED"
        with self.assertRaisesRegex(DevelopmentRunError, "canonical manifest order"):
            validate_result_ledger(forged_id, self.candidates)

        forged_hash = copy.deepcopy(ledger)
        forged_hash["candidate_results"][1]["candidate_sha256"] = "f" * 64
        with self.assertRaisesRegex(DevelopmentRunError, "canonical manifest order"):
            validate_result_ledger(forged_hash, self.candidates)

    def test_ledger_rejects_evaluation_after_first_passing_shell(self) -> None:
        def shell_one_passes(rows: tuple[str, ...], origin: int) -> DetectorResult:
            return passing(origin, 3) if len(rows) == 1 else censored()

        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            directory = Path(temporary)
            open_path = directory / "open.json"
            open_path.write_text("{}\n", encoding="utf-8")
            open_seal = {
                "parent_outcome_seal": {"path": "parent.json", "sha256": "0" * 64},
                "candidate_manifest": {"path": "candidates.jsonl", "sha256": "1" * 64},
            }
            stopped = build_result_ledger(
                root=ROOT,
                open_seal_path=open_path,
                open_seal=open_seal,
                candidates=self.candidates,
                evaluator=shell_one_passes,
            )
            all_censored = build_result_ledger(
                root=ROOT,
                open_seal_path=open_path,
                open_seal=open_seal,
                candidates=self.candidates,
                evaluator=lambda rows, origin: censored(),
            )

        evaluated_later = copy.deepcopy(stopped)
        later_index = next(
            index
            for index, result in enumerate(evaluated_later["candidate_results"])
            if result["atomic_n_l"] == 2
        )
        evaluated_later["candidate_results"][later_index] = copy.deepcopy(
            all_censored["candidate_results"][later_index]
        )
        with self.assertRaisesRegex(DevelopmentRunError, "after the first passing shell"):
            validate_result_ledger(evaluated_later, self.candidates)

    def test_result_write_is_canonical_and_no_clobber(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            directory = Path(temporary)
            ledger = self._all_censored_ledger(directory / "open.json")
            output = directory / "result.json"
            write_result_ledger(output, ledger, self.candidates)
            self.assertEqual(
                output.read_text(encoding="utf-8"),
                canonical_json(ledger) + "\n",
            )
            with self.assertRaisesRegex(DevelopmentRunError, "refusing to overwrite"):
                write_result_ledger(output, ledger, self.candidates)


if __name__ == "__main__":
    unittest.main()
