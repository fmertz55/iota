from __future__ import annotations

import copy
import unittest

from src.minimal_realization_role_succession.manifest import compile_candidates
from src.minimal_realization_role_succession.protocol import (
    PARENT_EXACT_RESULT_REF,
    PARENT_EXACT_RESULT_SHA256,
)
from src.minimal_realization_role_succession.runner import (
    ExactOrbitOutcome,
    RoleSuccessionRunError,
    build_result_ledger,
    synthetic_candidate_evaluation,
    validate_result_ledger,
)


def recurrence(rows: tuple[str, ...]):
    return synthetic_candidate_evaluation(
        rows,
        ExactOrbitOutcome(
            "recurrence_excluded_on_fixed_orbit",
            None,
            33,
            None,
            None,
            None,
            None,
            (32, 33, 1, 0, 0),
            "a" * 64,
        ),
    )


def bindings() -> dict[str, dict[str, str]]:
    result = {
        name: {
            "path": f"synthetic/{name}.json",
            "sha256": f"{index:x}" * 64,
        }
        for index, name in enumerate(
            (
                "open_manifest_binding",
                "outcome_seal_binding",
                "candidate_manifest_binding",
                "result_schema_binding",
            ),
            start=1,
        )
    }
    result["parent_exact_result_binding"] = {
        "path": PARENT_EXACT_RESULT_REF,
        "sha256": PARENT_EXACT_RESULT_SHA256,
    }
    return result


class FrozenParentBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.candidates = compile_candidates()
        cls.ledger = build_result_ledger(
            candidates=cls.candidates,
            evaluator=lambda _candidate, rows: recurrence(rows),
            **bindings(),
        )

    def test_builder_rejects_wrong_parent_before_family_evaluation(self) -> None:
        wrong = bindings()
        wrong["parent_exact_result_binding"]["sha256"] = "f" * 64
        called = False

        def forbidden_evaluator(_candidate, rows):
            nonlocal called
            called = True
            return recurrence(rows)

        with self.assertRaisesRegex(RoleSuccessionRunError, "parent exact-result"):
            build_result_ledger(
                candidates=self.candidates,
                evaluator=forbidden_evaluator,
                **wrong,
            )
        self.assertFalse(called)

    def test_validator_rejects_wrong_parent_binding(self) -> None:
        malformed = copy.deepcopy(self.ledger)
        malformed["parent_exact_result"]["path"] = "synthetic/wrong-parent.json"
        with self.assertRaisesRegex(RoleSuccessionRunError, "parent exact-result"):
            validate_result_ledger(malformed, self.candidates)


if __name__ == "__main__":
    unittest.main()
