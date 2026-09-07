#!/usr/bin/env python3
"""Make the Q10 Hei font monospaced.

Term49 sizes every cell by the advance of 'X'. The stock GB18030 Hei has
narrow Latin and wide CJK, so Chinese glyphs paint into the next cell.

Also stretches horizontal box-drawing glyphs (U+2500-U+257F, the ones whose
ink is wider than tall) so a run of U+2500 paints one continuous rule
instead of a dashed line: the original ink stops ~15% short of the cell
edge on both sides.
"""
from __future__ import print_function

import os
import sys


def stretch_rules(font, target):
    from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates

    cmap = font.getBestCmap()
    glyf = font["glyf"]
    hmtx = font["hmtx"].metrics
    fixed = 0
    for cp in range(0x2500, 0x2580):
        name = cmap.get(cp)
        if not name or name not in glyf:
            continue
        g = glyf[name]
        if g.numberOfContours <= 0:  # empty or composite
            continue
        w = g.xMax - g.xMin
        h = g.yMax - g.yMin
        if w <= 0 or h <= 0 or h > w * 0.5:
            continue
        if g.xMin <= 0 and g.xMax >= target:
            continue
        scale = float(target) / float(w)
        g.coordinates = GlyphCoordinates(
            [(int(round((x - g.xMin) * scale)), y) for (x, y) in g.coordinates]
        )
        g.xMin, g.xMax = 0, target
        hmtx[name] = (target, 0)
        fixed += 1
    return fixed

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "/tmp/q10-fonts/mhei.ttf"
    dst = sys.argv[2] if len(sys.argv) > 2 else "/tmp/q10-fonts/q10-cjk-mono.ttf"
    sys.path.insert(0, "/tmp/q10-fonttools")
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        print("需要 fontTools。先: python3 -m pip install --target /tmp/q10-fonttools fonttools", file=sys.stderr)
        return 2
    font = TTFont(src, lazy=False)
    cmap = font.getBestCmap()
    x_name = cmap.get(ord("X"))
    cjk_name = cmap.get(0x72B6)  # 状
    hmtx = font["hmtx"].metrics
    x_adv = hmtx[x_name][0] if x_name in hmtx else 1229
    cjk_adv = hmtx[cjk_name][0] if cjk_name in hmtx else 1843
    target = max(x_adv, cjk_adv)
    for name, (adv, lsb) in list(hmtx.items()):
        extra = target - adv
        hmtx[name] = (target, lsb + extra // 2)
    font["post"].isFixedPitch = 1
    font["hhea"].advanceWidthMax = target
    rules = stretch_rules(font, target)
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    font.save(dst)
    print("MONO %s  cell=%s  (X=%s CJK=%s rules=%s)" % (dst, target, x_adv, cjk_adv, rules))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
