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
# GBA: palette index 0 is invisible. Opaque black outlines must use a non-zero index.
OUTLINE_COLOR = (0, 0, 0)
QUANTIZE_FILL = (255, 254, 255)  # unique filler; not used in source art

# Exact RGB values that must survive quantize (glasses lenses, shirt highlights, etc.).
PROTECTED_COLORS: tuple[tuple[int, int, int], ...] = (
    (236, 236, 229),  # glasses lens / highlight white
    (161, 162, 166),  # glasses rim gray
)


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


def is_outline(rgb: tuple[int, int, int]) -> bool:
    """Pure black pixels are the 1px outer outline in pret-style sprites."""
    return rgb == (0, 0, 0)


def apply_palette(img: Image.Image, colors: list[tuple[int, int, int]]) -> Image.Image:
    out = img.copy()
    flat = [channel for rgb in colors for channel in rgb]
    out.putpalette(flat + [0] * (768 - len(flat)))
    return out


def finalize_transparent_index(img: Image.Image) -> Image.Image:
    """Ensure palette slot 0 is RGB(0,0,0); only backdrop pixels use index 0."""
    colors = palette_from_indexed(img)
    colors[0] = TRANSPARENT
    return apply_palette(img, colors)


def find_or_add_color(colors: list[tuple[int, int, int]], rgb: tuple[int, int, int], px: list[int]) -> int:
    """Return palette index for rgb, reusing an existing slot or the least-used one."""
    for i, c in enumerate(colors):
        if c == rgb:
            return i
    used = {p for p in px if p != 0}
    for i in range(MAX_COLORS - 1, 0, -1):
        if i not in used:
            colors[i] = rgb
            return i
    counts: dict[int, int] = {}
    for p in px:
        if p != 0:
            counts[p] = counts.get(p, 0) + 1
    victim = min(used, key=lambda i: counts.get(i, 0))
    colors[victim] = rgb
    return victim


def pick_outline_index(colors: list[tuple[int, int, int]]) -> int:
    """Pick a palette slot for outlines that does not hold protected lens colors."""
    protected_indices = {i for i, c in enumerate(colors) if c in PROTECTED_COLORS}
    for candidate in range(MAX_COLORS - 1, 0, -1):
        if candidate not in protected_indices:
            return candidate
    return MAX_COLORS - 1


def preserve_exact_colors(indexed: Image.Image, source_rgb: Image.Image) -> Image.Image:
    """Keep small highlight colors (glasses lenses) from being merged into black."""
    src = source_rgb.load()
    px = list(indexed.getdata())
    colors = palette_from_indexed(indexed)

    for y in range(SPRITE_SIZE[1]):
        for x in range(SPRITE_SIZE[0]):
            c = src[x, y]
            if c not in PROTECTED_COLORS or is_magenta(c):
                continue
            px[y * SPRITE_SIZE[0] + x] = find_or_add_color(colors, c, px)

    out = apply_palette(indexed, colors)
    out.putdata(px)
    return out


def restore_outlines(indexed: Image.Image, source_rgb: Image.Image) -> Image.Image:
    """Re-apply source black outline pixels to a visible (non-zero) palette index."""
    src = source_rgb.load()
    px = list(indexed.getdata())
    colors = palette_from_indexed(indexed)
    outline_index = pick_outline_index(colors)
    colors[outline_index] = OUTLINE_COLOR

    for y in range(SPRITE_SIZE[1]):
        for x in range(SPRITE_SIZE[0]):
            if is_magenta(src[x, y]):
                continue
            if is_outline(src[x, y]):
                px[y * SPRITE_SIZE[0] + x] = outline_index

    out = apply_palette(indexed, colors)
    out.putdata(px)
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

    flat = Image.new("RGB", SPRITE_SIZE, QUANTIZE_FILL)
    src = rgb.load()
    flat_px = flat.load()
    for y in range(SPRITE_SIZE[1]):
        for x in range(SPRITE_SIZE[0]):
            c = src[x, y]
            flat_px[x, y] = QUANTIZE_FILL if is_magenta(c) else c

    indexed = flat.quantize(colors=MAX_COLORS, method=Image.Quantize.MEDIANCUT)

    px = list(indexed.getdata())
    for y in range(SPRITE_SIZE[1]):
        for x in range(SPRITE_SIZE[0]):
            if is_magenta(src[x, y]):
                px[y * SPRITE_SIZE[0] + x] = 0
    indexed.putdata(px)

    indexed = finalize_transparent_index(indexed)
    indexed = remove_orphans(indexed)
    indexed = preserve_exact_colors(indexed, rgb)
    indexed = restore_outlines(indexed, rgb)
    return finalize_transparent_index(indexed)


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
