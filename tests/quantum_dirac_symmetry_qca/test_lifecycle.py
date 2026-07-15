from __future__ import annotations

import unittest
from pathlib import Path

from src.quantum_dirac_symmetry_qca.authorization import (
    RegisteredEvaluationPermit,
    authorization_status,
    validate_registered_permit,
)
from src.quantum_dirac_symmetry_qca.cli import build_parser
from src.quantum_dirac_symmetry_qca.protocol import OUTCOME_SEAL_REF
from src.quantum_dirac_symmetry_qca.spec import SymmetryQCASpecError
from src.quantum_dirac_symmetry_qca.states import build_certified_state
from src.quantum_dirac_symmetry_qca.independent_states import build_independent_state


ROOT = Path(__file__).resolve().parents[2]


class DisabledLifecycleTests(unittest.TestCase):
    def test_current_checkout_has_no_authorization_or_seal(self) -> None:
        status = authorization_status(ROOT)
        self.assertFalse(status["registered_outcomes_authorized"])
        self.assertFalse(status["evaluation_permit_issued"])
        self.assertFalse((ROOT / OUTCOME_SEAL_REF).exists())

    def test_permit_dataclass_cannot_be_forged(self) -> None:
        forged = RegisteredEvaluationPermit(
            stage="development",
            root=ROOT,
            freeze_commit="0" * 40,
            opening_commit="1" * 40,
            opening_sha256="2" * 64,
            _nonce=object(),
        )
        with self.assertRaises(SymmetryQCASpecError):
            validate_registered_permit(forged)
        with self.assertRaises(SymmetryQCASpecError):
            build_certified_state(
                forged,
                state_id="DEV-DIRECT-STATE-POS",
                initial_mass=__import__("fractions").Fraction(1, 3),
            )
        with self.assertRaises(SymmetryQCASpecError):
            build_independent_state(
                forged,
                state_id="DEV-DIRECT-STATE-POS",
                initial_mass=__import__("fractions").Fraction(1, 3),
            )

    def test_cli_has_no_registered_run_command(self) -> None:
        commands = set(build_parser()._subparsers._group_actions[0].choices)
        self.assertEqual(
            commands,
            {
                "audit-design",
                "validate-manifests",
                "preview-disabled-seal",
                "authorization-status",
                "seal-outcomes",
                "verify-seal",
                "open-stage",
                "authorize-stage",
            },
        )
        self.assertNotIn("run-stage", commands)


if __name__ == "__main__":
    unittest.main()
