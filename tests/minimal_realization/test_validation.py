from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import validate_minimal_realization as validator  # noqa: E402


V01_NULL = ROOT / "specs/icp_minimal_realization/v0.1-draft/lower_shell_null.json"
V02_NULL = ROOT / "specs/icp_minimal_realization/v0.2-draft/lower_shell_null.json"
V02_DIR = ROOT / "specs/icp_minimal_realization/v0.2-draft"


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def valid_v02_one_law() -> dict:
    data = load(V02_NULL)
    data["candidate_id"] = "MIR-P2-L1-00"
    data["status"] = "development"
    data.pop("exclusion_reason")
    data["laws"] = [
        {
            "id": "L_00",
            "operator": "emit_one_if_signature",
            "signature": "00",
            "governed_degree": "event",
            "input_ports": ["self", "predecessor"],
            "duration_ticks": 1,
            "write_count": 1,
        }
    ]
    return data


def valid_v01_one_law() -> dict:
    data = load(V01_NULL)
    data["candidate_id"] = "MIR-V01-L1"
    data["status"] = "development"
    data.pop("exclusion_reason")
    data["laws"] = [
        {
            "id": "L1",
            "statement": "event[t+1] := event[t]",
            "governed_degree": "event",
            "local_input_signature": "event[t]",
            "next_state_effect": "copy event",
            "duration_ticks": 1,
            "branch_count": 0,
            "write_count": 1,
            "helper_references": [],
            "lookup_entries": 0,
            "uses_continuant": False,
            "atomicity_attestation": True,
        }
    ]
    return data


class CandidateValidationTests(unittest.TestCase):
    def test_v02_null_manifest_passes(self) -> None:
        data = validator.load_json(V02_NULL)
        self.assertEqual(validator.validate_candidate(data, V02_NULL), (2, 0))

    def test_v02_valid_nonempty_law_passes(self) -> None:
        self.assertEqual(
            validator.validate_candidate(valid_v02_one_law(), Path("valid-v02.json")),
            (2, 1),
        )

    def test_v01_valid_nonempty_law_no_longer_crashes(self) -> None:
        self.assertEqual(
            validator.validate_candidate(valid_v01_one_law(), Path("valid-v01.json")),
            (1, 1),
        )

    def test_v01_forbidden_word_rejects_cleanly(self) -> None:
        data = valid_v01_one_law()
        data["laws"][0]["next_state_effect"] = "copy AND toggle"
        with self.assertRaisesRegex(validator.ValidationError, "forbidden word"):
            validator.validate_candidate(data, Path("forbidden.json"))

    def test_extra_root_property_is_rejected(self) -> None:
        data = valid_v02_one_law()
        data["oracle"] = "hidden"
        with self.assertRaisesRegex(validator.ValidationError, "unexpected keys"):
            validator.validate_candidate(data, Path("extra.json"))

    def test_boolean_cannot_impersonate_integer(self) -> None:
        data = valid_v02_one_law()
        data["primitive_accounting"]["normalized_n_p"] = True
        with self.assertRaisesRegex(validator.ValidationError, "must be an integer"):
            validator.validate_candidate(data, Path("boolean.json"))

    def test_boolean_alphabet_is_rejected(self) -> None:
        data = valid_v02_one_law()
        data["primitives"][0]["alphabet"] = [False, True]
        with self.assertRaisesRegex(validator.ValidationError, "booleans are forbidden"):
            validator.validate_candidate(data, Path("alphabet.json"))

    def test_signature_id_mismatch_is_rejected(self) -> None:
        data = valid_v02_one_law()
        data["laws"][0]["id"] = "L_01"
        with self.assertRaisesRegex(validator.ValidationError, "id must be"):
            validator.validate_candidate(data, Path("law-id.json"))

    def test_candidate_id_must_encode_canonical_law_tuple(self) -> None:
        data = valid_v02_one_law()
        data["candidate_id"] = "MIR-WRONG-ID"
        with self.assertRaisesRegex(validator.ValidationError, "candidate_id must be"):
            validator.validate_candidate(data, Path("candidate-id.json"))

    def test_nonzero_candidate_cannot_claim_analytic_exclusion(self) -> None:
        data = valid_v02_one_law()
        data["status"] = "analytically_excluded"
        data["exclusion_reason"] = "unsupported assertion"
        with self.assertRaisesRegex(validator.ValidationError, "cannot be analytically_excluded"):
            validator.validate_candidate(data, Path("bad-exclusion.json"))

    def test_zero_row_candidate_must_be_analytically_excluded(self) -> None:
        data = load(V02_NULL)
        data["status"] = "development"
        data.pop("exclusion_reason")
        with self.assertRaisesRegex(validator.ValidationError, "must be analytically_excluded"):
            validator.validate_candidate(data, Path("live-null.json"))

    def test_duplicate_signature_is_rejected(self) -> None:
        data = valid_v02_one_law()
        data["laws"].append(copy.deepcopy(data["laws"][0]))
        with self.assertRaisesRegex(validator.ValidationError, "duplicate production signature"):
            validator.validate_candidate(data, Path("duplicate-law.json"))

    def test_noncanonical_law_order_is_rejected(self) -> None:
        data = valid_v02_one_law()
        law_00 = data["laws"][0]
        law_01 = copy.deepcopy(law_00)
        law_01["id"] = "L_01"
        law_01["signature"] = "01"
        data["laws"] = [law_01, law_00]
        with self.assertRaisesRegex(validator.ValidationError, "canonical signature order"):
            validator.validate_candidate(data, Path("order.json"))

    def test_frozen_candidate_requires_bound_hashes(self) -> None:
        data = valid_v02_one_law()
        data["status"] = "frozen"
        with self.assertRaisesRegex(validator.ValidationError, "unsealed substrate hash"):
            validator.validate_candidate(data, Path("frozen.json"))

    def test_bound_reference_digest_must_match_actual_design_file(self) -> None:
        data = valid_v02_one_law()
        data["substrate"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(validator.ValidationError, "digest does not match"):
            validator.validate_candidate(data, Path("stale-reference.json"))

    def test_duplicate_json_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicate.json"
            path.write_text('{"contract_version":"0.2-draft","contract_version":"0.2-draft"}', encoding="utf-8")
            with self.assertRaisesRegex(validator.ValidationError, "duplicate JSON key"):
                validator.load_json(path)

    def test_nonfinite_json_number_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nan.json"
            path.write_text('{"value":NaN}', encoding="utf-8")
            with self.assertRaisesRegex(validator.ValidationError, "non-finite JSON number"):
                validator.load_json(path)

    def test_all_v02_design_files_are_strict_json(self) -> None:
        for path in sorted(V02_DIR.glob("*.json")):
            with self.subTest(path=path.name):
                validator.load_json(path)

    def test_cli_reports_later_file_after_failure(self) -> None:
        command = [
            sys.executable,
            str(SCRIPTS / "validate_minimal_realization.py"),
            str(ROOT / "does-not-exist.json"),
            str(V02_NULL),
        ]
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL", result.stderr)
        self.assertIn("PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
