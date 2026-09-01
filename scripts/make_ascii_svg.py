"""Turn source-prepped.png into a self-typing ASCII-art SVG.

Writes avi-ascii.svg: one light-gray, monochrome portrait that prints
row by row (an SMIL clip wipe with a small block cursor riding the
edge), staggered top to bottom, then freezes. No looping.

GitHub strips <script> and most inline CSS from READMEs but does run
SMIL animation inside an <img>-embedded SVG, which is why the motion
lives entirely in this file.
"""
from __future__ import annotations

import os
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image

SRC = Path(os.environ.get("ASCII_SRC", "source-prepped.png"))
OUT = Path("avi-ascii.svg")

COLS = 100
ROWS = 53
RAMP = " .`:-=+*cs#%@"          # bright (sparse) -> dark (dense); leading space clears bg

CELL_W = 7.2                    # px advance per glyph
CELL_H = 12.0                   # px per line
FONT_SIZE = 10.5
FILL = "#b8c0cc"               # single light-gray fill -- no per-char rainbow
BG = "#0d1117"
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"

ROW_DUR = 0.26                  # seconds to wipe one row
ROW_STAGGER = 0.05             # seconds between successive row starts


def sample() -> list[str]:
    img = Image.open(SRC).convert("L").resize((COLS, ROWS), Image.LANCZOS)
    px = img.load()
    last = len(RAMP) - 1
    lines: list[str] = []
    for y in range(ROWS):
        row = [RAMP[last - round(px[x, y] / 255.0 * last)] for x in range(COLS)]
        lines.append("".join(row).rstrip())
    return lines


def build(lines: list[str]) -> str:
    w = round(COLS * CELL_W)
    h = round(ROWS * CELL_H) + 8
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="{escape(FONT)}" '
        f'font-size="{FONT_SIZE}" xml:space="preserve">',
        f'<rect width="100%" height="100%" fill="{BG}"/>',
        f'<g fill="{FILL}">',
    ]
    for i, line in enumerate(lines):
        if not line:
            continue
        baseline = 11 + i * CELL_H
        top = baseline - CELL_H + 2
        begin = round(i * ROW_STAGGER, 3)
        row_w = len(line) * CELL_W
        cid = f"w{i}"
        out.append(
            f'<clipPath id="{cid}"><rect x="0" y="{top:.1f}" width="0" '
            f'height="{CELL_H:.1f}"><animate attributeName="width" from="0" '
            f'to="{row_w:.1f}" begin="{begin}s" dur="{ROW_DUR}s" '
            f'calcMode="linear" fill="freeze"/></rect></clipPath>'
        )
        out.append(f'<g clip-path="url(#{cid})">')
        out.append(f'<text x="0" y="{baseline:.1f}">{escape(line)}</text>')
        out.append(
            f'<rect x="0" y="{top:.1f}" width="{CELL_W:.1f}" '
            f'height="{CELL_H - 2:.1f}" opacity="0.85">'
            f'<animate attributeName="x" from="0" to="{row_w:.1f}" '
            f'begin="{begin}s" dur="{ROW_DUR}s" fill="freeze"/>'
            f'<animate attributeName="opacity" from="0.85" to="0" '
            f'begin="{round(begin + ROW_DUR, 3)}s" dur="0.12s" fill="freeze"/>'
            f'</rect>'
        )
        out.append("</g>")
    out.append("</g></svg>")
    return "\n".join(out)


if __name__ == "__main__":
    if not SRC.exists():
        raise SystemExit(f"missing {SRC} -- run: python scripts/prep_photo.py source-photo.jpg")
    OUT.write_text(build(sample()), encoding="utf-8")
    print(f"wrote {OUT}")
