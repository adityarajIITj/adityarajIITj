#!/usr/bin/env python3
"""
render_heatmap_svg.py
Reads data/contributions.json and renders an animated 53×7 contribution
heatmap SVG with GitHub-green palette, month/day labels, legend, and stats footer.
Animation: diagonal line-after-line slide-down reveal, plays once and freezes.
"""

import json
import math
from datetime import datetime, timedelta
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "contributions.json"
OUT_FILE = Path(__file__).resolve().parent.parent / "contrib-heatmap.svg"

# GitHub-ish green ramp (level 0–5; level 5 = neon top-end for visual pop)
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

# Layout constants
CELL = 13          # cell size px
GAP = 3            # gap between cells
CORNER = 2         # border-radius
LEFT_LABEL_W = 36  # space for Mon/Wed/Fri labels
TOP_LABEL_H = 20   # space for month labels
PAD_X = 20         # horizontal padding
PAD_Y = 20         # top padding
FOOTER_H = 50      # space for legend + stats line

DAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""]
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load_data():
    raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return raw["days"], raw["stats"]


def build_week_grid(days):
    """
    Organize days into a 53-week × 7-day grid.
    Returns list of weeks, where each week is a list of (date, count, level) or None.
    Also returns the date of the first Sunday (start of the grid).
    """
    if not days:
        return [], None

    first_date = datetime.strptime(days[0]["date"], "%Y-%m-%d")
    # Align to the start-of-week (Sunday)
    start = first_date - timedelta(days=first_date.weekday() + 1)
    if start > first_date:
        start -= timedelta(days=7)

    date_map = {d["date"]: d for d in days}

    weeks = []
    current = start
    last_date = datetime.strptime(days[-1]["date"], "%Y-%m-%d")

    while current <= last_date:
        week = []
        for dow in range(7):
            d = current + timedelta(days=dow)
            ds = d.strftime("%Y-%m-%d")
            if ds in date_map:
                entry = date_map[ds]
                week.append((ds, entry["count"], entry["level"]))
            else:
                week.append(None)
        weeks.append(week)
        current += timedelta(days=7)

    return weeks, start


def month_labels(weeks, start):
    """Generate (week_index, month_name) for the first week of each month."""
    labels = []
    prev_month = -1
    for wi, week in enumerate(weeks):
        for day_data in week:
            if day_data is not None:
                d = datetime.strptime(day_data[0], "%Y-%m-%d")
                if d.month != prev_month:
                    labels.append((wi, MONTH_NAMES[d.month - 1]))
                    prev_month = d.month
                break
    return labels


def render_svg(weeks, start, stats):
    n_weeks = len(weeks)
    grid_w = n_weeks * (CELL + GAP) - GAP
    grid_h = 7 * (CELL + GAP) - GAP

    svg_w = PAD_X * 2 + LEFT_LABEL_W + grid_w
    svg_h = PAD_Y * 2 + TOP_LABEL_H + grid_h + FOOTER_H

    grid_ox = PAD_X + LEFT_LABEL_W
    grid_oy = PAD_Y + TOP_LABEL_H

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}">')
    parts.append('<style>')
    parts.append('''
      @keyframes fadeSlideIn {
        0% { opacity: 0; transform: translateY(-8px); }
        100% { opacity: 1; transform: translateY(0); }
      }
      .hm-cell {
        opacity: 0;
        animation: fadeSlideIn 0.3s ease-out forwards;
      }
      text { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
    ''')
    parts.append('</style>')

    # Background
    parts.append(f'<rect width="{svg_w}" height="{svg_h}" rx="6" fill="#0d1117"/>')

    # Month labels
    m_labels = month_labels(weeks, start)
    for wi, name in m_labels:
        x = grid_ox + wi * (CELL + GAP)
        y = PAD_Y + 14
        parts.append(f'<text x="{x}" y="{y}" fill="#8b949e" font-size="11">{name}</text>')

    # Day-of-week labels
    for dow, label in enumerate(DAY_LABELS):
        if label:
            y = grid_oy + dow * (CELL + GAP) + CELL - 2
            parts.append(f'<text x="{PAD_X}" y="{y}" fill="#8b949e" font-size="11" text-anchor="start">{label}</text>')

    # Day cells with staggered animation
    cell_idx = 0
    for wi, week in enumerate(weeks):
        for dow, day_data in enumerate(week):
            if day_data is None:
                continue
            date_str, count, level = day_data
            # Clamp level to palette range
            lvl = min(level, len(PALETTE) - 1)
            # Map higher counts to level 5 (neon) if level is already 4
            if count >= 10 and lvl < 5:
                lvl = min(5, lvl + 1)

            color = PALETTE[lvl]
            x = grid_ox + wi * (CELL + GAP)
            y = grid_oy + dow * (CELL + GAP)

            # Diagonal stagger: delay based on (week + dow)
            delay = (wi + dow) * 0.012
            parts.append(
                f'<rect class="hm-cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="{CORNER}" fill="{color}" style="animation-delay:{delay:.3f}s">'
                f'<title>{date_str}: {count} contributions</title></rect>'
            )
            cell_idx += 1

    # ─── Legend ───
    legend_y = grid_oy + grid_h + 20
    legend_x = grid_ox + grid_w - 180

    parts.append(f'<text x="{legend_x}" y="{legend_y + 10}" fill="#8b949e" font-size="11">Less</text>')
    for i, color in enumerate(PALETTE):
        bx = legend_x + 32 + i * (CELL + 3)
        parts.append(f'<rect x="{bx}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="{CORNER}" fill="{color}"/>')
    more_x = legend_x + 32 + len(PALETTE) * (CELL + 3) + 4
    parts.append(f'<text x="{more_x}" y="{legend_y + 10}" fill="#8b949e" font-size="11">More</text>')

    # Stats line
    total = stats["total"]
    stats_text = f"{total:,} contributions in the last year"
    parts.append(
        f'<text x="{grid_ox}" y="{legend_y + 10}" fill="#8b949e" font-size="11">{stats_text}</text>'
    )

    # Streak info (subtle, right-aligned below legend)
    streak_y = legend_y + 24
    cur = stats.get("current_streak", 0)
    longest = stats.get("longest_streak", 0)
    streak_text = f"Current streak: {cur} days  ·  Longest: {longest} days"
    parts.append(
        f'<text x="{grid_ox}" y="{streak_y}" fill="#484f58" font-size="10">{streak_text}</text>'
    )

    parts.append('</svg>')
    return '\n'.join(parts)


def main():
    days, stats = load_data()
    weeks, start = build_week_grid(days)
    print(f"Grid: {len(weeks)} weeks, {sum(1 for w in weeks for d in w if d)} day cells")

    svg = render_svg(weeks, start, stats)
    OUT_FILE.write_text(svg, encoding="utf-8")
    print(f"Written -> {OUT_FILE}  ({len(svg):,} bytes)")


if __name__ == "__main__":
    main()
