from __future__ import annotations

import unittest
from decimal import Decimal
import json
from pathlib import Path

from src.quantum_dirac_symmetry_qca.threshold_certificate import (
    ThresholdCertificateError,
    build_threshold_certificate,
)


class OutwardThresholdCertificateTests(unittest.TestCase):
    def test_absolute_envelopes_fit_every_proposed_gate(self) -> None:
        certificate = build_threshold_certificate()
        self.assertFalse(certificate["registered_propagation_performed"])
        self.assertIn("outcomes remain uncomputed", certificate["scope"])
        for record in certificate["refinements"].values():
            self.assertTrue(record["direct_absolute_gate_certified"])
            self.assertTrue(record["potential_absolute_gate_certified"])
            self.assertLess(
                Decimal(record["direct"]["certified_distance_envelope"]),
                Decimal(record["direct_threshold"]),
            )
            for potential in ("potential_h2", "potential_h3"):
                self.assertLess(
                    Decimal(record[potential]["certified_distance_envelope"]),
                    Decimal(record["potential_threshold"]),
                )
                self.assertLessEqual(
                    Decimal(record[potential]["pi_probability_tail"]),
                    Decimal("1e-24"),
                )

    def test_certificate_rejects_insufficient_precision(self) -> None:
        with self.assertRaises(ThresholdCertificateError):
            build_threshold_certificate(bits=128)

    def test_committed_short_uppers_enclose_generated_balls(self) -> None:
        root = Path(__file__).resolve().parents[2]
        committed = json.loads(
            (
                root
                / "specs/icp_quantum_dirac_symmetry_qca/v0.1-draft/threshold_certificate.json"
            ).read_text(encoding="utf-8")
        )
        generated = build_threshold_certificate()
        for record in committed["refinements"]:
            actual = generated["refinements"][str(record["n_sites"])]
            self.assertGreaterEqual(
                Decimal(record["direct_distance_envelope_upper"]),
                Decimal(actual["direct"]["certified_distance_envelope"]),
            )
            self.assertGreaterEqual(
                Decimal(record["potential_h2_distance_envelope_upper"]),
                Decimal(actual["potential_h2"]["certified_distance_envelope"]),
            )
            self.assertGreaterEqual(
                Decimal(record["potential_h3_distance_envelope_upper"]),
                Decimal(actual["potential_h3"]["certified_distance_envelope"]),
            )


if __name__ == "__main__":
    unittest.main()
