#!/usr/bin/env python3
"""Apply consensus name corrections from dex review."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "docs/toepfer-matrix.csv"
DEX = ROOT / "docs/toepfer-dex-entries.csv"

# First-pass renames (historical; already applied).
PASS1 = {
    11: ("QUEENTOEP", "QUEENTOEPF"),
    12: ("PRINCEOEP", "PRINCEOEPF"),
    21: ("MICRTOEPF", "MICROTOEP"),
    51: ("PIRATTOEPF", "PIRATEOEPF"),
    69: ("MARTTOEPF", "MARSTOEPF"),
    74: ("CYBORGTEPF", "CYBORGTOEP"),
    99: ("LEGIONOEP", "LEGIONOEPF"),
    102: ("MARINETOEP", "MARINEOEPF"),
    103: ("CAPTTOEPF", "CAPTOEPF"),
    105: ("GENERALTPF", "GNRLTOEPF"),
    106: ("SERGTOEPF", "SGTTOEPF"),
    121: ("SHINYTOEP", "SHINYTOEPF"),
    123: ("SILVTOEPF", "SILVRTOEP"),
    125: ("DIAMDTOEPF", "DIAMTOEPF"),
    129: ("PROTOEPF", "PROTOOEPF"),
    132: ("OVER9TOEP", "OVERNTOEP"),
    134: ("CHAOSFRMTP", "CHAOSFMTP"),
    135: ("GLITCH2EPF", "GLITCHBEPF"),
    136: ("MOONMOONO", "MOONMOON"),
    141: ("GARLICTEP", "GARLICTOEP"),
    142: ("PICKLETOEP", "PICKLEOEPF"),
    150: ("COFFEETOEP", "COFFETOEPF"),
}

# Second-pass polish for names that still read awkwardly.
RENAMES = {
    69: ("MARSTOEPF", "SPROUTOEP"),
    105: ("GNRLTOEPF", "GENRLTOEP"),
    106: ("SGTTOEPF", "SERGTOEP"),
    129: ("PROTOOEPF", "PROTOTOEPF"),
    132: ("OVERNTOEP", "MIMETOEPF"),
    134: ("CHAOSFMTP", "CHAOTTOEPF"),
    135: ("GLITCHBEPF", "GLTCHTOEPF"),
    136: ("MOONMOON", "MOONMOOEP"),
    150: ("COFFETOEPF", "COFFEEOEPF"),
}


def patch_file(path: Path, name_col: str) -> None:
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        for row in reader:
            num = int(row["dex_num"])
            if num in RENAMES:
                old, new = RENAMES[num]
                current = row[name_col].strip().upper()
                if current != old:
                    sys.exit(f"{path} #{num}: expected {old}, got {current}")
                row[name_col] = new
                entry = row["dex_entry"]
                if entry.startswith(old):
                    entry = new + entry[len(old) :]
                elif old in entry:
                    entry = entry.replace(old, new, 1)
                row["dex_entry"] = entry
            if num == 54:
                row["dex_entry"] = row["dex_entry"].replace("golduck", "WITCHTOEP")
            length = len(row["dex_entry"])
            row["char_count"] = str(length)
            if not 80 <= length <= 120:
                sys.exit(f"Bad entry length {length} for #{num} {row[name_col]}")
            if len(row[name_col]) > 10:
                sys.exit(f"Name too long: #{num} {row[name_col]}")
            rows.append(row)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def fix_double_suffix_entries(path: Path, name_col: str) -> None:
    """Repair QUEENTOEPFF-style typos from substring replace on *OEPF names."""
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        for row in reader:
            name = row[name_col].strip().upper()
            entry = row["dex_entry"]
            if entry.startswith(name + "F"):
                entry = name + entry[len(name) + 1 :]
            row["dex_entry"] = entry
            row["char_count"] = str(len(entry))
            rows.append(row)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    fix_double_suffix_entries(MATRIX, "ingame_name")
    fix_double_suffix_entries(DEX, "ingame_name")
    patch_file(MATRIX, "ingame_name")
    patch_file(DEX, "ingame_name")
    print(f"Patched {len(RENAMES)} polish renames in matrix and dex-entries CSV")
    return 0


if __name__ == "__main__":
    sys.exit(main())
