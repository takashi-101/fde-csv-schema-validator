"""examples/sample_applications.csv を読み、validate_csv_rows の結果を表示します。"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from csv_validator import validate_csv_rows  # noqa: E402

SAMPLE = ROOT / "examples" / "sample_applications.csv"
ID_COL = "申請ID"
DATE_COL = "申請日"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    with SAMPLE.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    summary = validate_csv_rows(rows, id_col=ID_COL, date_col=DATE_COL)
    print(f"input: examples/{SAMPLE.name} (id_col={ID_COL}, date_col={DATE_COL})")
    print(f"total_rows: {summary.total_rows}")
    print(f"valid_rows: {summary.valid_rows}")
    print(f"duplicate_ids: {summary.duplicate_ids}")
    print("errors:")
    for error in summary.errors:
        print(f"  {error}")


if __name__ == "__main__":
    main()
