from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from src.minimal_realization.manifest import compile_candidates, read_jsonl, write_jsonl
from src.minimal_realization.spec import DESIGN_FILENAMES, SpecError, audit_design


ROOT = Path(__file__).resolve().parents[2]
SPEC_DIR = ROOT / "specs/icp_minimal_realization/v0.2-draft"
sys.path.insert(0, str(ROOT / "scripts"))

import validate_minimal_realization as validator  # noqa: E402


class SpecAuditTests(unittest.TestCase):
    def test_cross_file_design_audit_passes(self) -> None:
        audit = audit_design(SPEC_DIR)
        self.assertEqual(audit.contract_version, "0.2-draft")
        self.assertEqual(audit.status, "outcomes_sealed")
        self.assertEqual(set(audit.hashes), set(DESIGN_FILENAMES))
        self.assertTrue(all(len(digest) == 64 for digest in audit.hashes.values()))

    def test_compiled_candidate_space_is_complete_and_valid(self) -> None:
        candidates = compile_candidates(SPEC_DIR)
        self.assertEqual(len(candidates), 16)
        ids = []
        shell_sizes = [0, 0, 0, 0, 0]
        for candidate in candidates:
            ids.append(candidate["candidate_id"])
            shell_sizes[len(candidate["laws"])] += 1
            n_p, n_l = validator.validate_candidate(candidate, Path(candidate["candidate_id"]))
            self.assertEqual(n_p, 2)
            self.assertEqual(n_l, len(candidate["laws"]))
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(shell_sizes, [1, 4, 6, 4, 1])

    def test_compiled_candidates_bind_design_hashes(self) -> None:
        audit = audit_design(SPEC_DIR)
        for candidate in compile_candidates(SPEC_DIR):
            self.assertEqual(candidate["substrate"]["sha256"], audit.hashes["topology.json"])
            self.assertEqual(
                candidate["proto_object_detector"]["sha256"],
                audit.hashes["proto_object_detector.json"],
            )

    def test_design_audit_rejects_runtime_semantic_mutations(self) -> None:
        mutations = (
            ("candidate.schema.json", lambda data: data["properties"]["clock"]["properties"]["tick_unit"].update({"const": "wrong"})),
            ("operator_alphabet.json", lambda data: data["input_ports"].reverse()),
            ("topology.json", lambda data: data["loci"].update({"boundary": "open"})),
            ("causal_cone.json", lambda data: data["baseline"].update({"initial_event_count": 1})),
            ("proto_object_detector.json", lambda data: data["succession"].update({"confirmation_lag_ticks": 2})),
            ("result.schema.json", lambda data: data.update({"allOf": []})),
            ("search_plan.json", lambda data: data["enumeration"]["shell_sizes_by_n_l"].update({"1": 5})),
        )
        for filename, mutate in mutations:
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as tmp:
                copied = Path(tmp) / "spec"
                shutil.copytree(SPEC_DIR, copied)
                path = copied / filename
                data = json.loads(path.read_text(encoding="utf-8"))
                mutate(data)
                path.write_text(json.dumps(data, sort_keys=True) + "\n", encoding="utf-8")
                with self.assertRaises(SpecError):
                    audit_design(copied)

    def test_jsonl_reader_requires_exact_canonical_bytes(self) -> None:
        candidate = copy.deepcopy(compile_candidates(SPEC_DIR)[0])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "candidates.jsonl"
            write_jsonl(path, [candidate])
            self.assertEqual(read_jsonl(path), (candidate,))

            path.write_text(json.dumps(candidate, sort_keys=True) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not canonical JSONL"):
                read_jsonl(path)

            canonical = json.dumps(candidate, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
            path.write_bytes((canonical + "\r\n").encode("ascii"))
            with self.assertRaisesRegex(ValueError, "not canonical JSONL"):
                read_jsonl(path)

    def test_jsonl_reader_rejects_duplicate_keys_and_blank_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "candidates.jsonl"
            path.write_text('{"candidate_id":"first","candidate_id":"second"}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                read_jsonl(path)
            path.write_text("\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "blank lines"):
                read_jsonl(path)


if __name__ == "__main__":
    unittest.main()
