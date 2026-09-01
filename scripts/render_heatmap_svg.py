"""Render data/contributions.json as contrib-heatmap.svg.

The classic 53-week x 7-day calendar of rounded, colored boxes. It
reveals once with a diagonal, line-after-line slide-down (CSS keyframes
that play on load, then freeze -- no looping glow), with a Less->More
legend and a stats footer.

CSS animation inside an SVG runs in GitHub's <img> context; SMIL is not
needed here and keyframes keep the per-cell stagger compact.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

DATA = Path("data/contributions.json")
OUT = Path("contrib-heatmap.svg")

CELL = 13
GAP = 3
PAD = 16
TOP = 34
STEP = CELL + GAP

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BG = "#0d1117"
TEXT = "#8b949e"
BRIGHT = "#c9d1d9"

REVEAL_STEP = 0.012  # seconds added per (col + row) diagonal


def to_weeks(days: list[dict]) -> list[list[dict | None]]:
    if not days:
        return []
    first = date.fromisoformat(days[0]["date"])
    lead = (first.weekday() + 1) % 7  # calendar columns start on Sunday
    cells: list[dict | None] = [None] * lead + list(days)
    return [cells[i : i + 7] for i in range(0, len(cells), 7)]


def level_of(cell: dict) -> int:
    lv = cell.get("level")
    if lv is None:
        c = cell["count"]
        lv = 0 if c == 0 else 1 if c < 3 else 2 if c < 6 else 3 if c < 10 else 4
    if lv >= 4 and cell["count"] >= 15:  # neon top end for the very best days
        return 5
    return lv


def main() -> None:
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    days = payload["days"]
    st = payload["stats"]
    weeks = to_weeks(days)

    w = PAD * 2 + len(weeks) * STEP
    h = TOP + 7 * STEP + 48

    css = (
        "@keyframes pop{from{opacity:0;transform:translateY(-3px)}"
        "to{opacity:1;transform:translateY(0)}}"
        ".c{opacity:0;animation:pop .34s ease-out forwards}"
        f"text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;fill:{TEXT}}}"
    )
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}">',
        f"<style>{css}</style>",
        f'<rect width="100%" height="100%" rx="10" fill="{BG}"/>',
        f'<text x="{PAD}" y="21" font-size="13" fill="{BRIGHT}">'
        f'{st["total"]:,} contributions in the last year</text>',
    ]

    seen: set[str] = set()
    for ci, col in enumerate(weeks):
        anchor = next((c for c in col if c), None)
        if not anchor:
            continue
        d = date.fromisoformat(anchor["date"])
        key = anchor["date"][:7]
        if key not in seen and d.day <= 7:
            seen.add(key)
            out.append(
                f'<text x="{PAD + ci * STEP}" y="{TOP - 6}" font-size="10">'
                f'{d.strftime("%b")}</text>'
            )

    for ci, col in enumerate(weeks):
        for ri, cell in enumerate(col):
            if cell is None:
                continue
            x = PAD + ci * STEP
            y = TOP + ri * STEP
            delay = (ci + ri) * REVEAL_STEP
            out.append(
                f'<rect class="c" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="3" fill="{PALETTE[level_of(cell)]}" '
                f'style="animation-delay:{delay:.2f}s">'
                f'<title>{cell["count"]} on {cell["date"]}</title></rect>'
            )

    legend_w = 5 * (CELL + 4)
    lx = w - PAD - legend_w - 34
    ly = h - 30
    out.append(f'<text x="{lx - 6}" y="{ly + 10}" font-size="10" text-anchor="end">Less</text>')
    for k, colr in enumerate(PALETTE[:5]):
        out.append(
            f'<rect x="{lx + k * (CELL + 4)}" y="{ly}" width="{CELL}" height="{CELL}" '
            f'rx="3" fill="{colr}"/>'
        )
    out.append(f'<text x="{lx + legend_w + 6}" y="{ly + 10}" font-size="10">More</text>')

    best = st["best_day"]
    footer = (
        f'current streak {st["current_streak"]}d  .  longest {st["longest_streak"]}d'
        f'  .  best day {best["count"]} ({best["date"]})'
    )
    if payload.get("estimated_counts"):
        footer += "  .  counts approx"
    out.append(f'<text x="{PAD}" y="{h - 12}" font-size="11">{footer}</text>')

    out.append("</svg>")
    OUT.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {OUT} ({w}x{h}, {len(weeks)} weeks)")


if __name__ == "__main__":
    main()
