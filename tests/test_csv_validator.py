import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from csv_validator import validate_csv_rows


class TestCsvValidator(unittest.TestCase):
    def test_detects_duplicates_and_bad_dates(self) -> None:
        rows = [
            {"id": "A1", "date": "2026年11月1日"},
            {"id": "A1", "date": "2026/11/02"},
            {"id": "A2", "date": "invalid"},
        ]
        res = validate_csv_rows(rows, "id", "date")
        self.assertEqual(res.total_rows, 3)
        self.assertEqual(res.valid_rows, 1)
        self.assertEqual(res.duplicate_ids, ["A1"])
        self.assertEqual(len(res.errors), 2)


if __name__ == "__main__":
    unittest.main()
