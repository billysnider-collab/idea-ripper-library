#!/usr/bin/env python3
"""Bake the IDEA RIPPER visual lock (Billy lock, 2026-09-23).

Outputs (all pure-vector, no font dependency):
  wordmark-inline.svg  - black IDEA RIPPER, red tear through RIPPER (site header, inline)
  wordmark-mono.svg    - single-color version: black halves, paper gap, black rip line
  r-mark.svg           - torn-page R tile (favicon / seal)
"""
import re
import random
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.font_manager import FontProperties
from matplotlib.text import TextPath

INK = "#14110c"
PAPER = "#f2e8d5"
YELLOW = "#ffd21f"
RED = "#d92b1f"
FONT = "/usr/share/fonts/truetype/noto/NotoSans-CondensedBlack.ttf"
FP = FontProperties(fname=FONT)

plt.rcParams["svg.fonttype"] = "path"


def cap_height(fontsize):
    return TextPath((0, 0), "H", size=fontsize, prop=FP).get_extents().height


def wordmark(band_color, edge_color=None, out="wordmark-inline.svg"):
    """Manual SVG assembly: baked glyph paths, jagged rip through RIPPER.

    No backend text rendering involved, so geometry is exactly what we draw.
    """
    rng = random.Random(20260923)
    fs = 120.0
    tp_idea = TextPath((0, 0), "IDEA", size=fs, prop=FP)
    tp_rip = TextPath((0, 0), "RIPPER", size=fs, prop=FP)
    ei, er = tp_idea.get_extents(), tp_rip.get_extents()
    ch = TextPath((0, 0), "H", size=fs, prop=FP).get_extents().height

    pad = fs * 0.08
    space = fs * 0.30
    idea_w = ei.width
    rip_w = er.width
    # normalize: strip each word's own x0 bearing, we place them ourselves
    ix0, rx0 = ei.x0, er.x0
    rip_x = pad + idea_w + space          # svg x where RIPPER's x0 lands

    dy = fs * 0.012                        # whisper of displacement
    band_half = 0.0                          # no band: the rip is a cut line
    amp = fs * 0.06
    tear_y = ch * 0.52                     # y-up, measured from baseline

    # Baseline placed so the top of the (shifted) caps sits at pad.
    B = pad + ch + dy

    def up2svg(x, y):
        return (x, B - y)

    x0e = rip_x - fs * 0.12
    x1e = rip_x + rip_w + fs * 0.12
    n_teeth = 18
    tear = []
    for i in range(n_teeth + 1):
        t = i / n_teeth
        x = x0e + (x1e - x0e) * t
        y = tear_y + (rng.uniform(-amp, amp) if 0 < i < n_teeth else 0.0)
        tear.append(up2svg(x, y))

    W = pad + idea_w + space + rip_w + fs * 0.15 + pad
    H = B + dy + pad

    def pts(seq):
        return " ".join("%.1f,%.1f" % p for p in seq)

    upper = [(x, y - band_half) for x, y in tear]      # svg y-down: minus = up
    lower = [(x, y + band_half) for x, y in reversed(tear)]
    band = ("<polygon points=\"%s\" fill=\"%s\"/>" % (pts(upper + lower), band_color)) if band_color else ""

    edge = ""
    if edge_color:
        edge = ("<polyline points=\"%s\" fill=\"none\" stroke=\"%s\" "
                "stroke-width=\"1.6\" stroke-linecap=\"round\"/>" % (pts(tear), edge_color))

    clip_top = ("<clipPath id=\"ripTop\"><polygon points=\"%.1f,0 %.1f,0 %s\"/></clipPath>"
                % (x0e, x1e, pts(list(reversed(tear)))))
    clip_bot = ("<clipPath id=\"ripBot\"><polygon points=\"%.1f,%.1f %.1f,%.1f %s\"/></clipPath>"
                % (x0e, H, x1e, H, pts(list(reversed(tear)))))

    # NOTE: clip-path must sit on an UNTRANSFORMED wrapper: clipPathUnits=userSpaceOnUse
    # resolves the clip polygon in the referencing element's user space, so the
    # glyph flip (scale(1,-1)) has to live on an inner group.
    g_idea = ("<g fill=\"%s\"><g transform=\"translate(%.1f,%.1f) scale(1,-1)\">"
              "<use xlink:href=\"#wmIdea\"/></g></g>" % (INK, pad - ix0, B))
    # up-shifted half = +dy in y-up = -dy in svg
    g_up = ("<g clip-path=\"url(#ripTop)\"><g fill=\"%s\" "
            "transform=\"translate(%.1f,%.1f) scale(1,-1)\">"
            "<use xlink:href=\"#wmRip\"/></g></g>" % (INK, rip_x - rx0, B - dy))
    g_dn = ("<g clip-path=\"url(#ripBot)\"><g fill=\"%s\" "
            "transform=\"translate(%.1f,%.1f) scale(1,-1)\">"
            "<use xlink:href=\"#wmRip\"/></g></g>" % (INK, rip_x - rx0, B + dy))

    svg = (
        "<svg xmlns=\"http://www.w3.org/2000/svg\" "
        "xmlns:xlink=\"http://www.w3.org/1999/xlink\" "
        "viewBox=\"0 0 %.1f %.1f\" width=\"100%%\" role=\"img\" "
        "aria-label=\"Idea Ripper\">\n"
        "<defs><path id=\"wmIdea\" d=\"%s\"/><path id=\"wmRip\" d=\"%s\"/>%s%s</defs>\n"
        "%s\n%s\n%s\n%s\n%s\n</svg>\n"
        % (W, H, path_from_mpl(tp_idea), path_from_mpl(tp_rip),
           clip_top, clip_bot, band, g_idea, g_up, g_dn, edge))
    open(out, "w", encoding="utf-8").write(svg)
    print("wrote", out)


