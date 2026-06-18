#!/usr/bin/env python3
"""Import numbered Toepfer front/back PNGs into graphics/pokemon/."""

from __future__ import annotations

import csv
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from apply_dex_csv import DEX_ORDER  # noqa: E402
from import_master_front import (  # noqa: E402
    convert_pair_to_indexed,
    load_source_rgb,
    validate_sprite,
    write_jasc_pal,
)

FRONT_SRC = ROOT / "art/sprites/front"
BACK_SRC = ROOT / "art/sprites/back"
STAGING = ROOT / "docs/sprites/staging"
POKEMON_DIR = ROOT / "graphics/pokemon"
VALIDATE = ROOT / "tools/validate_sprite.py"


@dataclass
class ImportReport:
    imported: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def parse_numbered_stem(stem: str) -> tuple[int, str]:
    num_str, name = stem.split("_", 1)
    return int(num_str), name


def parse_front_sources() -> dict[int, list[tuple[str, Path]]]:
    by_dex: dict[int, list[tuple[str, Path]]] = defaultdict(list)
    for path in sorted(FRONT_SRC.glob("*.png")):
        dex_num, raw_name = parse_numbered_stem(path.stem)
        by_dex[dex_num].append((raw_name, path))
    return by_dex


def parse_back_sources() -> dict[int, list[tuple[str, Path]]]:
    backs: dict[int, list[tuple[str, Path]]] = defaultdict(list)
    for path in sorted(BACK_SRC.glob("*.png")):
        stem = path.stem.strip()
        for suffix in ("_BACKS", "_BACK"):
            if stem.endswith(suffix):
                stem = stem[: -len(suffix)]
                break
        dex_num, raw_name = parse_numbered_stem(stem)
        backs[dex_num].append((raw_name, path))
    return backs


def match_back(
    backs: dict[int, list[tuple[str, Path]]],
    dex_num: int,
    raw_name: str,
) -> Path | None:
    options = backs.get(dex_num, [])
    if not options:
        return None
    for candidate, path in options:
        if candidate == raw_name:
            return path
    front_key = raw_name.replace("_", "")
    for candidate, path in options:
        cand_key = candidate.replace("_", "")
        if front_key.startswith(cand_key) or cand_key.startswith(front_key):
            return path
    if len(options) == 1:
        return options[0][1]
    return sorted(options, key=lambda item: item[0])[0][1]


def deploy_species(slug: str, front_png: Path, back_png: Path) -> None:
    species_dir = POKEMON_DIR / slug
    if not species_dir.is_dir():
        raise FileNotFoundError(f"missing species dir: {species_dir}")

    front_rgb = load_source_rgb(front_png)
    back_rgb = load_source_rgb(back_png)
    front, back = convert_pair_to_indexed(front_rgb, back_rgb)

    STAGING.mkdir(parents=True, exist_ok=True)
    front_staged = STAGING / f"{slug}-front.png"
    back_staged = STAGING / f"{slug}-back.png"
    front.save(front_staged)
    back.save(back_staged)
    validate_sprite(front_staged)
    validate_sprite(back_staged)

    front.save(species_dir / "front.png")
    back.save(species_dir / "back.png")
    palette = front.getpalette() or []
    colors = []
    for i in range(16):
        offset = i * 3
        colors.append((palette[offset], palette[offset + 1], palette[offset + 2]))
    write_jasc_pal(species_dir / "normal.pal", colors)
    write_jasc_pal(species_dir / "shiny.pal", colors)


def main() -> int:
    if not FRONT_SRC.is_dir():
        sys.exit(f"missing {FRONT_SRC}")
    if not BACK_SRC.is_dir():
        sys.exit(f"missing {BACK_SRC}")

    fronts = parse_front_sources()
    backs = parse_back_sources()
    report = ImportReport()

    for index, slug in enumerate(DEX_ORDER, 1):
        options = fronts.get(index, [])
        if not options:
            report.errors.append(f"#{index:03d} {slug}: missing front sprite")
            continue
        raw_name, front_path = sorted(options, key=lambda item: item[0])[0]
        back_path = match_back(backs, index, raw_name)
        if back_path is None:
            report.errors.append(f"#{index:03d} {slug}: missing back for {raw_name}")
            continue
        try:
            deploy_species(slug, front_path, back_path)
            report.imported += 1
        except (SystemExit, OSError, subprocess.CalledProcessError) as exc:
            report.errors.append(f"#{index:03d} {slug}: {exc}")

    print(f"Imported {report.imported}/{len(DEX_ORDER)} species")
    for warning in report.warnings:
        print(f"  WARN: {warning}")
    for error in report.errors:
        print(f"  ERROR: {error}", file=sys.stderr)
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
