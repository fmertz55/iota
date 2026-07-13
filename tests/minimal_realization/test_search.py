from __future__ import annotations

import unittest

from src.minimal_realization.search import candidate_id, enumerate_rule_rows, law_records


class SearchEnumerationTests(unittest.TestCase):
    def test_rule_space_is_complete_and_canonical(self) -> None:
        rows = enumerate_rule_rows()
        self.assertEqual(len(rows), 16)
        self.assertEqual([sum(len(item) == n for item in rows) for n in range(5)], [1, 4, 6, 4, 1])
        self.assertEqual(rows[0], ())
        self.assertEqual(rows[-1], ("00", "01", "10", "11"))

    def test_candidate_ids_are_unique(self) -> None:
        ids = [candidate_id(rows) for rows in enumerate_rule_rows()]
        self.assertEqual(len(ids), len(set(ids)))

    def test_law_records_match_rows(self) -> None:
        rows = ("00", "11")
        records = law_records(rows)
        self.assertEqual([record["signature"] for record in records], list(rows))
        self.assertEqual([record["id"] for record in records], ["L_00", "L_11"])


if __name__ == "__main__":
    unittest.main()
