from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from src.minimal_realization_role_succession.manifest import (
    build_candidate,
    candidate_sha256,
)
from src.minimal_realization_role_succession.protocol import SEARCH_ID
from src.minimal_realization_role_succession import runner, verifier


ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_SPEC = (
    ROOT
    / "specs"
    / "icp_minimal_realization_role_succession"
    / "v0.1-draft"
    / "protocol.json"
)


class TraceEncodingTests(unittest.TestCase):
    def test_trace_prefix_domain_and_joint_state_bytes_are_exact(self) -> None:
        candidate = build_candidate(("001",))
        domain = (
            f"{SEARCH_ID}\0{candidate['candidate_id']}\0{candidate_sha256(candidate)}"
        ).encode("ascii")
        prefix = b"IOTA-MIR-ROLE-SUCCESSION-TRACE-V1\x00"
        self.assertEqual(runner.TRACE_PREFIX, prefix)
        self.assertEqual(verifier.TRACE_PREFIX, prefix)
        self.assertEqual(runner.candidate_trace_domain(candidate), domain)
        self.assertEqual(verifier._trace_domain(candidate), domain)

        seeded = (1 << 2) | (1 << 61)
        comparator = (1 << 7) | (1 << 40)
        expected_bytes = (
            prefix
            + len(domain).to_bytes(8, "big")
            + domain
            + (1).to_bytes(8, "big")
            + b"0"
            + seeded.to_bytes(8, "big")
            + comparator.to_bytes(8, "big")
        )
        expected = hashlib.sha256(expected_bytes).hexdigest()

        production_digest = runner._new_trace_digest(domain)
        runner._update_trace_digest(
            production_digest,
            0,
            (seeded, comparator),
            cycle_size=64,
        )
        independent_digest = verifier._new_digest(candidate)
        verifier._update_digest(independent_digest, 0, seeded, comparator)
        self.assertEqual(production_digest.hexdigest(), expected)
        self.assertEqual(independent_digest.hexdigest(), expected)

    def test_state_hex_maps_locus_zero_to_least_significant_bit(self) -> None:
        self.assertEqual(runner._hex_state(1 << 0), "0000000000000001")
        self.assertEqual(runner._hex_state(1 << 63), "8000000000000000")
        self.assertEqual(verifier._state_hex(1 << 0, 64), "0000000000000001")
        self.assertEqual(verifier._state_hex(1 << 63, 64), "8000000000000000")

    def test_machine_spec_carries_every_normative_encoding_field(self) -> None:
        spec = json.loads(PROTOCOL_SPEC.read_text(encoding="ascii"))[
            "trace_and_state_encoding"
        ]
        self.assertEqual(spec["trace_hash"], "SHA-256")
        self.assertIn("least-significant bit", spec["locus_bit_mapping"])
        self.assertIn("0x00", spec["trace_prefix_ascii_plus_nul"])
        self.assertIn("8-byte big-endian", spec["length_encoding"])
        self.assertIn("layer 0 through terminal", spec["digest_sequence"])
        self.assertEqual(
            spec["excluded_from_trace"],
            "intervention arms and conditional larger-ring controls",
        )


if __name__ == "__main__":
    unittest.main()
