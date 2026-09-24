#!/usr/bin/env python3
"""Apply Phase 4 (option A) to build_site.py: swap CSS block, add markings,
fonts, exlibris strips, motto, live curated date. Every replacement asserts
exactly one match; any miss aborts before writing."""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(BASE, "build_site.py")
src = open(P, encoding="utf-8").read()

def rep(old, new, n=1):
    global src
    c = src.count(old)
    assert c == n, "expected %d of %r, found %d" % (n, old[:70], c)
    src = src.replace(old, new)

# 1. swap the whole CSS block
new_css = open(os.path.join(BASE, "phase4.css"), encoding="utf-8").read().rstrip("\n")
start = src.index('CSS = """\n') + len('CSS = """\n')
end = src.index('\n"""\n\nJS = r"""')
src = src[:start] + new_css + src[end:]

# 2. kicker rip mark -> accent-rip (the CSS attribute selector for the
#    wordmark recolor must keep matching the ORIGINAL #d92b1f, so scope this
#    to the RIP_SVG polyline only)
rep('fill="none" stroke="#d92b1f"', 'fill="none" stroke="#E5322A"')

# 3. font links (Plex Mono 400/700 + Spectral 400/italic-400, display=swap)
rep('<meta name="viewport" content="width=device-width, initial-scale=1"/>\n',
    '<meta name="viewport" content="width=device-width, initial-scale=1"/>\n'
    '<link rel="preconnect" href="https://fonts.googleapis.com"/>\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>\n'
    '<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&family=Spectral:ital,wght@0,400;1,400&display=swap"/>\n'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&family=Spectral:ital,wght@0,400;1,400&display=swap"/>\n')

# 4. masthead: institutional marking + print-only plain title
rep('<header class="masthead"><div class="mast-inner">\n'
    '<h1 class="wordmark"><span class="sr-only">Idea Ripper</span>%s</h1>\n',
    '<header class="masthead"><div class="mast-inner">\n'
    '<p class="marking">IDEA RIPPER <span class="sep">//</span> EYES ONLY</p>\n'
    '<h1 class="wordmark"><span class="sr-only">Idea Ripper</span>%s</h1>\n'
    '<p class="print-title">Idea Ripper \\u2014 the idea-hunting library</p>\n')

# 5. book strip: EX LIBRIS // TITLE // N RIPS
rep("'<span class=\"bmain\"><span class=\"btitle\">%s <span class=\"bcount\">%d rip%s</span></span>'",
    "'<span class=\"bmain\"><span class=\"exlibris\">EX LIBRIS // %s // %d RIPS</span>"
    "<span class=\"btitle\">%s <span class=\"bcount\">%d rip%s</span></span>'")
rep('% (gh, esc(b["book"]), len(bcards), "" if len(bcards) == 1 else "s",',
    '% (gh, esc(b["book"]), len(bcards), esc(b["book"]), len(bcards), "" if len(bcards) == 1 else "s",')

# 6. footer: motto + live curated date
rep('import json, html, os',
    'import json, html, os, datetime as _dt\n'
    'def _curated_long(v):\n'
    '    try:\n'
    '        return _dt.date(*map(int, str(v).split("-"))).strftime("%B %d, %Y").replace(" 0", " ")\n'
    '    except Exception:\n'
    '        return str(v)')
rep('curated = ds.get("curated", "")',
    'curated = ds.get("curated", "")\ncurated_long = _curated_long(curated)')
rep('<footer>Last curated September 22, 2026 &middot; %d books &middot; %d theses &middot; %d rips%s &middot; ripped with the Idea Ripper pipeline</footer>',
    '<footer><p class="motto">MULTUM NON MULTA</p><p class="fmeta">Last curated %s &middot; %d books &middot; %d theses &middot; %d rips%s &middot; ripped with the Idea Ripper pipeline</p></footer>')
rep('"\\n\\n".join(sections), n_books, n_theses, n, fb_footer, JS)',
    '"\\n\\n".join(sections), curated_long, n_books, n_theses, n, fb_footer, JS)')

open(P, "w", encoding="utf-8").write(src)
print("phase 4 applied OK")
