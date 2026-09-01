"""Prep a photo for ASCII conversion.

Usage:
    python scripts/prep_photo.py source-photo.jpg [source-prepped.png]

A flatly-lit face converts to a dark, unreadable blob, and a busy
background prints as noise around the subject. Fix both:

  1. Isolate the subject. rembg if it is installed; otherwise an
     OpenCV grabCut pass seeded from a border rectangle (no downloads).
     Pass --keep-bg to skip this entirely.
  2. Composite onto pure white so the background maps to the blank end
     of the ASCII ramp (white -> spaces).
  3. Crop to the aspect ratio of the ASCII glyph grid, biased toward
     the top so the face is not cut off.
  4. Boost local contrast with CLAHE, then a gentle S-curve so a flat
     face gets real highlights and shadows at low resolution.

Output: a grayscale PNG.
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

# Matches the 100x53 glyph grid in make_ascii_svg.py: each glyph cell is
# about half as wide as it is tall, so 100*0.5 : 53 in pixels.
TARGET_WH = (100 * 0.5) / 53


def rembg_cut(rgb: np.ndarray) -> np.ndarray | None:
    try:
        from rembg import remove
    except Exception as exc:  # noqa: BLE001 - any import/runtime failure is fine
        print(f"  rembg unavailable ({exc}); falling back to grabCut")
        return None
    print("  isolating subject with rembg ...")
    cut = remove(Image.fromarray(rgb))  # RGBA
    arr = np.array(cut)
    alpha = arr[:, :, 3:4] / 255.0
    return (arr[:, :, :3] * alpha + 255 * (1 - alpha)).astype(np.uint8)


def grabcut_cut(rgb: np.ndarray, margin: float = 0.06, iters: int = 6) -> np.ndarray:
    print("  isolating subject with grabCut ...")
    h, w = rgb.shape[:2]
    mx, my = int(w * margin), int(h * margin)
    rect = (mx, my, w - 2 * mx, h - 2 * my)
    mask = np.zeros((h, w), np.uint8)
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    cv2.grabCut(bgr, mask, rect, bgd, fgd, iters, cv2.GC_INIT_WITH_RECT)
    fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    fg = cv2.GaussianBlur(fg, (7, 7), 0)
    alpha = (fg / 255.0)[:, :, None]
    return (rgb * alpha + 255 * (1 - alpha)).astype(np.uint8)


def crop_to_ratio(arr: np.ndarray, wh: float, top_bias: float = 0.10) -> np.ndarray:
    h, w = arr.shape[:2]
    if w / h > wh:  # too wide -> trim sides
        nw = int(round(h * wh))
        x = (w - nw) // 2
        return arr[:, x : x + nw]
    nh = int(round(w / wh))  # too tall -> trim top/bottom, keep more of the top
    y = int(round((h - nh) * top_bias))
    return arr[y : y + nh, :]


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--keep-bg"]
    keep_bg = "--keep-bg" in sys.argv
    if not args:
        print("usage: python scripts/prep_photo.py <source-photo> [output.png] [--keep-bg]")
        raise SystemExit(2)

    src = Path(args[0])
    out = Path(args[1]) if len(args) > 1 else Path("source-prepped.png")
    if not src.exists():
        print(f"no such file: {src}")
        raise SystemExit(1)

    rgb = np.array(Image.open(src).convert("RGB"))
    print(f"  loaded {src} ({rgb.shape[1]}x{rgb.shape[0]})")

    if keep_bg:
        print("  --keep-bg: leaving background untouched")
    else:
        cut = rembg_cut(rgb)
        rgb = cut if cut is not None else grabcut_cut(rgb)

    rgb = crop_to_ratio(rgb, TARGET_WH)

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    eq = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(gray)

    ramp = np.linspace(0.0, 1.0, 256)
    curve = np.clip(np.power(ramp, 0.85) * 255.0, 0, 255).astype(np.uint8)
    eq = cv2.LUT(eq, curve)

    Image.fromarray(eq).save(out)
    print(f"wrote {out} ({eq.shape[1]}x{eq.shape[0]}, {out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
