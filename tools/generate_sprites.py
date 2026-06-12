"""Import Toepfer battle sprites for FireRed (64x64, 16-color GBA).

Copies the master front PNG to every Kanto species front.png and back.png.
Only processing applied: NEAREST resize to 64x64 and quantize to 16 colors
(first palette entry = transparent black) for gbagfx compatibility.
"""

from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "docs/toepfer-matrix.csv"
FRONT_BASE = ROOT / "docs/base-toepfer-front.png"
POKEMON_DIR = ROOT / "graphics/pokemon"
SPRITE_SIZE = (64, 64)
MAX_COLORS = 16
TRANSPARENT = (0, 0, 0)


def load_slugs() -> list[str]:
    with MATRIX.open(encoding="utf-8", newline="") as handle:
        return [row["slug"] for row in csv.DictReader(handle)]


def palette_from_indexed(img: Image.Image) -> list[tuple[int, int, int]]:
    raw = img.getpalette() or []
    colors: list[tuple[int, int, int]] = []
    for i in range(MAX_COLORS):
        offset = i * 3
        colors.append((raw[offset], raw[offset + 1], raw[offset + 2]))
    return colors


def write_jasc_pal(path: Path, colors: list[tuple[int, int, int]]) -> None:
    lines = ["JASC-PAL", "0100", str(MAX_COLORS)]
    for r, g, b in colors:
        lines.append(f"{r:4d} {g:4d} {b:4d}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def ensure_black_index_zero(img: Image.Image) -> Image.Image:
    """Remap palette so transparent black is palette index 0."""
    colors = palette_from_indexed(img)
    try:
        black_idx = colors.index(TRANSPARENT)
    except ValueError:
        black_idx = None

    if black_idx == 0:
        return img

    pixels = list(img.getdata())
    if black_idx is None:
        # Force unused slot 0 to black; remap darkest color to index 0.
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


def import_sprite(source: Image.Image) -> Image.Image:
    rgba = source.convert("RGBA")
    if rgba.size != SPRITE_SIZE:
        rgba = rgba.resize(SPRITE_SIZE, Image.Resampling.NEAREST)

    rgb = Image.new("RGB", SPRITE_SIZE, TRANSPARENT)
    rgb.paste(rgba, mask=rgba.split()[3])

    indexed = rgb.quantize(colors=MAX_COLORS, method=Image.Quantize.MEDIANCUT)
    return ensure_black_index_zero(indexed)


def main() -> None:
    if not FRONT_BASE.is_file():
        raise SystemExit(f"Missing master sprite: {FRONT_BASE}")
    if not MATRIX.is_file():
        raise SystemExit(f"Missing species matrix: {MATRIX}")

    master = Image.open(FRONT_BASE)
    front = import_sprite(master)
    back = front.copy()
    palette = palette_from_indexed(front)

    slugs = load_slugs()
    missing: list[str] = []
    updated = 0

    for slug in slugs:
        species_dir = POKEMON_DIR / slug
        if not species_dir.is_dir():
            missing.append(slug)
            continue

        front.save(species_dir / "front.png")
        back.save(species_dir / "back.png")
        write_jasc_pal(species_dir / "normal.pal", palette)
        write_jasc_pal(species_dir / "shiny.pal", palette)
        updated += 1

    print(f"Imported Toepfer sprites for {updated} species (front/back + palettes).")
    if missing:
        print(f"Warning: {len(missing)} slugs had no graphics folder: {', '.join(missing)}")


if __name__ == "__main__":
    main()
