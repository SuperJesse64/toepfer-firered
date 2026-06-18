#!/usr/bin/env python3
"""Verify species names and dialogue are synced with dex CSV."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_species_names() -> int:
    rows = list(csv.DictReader((ROOT / "docs/toepfer-dex.csv").open(encoding="utf-8")))
    text = (ROOT / "src/data/text/species_names.h").read_text(encoding="utf-8")
    asm = dict(re.findall(r'\[SPECIES_(\w+)\] = _\("([^"]+)"\)', text))

    def const(slug: str) -> str:
        return {"nidoran_f": "NIDORAN_F", "nidoran_m": "NIDORAN_M", "mr_mime": "MR_MIME"}.get(
            slug, slug.upper()
        )

    bad = [
        (r["dex_num"], r["slug"], r["ingame_name"], asm.get(const(r["slug"]), "?"))
        for r in rows
        if asm.get(const(r["slug"]), "?") != r["ingame_name"].upper()
    ]
    print(f"species_names.h mismatches: {len(bad)}")
    for row in bad[:10]:
        print(" ", row)
    return len(bad)


def check_stale_dialogue() -> int:
    old = list(csv.DictReader((ROOT / "docs/toepfer-spreadsheet.csv").open(encoding="utf-8")))
    current = {
        r["slug"]: r["ingame_name"].upper()
        for r in csv.DictReader((ROOT / "docs/toepfer-dex-entries.csv").open(encoding="utf-8"))
    }
    stale = {
        r["ingame_name"].upper(): current[r["slug"]]
        for r in old
        if r["ingame_name"].upper() != current[r["slug"]]
    }
    stale.pop("TOEPFER", None)
    stale.update(
        {
            "QUEENBEE": "MAIDEN",
            "NEWHIRE": "MAIDEN",
            "PETTYCASH": "THIEF",
            "CHIEFFIN": "BARON",
            "PARTTIMER": "PIXIE",
            "PLANTBOY": "FROG",
            "COLDCALLER": "NEWT",
            "HELPDESK": "PIRATE",
        }
    )
    hits: list[tuple[str, list[str]]] = []
    scan_dirs = [ROOT / "data", ROOT / "src"]
    skip_parts = ("species_names.h", "pokedex_text", "pokedex_entries.h", "easy_chat_group_pokemon")
    for base in scan_dirs:
        for path in sorted(base.rglob("*")):
            if path.suffix not in {".inc", ".c", ".h"}:
                continue
            if any(part in str(path) for part in skip_parts):
                continue
            text = path.read_text(encoding="utf-8").upper()
            found = [name for name in stale if name in text]
            if found:
                hits.append((str(path.relative_to(ROOT)), found))
    print(f"stale dialogue species tokens: {len(hits)} files")
    for rel, found in hits:
        print(f"  {rel}: {found}")
    return len(hits)


def main() -> int:
    issues = check_species_names() + check_stale_dialogue()
    if issues:
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
