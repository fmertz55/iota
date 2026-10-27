from __future__ import annotations

import hashlib
import unittest

import numpy as np

from src.dp_persistence import rng


class SeedDerivationTests(unittest.TestCase):
    def test_iota_streams_follow_partitions_json(self) -> None:
        domain = b"ICP-DP-PERSISTENCE-001\0medium\0" + b"12345"
        expected = int.from_bytes(hashlib.sha256(domain).digest()[:8], "big")
        self.assertEqual(rng.iota_seed("medium", 12345), expected)
        domain = b"ICP-DP-PERSISTENCE-001\0dynamics\0" + b"12345"
        expected = int.from_bytes(hashlib.sha256(domain).digest()[:8], "big")
        self.assertEqual(rng.iota_seed("dynamics", 12345), expected)
        medium, dynamics = rng.iota_streams(12345)
        self.assertNotEqual(medium.random(), dynamics.random())

    def test_calibration_seed_follows_calibration_json(self) -> None:
        domain = b"ICP-DP-PERSISTENCE-001\0CAL-DK-BOND-1P1\x000.6\x007"
        expected = int.from_bytes(hashlib.sha256(domain).digest()[:8], "big")
        self.assertEqual(rng.calibration_seed("CAL-DK-BOND-1P1", 0.60, 7), expected)
        self.assertEqual(rng.control_string(0.3116), "0.3116")

    def test_domains_are_separated(self) -> None:
        seeds = {
            rng.iota_seed("medium", 1),
            rng.iota_seed("dynamics", 1),
            rng.calibration_seed("CAL-SIR-SC-3", 0.25, 1),
            rng.domain_seed(rng.TIMING_DOMAIN, "medium", "1"),
            rng.domain_seed("ICP-DP-PERSISTENCE-001", rng.BOOTSTRAP_TAG, "IOTA-MIN-L0", "0.3", "criticality"),
        }
        self.assertEqual(len(seeds), 5)
        with self.assertRaises(ValueError):
            rng.domain_seed("a\0b")
        with self.assertRaises(ValueError):
            rng.iota_seed("bootstrap", 1)

    def test_vector_and_scalar_draws_are_the_same_stream(self) -> None:
        a = rng.generator(42)
        b = rng.generator(42)
        vector = a.random(1000)
        scalar = np.array([b.random() for _ in range(1000)])
        np.testing.assert_array_equal(vector, scalar)
        self.assertEqual(a.bit_generator.state, b.bit_generator.state)


if __name__ == "__main__":
    unittest.main()
