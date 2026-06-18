#!/usr/bin/env python3
"""Sync docs/toepfer-dex-entries.csv from the canonical toepfer-dex.csv."""

from __future__ import annotations

import csv
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r"C:\Users\J3553\Documents\Cursor Projects\toepfer-red\docs\toepfer-dex.csv")
LOCAL_SOURCE = ROOT / "docs" / "toepfer-dex.csv"
TARGET = ROOT / "docs" / "toepfer-dex-entries.csv"
MIN_LEN = 55
MAX_LEN = 120


def pick_source() -> Path:
    if LOCAL_SOURCE.is_file():
        return LOCAL_SOURCE
    if SOURCE.is_file():
        return SOURCE
    sys.exit(f"missing dex source: {LOCAL_SOURCE} or {SOURCE}")


def main() -> int:
    src = pick_source()
    if src != LOCAL_SOURCE:
        shutil.copy2(src, LOCAL_SOURCE)

    rows_in = list(csv.DictReader(src.open(encoding="utf-8")))
    out_rows: list[dict[str, str]] = []
    bad: list[str] = []

    for row in rows_in:
        entry = row["dex_entry"].strip()
        n = len(entry)
        if not MIN_LEN <= n <= MAX_LEN:
            bad.append(f"#{row['dex_num']} {row['ingame_name']} len {n}")
        out_rows.append(
            {
                "dex_num": row["dex_num"],
                "slug": row["slug"],
                "pokemon": row["pokemon"],
                "ingame_name": row["ingame_name"],
                "category": row.get("category", "TOEPFER"),
                "height_ft": row.get("height_ft", "6"),
                "height_in": row.get("height_in", "2"),
                "weight_lb": row.get("weight_lb", "280"),
                "dex_entry": entry,
                "char_count": str(n),
            }
        )

    if bad:
        print("Invalid entry lengths:", file=sys.stderr)
        for line in bad:
            print(f"  {line}", file=sys.stderr)
        return 1

    fields = [
        "dex_num",
        "slug",
        "pokemon",
        "ingame_name",
        "category",
        "height_ft",
        "height_in",
        "weight_lb",
        "dex_entry",
        "char_count",
    ]
    with TARGET.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Synced {len(out_rows)} entries from {src.name} -> {TARGET.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
