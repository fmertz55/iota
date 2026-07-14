from __future__ import annotations

import unittest
from pathlib import Path

from src.minimal_realization_role_succession_exact.manifest import (
    compile_continuation_candidates,
    load_and_validate_parent,
    manifest_bytes,
    parent_censor_predicate,
)
from src.minimal_realization_role_succession_exact.protocol import (
    CANDIDATE_MANIFEST_REF,
    PARENT_RESULT_REF,
    PARENT_RESULT_SHA256,
)
from src.minimal_realization_role_succession.manifest import sha256_file


ROOT = Path(__file__).resolve().parents[2]


class ParentDerivedManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parent = load_and_validate_parent(ROOT)
        cls.records = compile_continuation_candidates(cls.parent)

    def test_parent_result_bytes_match_frozen_binding(self) -> None:
        self.assertEqual(sha256_file(ROOT / PARENT_RESULT_REF), PARENT_RESULT_SHA256)

    def test_predicate_selects_exactly_ten_in_parent_order(self) -> None:
        selected_indices = tuple(
            index
            for index, record in enumerate(self.parent["candidate_results"])
            if parent_censor_predicate(record)
        )
        self.assertEqual(selected_indices, (97, 100, 109, 114, 115, 119, 122, 127, 128, 133))
        self.assertEqual(
            tuple(record["parent_candidate_index"] for record in self.records),
            selected_indices,
        )

    def test_records_bind_parent_result_records_and_prefixes(self) -> None:
        for record in self.records:
            parent = self.parent["candidate_results"][record["parent_candidate_index"]]
            self.assertEqual(record["candidate_id"], parent["candidate_id"])
            self.assertEqual(record["candidate_sha256"], parent["candidate_sha256"])
            self.assertEqual(record["production_rows"], parent["production_rows"])
            self.assertEqual(
                record["parent_prefix_trace_sha256"],
                parent["trace_sha256"],
            )
            self.assertEqual(record["parent_boundary_layer"], 1_000_000)

    def test_manifest_encoding_is_ascii_canonical_jsonl(self) -> None:
        data = manifest_bytes(self.records)
        self.assertTrue(data.endswith(b"\n"))
        self.assertEqual(data.decode("ascii").count("\n"), 10)

    def test_registered_manifest_is_exactly_the_parent_derivation(self) -> None:
        self.assertEqual(
            (ROOT / CANDIDATE_MANIFEST_REF).read_bytes(),
            manifest_bytes(self.records),
        )


if __name__ == "__main__":
    unittest.main()
