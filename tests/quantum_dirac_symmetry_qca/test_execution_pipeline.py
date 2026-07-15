from __future__ import annotations

import inspect
import unittest
from fractions import Fraction
from pathlib import Path

from flint import acb_mat, arb
from mpmath import mp

from src.quantum_dirac_symmetry_qca import independent_verifier, ledger
from src.quantum_dirac_symmetry_qca.authorization import (
    RegisteredEvaluationPermit,
    RegisteredVerificationPermit,
)
from src.quantum_dirac_symmetry_qca.independent_verifier import _dft
from src.quantum_dirac_symmetry_qca.independent_registered import (
    spectral_norm_from_gram,
)
from src.quantum_dirac_symmetry_qca.production import (
    _certified_direct_step_adjoint,
    ball_precision,
    production_candidate_fixture,
)
from src.quantum_dirac_symmetry_qca.runner import build_stage_ledger
from src.quantum_dirac_symmetry_qca.spec import SymmetryQCASpecError


ROOT = Path(__file__).resolve().parents[2]


class OutcomeFreeExecutionPipelineTests(unittest.TestCase):
    def test_independent_norm_accepts_a_complex_hermitian_gram_matrix(self) -> None:
        with mp.workdps(120):
            value = mp.matrix([[1, 1j], [0, 2]])
            expected = mp.sqrt(3 + mp.sqrt(5))
            self.assertLess(
                abs(spectral_norm_from_gram(value) - expected),
                mp.mpf("1e-105"),
            )

    def test_disclosed_n6_step_has_a_certified_adjoint(self) -> None:
        with ball_precision():
            state = acb_mat(12, 2)
            state[0, 0] = 1
            state[5, 1] = arb(2) / 7
            evolved = production_candidate_fixture(
                state, n_sites=6, mu=Fraction(2, 9)
            )
            recovered = _certified_direct_step_adjoint(
                evolved, n_sites=6, mu=Fraction(2, 9)
            )
            maximum = max(
                float(abs(recovered[row, column] - state[row, column]).upper())
                for row in range(12)
                for column in range(2)
            )
            self.assertLess(maximum, 1e-70)

    def test_independent_mixed_radix_dft_recovers_disclosed_n10_mode(self) -> None:
        with mp.workdps(120):
            values = [mp.exp(2j * mp.pi * 3 * site / 10) for site in range(10)]
            transformed = _dft(values)
            self.assertLess(abs(transformed[3] - 10), mp.mpf("1e-110"))
            self.assertLess(
                max(abs(value) for index, value in enumerate(transformed) if index != 3),
                mp.mpf("1e-110"),
            )

    def test_registered_runner_rejects_a_forged_permit_before_evaluation(self) -> None:
        forged = RegisteredEvaluationPermit(
            stage="development",
            root=ROOT,
            freeze_commit="0" * 40,
            opening_commit="1" * 40,
            opening_sha256="2" * 64,
            _nonce=object(),
        )
        with self.assertRaises(SymmetryQCASpecError):
            build_stage_ledger(forged, bindings={})

    def test_full_verifier_rejects_a_forged_checkpoint_permit_first(self) -> None:
        forged = RegisteredVerificationPermit(
            stage="development",
            root=ROOT,
            freeze_commit="0" * 40,
            opening_commit="1" * 40,
            result_commit="2" * 40,
            opening_sha256="3" * 64,
            result_sha256="4" * 64,
            _nonce=object(),
        )
        with self.assertRaises(SymmetryQCASpecError):
            independent_verifier.verify_ledger_independently(forged, {})

    def test_independent_verifier_imports_no_primary_constructor(self) -> None:
        source = inspect.getsource(independent_verifier)
        self.assertNotIn("from .production", source)
        self.assertNotIn("from .runner", source)
        self.assertNotIn("from .reducers", source)
        self.assertNotIn("from .states import", source)
        ledger_source = inspect.getsource(ledger)
        self.assertNotIn("from .production", ledger_source)
        self.assertNotIn("from .reducers", ledger_source)


if __name__ == "__main__":
    unittest.main()
