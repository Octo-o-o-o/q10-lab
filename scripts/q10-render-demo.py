#!/usr/bin/env python3
"""Render Q10 monitor --demo pages into docs/images/*.png."""
from __future__ import print_function

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "images"
MONITOR = ROOT / "ai-terminal" / "q10_monitor.py"
WIDTH_COLS = 36
FONT_SIZE = 28
PAD_X = 28
PAD_Y = 24
BG = (13, 13, 13)
FG = (230, 225, 213)

FONT_CANDIDATES = [
    ROOT / "local-config" / "q10-cjk-mono.ttf",
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/System/Library/Fonts/STHeiti Light.ttc"),
    Path("/System/Library/Fonts/Menlo.ttc"),
    Path("/System/Library/Fonts/Supplemental/Courier New.ttf"),
]


def load_font(size):
    last = None
    for path in FONT_CANDIDATES:
        if not path.is_file():
            continue
        try:
            return ImageFont.truetype(str(path), size=size)
        except OSError as exc:
            last = exc
    raise SystemExit("no usable font: {0}".format(last))


def capture(page):
    raw = subprocess.check_output(
        [
            sys.executable,
            str(MONITOR),
            "--once",
            "--lang",
            "zh",
            "--demo",
            "--width",
            str(WIDTH_COLS),
            "--page",
            page,
        ],
        cwd=str(ROOT),
    )
    text = raw.decode("utf-8")
    return [line.replace("\n", "") for line in text.splitlines()]


def render_page(lines, font, cell_w, row_h):
    width = PAD_X * 2 + int(round(cell_w * WIDTH_COLS))
    height = PAD_Y * 2 + row_h * max(1, len(lines))
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    for row, line in enumerate(lines):
        y = PAD_Y + row * row_h
        draw.text((PAD_X, y), line[:WIDTH_COLS], font=font, fill=FG)
    return img


def main():
    font = load_font(FONT_SIZE)
    cell_w = font.getlength("限")
    bbox = font.getbbox("限")
    glyph_h = bbox[3] - bbox[1]
    row_h = glyph_h + 12
    pages = (("quota", "demo-quota.png"), ("tasks", "demo-tasks.png"), ("ask", "demo-ask.png"))
    frames = []
    OUT.mkdir(parents=True, exist_ok=True)
    for page, name in pages:
        lines = capture(page)
        img = render_page(lines, font, cell_w, row_h)
        dest = OUT / name
        img.save(dest, "PNG")
        print(dest.relative_to(ROOT), "{0}x{1}".format(*img.size), "lines", len(lines))
        frames.append(img)
    max_h = max(im.size[1] for im in frames)
    total_w = sum(im.size[0] for im in frames)
    strip = Image.new("RGB", (total_w, max_h), BG)
    x = 0
    for frame in frames:
        strip.paste(frame, (x, 0))
        x += frame.size[0]
    dest = OUT / "demo-pages.png"
    strip.save(dest, "PNG")
    print(dest.relative_to(ROOT), "{0}x{1}".format(*strip.size))


if __name__ == "__main__":
    main()
