"""Generate Toepfer FireRed title screen graphics."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
TITLE_DIR = ROOT / "graphics/title_screen/firered"
SHARED_DIR = ROOT / "graphics/title_screen"
TOEPFER_SRC = ROOT / "docs/base-toepfer-front.png"

LOGO_SIZE = (256, 64)
LOGO_CHROMA = (0, 255, 41)
MON_SIZE = (96, 96)
MON_CHROMA = (0, 0, 255)

# 5x7 pixel font (1 = ink)
FONT: dict[str, list[str]] = {
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
}

YELLOW = (255, 222, 0)
BLUE = (0, 90, 206)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
TAN = (210, 180, 130)


def draw_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    origin: tuple[int, int],
    scale: int,
    fill: tuple[int, int, int],
    outline: tuple[int, int, int] | None = None,
) -> int:
    x, y = origin
    for ch in text:
        pattern = FONT.get(ch, FONT[" "])
        for row, line in enumerate(pattern):
            for col, bit in enumerate(line):
                if bit != "1":
                    continue
                px = x + col * scale
                py = y + row * scale
                if outline:
                    for ox, oy in (
                        (-scale, 0),
                        (scale, 0),
                        (0, -scale),
                        (0, scale),
                        (-scale, -scale),
                        (scale, -scale),
                        (-scale, scale),
                        (scale, scale),
                    ):
                        draw.rectangle(
                            [px + ox, py + oy, px + ox + scale - 1, py + oy + scale - 1],
                            fill=outline,
                        )
                draw.rectangle(
                    [px, py, px + scale - 1, py + scale - 1],
                    fill=fill,
                )
        x += (len(pattern[0]) + 1) * scale
    return x


def to_indexed(img: Image.Image, chroma: tuple[int, int, int], max_colors: int) -> Image.Image:
    rgb = img.convert("RGB")
    indexed = rgb.quantize(colors=max_colors, method=Image.Quantize.MEDIANCUT)
    palette = indexed.getpalette() or []
    colors = [tuple(palette[i : i + 3]) for i in range(0, len(palette), 3)]
    try:
        chroma_idx = colors.index(chroma)
    except ValueError:
        chroma_idx = None
    if chroma_idx != 0:
        pixels = list(indexed.getdata())
        if chroma_idx is None:
            pixels = [0 if rgb.getpixel((i % indexed.width, i // indexed.width)) == chroma else p
                      for i, p in enumerate(pixels)]
        else:
            pixels = [0 if p == chroma_idx else (p if p != 0 else chroma_idx) for p in pixels]
            colors[0], colors[chroma_idx] = colors[chroma_idx], colors[0]
        flat = [c for rgb in colors for c in rgb]
        indexed.putpalette(flat + [0] * (768 - len(flat)))
        indexed.putdata(pixels)
    return indexed


def write_jasc_pal(path: Path, colors: list[tuple[int, int, int]]) -> None:
    lines = ["JASC-PAL", "0100", str(len(colors))]
    for r, g, b in colors:
        lines.append(f"{r} {g} {b}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_logo() -> None:
    img = Image.new("RGB", LOGO_SIZE, LOGO_CHROMA)
    draw = ImageDraw.Draw(img)
    draw_text(draw, "TOEPFER", (8, 10), scale=3, fill=YELLOW, outline=BLUE)
    draw_text(draw, "RED", (168, 12), scale=2, fill=WHITE, outline=BLACK)
    draw_text(draw, "VERSION", (156, 30), scale=2, fill=WHITE, outline=BLACK)
    out = to_indexed(img, LOGO_CHROMA, 256)
    out.save(TITLE_DIR / "game_title_logo.png")


def generate_box_art() -> None:
    canvas = Image.new("RGB", MON_SIZE, MON_CHROMA)
    src = Image.open(TOEPFER_SRC).convert("RGBA")
    # Fit Toepfer sprite in the center with NEAREST upscale.
    bbox = src.getbbox()
    if bbox:
        src = src.crop(bbox)
    target = 72
    ratio = min(target / src.width, target / src.height)
    size = (max(1, int(src.width * ratio)), max(1, int(src.height * ratio)))
    sprite = src.resize(size, Image.Resampling.NEAREST)
    ox = (MON_SIZE[0] - size[0]) // 2
    oy = (MON_SIZE[1] - size[1]) // 2
    canvas.paste(sprite, (ox, oy), sprite)
    out = to_indexed(canvas, MON_CHROMA, 16)
    out.save(TITLE_DIR / "box_art_mon.png")
    colors = [tuple((out.getpalette() or [0] * 768)[i : i + 3]) for i in range(0, 48, 3)]
    write_jasc_pal(TITLE_DIR / "box_art_mon.pal", colors)


def generate_background_pal() -> None:
    # Corporate office palette: tan header, grey-blue main, burgundy footer band.
    colors = [
        (210, 190, 150),
        (0, 0, 0),
        (90, 90, 90),
        (150, 150, 150),
        (190, 190, 190),
        (255, 255, 255),
        (0, 0, 0),
        (90, 90, 90),
        (150, 150, 150),
        (190, 190, 190),
        (255, 255, 255),
        (95, 125, 140),
        (80, 30, 30),
        (110, 40, 40),
        (140, 55, 55),
        (170, 70, 70),
    ]
    write_jasc_pal(TITLE_DIR / "background.pal", colors)


def main() -> None:
    if not TOEPFER_SRC.is_file():
        raise SystemExit(f"Missing Toepfer master sprite: {TOEPFER_SRC}")
    generate_logo()
    generate_box_art()
    generate_background_pal()
    print("Generated Toepfer title screen assets in graphics/title_screen/firered/")


if __name__ == "__main__":
    main()
