#!/usr/bin/env python3
"""
make_info_card.py
Hand-authors a neofetch-style info card SVG with animated key/value rows.
Each line fades and slides in on a short stagger to look like it's printing.
Set STATIC=1 env var for a frozen-frame preview (no animation).
"""

import os
from pathlib import Path

OUT_FILE = Path(__file__).resolve().parent.parent / "info-card.svg"
STATIC = os.environ.get("STATIC", "0") == "1"

USERNAME = "adityarajIITj"

# ─── Info rows: (key, value, key_color) ───
ROWS = [
    ("Now",        "B.Tech @ IIT Jodhpur",                              "#69f0a0"),
    ("Prev",       "Building cool side-projects",                       "#39d353"),
    ("Stack",      "Python · C++ · JS/TS · React · Node · Git",        "#26a641"),
    ("Highlights", "Open-source contributor · Real world solutions",   "#0e9444"),
]

# Layout
W = 490
ROW_H = 28
TITLE_H = 44
PAD_X = 20
PAD_Y = 14
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji'"
TERM_BG = "#0d1117"
TITLE_BG = "#161b22"
TITLE_FG = "#c9d1d9"
VALUE_FG = "#8b949e"
SEPARATOR_COLOR = "#21262d"


def build_svg():
    n = len(ROWS)
    H = PAD_Y + TITLE_H + n * ROW_H + PAD_Y + 30  # extra for separator + color bar

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')

    # ─── Styles ───
    if not STATIC:
        lines.append('<style>')
        lines.append('''
          @keyframes infoFadeSlide {
            0%   { opacity: 0; transform: translateX(-12px); }
            100% { opacity: 1; transform: translateX(0); }
          }
          .info-row {
            opacity: 0;
            animation: infoFadeSlide 0.4s ease-out forwards;
          }
        ''')
        lines.append('</style>')

    # ─── Background ───
    lines.append(f'<rect width="{W}" height="{H}" rx="8" fill="{TERM_BG}"/>')

    # ─── Title bar ───
    lines.append(f'<rect width="{W}" height="{TITLE_H}" rx="8" fill="{TITLE_BG}"/>')
    lines.append(f'<rect x="0" y="{TITLE_H - 8}" width="{W}" height="8" fill="{TITLE_BG}"/>')

    # Traffic light dots
    dot_y = TITLE_H // 2
    for i, color in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        cx = PAD_X + i * 22
        lines.append(f'<circle cx="{cx}" cy="{dot_y}" r="6" fill="{color}"/>')

    # Title text
    title_x = PAD_X + 80
    lines.append(
        f'<text x="{title_x}" y="{dot_y + 5}" fill="{TITLE_FG}" '
        f'font-family="{FONT}" font-size="14" font-weight="bold">'
        f'{USERNAME}@github</text>'
    )

    # ─── Separator line ───
    sep_y = TITLE_H + PAD_Y
    lines.append(f'<line x1="{PAD_X}" y1="{sep_y}" x2="{W - PAD_X}" y2="{sep_y}" stroke="{SEPARATOR_COLOR}" stroke-width="1"/>')

    # ─── Info rows ───
    for i, (key, value, key_color) in enumerate(ROWS):
        y = TITLE_H + PAD_Y + 10 + i * ROW_H + ROW_H // 2
        delay = 0.8 + i * 0.25  # stagger after portrait starts printing

        anim_class = "info-row" if not STATIC else ""
        style = f'style="animation-delay:{delay:.2f}s"' if not STATIC else 'style="opacity:1"'

        lines.append(f'<g class="{anim_class}" {style}>')

        # Key (colored)
        lines.append(
            f'  <text x="{PAD_X + 8}" y="{y}" fill="{key_color}" '
            f'font-family="{FONT}" font-size="14" font-weight="600">'
            f'{key}</text>'
        )

        # Tilde separator
        sep_x = PAD_X + 110
        lines.append(
            f'  <text x="{sep_x}" y="{y}" fill="#484f58" '
            f'font-family="{FONT}" font-size="14">~</text>'
        )

        # Value
        val_x = sep_x + 18
        lines.append(
            f'  <text x="{val_x}" y="{y}" fill="{VALUE_FG}" '
            f'font-family="{FONT}" font-size="13">'
            f'{value}</text>'
        )

        lines.append('</g>')

    # ─── Color palette bar (neofetch-style) ───
    bar_y = TITLE_H + PAD_Y + 10 + n * ROW_H + 16
    palette = ["#282a36", "#ff5555", "#50fa7b", "#f1fa8c", "#bd93f9", "#ff79c6", "#8be9fd", "#f8f8f2"]
    block_w = 24
    block_h = 10
    bar_x = PAD_X + 8
    for i, color in enumerate(palette):
        x = bar_x + i * (block_w + 4)
        lines.append(f'<rect x="{x}" y="{bar_y}" width="{block_w}" height="{block_h}" rx="2" fill="{color}"/>')

    lines.append('</svg>')
    return '\n'.join(lines)


def main():
    svg = build_svg()
    OUT_FILE.write_text(svg, encoding="utf-8")
    mode = "STATIC" if STATIC else "ANIMATED"
    print(f"[{mode}] Written -> {OUT_FILE}  ({len(svg):,} bytes)")


if __name__ == "__main__":
    main()
