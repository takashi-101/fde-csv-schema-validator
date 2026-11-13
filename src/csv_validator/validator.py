"""Defensive CSV validator for dirty municipal/enterprise tabular exports."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class ValidationSummary:
    total_rows: int
    valid_rows: int
    duplicate_ids: List[str]
    errors: List[str]


_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def normalize_japanese_date(raw: str) -> str:
    s = raw.strip().replace("/", "-")
    if _ISO_DATE_RE.match(s):
        return s
    m = re.match(r"^(\d{4})年(\d{1,2})月(\d{1,2})日$", s)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    raise ValueError(f"Unrecognized date format: {raw}")


def validate_csv_rows(rows: List[Dict[str, str]], id_col: str, date_col: str) -> ValidationSummary:
    seen = set()
    duplicates: List[str] = []
    errors: List[str] = []
    valid = 0

    for idx, row in enumerate(rows, start=1):
        rid = (row.get(id_col) or "").strip()
        rdate = (row.get(date_col) or "").strip()
        if not rid:
            errors.append(f"row {idx}: missing {id_col}")
            continue
        if rid in seen:
            duplicates.append(rid)
            errors.append(f"row {idx}: duplicate {id_col}={rid}")
            continue
        seen.add(rid)
        try:
            normalize_japanese_date(rdate)
        except ValueError as exc:
            errors.append(f"row {idx}: {exc}")
            continue
        valid += 1

    return ValidationSummary(
        total_rows=len(rows),
        valid_rows=valid,
        duplicate_ids=duplicates,
        errors=errors,
    )
