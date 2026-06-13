#!/usr/bin/env python3
"""Convert a magenta-keyed RGB front PNG to GBA format and push to all species."""

from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "docs/toepfer-matrix.csv"
POKEMON_DIR = ROOT / "graphics/pokemon"
VALIDATE = ROOT / "tools/validate_sprite.py"
SPRITE_SIZE = (64, 64)
MAX_COLORS = 16
TRANSPARENT = (0, 0, 0)
MAGENTA = (255, 0, 255)


def load_slugs() -> list[str]:
    with MATRIX.open(encoding="utf-8", newline="") as handle:
        return [row["slug"] for row in csv.DictReader(handle)]


def palette_from_indexed(img: Image.Image) -> list[tuple[int, int, int]]:
    raw = img.getpalette() or []
    colors: list[tuple[int, int, int]] = []
    for i in range(MAX_COLORS):
        offset = i * 3
        if offset + 2 < len(raw):
            colors.append((raw[offset], raw[offset + 1], raw[offset + 2]))
        else:
            colors.append(TRANSPARENT)
    return colors


def write_jasc_pal(path: Path, colors: list[tuple[int, int, int]]) -> None:
    lines = ["JASC-PAL", "0100", str(MAX_COLORS)]
    for r, g, b in colors:
        lines.append(f"{r} {g} {b}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def is_magenta(rgb: tuple[int, int, int]) -> bool:
    r, g, b = rgb
    return r >= 240 and g <= 20 and b >= 240


def ensure_black_index_zero(img: Image.Image) -> Image.Image:
    colors = palette_from_indexed(img)
    try:
        black_idx = colors.index(TRANSPARENT)
    except ValueError:
        black_idx = None

    pixels = list(img.getdata())
    if black_idx == 0:
        return img

    if black_idx is None:
        darkest = min(
            range(len(colors)),
            key=lambda i: colors[i][0] + colors[i][1] + colors[i][2],
        )
        swap = {darkest: 0, 0: darkest}
        pixels = [swap.get(p, p) for p in pixels]
        colors[0], colors[darkest] = colors[darkest], colors[0]
    else:
        pixels = [0 if p == black_idx else (p if p != 0 else black_idx) for p in pixels]
        colors[0], colors[black_idx] = colors[black_idx], colors[0]

    out = Image.new("P", img.size)
    flat_palette = [channel for rgb in colors for channel in rgb]
    out.putpalette(flat_palette + [0] * (768 - len(flat_palette)))
    out.putdata(pixels)
    return out


def remove_orphans(img: Image.Image) -> Image.Image:
    px = list(img.getdata())
    changed = True
    while changed:
        changed = False
        for y in range(SPRITE_SIZE[1]):
            for x in range(SPRITE_SIZE[0]):
                idx = y * SPRITE_SIZE[0] + x
                if px[idx] == 0:
                    continue
                neighbors = 0
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < SPRITE_SIZE[0] and 0 <= ny < SPRITE_SIZE[1]:
                        if px[ny * SPRITE_SIZE[0] + nx] != 0:
                            neighbors += 1
                if neighbors == 0:
                    px[idx] = 0
                    changed = True
    out = img.copy()
    out.putdata(px)
    return out


def rgb_to_indexed(source: Path) -> Image.Image:
    rgb = Image.open(source).convert("RGB")
    if rgb.size != SPRITE_SIZE:
        rgb = rgb.resize(SPRITE_SIZE, Image.Resampling.NEAREST)

    rgba = Image.new("RGBA", SPRITE_SIZE, (0, 0, 0, 0))
    px = rgb.load()
    for y in range(SPRITE_SIZE[1]):
        for x in range(SPRITE_SIZE[0]):
            c = px[x, y]
            if not is_magenta(c):
                rgba.putpixel((x, y), (*c, 255))

    flat = Image.new("RGB", SPRITE_SIZE, TRANSPARENT)
    flat.paste(rgba, mask=rgba.split()[3])
    indexed = flat.quantize(colors=MAX_COLORS, method=Image.Quantize.MEDIANCUT)
    indexed = ensure_black_index_zero(indexed)
    return remove_orphans(indexed)


def validate_sprite(path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(VALIDATE), str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr.rstrip(), file=sys.stderr)
        raise SystemExit(f"Validation failed for {path}")


def deploy_front(indexed: Image.Image, slugs: list[str], update_back: bool) -> None:
    palette = palette_from_indexed(indexed)
    staging = ROOT / "docs/sprites/toepfer-front-master.png"
    staging.parent.mkdir(parents=True, exist_ok=True)
    indexed.save(staging)

    for slug in slugs:
        species_dir = POKEMON_DIR / slug
        if not species_dir.is_dir():
            raise SystemExit(f"Missing species dir: {species_dir}")
        shutil.copy2(staging, species_dir / "front.png")
        if update_back:
            shutil.copy2(staging, species_dir / "back.png")
        write_jasc_pal(species_dir / "normal.pal", palette)
        write_jasc_pal(species_dir / "shiny.pal", palette)

    print(f"Deployed front sprite to {len(slugs)} species")


def main() -> int:
    parser = argparse.ArgumentParser(description="Import master Toepfer front to all species")
    parser.add_argument("source", type=Path, help="RGB/RGBA PNG (64x64, magenta background)")
    parser.add_argument(
        "--update-back",
        action="store_true",
        help="Also overwrite back.png (default: front + palettes only)",
    )
    args = parser.parse_args()

    source = args.source if args.source.is_absolute() else ROOT / args.source
    if not source.is_file():
        raise SystemExit(f"Source not found: {source}")

    indexed = rgb_to_indexed(source)
    staging = ROOT / "docs/sprites/toepfer-front-master.png"
    staging.parent.mkdir(parents=True, exist_ok=True)
    indexed.save(staging)
    validate_sprite(staging)

    slugs = load_slugs()
    deploy_front(indexed, slugs, update_back=args.update_back)
    return 0


if __name__ == "__main__":
    sys.exit(main())
