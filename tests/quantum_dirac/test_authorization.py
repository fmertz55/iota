from __future__ import annotations

import unittest
from pathlib import Path

from src.quantum_dirac.authorization import (
    RegisteredEvaluationPermit,
    RegisteredVerificationPermit,
    issue_registered_permit,
    validate_verification_permit,
)
from src.quantum_dirac.protocol import OUTCOME_SEAL_REF
from src.quantum_dirac.production import RegisteredCandidateEngine, RegisteredTargetSolver
from src.quantum_dirac.certified import CertifiedRegisteredEvaluator
from src.quantum_dirac.independent_registered import IndependentRegisteredEvaluator
from src.quantum_dirac.spec import QuantumDiracSpecError


ROOT = Path(__file__).resolve().parents[2]


class RegisteredAuthorizationTests(unittest.TestCase):
    def test_current_draft_cannot_issue_development_or_confirmation_permit(self) -> None:
        if (ROOT / OUTCOME_SEAL_REF).exists():
            self.skipTest("repository has advanced beyond the pre-freeze checkpoint")
        for stage in ("development", "confirmation"):
            with self.subTest(stage=stage):
                with self.assertRaises(QuantumDiracSpecError):
                    issue_registered_permit(stage=stage, root=ROOT)

    def test_forged_permit_cannot_construct_registered_engines(self) -> None:
        forged = RegisteredEvaluationPermit(
            stage="development",
            root=ROOT,
            freeze_commit="0" * 40,
            opening_commit="0" * 40,
            opening_sha256="0" * 64,
            _nonce=object(),
        )
        with self.assertRaises(QuantumDiracSpecError):
            RegisteredCandidateEngine(forged, n_sites=256)
        with self.assertRaises(QuantumDiracSpecError):
            RegisteredTargetSolver(forged, n_sites=256)
        with self.assertRaises(QuantumDiracSpecError):
            CertifiedRegisteredEvaluator(forged, n_sites=256)
        with self.assertRaises(QuantumDiracSpecError):
            IndependentRegisteredEvaluator(forged, n_sites=256)

    def test_forged_verification_permit_is_rejected(self) -> None:
        forged = RegisteredVerificationPermit(
            stage="development",
            root=ROOT,
            freeze_commit="0" * 40,
            opening_commit="0" * 40,
            result_commit="0" * 40,
            opening_sha256="0" * 64,
            result_sha256="0" * 64,
            _nonce=object(),
        )
        with self.assertRaises(QuantumDiracSpecError):
            validate_verification_permit(forged)


if __name__ == "__main__":
    unittest.main()
