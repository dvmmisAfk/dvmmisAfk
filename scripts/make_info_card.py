"""Generate info-card.svg -- a neofetch-style panel that prints line by line.

The contribution heatmap already covers the GitHub numbers, so this card
carries the story the numbers can't: role, current work, stack, the wins.

Each line fades and slides in on a short stagger (SMIL, so GitHub plays
it). Set STATIC=1 to emit a frozen final frame for local previews.
"""
from __future__ import annotations

import os
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path("info-card.svg")
STATIC = os.environ.get("STATIC") == "1"

BG = "#0d1117"
BORDER = "#30363d"
TITLE = "#39d353"
KEY = "#58a6ff"
SEP = "#6e7681"
VAL = "#c9d1d9"

TITLE_LINE = "divyam@vit-bhopal"
ROWS: list[tuple[str, str]] = [
    ("Role", "Full-Stack Developer / ML Researcher"),
    ("Now", "SWE Intern - TechMasterAI, AgeWell, EvePaper"),
    ("Stack", "React, Node, Express, MongoDB, FastAPI"),
    ("ML", "scikit-learn, pandas, numpy, OpenCV"),
    ("Papers", "3 published - IJNRD, IJRAR, IRJ"),
    ("Wins", "SEBI National Finalist, Code Garuda 2nd Runner-Up"),
    ("Edu", "B.Tech CS @ VIT Bhopal"),
    ("Loc", "Lucknow, India"),
]
SWATCHES = ["#f85149", "#39d353", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#c9d1d9"]

PAD = 18
LINE_H = 22
KEY_W = 66
CHAR_W = 7.3
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"

STAGGER = 0.11
DUR = 0.32


def main() -> None:
    n = len(ROWS)
    row_px = [KEY_W + 2 * CHAR_W + len(v) * CHAR_W for _, v in ROWS]
    width = int(round(max(row_px + [len(TITLE_LINE) * CHAR_W]) + PAD * 2))
    height = PAD * 2 + LINE_H * (n + 3)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{escape(FONT)}" font-size="13">',
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="8" '
        f'fill="{BG}" stroke="{BORDER}"/>',
    ]

    def row(i: int, inner: str) -> str:
        y = PAD + LINE_H * (i + 1)
        if STATIC:
            return f'<g transform="translate({PAD} {y})">{inner}</g>'
        begin = round(i * STAGGER, 3)
        return (
            f'<g transform="translate({PAD - 9} {y})" opacity="0">'
            f'<animate attributeName="opacity" from="0" to="1" '
            f'begin="{begin}s" dur="{DUR}s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="{PAD - 9} {y}" to="{PAD} {y}" begin="{begin}s" '
            f'dur="{DUR}s" calcMode="spline" keySplines="0.2 0.8 0.2 1" '
            f'fill="freeze"/>{inner}</g>'
        )

    out.append(row(0, f'<text fill="{TITLE}" font-weight="700">{escape(TITLE_LINE)}</text>'))
    out.append(row(1, f'<text fill="{SEP}">{"-" * len(TITLE_LINE)}</text>'))
    for idx, (k, v) in enumerate(ROWS):
        inner = (
            f'<text fill="{KEY}" font-weight="700">{escape(k)}</text>'
            f'<text x="{KEY_W:.0f}" fill="{SEP}">:</text>'
            f'<text x="{KEY_W + 2 * CHAR_W:.0f}" fill="{VAL}">{escape(v)}</text>'
        )
        out.append(row(idx + 2, inner))

    swg = "".join(
        f'<rect x="{j * 22}" y="-11" width="18" height="12" rx="2" fill="{c}"/>'
        for j, c in enumerate(SWATCHES)
    )
    out.append(row(n + 2, swg))

    out.append("</svg>")
    OUT.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {OUT} ({width}x{height})")


if __name__ == "__main__":
    main()
