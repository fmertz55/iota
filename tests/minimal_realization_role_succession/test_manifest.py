from __future__ import annotations

import tempfile
import unittest
from collections import Counter
from pathlib import Path

from src.minimal_realization_role_succession.manifest import (
    ManifestError,
    candidate_sha256,
    compile_candidates,
    manifest_bytes,
    read_jsonl_bytes,
    validate_candidate_manifest,
    write_jsonl,
)
from src.minimal_realization_role_succession.protocol import (
    CANDIDATE_COUNT,
    GRAMMAR_ID,
    SHELL_SIZES,
)


class CandidateManifestTests(unittest.TestCase):
    def test_complete_family_is_canonical_without_evaluation(self) -> None:
        candidates = compile_candidates()
        validate_candidate_manifest(candidates)
        self.assertEqual(len(candidates), CANDIDATE_COUNT)
        self.assertEqual(
            tuple(Counter(len(candidate["laws"]) for candidate in candidates)[index] for index in range(9)),
            SHELL_SIZES,
        )
        self.assertEqual(candidates[0]["status"], "analytically_excluded")
        self.assertTrue(all(candidate["grammar_id"] == GRAMMAR_ID for candidate in candidates))
        self.assertEqual(len({candidate["candidate_id"] for candidate in candidates}), 256)
        self.assertTrue(all(len(candidate_sha256(candidate)) == 64 for candidate in candidates))

    def test_added_capacity_is_explicitly_accounted(self) -> None:
        accounting = compile_candidates()[1]["primitive_accounting"]
        self.assertEqual(accounting["normalized_n_p"], 2)
        self.assertEqual(accounting["relation_kind_count"], 1)
        self.assertEqual(accounting["relation_incidence_reads_per_site"], 2)
        self.assertEqual(accounting["event_reads_per_site"], 3)
        self.assertEqual(accounting["local_signature_fan_in"], 3)
        self.assertEqual(accounting["causal_traversal_directions"], 2)

    def test_canonical_jsonl_round_trip(self) -> None:
        candidates = compile_candidates()
        encoded = manifest_bytes(candidates)
        self.assertEqual(read_jsonl_bytes(encoded), candidates)

    def test_reader_rejects_duplicate_keys_and_noncanonical_bytes(self) -> None:
        with self.assertRaisesRegex(ManifestError, "duplicate JSON key"):
            read_jsonl_bytes(b'{"candidate_id":"a","candidate_id":"b"}\n')
        with self.assertRaisesRegex(ManifestError, "noncanonical"):
            read_jsonl_bytes(b'{"candidate_id": "a"}\n')

    def test_writer_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "candidates.jsonl"
            candidates = compile_candidates()
            write_jsonl(path, candidates)
            with self.assertRaisesRegex(ManifestError, "overwrite"):
                write_jsonl(path, candidates)


if __name__ == "__main__":
    unittest.main()
