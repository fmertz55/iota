from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.quantum_dirac.ledger import LEDGER_KEYS, validate_result_ledger
from src.quantum_dirac.spec import (
    QuantumDiracSpecError,
    load_json,
    write_canonical_json_once,
)


ROOT = Path(__file__).resolve().parents[2]


class LedgerContractTests(unittest.TestCase):
    def test_result_schema_root_matches_exact_ledger_shape(self) -> None:
        schema = load_json(
            ROOT
            / "specs/icp_quantum_dirac_role_recovery/v0.1-draft/result.schema.json"
        )
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), LEDGER_KEYS)
        self.assertEqual(set(schema["properties"]), LEDGER_KEYS)

    def test_result_validator_rejects_partial_ledger(self) -> None:
        with self.assertRaises(QuantumDiracSpecError):
            validate_result_ledger({"protocol_version": "0.1-draft"})

    def test_atomic_writer_never_clobbers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "ledger.json"
            write_canonical_json_once(path, {"status": "synthetic"})
            with self.assertRaises(QuantumDiracSpecError):
                write_canonical_json_once(path, {"status": "replacement"})


if __name__ == "__main__":
    unittest.main()
