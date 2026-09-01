"""Fetch a GitHub contribution calendar without a token.

GitHub serves the calendar as public HTML at
    https://github.com/users/<username>/contributions
(the same fragment the profile page uses). We scrape the day cells and
write data/contributions.json: raw days plus derived stats.

Usage:
    python scripts/fetch_contributions.py [username]
    GH_USER=<username> python scripts/fetch_contributions.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USER = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GH_USER", "dvmmisAfk")).strip()
URL = f"https://github.com/users/{USER}/contributions"
OUT = Path("data/contributions.json")

# rough count when only the level is available (markup change / fallback)
LEVEL_COUNT = {0: 0, 1: 1, 2: 3, 3: 6, 4: 10, 5: 15}


def fetch_html() -> str:
    resp = requests.get(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; profile-art/1.0)",
            "Accept": "text/html",
            "X-Requested-With": "XMLHttpRequest",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.text


def parse_days(html: str) -> tuple[list[dict], bool]:
    soup = BeautifulSoup(html, "html.parser")

    tips: dict[str, int] = {}
    for tip in soup.select("tool-tip"):
        target = tip.get("for")
        if not target:
            continue
        match = re.match(r"\s*(\d[\d,]*)", tip.get_text(strip=True))
        tips[target] = int(match.group(1).replace(",", "")) if match else 0

    days: list[dict] = []
    for cell in soup.select("td.ContributionCalendar-day"):
        iso = cell.get("data-date")
        if not iso:
            continue
        level = int(cell.get("data-level") or 0)
        count = cell.get("data-count")
        if count is not None:
            count = int(count)
        elif cell.get("id") in tips:
            count = tips[cell["id"]]
        else:
            count = None
        days.append({"date": iso, "level": level, "count": count})

    days.sort(key=lambda d: d["date"])

    have_counts = any(d["count"] not in (None, 0) for d in days)
    estimated = not have_counts
    for d in days:
        if d["count"] is None or estimated:
            d["count"] = LEVEL_COUNT.get(d["level"], 0)
    return days, estimated


def derive_stats(days: list[dict]) -> dict:
    if not days:
        return {}
    total = sum(d["count"] for d in days)

    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)

    today = date.today().isoformat()
    current = 0
    for i, d in enumerate(reversed(days)):
        if i == 0 and d["count"] == 0 and d["date"] == today:
            continue  # today may simply not have started yet
        if d["count"] > 0:
            current += 1
        else:
            break

    best = max(days, key=lambda d: d["count"])
    months: dict[str, int] = {}
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]

    return {
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "months": months,
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
    }


def main() -> None:
    days, estimated = parse_days(fetch_html())
    if not days:
        raise SystemExit(f"no contribution cells found for '{USER}' -- check the username")
    payload = {
        "user": USER,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "estimated_counts": estimated,
        "days": days,
        "stats": derive_stats(days),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    note = " (counts estimated from levels)" if estimated else ""
    print(f"wrote {OUT}: {len(days)} days, {payload['stats']['total']} contributions{note}")


if __name__ == "__main__":
    main()
