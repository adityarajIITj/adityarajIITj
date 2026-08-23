#!/usr/bin/env python3
"""
fetch_contributions.py
Scrapes the public GitHub contribution calendar for adityarajIITj
and writes data/contributions.json with raw day data + derived stats.
No GitHub token required — uses the same public HTML fragment the profile page loads.
"""

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = "adityarajIITj"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUT_FILE = OUT_DIR / "contributions.json"


def fetch_html() -> str:
    """Fetch the raw contribution calendar HTML fragment."""
    resp = requests.get(URL, headers={"Accept": "text/html"}, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_days(html: str) -> list[dict]:
    """
    Extract per-day contribution data from the calendar table.
    Each <td> has data-date (YYYY-MM-DD) and data-level (0-4).
    The tooltip text contains the actual count, e.g. "5 contributions on January 4th."
    """
    soup = BeautifulSoup(html, "html.parser")
    days = []

    for td in soup.find_all("td", class_="ContributionCalendar-day"):
        date_str = td.get("data-date")
        level = int(td.get("data-level", 0))
        if not date_str:
            continue

        # Try to parse contribution count from the associated tooltip
        count = 0
        td_id = td.get("id", "")
        if td_id:
            tooltip = soup.find("tool-tip", attrs={"for": td_id})
            if tooltip:
                text = tooltip.get_text(strip=True)
                m = re.match(r"(\d+)\s+contribution", text)
                if m:
                    count = int(m.group(1))
                # "No contributions" → count stays 0

        days.append({
            "date": date_str,
            "count": count,
            "level": level,
        })

    # Sort chronologically
    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days: list[dict]) -> dict:
    """Derive streak, best-day, monthly totals, and total from raw day data."""
    total = sum(d["count"] for d in days)

    # --- Streaks ---
    current_streak = 0
    longest_streak = 0
    streak = 0
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Walk backwards from today to compute current streak
    date_map = {d["date"]: d["count"] for d in days}
    d = datetime.now(timezone.utc)
    while True:
        ds = d.strftime("%Y-%m-%d")
        if date_map.get(ds, 0) > 0:
            current_streak += 1
            d -= timedelta(days=1)
        else:
            # Allow today to have 0 if it's still early
            if ds == today:
                d -= timedelta(days=1)
                continue
            break

    # Longest streak (scan forward)
    for day in days:
        if day["count"] > 0:
            streak += 1
            longest_streak = max(longest_streak, streak)
        else:
            streak = 0

    # Best day
    best_day = max(days, key=lambda d: d["count"]) if days else {"date": "", "count": 0}

    # Monthly totals
    monthly: dict[str, int] = {}
    for day in days:
        month_key = day["date"][:7]  # YYYY-MM
        monthly[month_key] = monthly.get(month_key, 0) + day["count"]

    return {
        "total": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": {"date": best_day["date"], "count": best_day["count"]},
        "monthly_totals": monthly,
    }


def main():
    print(f"Fetching contributions for {USERNAME}...")
    html = fetch_html()
    days = parse_days(html)
    print(f"  Parsed {len(days)} day cells.")

    stats = compute_stats(days)
    print(f"  Total contributions: {stats['total']}")
    print(f"  Current streak: {stats['current_streak']} days")
    print(f"  Longest streak: {stats['longest_streak']} days")
    print(f"  Best day: {stats['best_day']['date']} ({stats['best_day']['count']})")

    payload = {
        "username": USERNAME,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days": days,
        "stats": stats,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"  Written -> {OUT_FILE}")


if __name__ == "__main__":
    main()
