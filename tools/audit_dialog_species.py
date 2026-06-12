#!/usr/bin/env python3
"""Audit user-visible strings for leftover vanilla Pokemon names in FireRed."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "docs" / "toepfer-dex-entries.csv"

SCAN_ROOTS = [
    ROOT / "data" / "text",
    ROOT / "data" / "maps",
    ROOT / "data" / "scripts",
    ROOT / "src",
]

SKIP_FILES = {
    ROOT / "src" / "data" / "pokemon" / "pokedex_text_lg.h",
}

SKIP_SUBSTRINGS = {
    "MISSINGNO",
    "TOEPFER",
    "TOEPFERDEX",
    "TOEPFER BALL",
    "SPECIES_",
    "NATIONAL_DEX_",
    "TRAINER_",
    "OBJ_EVENT_GFX_",
    "LOCALID_",
    "FLAG_",
    "VAR_",
    "CRY_MODE_",
    "INGAME_TRADE_",
}


def vanilla_keys(display: str) -> list[str]:
    keys: list[str] = []
    keys.append(display)
    keys.append(display.upper())
    keys.append(display.title())
    keys.append(re.sub(r"[^A-Za-z0-9]", "", display))
    keys.append(re.sub(r"[^A-Za-z0-9]", "", display).upper())
    if display == "Farfetch'd":
        keys.extend(["Farfetch'd", "FARFETCH'D", "FARFETCHD"])
    if display == "Mr. Mime":
        keys.extend(["Mr. Mime", "MR. MIME", "Mr.Mime", "MRMIME"])
    if "Nidoran" in display:
        keys.extend(["Nidoran", "NIDORAN", "Nidoran♀", "Nidoran♂", "NIDORAN♀", "NIDORAN♂"])
    return list(dict.fromkeys(key for key in keys if len(key) >= 3))


def load_vanilla_names() -> list[str]:
    names: set[str] = set()
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            for key in vanilla_keys(row["pokemon"].strip()):
                names.add(key)
    return sorted(names, key=len, reverse=True)


def extract_strings(line: str) -> list[str]:
    strings: list[str] = []
    for match in re.finditer(r'\.string "([^"]*)"', line):
        strings.append(match.group(1))
    for match in re.finditer(r'_\("((?:[^"\\]|\\.)*)"\)', line):
        strings.append(match.group(1))
    return strings


def audit_file(path: Path, vanilla_names: list[str]) -> list[tuple[int, str, str]]:
    hits: list[tuple[int, str, str]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip().startswith("//") or line.strip().startswith(";"):
            continue
        for string in extract_strings(line):
            if not string or string in {"@", ""}:
                continue
            upper_blob = string.upper()
            if any(skip in upper_blob for skip in SKIP_SUBSTRINGS):
                continue
            if "POKéMON" in string or "POKéDEX" in string or "POKé BALL" in string:
                hits.append((line_no, "BRANDING", string))
                continue
            for name in vanilla_names:
                if len(name) < 4:
                    continue
                pattern = re.compile(rf"\b{re.escape(name)}\b", re.IGNORECASE)
                if pattern.search(string):
                    hits.append((line_no, name, string))
                    break
    return hits


def main() -> int:
    vanilla_names = load_vanilla_names()
    total = 0
    for root in SCAN_ROOTS:
        if not root.is_dir():
            continue
        patterns = ["*.inc", "*.c", "*.h", "*.s", "*.json"]
        for pattern in patterns:
            for path in sorted(root.rglob(pattern)):
                if path in SKIP_FILES:
                    continue
                hits = audit_file(path, vanilla_names)
                if hits:
                    total += len(hits)
                    print(f"\n{path.relative_to(ROOT)}")
                    for line_no, name, string in hits:
                        preview = string if len(string) <= 60 else string[:57] + "..."
                        print(f"  L{line_no}: {name!r} in {preview!r}")
    if total:
        print(f"\n{total} potential hit(s)")
        return 1
    print("No vanilla species names or branding found in quoted strings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
