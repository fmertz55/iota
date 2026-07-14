from __future__ import annotations

import unittest

from src.minimal_realization_role_succession_exact.local_impossibility import (
    analyze_local_impossibility,
)
from src.minimal_realization_role_succession_exact.verifier import (
    independent_local_certificate,
)


SIGNATURES = tuple(f"{value:03b}" for value in range(8))


class IndependentCertificateTests(unittest.TestCase):
    def test_anf_reexpression_matches_direct_certificate_for_complete_family(self) -> None:
        # Generic truth-table audit only: no parent result, candidate allocation,
        # or registered trajectory is opened here.
        for rule_number in range(256):
            rows = tuple(
                signature
                for signature in SIGNATURES
                if rule_number & (1 << int(signature, 2))
            )
            with self.subTest(rule_number=rule_number):
                self.assertEqual(
                    independent_local_certificate(rows),
                    analyze_local_impossibility(rows).to_dict(),
                )

    def test_unknown_row_is_rejected_independently(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown production row"):
            independent_local_certificate(("012",))


if __name__ == "__main__":
    unittest.main()
