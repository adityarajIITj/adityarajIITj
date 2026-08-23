#!/usr/bin/env python3
"""
make_ascii_svg.py
Converts source-prepped.png into a monochrome self-typing ASCII art SVG.
Each row wipes left-to-right with a cursor block, staggered top to bottom.
The animation plays once and freezes — no looping.

Design choices:
  - Monochrome light-gray: avoids the noisy rainbow look of per-char coloring
  - High contrast: busy background maps to space glyphs, only the subject prints
  - SMIL animation: works natively on GitHub (no JS, no external CSS)
"""

from pathlib import Path
from PIL import Image

SOURCE = Path(__file__).resolve().parent.parent / "source-prepped.png"
OUT_FILE = Path(__file__).resolve().parent.parent / "avi-ascii.svg"

# Bright (sparse) → Dark (dense)
# Leading space clears the background to nothing
RAMP = " .`':-=+*cs#%@"

# Grid dimensions
COLS = 100
ROWS = 53

# SVG text sizing
CHAR_W = 6.6     # approximate width of a monospace character at font-size 10
CHAR_H = 11.0    # line height
FONT_SIZE = 10
TEXT_COLOR = "#b0b8c4"   # light gray — monochrome look
BG_COLOR = "#0d1117"     # dark terminal background
CURSOR_COLOR = "#39d353" # green cursor block

# Animation timing
ROW_WIPE_DURATION = 0.6   # seconds per row wipe
ROW_STAGGER = 0.04        # seconds between row start times
CURSOR_WIDTH = CHAR_W * 2


def load_and_sample(path: Path) -> list[list[int]]:
    """Load grayscale image and downsample to COLS×ROWS grid of brightness values (0-255)."""
    img = Image.open(path).convert("L")
    img = img.resize((COLS, ROWS), Image.Resampling.LANCZOS)
    pixels = list(img.getdata())
    grid = []
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            row.append(pixels[r * COLS + c])
        grid.append(row)
    return grid


def brightness_to_char(brightness: int) -> str:
    """Map a 0-255 brightness value to an ASCII character from the density ramp."""
    # Invert: bright pixels → sparse chars, dark pixels → dense chars
    # brightness 255 (white) → index 0 (space)
    # brightness 0 (black) → last index (dense)
    idx = int((255 - brightness) / 255 * (len(RAMP) - 1))
    idx = max(0, min(len(RAMP) - 1, idx))
    return RAMP[idx]


def escape_xml(ch: str) -> str:
    """Escape special XML characters."""
    if ch == "&":
        return "&amp;"
    if ch == "<":
        return "&lt;"
    if ch == ">":
        return "&gt;"
    if ch == '"':
        return "&quot;"
    if ch == "'":
        return "&apos;"
    return ch


def build_svg(grid: list[list[int]]) -> str:
    svg_w = COLS * CHAR_W + 20
    svg_h = ROWS * CHAR_H + 20
    total_duration = ROW_STAGGER * ROWS + ROW_WIPE_DURATION

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
                 f'xmlns:xlink="http://www.w3.org/1999/xlink" '
                 f'width="{svg_w:.1f}" height="{svg_h:.1f}" '
                 f'viewBox="0 0 {svg_w:.1f} {svg_h:.1f}">')

    # Background
    parts.append(f'<rect width="{svg_w:.1f}" height="{svg_h:.1f}" fill="{BG_COLOR}"/>')

    # Defs: clipPaths for each row's wipe reveal
    parts.append('<defs>')
    for r in range(ROWS):
        clip_id = f"clip-row-{r}"
        row_w = COLS * CHAR_W
        row_y = 6 + r * CHAR_H
        begin_time = r * ROW_STAGGER

        parts.append(f'<clipPath id="{clip_id}">')
        parts.append(f'  <rect x="10" y="{row_y:.1f}" width="0" height="{CHAR_H + 2}">')
        parts.append(f'    <animate attributeName="width" '
                     f'from="0" to="{row_w:.1f}" '
                     f'dur="{ROW_WIPE_DURATION}s" '
                     f'begin="{begin_time:.3f}s" '
                     f'fill="freeze"/>')
        parts.append(f'  </rect>')
        parts.append(f'</clipPath>')
    parts.append('</defs>')

    # Render each row as a <text> element clipped by its wipe
    for r in range(ROWS):
        clip_id = f"clip-row-{r}"
        text_y = 6 + r * CHAR_H + FONT_SIZE
        begin_time = r * ROW_STAGGER

        # Build the text content for this row
        row_text = ""
        for c in range(COLS):
            ch = brightness_to_char(grid[r][c])
            row_text += escape_xml(ch)

        parts.append(f'<g clip-path="url(#{clip_id})">')
        parts.append(f'  <text x="10" y="{text_y:.1f}" '
                     f'font-family="Menlo,Monaco,Consolas,\'Courier New\',monospace" '
                     f'font-size="{FONT_SIZE}" '
                     f'fill="{TEXT_COLOR}" '
                     f'xml:space="preserve">{row_text}</text>')
        parts.append(f'</g>')

        # Cursor block: rides the wipe edge
        cursor_y = 6 + r * CHAR_H
        parts.append(f'<rect x="10" y="{cursor_y:.1f}" '
                     f'width="{CURSOR_WIDTH:.1f}" height="{CHAR_H:.1f}" '
                     f'fill="{CURSOR_COLOR}" opacity="0.85" rx="1">')
        # Animate cursor position
        parts.append(f'  <animate attributeName="x" '
                     f'from="10" to="{10 + COLS * CHAR_W:.1f}" '
                     f'dur="{ROW_WIPE_DURATION}s" '
                     f'begin="{begin_time:.3f}s" '
                     f'fill="freeze"/>')
        # Fade out cursor after row finishes
        end_time = begin_time + ROW_WIPE_DURATION
        parts.append(f'  <animate attributeName="opacity" '
                     f'from="0.85" to="0" '
                     f'dur="0.15s" '
                     f'begin="{end_time:.3f}s" '
                     f'fill="freeze"/>')
        # Keep cursor invisible until its row starts
        parts.append(f'  <set attributeName="opacity" to="0" '
                     f'begin="0s" />')
        parts.append(f'  <set attributeName="opacity" to="0.85" '
                     f'begin="{begin_time:.3f}s" />')
        parts.append(f'</rect>')

    parts.append('</svg>')
    return '\n'.join(parts)


def main():
    if not SOURCE.exists():
        print(f"ERROR: {SOURCE} not found.")
        print("Run  python scripts/prep_photo.py  first to generate the prepped image.")
        raise SystemExit(1)

    grid = load_and_sample(SOURCE)
    print(f"Loaded {COLS}×{ROWS} grid from {SOURCE}")

    svg = build_svg(grid)
    OUT_FILE.write_text(svg, encoding="utf-8")
    print(f"Written -> {OUT_FILE}  ({len(svg):,} bytes)")


if __name__ == "__main__":
    main()
