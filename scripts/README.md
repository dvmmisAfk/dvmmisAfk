# Profile art pipeline

Everything animated on the profile is a self-contained SVG committed to
this repo. GitHub strips `<script>` and sanitizes inline CSS from
READMEs but renders SVGs embedded via `<img>` and plays their SMIL /
CSS-keyframe animations, so all motion lives inside the SVG files.

## Files produced

| Output | Script | Refresh |
|---|---|---|
| `avi-ascii.svg` | `prep_photo.py` + `make_ascii_svg.py` | manual, when the photo changes |
| `info-card.svg` | `make_info_card.py` | manual, when your details change |
| `contrib-heatmap.svg` | `fetch_contributions.py` + `render_heatmap_svg.py` | daily, via GitHub Actions |

## One-time local setup

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r scripts/requirements.txt
```

## Regenerate the portrait (after changing your photo)

```bash
python scripts/prep_photo.py source-photo.jpg   # -> source-prepped.png
python scripts/make_ascii_svg.py                # -> avi-ascii.svg
```

`prep_photo.py` removes the background (rembg), composites onto white so
it maps to blank glyphs, crops to the glyph-grid aspect ratio, and
boosts local contrast with CLAHE. `rembg` is optional — without it the
step just keeps the original background.

## Regenerate the info card (after changing your details)

Edit the `ROWS` list in `make_info_card.py`, then:

```bash
python scripts/make_info_card.py               # -> info-card.svg
STATIC=1 python scripts/make_info_card.py       # frozen frame for previews
```

## Heatmap

```bash
python scripts/fetch_contributions.py           # -> data/contributions.json  (no token needed)
python scripts/render_heatmap_svg.py            # -> contrib-heatmap.svg
```

The daily workflow (`.github/workflows/update-profile-art.yml`) runs
these two on a cron and commits the result. `[skip ci]` in its commit
message stops the bot's own commit from re-triggering it. Trigger it
once by hand from the **Actions** tab to confirm it commits a fresh SVG.

Override the username with `python scripts/fetch_contributions.py <user>`
or `GH_USER=<user>`.
