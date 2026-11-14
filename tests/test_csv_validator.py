import sys
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from csv_validator import ValidationSummary, validate_csv_rows
from csv_validator.validator import normalize_japanese_date


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


# 正常系
class TestNormalizeJapaneseDateNormal(unittest.TestCase):
    def test_iso_date_is_returned_as_is(self) -> None:
        self.assertEqual(normalize_japanese_date("2026-11-01"), "2026-11-01")

    def test_slash_separated_date_becomes_hyphen_separated(self) -> None:
        self.assertEqual(normalize_japanese_date("2026/11/02"), "2026-11-02")

    def test_kanji_date_is_zero_padded(self) -> None:
        self.assertEqual(normalize_japanese_date("2026年1月5日"), "2026-01-05")

    def test_surrounding_whitespace_is_removed(self) -> None:
        self.assertEqual(normalize_japanese_date("  2026/11/02\t"), "2026-11-02")


class TestValidateCsvRowsNormal(unittest.TestCase):
    def test_all_rows_valid(self) -> None:
        rows = [
            {"id": "A1", "date": "2026-11-01"},
            {"id": "A2", "date": "2026/11/02"},
            {"id": "A3", "date": "2026年11月3日"},
        ]
        res = validate_csv_rows(rows, "id", "date")
        self.assertEqual(
            res,
            ValidationSummary(total_rows=3, valid_rows=3, duplicate_ids=[], errors=[]),
        )

    def test_column_names_are_taken_from_arguments(self) -> None:
        rows = [{"申請ID": "R-1", "申請日": "2026/11/02", "窓口": "架空窓口A"}]
        res = validate_csv_rows(rows, "申請ID", "申請日")
        self.assertEqual(res.valid_rows, 1)
        self.assertEqual(res.errors, [])

    def test_error_messages_use_row_number_and_column_name(self) -> None:
        rows = [
            {"申請ID": "R-1", "申請日": "2026-11-01"},
            {"申請ID": "", "申請日": "2026-11-01"},
            {"申請ID": "R-1", "申請日": "2026-11-01"},
            {"申請ID": "R-2", "申請日": "11/01"},
        ]
        res = validate_csv_rows(rows, "申請ID", "申請日")
        self.assertEqual(
            res.errors,
            [
                "row 2: missing 申請ID",
                "row 3: duplicate 申請ID=R-1",
                "row 4: Unrecognized date format: 11/01",
            ],
        )


# 境界値
class TestNormalizeJapaneseDateBoundary(unittest.TestCase):
    def test_kanji_date_with_two_digit_month_and_day(self) -> None:
        self.assertEqual(normalize_japanese_date("2026年01月05日"), "2026-01-05")

    def test_month_and_day_ranges_are_not_checked(self) -> None:
        self.assertEqual(normalize_japanese_date("2026-02-30"), "2026-02-30")
        self.assertEqual(normalize_japanese_date("2026/13/45"), "2026-13-45")

    def test_full_width_digits_in_iso_form_are_returned_unchanged(self) -> None:
        # \d は全角数字にも一致するため、全角のまま問題なしになる
        self.assertEqual(normalize_japanese_date("２０２６-11-01"), "２０２６-11-01")


class TestValidateCsvRowsBoundary(unittest.TestCase):
    def test_empty_input(self) -> None:
        res = validate_csv_rows([], "id", "date")
        self.assertEqual(
            res,
            ValidationSummary(total_rows=0, valid_rows=0, duplicate_ids=[], errors=[]),
        )

    def test_ids_are_compared_after_stripping_whitespace(self) -> None:
        rows = [{"id": " B1 ", "date": "2026-11-01"}, {"id": "B1", "date": "2026-11-01"}]
        res = validate_csv_rows(rows, "id", "date")
        self.assertEqual(res.duplicate_ids, ["B1"])
        self.assertEqual(res.errors, ["row 2: duplicate id=B1"])

    def test_id_appearing_three_times_is_listed_twice(self) -> None:
        rows = [{"id": "C1", "date": "2026-11-01"}] * 3
        res = validate_csv_rows(rows, "id", "date")
        self.assertEqual(res.valid_rows, 1)
        self.assertEqual(res.duplicate_ids, ["C1", "C1"])

    def test_id_of_row_with_bad_date_still_counts_for_duplicates(self) -> None:
        rows = [{"id": "D1", "date": "bad"}, {"id": "D1", "date": "2026-11-01"}]
        res = validate_csv_rows(rows, "id", "date")
        self.assertEqual(res.valid_rows, 0)
        self.assertEqual(res.duplicate_ids, ["D1"])
        self.assertEqual(
            res.errors,
            ["row 1: Unrecognized date format: bad", "row 2: duplicate id=D1"],
        )

    def test_one_error_per_row(self) -> None:
        rows = [
            {"id": "E1", "date": "2026-11-01"},
            {"id": "E1", "date": "bad"},  # 重複と日付の両方に問題があるが、重複だけ
            {"id": "", "date": "bad"},  # 欠損と日付の両方に問題があるが、欠損だけ
        ]
        res = validate_csv_rows(rows, "id", "date")
        self.assertEqual(res.errors, ["row 2: duplicate id=E1", "row 3: missing id"])

    def test_summary_is_frozen(self) -> None:
        res = validate_csv_rows([], "id", "date")
        with self.assertRaises(FrozenInstanceError):
            res.valid_rows = 1  # type: ignore[misc]


# 異常系
class TestNormalizeJapaneseDateError(unittest.TestCase):
    def test_wareki_is_not_supported(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            normalize_japanese_date("令和8年11月3日")
        self.assertEqual(str(ctx.exception), "Unrecognized date format: 令和8年11月3日")

    def test_single_digit_month_or_day_with_separator_is_rejected(self) -> None:
        for raw in ("2026/1/2", "2026-11-7", "2026/11/9"):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    normalize_japanese_date(raw)

    def test_other_formats_are_rejected(self) -> None:
        for raw in ("", "   ", "20261101", "2026-11-01T09:00", "2026.11.01", "11/02/2026", "2026 年11月1日"):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    normalize_japanese_date(raw)


class TestValidateCsvRowsError(unittest.TestCase):
    def test_missing_id_variants(self) -> None:
        rows = [
            {"id": "", "date": "2026-11-01"},
            {"id": "   ", "date": "2026-11-01"},
            {"id": None, "date": "2026-11-01"},
            {"date": "2026-11-01"},
        ]
        res = validate_csv_rows(rows, "id", "date")
        self.assertEqual(res.valid_rows, 0)
        self.assertEqual(res.duplicate_ids, [])
        self.assertEqual(res.errors, [f"row {i}: missing id" for i in range(1, 5)])

    def test_missing_date_is_reported_as_unrecognized_format(self) -> None:
        rows = [
            {"id": "F1", "date": ""},
            {"id": "F2", "date": None},
            {"id": "F3"},
        ]
        res = validate_csv_rows(rows, "id", "date")
        self.assertEqual(res.valid_rows, 0)
        self.assertEqual(
            res.errors,
            [f"row {i}: Unrecognized date format: " for i in range(1, 4)],
        )

    def test_wrong_column_name_marks_every_row_as_missing(self) -> None:
        rows = [{"id": "G1", "date": "2026-11-01"}, {"id": "G2", "date": "2026-11-02"}]
        res = validate_csv_rows(rows, "ID", "date")
        self.assertEqual(res.valid_rows, 0)
        self.assertEqual(res.errors, ["row 1: missing ID", "row 2: missing ID"])


if __name__ == "__main__":
    unittest.main()
