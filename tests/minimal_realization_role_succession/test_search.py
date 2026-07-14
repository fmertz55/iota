from __future__ import annotations

import unittest

from src.minimal_realization_role_succession.protocol import GRAMMAR_ID, INPUT_PORTS
from src.minimal_realization_role_succession.search import (
    candidate_id,
    enumerate_rule_rows,
    law_records,
    reflected_rows,
    wolfram_code,
)


class SearchEnumerationTests(unittest.TestCase):
    def test_rule_space_is_complete_and_canonical(self) -> None:
        rows = enumerate_rule_rows()
        self.assertEqual(len(rows), 256)
        self.assertEqual(
            [sum(len(candidate) == count for candidate in rows) for count in range(9)],
            [1, 8, 28, 56, 70, 56, 28, 8, 1],
        )
        self.assertEqual(rows[0], ())
        self.assertEqual(
            rows[-1],
            ("000", "001", "010", "011", "100", "101", "110", "111"),
        )

    def test_candidate_ids_are_unique_and_canonical(self) -> None:
        ids = [candidate_id(rows) for rows in enumerate_rule_rows()]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(candidate_id(()), "MIR-RS-P2-L0-NONE")
        self.assertEqual(
            candidate_id(("111", "000", "010")),
            "MIR-RS-P2-L3-000-010-111",
        )

    def test_law_records_disclose_three_ordered_input_ports(self) -> None:
        records = law_records(("110", "001"))
        self.assertEqual([record["signature"] for record in records], ["001", "110"])
        self.assertEqual([record["id"] for record in records], ["L_001", "L_110"])
        for record in records:
            self.assertEqual(record["input_ports"], list(INPUT_PORTS))
            self.assertEqual(
                record["operator"],
                "emit_one_if_neighborhood_signature",
            )
            self.assertEqual(record["grammar_id"], GRAMMAR_ID)
            self.assertEqual(record["duration_ticks"], 1)
            self.assertEqual(record["write_count"], 1)

    def test_wolfram_code_uses_signature_value_as_bit_index(self) -> None:
        self.assertEqual(wolfram_code(()), 0)
        self.assertEqual(wolfram_code(("000", "111")), 129)
        self.assertEqual(wolfram_code(("100", "101", "110", "111")), 240)

    def test_enumerator_is_closed_under_relation_incidence_reflection(self) -> None:
        family = set(enumerate_rule_rows())
        for rows in family:
            self.assertIn(reflected_rows(rows), family)
        self.assertEqual(reflected_rows(("001", "110")), ("011", "100"))


if __name__ == "__main__":
    unittest.main()