def path_from_mpl(mpl_path):
    """matplotlib Path -> SVG path data string (curve codes consume 2-3 verts)."""
    from matplotlib.path import Path as MplPath
    d = []
    verts = mpl_path.vertices
    codes = mpl_path.codes
    i, n = 0, len(verts)
    while i < n:
        c = codes[i]
        if c == MplPath.MOVETO:
            d.append("M%.1f %.1f" % (verts[i][0], verts[i][1]))
            i += 1
        elif c == MplPath.LINETO:
            d.append("L%.1f %.1f" % (verts[i][0], verts[i][1]))
            i += 1
        elif c == MplPath.CURVE3:
            d.append("Q%.1f %.1f %.1f %.1f" % (
                verts[i][0], verts[i][1], verts[i + 1][0], verts[i + 1][1]))
            i += 2
        elif c == MplPath.CURVE4:
            d.append("C%.1f %.1f %.1f %.1f %.1f %.1f" % (
                verts[i][0], verts[i][1], verts[i + 1][0], verts[i + 1][1],
                verts[i + 2][0], verts[i + 2][1]))
            i += 3
        elif c == MplPath.CLOSEPOLY:
            d.append("Z")
            i += 1
        else:
            i += 1
    return "".join(d)


def r_mark(out="r-mark.svg"):
    rng = random.Random(923)
    S = 512
    m = 44                      # tile margin
    r = 96                      # corner radius
    x0, y0, x1, y1 = m, m, S - m, S - m

    # Tile: rounded rect, top-right corner torn off (jagged rip).
    teeth = 5
    jx0, jy0 = x1 - r, y0       # where the tear starts on the top edge
    jx1, jy1 = x1, y0 + r       # where the tear ends on the right edge
    jag = []
    for i in range(teeth + 1):
        t = i / teeth
        # bite inward (toward tile center) with ragged teeth
        bite = (rng.uniform(28, 64) if 0 < i < teeth else 0)
        jag.append((jx0 + (jx1 - jx0) * t - bite * 0.7,
                    jy0 + (jy1 - jy0) * t - bite * 0.7))
    p = ["M%.0f,%.0f" % (x0 + r, y0),
         "L%.0f,%.0f" % jag[0]]
    p += ["L%.0f,%.0f" % pt for pt in jag[1:]]
    p.append("L%.0f,%.0f" % (x1, y0 + r))
    p.append("Q%.0f,%.0f %.0f,%.0f" % (x1, y1 - r, x1 - r, y1))
    p.append("L%.0f,%.0f" % (x0 + r, y1))
    p.append("Q%.0f,%.0f %.0f,%.0f" % (x0, y1, x0, y1 - r))
    p.append("L%.0f,%.0f" % (x0, y0 + r))
    p.append("Q%.0f,%.0f %.0f,%.0fZ" % (x0, y0, x0 + r, y0))
    tile = "".join(p)

    # R glyph, baked to a path, centered on the tile.
    tp = TextPath((0, 0), "R", size=300, prop=FP)
    bb = tp.get_extents()
    gw, gh = bb.width, bb.height
    target_h = (y1 - y0) * 0.58
    sc = target_h / gh
    cx = (x0 + x1) / 2 - (bb.x0 + gw / 2) * sc
    cy = (y0 + y1) / 2 - (bb.y0 + gh / 2) * sc - target_h * 0.02
    rd = path_from_mpl(tp)
    # TextPath y grows up; SVG y grows down. Map glyph top->Y_top.
    tile_cx = (x0 + x1) / 2
    tile_cy = (y0 + y1) / 2
    y_top = tile_cy - target_h / 2 - target_h * 0.02
    cx = tile_cx - (bb.x0 + gw / 2) * sc
    ty = y_top + bb.y1 * sc
    r_path = ("<g transform=\"translate(%.1f,%.1f) scale(%.4f,-%.4f)\">"
              "<path d=\"%s\" fill=\"%s\"/></g>"
              % (cx, ty, sc, sc, rd, PAPER))

    # Red rip: jagged diagonal slash across the R.
    sx0, sy0 = x0 + 78, y1 - 92
    sx1, sy1 = x1 - 96, y0 + 108
    wdt = 30
    n = 7
    up, dn = [], []
    for i in range(n + 1):
        t = i / n
        px = sx0 + (sx1 - sx0) * t
        py = sy0 + (sy1 - sy0) * t
        jog = rng.uniform(-16, 16) if 0 < i < n else 0
        # perpendicular offset
        dx, dy = sx1 - sx0, sy1 - sy0
        ln = (dx * dx + dy * dy) ** 0.5
        nx, ny = -dy / ln, dx / ln
        up.append((px + nx * (wdt + jog), py + ny * (wdt + jog)))
        dn.append((px - nx * (wdt + jog), py - ny * (wdt + jog)))
    slash = ("M" + "L".join("%.0f,%.0f" % q for q in up) +
             "L" + "L".join("%.0f,%.0f" % q for q in reversed(dn)) + "Z")

    svg = (
        "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 512 512\" "
        "width=\"512\" height=\"512\" role=\"img\" aria-label=\"Idea Ripper R mark\">\n"
        "<path d=\"%s\" fill=\"%s\"/>\n%s\n"
        "<path d=\"%s\" fill=\"%s\"/>\n</svg>\n"
        % (tile, INK, r_path, slash, RED))
    open(out, "w", encoding="utf-8").write(svg)
    print("wrote", out)


if __name__ == "__main__":
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    wordmark(band_color=None, edge_color=RED, out="wordmark-inline.svg")
    wordmark(band_color=None, edge_color=INK, out="wordmark-mono.svg")
    r_mark("r-mark.svg")
