#!/usr/bin/env python3
"""Replace vanilla species names and POKéMON branding in FireRed dialogue text."""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "docs" / "toepfer-dex-entries.csv"

TEXT_DIRS = [
    ROOT / "data" / "text",
    ROOT / "data" / "maps",
    ROOT / "data" / "scripts",
]
SRC_DIRS = [
    ROOT / "src",
]
EXTRA_FILES = [
    ROOT / "data" / "mystery_event_msg.s",
    ROOT / "data" / "event_scripts.s",
    ROOT / "src" / "data" / "items.json",
]

SKIP_FILES = {
    ROOT / "src" / "data" / "text" / "species_names.h",
    ROOT / "src" / "data" / "pokemon" / "pokedex_entries.h",
    ROOT / "src" / "data" / "pokemon" / "pokedex_text_fr.h",
    ROOT / "src" / "data" / "pokemon" / "pokedex_text_lg.h",
}

NIDORAN_OVERRIDES: dict[str, str] = {}

# Wrong intermediate names from earlier passes (not in the office spreadsheet).
MANUAL_LEGACY_NAMES: dict[str, str] = {
    "QUEENBEE": "MAIDEN",
    "NEWHIRE": "MAIDEN",
    "PETTYCASH": "THIEF",
    "CHIEFFIN": "BARON",
    "PARTTIMER": "PIXIE",
    "PLANTBOY": "FROG",
    "COLDCALLER": "NEWT",
    "HELPDESK": "PIRATE",
}

BRANDING_REPLACEMENTS = [
    ("POKéDEX", "TOEPFERDEX"),
    ("Pokédex", "Toepferdex"),
    ("Pokedex", "Toepferdex"),
    ("POKéMON", "TOEPFER"),
    ("POKé BALL", "TOEPFER BALL"),
    ("POKé BALLS", "TOEPFER BALLS"),
    ("POKé DOLL", "TOEPFER DOLL"),
    ("POKé FLUTE", "TOEPFER FLUTE"),
    ("POKéMANIAC", "TOEPFER FAN"),
    ("POKéMON LEAGUE", "TOEPFER LEAGUE"),
    ("POKéMON CENTER", "TOEPFER CENTER"),
    ("POKéMON MART", "TOEPFER MART"),
    ("POKéMON BOX", "TOEPFER BOX"),
    ("POKéMON JUMP", "TOEPFER JUMP"),
    ("POKéMON TRADES", "TOEPFER TRADES"),
    ("POKéMON PRINTER", "TOEPFER PRINTER"),
    ("POKéMON EGGS", "TOEPFER EGGS"),
    ("POKéMON GYM", "TOEPFER GYM"),
    ("POKéMON FAN", "TOEPFER FAN"),
    ("POK\u00e9 BALL", "TOEPFER BALL"),
    ("POK\u00e9 DOLL", "TOEPFER DOLL"),
    ("POK\u00e9 FLUTE", "TOEPFER FLUTE"),
]


def normalize_vanilla(display: str) -> list[str]:
    keys: list[str] = []
    upper = display.upper()
    keys.append(upper)
    keys.append(upper.replace("♀", "").replace("♂", "").strip())
    keys.append(re.sub(r"[^A-Z0-9]", "", upper))
    if display == "Farfetch'd":
        keys.extend(["FARFETCH'D", "FARFETCHD"])
    if display == "Mr. Mime":
        keys.extend(["MR. MIME", "MR MIME", "MRMIME"])
    if "Nidoran" in display:
        keys.append("NIDORAN")
        if "♀" in display or "F" in display.upper():
            keys.extend(["NIDORAN♀", "NIDORAN F"])
        if "♂" in display or "M" in display.upper():
            keys.extend(["NIDORAN♂", "NIDORAN M"])
    keys.append(display)
    keys.append(display.title())
    return list(dict.fromkeys(key for key in keys if key))


def load_species_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            toepfer = row["ingame_name"].strip().upper()
            for key in normalize_vanilla(row["pokemon"].strip()):
                if key in {"NIDORAN", "NIDORAN F", "NIDORAN M"}:
                    continue
                mapping[key] = toepfer
    return dict(sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True))


def load_legacy_species_map() -> dict[str, str]:
    """Map retired office / draft names to current archetype names."""
    legacy_path = ROOT / "docs" / "toepfer-spreadsheet.csv"
    mapping = dict(MANUAL_LEGACY_NAMES)
    if not legacy_path.is_file():
        return dict(sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True))

    current: dict[str, str] = {}
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            current[row["slug"].strip()] = row["ingame_name"].strip().upper()

    with legacy_path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            slug = row["slug"].strip()
            old = row["ingame_name"].strip().upper()
            new = current.get(slug, "")
            if not new or old == new or old == "TOEPFER":
                continue
            mapping[old] = new

    return dict(sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True))


def nidoran_name() -> str:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["slug"].strip() == "nidoran_f":
                return row["ingame_name"].strip().upper()
    return "MAIDEN"


def override_key(path: Path) -> str:
    parts = path.parts
    if "maps" in parts:
        idx = parts.index("maps")
        if idx + 2 < len(parts):
            return f"{parts[idx + 1]}/{path.name}"
    return path.name


