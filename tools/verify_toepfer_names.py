#!/usr/bin/env python3
"""Verify species names and player-facing text are synced with dex CSV."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEX_CSV = ROOT / "docs/toepfer-dex-entries.csv"
STRING_RE = re.compile(r'_\(\s*"((?:[^"\\]|\\.)*)"', re.MULTILINE)
DOT_STRING_RE = re.compile(r'\.string\s+"((?:[^"\\]|\\.)*)"', re.MULTILINE)

STALE_OFFICE = frozenset(
    {
        "PLANTBOY",
        "COLDCALLER",
        "HELPDESK",
        "QUEENBEE",
        "NEWHIRE",
        "PETTYCASH",
        "CHIEFFIN",
        "PARTTIMER",
        "TOEPFERJR",
        "GLOWTOEPF",
    }
)

# Pikachu shorthand still seen in decoration item names.
PIKACHU_SHORTHAND = frozenset({"PIKA"})

SKIP_PATH_PARTS = (
    "data/maps/",
    "pokedex_text",
    "pokedex_entries.h",
    "easy_chat_group_pokemon",
)

PLAYER_FACING_SCAN = (
    "src/**/*.c",
    "src/**/*.h",
    "src/strings.c",
    "src/trainer_tower_sets.c",
    "src/data/decoration/*.h",
    "data/text/*.inc",
)


def scoped_player_files() -> list[Path]:
    files: set[Path] = set()
    for pattern in PLAYER_FACING_SCAN:
        files.update(ROOT.glob(pattern))
    out: list[Path] = []
    for path in sorted(files):
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        if any(part in rel for part in SKIP_PATH_PARTS):
            continue
        out.append(path)
    return out


def load_gen1_names() -> tuple[dict[str, str], set[str], set[str]]:
    rows = list(csv.DictReader(DEX_CSV.open(encoding="utf-8")))
    vanilla_to_toepfer = {r["pokemon"].upper(): r["ingame_name"].upper() for r in rows}
    toepfer_names = set(vanilla_to_toepfer.values())
    return vanilla_to_toepfer, toepfer_names, set(vanilla_to_toepfer)


def check_species_names() -> int:
    rows = list(csv.DictReader(DEX_CSV.open(encoding="utf-8")))
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
        for r in csv.DictReader(DEX_CSV.open(encoding="utf-8"))
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


def iter_player_literals(path: Path) -> list[tuple[int, str]]:
    text = path.read_text(encoding="utf-8")
    literals: list[tuple[int, str]] = []
    for match in STRING_RE.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        literals.append((line, match.group(1)))
    for match in DOT_STRING_RE.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        literals.append((line, match.group(1)))
    return literals


def check_player_facing_vanilla() -> int:
    vanilla_to_toepfer, toepfer_names, vanilla_names = load_gen1_names()
    hits: list[tuple[str, int, str, str]] = []

    for path in scoped_player_files():
        rel = str(path.relative_to(ROOT))
        for line, literal in iter_player_literals(path):
            upper = literal.upper()
            for tok in STALE_OFFICE:
                if tok in upper:
                    hits.append((rel, line, tok, literal[:80]))
            for tok in PIKACHU_SHORTHAND:
                if re.search(rf"\b{re.escape(tok)}\b", upper):
                    hits.append((rel, line, tok, literal[:80]))
            for vanilla in vanilla_names:
                if vanilla in toepfer_names:
                    continue
                if re.search(rf"\b{re.escape(vanilla)}\b", upper):
                    hits.append(
                        (
                            rel,
                            line,
                            vanilla,
                            f"expected {vanilla_to_toepfer[vanilla]}",
                        )
                    )

    print(f"player-facing vanilla Gen1 / stale tokens: {len(hits)}")
    for hit in hits[:20]:
        print(" ", hit)
    return len(hits)


def check_trainer_tower_gen1_nicknames() -> int:
    path = ROOT / "src/trainer_tower_sets.c"
    if not path.exists():
        return 0
    vanilla_to_toepfer, toepfer_names, vanilla_names = load_gen1_names()
    hits: list[tuple[int, str, str]] = []
    nickname_re = re.compile(r'\.nickname\s*=\s*_\("([^"]+)"\)')
    text = path.read_text(encoding="utf-8")
    for match in nickname_re.finditer(text):
        nick = match.group(1).upper()
        line = text.count("\n", 0, match.start()) + 1
        if nick in vanilla_names and nick not in toepfer_names:
            hits.append((line, nick, vanilla_to_toepfer[nick]))
        if nick in PIKACHU_SHORTHAND:
            hits.append((line, nick, "SPARK"))

    print(f"trainer_tower_sets.c Gen1 vanilla nicknames: {len(hits)}")
    for hit in hits[:20]:
        print(" ", hit)
    return len(hits)


def main() -> int:
    issues = (
        check_species_names()
        + check_stale_dialogue()
        + check_player_facing_vanilla()
        + check_trainer_tower_gen1_nicknames()
    )
    if issues:
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
