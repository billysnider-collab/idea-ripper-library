#!/usr/bin/env python3
"""Wire the IDEA RIPPER visual lock into build_site.py (one-shot)."""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(BASE, "build_site.py")
s = open(P, encoding="utf-8").read()

def rep(old, new, count=1):
    global s
    assert s.count(old) >= 1, "anchor not found: %r" % old[:70]
    s = s.replace(old, new, count)

# 1) load the baked wordmark at build time
rep('curated = ds.get("curated", "")',
    'curated = ds.get("curated", "")\n'
    'wm_path = os.path.join(BASE, "brand", "wordmark-inline.svg")\n'
    'WORDMARK_SVG = open(wm_path, encoding="utf-8").read() if os.path.exists(wm_path) else "<strong>Idea Ripper</strong>"\n'
    'RIP_SVG = \'<svg class="ripmark" viewBox="0 0 20 8" aria-hidden="true">\'\n'
    '          \'<polyline points="1,4.5 5,2 9,5.5 13,2 17,5 19,3" fill="none" stroke="#d92b1f" stroke-width="2"/>\'\n'
    '          \'</svg>\'')

# 2) brand CSS appended to the CSS block
brand_css = '''
/* ===== IDEA RIPPER visual lock (Billy lock 2026-09-23) ===== */
header.masthead{max-width:none;padding:0;background:#f2e8d5;color:#14110c;border-bottom:3px solid #14110c}
.mast-inner{max-width:1180px;margin:0 auto;padding:1.1rem 1.25rem .95rem}
.wordmark{max-width:330px}
.wordmark svg{display:block}
.mast-sub{margin:.6rem 0 0;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.7rem;font-weight:700;letter-spacing:.24em;text-transform:uppercase}
.mast-sub .sep{color:#d92b1f}
.mast-meta{margin:.3rem 0 0;font-size:.82rem;color:#57503f}
.card{position:relative}
.stolentab{position:absolute;top:-10px;right:12px;z-index:2;background:#ffd21f;color:#14110c;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.6rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;padding:.22rem .55rem .26rem;transform:rotate(2deg);box-shadow:0 2px 5px rgba(0,0,0,.4);border-radius:1px;pointer-events:none}
.card[data-status="kill"] .stolentab,.card[data-status="rewrite"] .stolentab,.card[data-status="ungraded"] .stolentab{display:none}
.kicker{display:flex;align-items:center;gap:.45rem;margin:.55rem 0 .1rem;font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.62rem;font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:#8b97ad}
.kicker .ripmark{width:1.5rem;height:.6rem;flex:none}
.kicker .ktext{border-bottom:2px solid #d92b1f;padding-bottom:1px}
'''
rep('.fbook:not(.collapsed) .fbcards .card{margin:0}}\n"""',
    '.fbook:not(.collapsed) .fbcards .card{margin:0}}' + brand_css + '"""')

# 3) keeper card chrome: stolen tab + status hook (book_block only, before fb defs)
head, tail = s.split("def fb_chapter_detail", 1)
def hrep(old, new, count=1):
    global head
    assert head.count(old) >= 1, "card anchor not found: " + old[:60]
    head = head.replace(old, new, count)
hrep('data-type="%s" data-search="%s">\'\n            \'<div class="cardhead"',
     'data-type="%s" data-status="%s" data-search="%s">\'\n            \'<span class="stolentab">Stolen</span>\'\n            \'<div class="cardhead"')
hrep('esca(c["type"]), esca(search),',
     'esca(c["type"]), c.get("status", "keeper"), esca(search),')
hrep("\'<p class=\"steal\">%s</p>\'",
     "\'<div class=\"kicker\">' + RIP_SVG + '<span class=\"ktext\">Ripped from</span></div>\'\n            \'<p class=\"steal\">%s</p>\'")
hrep("\'<p class=\"uw\">%s</p>\'",
     "\'<div class=\"kicker\">' + RIP_SVG + '<span class=\"ktext\">Use when</span></div>\'\n            \'<p class=\"uw\">%s</p>\'")
s = head + "def fb_chapter_detail" + tail

# 4) paper masthead with the baked wordmark
rep('<header>\n<div class="hrow"><strong>Cool Keepers</strong><span class="meta">%d keepers &middot; %d books &middot; curated %s</span></div>\n</header>',
    '<header class="masthead"><div class="mast-inner">\n'
    '<div class="wordmark" role="img" aria-label="Idea Ripper">%s</div>\n'
    '<p class="mast-sub">the idea-hunting library</p>\n'
    '<p class="mast-meta">%d keepers &middot; %d books &middot; curated %s</p>\n'
    '</div></header>')

# 5) favicons
rep('<title>Idea Ripper - the idea-hunting library</title>',
    '<title>Idea Ripper - the idea-hunting library</title>\n'
    '<link rel="icon" type="image/svg+xml" href="brand/r-mark.svg"/>\n'
    '<link rel="icon" type="image/png" sizes="32x32" href="brand/r-mark-32.png"/>\n'
    '<link rel="apple-touch-icon" href="brand/apple-touch-icon.png"/>')

# 6) format tuple gains WORDMARK_SVG right after CSS
rep('""" % (CSS, n, len(books), curated,', '""" % (CSS, WORDMARK_SVG, n, len(books), curated,')

open(P, "w", encoding="utf-8").write(s)
print("patched build_site.py")