def apply_replacements(
    blob: str,
    species_map: dict[str, str],
    legacy_map: dict[str, str],
    filename: str,
) -> tuple[str, list[str]]:
    changes: list[str] = []
    nidoran = NIDORAN_OVERRIDES.get(filename, nidoran_name())
    updated = blob
    for old, new in BRANDING_REPLACEMENTS:
        if old in updated:
            updated = updated.replace(old, new)
            changes.append(f"{old} -> {new}")
    for old, new in legacy_map.items():
        pattern = re.compile(rf"\b{re.escape(old)}\b")
        if pattern.search(updated):
            updated = pattern.sub(new, updated)
            changes.append(f"{old} -> {new}")
    for token in ("NIDORAN♂", "NIDORAN♀", "NIDORAN"):
        if token in updated:
            updated = updated.replace(token, nidoran)
            changes.append(f"{token} -> {nidoran} ({filename})")
    for vanilla, toepfer in species_map.items():
        if vanilla.islower():
            pattern = re.compile(re.escape(vanilla), re.IGNORECASE)
        else:
            pattern = re.compile(rf"\b{re.escape(vanilla)}\b")
        if pattern.search(updated):
            updated = pattern.sub(toepfer, updated)
            changes.append(f"{vanilla} -> {toepfer}")
    return updated, changes


def process_inc(
    content: str,
    species_map: dict[str, str],
    legacy_map: dict[str, str],
    filename: str,
) -> tuple[str, list[str]]:
    changes: list[str] = []

    def sub_string(match: re.Match[str]) -> str:
        original = match.group(0)
        body = match.group(1)
        suffix = "$" if body.endswith("$") else ""
        core = body[:-1] if suffix else body
        updated, local_changes = apply_replacements(core, species_map, legacy_map, filename)
        changes.extend(local_changes)
        if updated != core:
            return f'.string "{updated}{suffix}"'
        return original

    return re.sub(r'\.string "([^"]*)"', sub_string, content), changes


def process_c_string(
    content: str,
    species_map: dict[str, str],
    legacy_map: dict[str, str],
    filename: str,
) -> tuple[str, list[str]]:
    changes: list[str] = []

    def sub_block(match: re.Match[str]) -> str:
        original = match.group(0)
        parts = re.findall(r'"((?:[^"\\]|\\.)*)"', match.group(1))
        if not parts:
            return original
        updated_parts: list[str] = []
        block_changed = False
        for part in parts:
            updated, local_changes = apply_replacements(part, species_map, legacy_map, filename)
            changes.extend(local_changes)
            updated_parts.append(updated)
            block_changed = block_changed or updated != part
        if not block_changed:
            return original
        rebuilt = []
        for index, part in enumerate(updated_parts):
            prefix = "    " if index else ""
            rebuilt.append(f'{prefix}"{part}"')
        return "_(" + "\n".join(rebuilt) + ")"

    pattern = r'_\(\s*((?:"(?:[^"\\]|\\.)*"(?:\s*\n\s*)?)+)\s*\)'
    return re.sub(pattern, sub_block, content), changes


def process_json(path: Path, species_map: dict[str, str], legacy_map: dict[str, str]) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    changes: list[str] = []
    for item in payload.get("items", []):
        for field in ("english", "description_english"):
            if field not in item:
                continue
            updated, local_changes = apply_replacements(
                item[field], species_map, legacy_map, path.name
            )
            if updated != item[field]:
                item[field] = updated
                changes.extend(local_changes)
    if changes:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return changes


def process_file(
    path: Path,
    species_map: dict[str, str],
    legacy_map: dict[str, str],
) -> list[str]:
    if path in SKIP_FILES:
        return []
    filename = override_key(path)
    if path.suffix == ".json":
        return process_json(path, species_map, legacy_map)
    original = path.read_text(encoding="utf-8")
    if path.suffix == ".inc" or path.suffix == ".s":
        updated, changes = process_inc(original, species_map, legacy_map, filename)
    elif path.suffix in {".c", ".h"}:
        updated, changes = process_c_string(original, species_map, legacy_map, filename)
    else:
        return []
    if updated != original:
        path.write_text(updated, encoding="utf-8", newline="\n")
    return changes


def iter_files() -> list[Path]:
    files: list[Path] = []
    for directory in TEXT_DIRS:
        if not directory.is_dir():
            continue
        files.extend(directory.rglob("*.inc"))
        files.extend(directory.rglob("*.s"))
    for directory in SRC_DIRS:
        if not directory.is_dir():
            continue
        files.extend(directory.rglob("*.c"))
        files.extend(directory.rglob("*.h"))
    for path in EXTRA_FILES:
        if path.is_file():
            files.append(path)
    return sorted(set(files))


def main() -> int:
    species_map = load_species_map()
    legacy_map = load_legacy_species_map()
    total_files = 0
    for path in iter_files():
        changes = process_file(path, species_map, legacy_map)
        if changes:
            total_files += 1
            print(f"{path.relative_to(ROOT)}: {len(changes)} replacements")
    print(f"Updated {total_files} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
