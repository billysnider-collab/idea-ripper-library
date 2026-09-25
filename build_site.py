#!/usr/bin/env python3
"""Build the Idea Ripper hunt-layer page from cards.json.

Design: deduped book blurbs (once per book header), sticky search/filter bar,
collapsed cards (scan layer), book color chips, copy buttons, trust footer.
"""
import json, html, os, datetime as _dt
def _curated_long(v):
    try:
        return _dt.date(*map(int, str(v).split("-"))).strftime("%B %d, %Y").replace(" 0", " ")
    except Exception:
        return str(v)

BASE = os.path.dirname(os.path.abspath(__file__))

def esc(s):
    return html.escape(s, quote=False)

def esca(s):
    return html.escape(s, quote=True)

ds = json.load(open(os.path.join(BASE, "cards.json"), encoding="utf-8"))
books = ds["books"]            # ordered by first appearance
cards = ds["cards"]
genre_order = ds["genre_order"]
# theses are ideas, not books: never count or label them as books
n_theses = sum(1 for b in books if b["genre"] == "Thesis")
n_books = len(books) - n_theses

# display order: within each genre, most recently added books first
def books_in_genre(g):
    return [b for b in books if b["genre"] == g][::-1]
curated = ds.get("curated", "")
curated_long = _curated_long(curated)
wm_path = os.path.join(BASE, "brand", "wordmark-inline.svg")
WORDMARK_SVG = open(wm_path, encoding="utf-8").read() if os.path.exists(wm_path) else "<strong>Idea Ripper</strong>"
WORDMARK_SVG = WORDMARK_SVG.replace('role="img" aria-label="Idea Ripper"', 'aria-hidden="true"')
RIP_SVG = ('<svg class="ripmark" viewBox="0 0 20 8" aria-hidden="true">'
           '<polyline points="1,4.5 5,2 9,5.5 13,2 17,5 19,3" fill="none" stroke-width="2"/>'
           '</svg>')

# full-book deep dives: standalone briefs too rich to shred into rips
fb_path = os.path.join(BASE, "fullbooks.json")
fbooks = json.load(open(fb_path, encoding="utf-8"))["books"] if os.path.exists(fb_path) else []

# validation: every card has all four fields; every book has genre + blurb
for c in cards:
    for f in ("title", "steal", "why", "uw"):
        assert c.get(f) and c[f].strip(), "missing field %s in %r" % (f, c.get("title"))
bookset = {b["book"] for b in books}
for c in cards:
    assert c["book"] in bookset, "unknown book " + c["book"]
for b in books:
    assert b["genre"] in genre_order and b["bookline"].strip()

# chip colors: one hue per genre so chips mean something (genre color)
ghue = {g: int(i * 360 / len(genre_order)) for i, g in enumerate(genre_order)}

types = sorted({c["type"] for c in cards})
n = len(cards)

# P0 freeze (2026-09-24): card identity is the permanent id stored in cards.json,
# NOT display order. This walk only sets render order. Never derive numbers from position.
_ordered = []
for _g in genre_order:
    for _b in books_in_genre(_g):
        for _c in cards:
            if _c["book"] == _b["book"]:
                _ordered.append(_c)
assert len(_ordered) == len(cards), "render walk missed cards"
_ids = [c["id"] for c in cards]
assert len(_ids) == len(set(_ids)) == len(cards), "card ids must be unique permanent ints"

def book_block(b):
    gh = ghue[b["genre"]]
    slug = slugify(b["book"])
    bcards = [c for c in cards if c["book"] == b["book"]]
    _bt, _ba = b["book"].rsplit(" — ", 1) if " — " in b["book"] else (b["book"], "")
    _bauthor = '<span class="bauthor">%s</span>' % esc(_ba) if _ba else ""
    samples = " · ".join("\u201c%s\u201d" % c["title"] for c in bcards[:2])
    parts = ['<section class="book collapsed" id="b-%s" data-book="%s" data-genre="%s">'
             % (slug, esca(b["book"]), esca(b["genre"]))]
    parts.append(
        '<h2 class="bh"><button type="button" class="bookhead" aria-expanded="false">'
        '<span class="chip" style="background:hsl(%d,45%%,55%%)"></span>'
        '<span class="bmain"><span class="btitle"><span class="bttext" title="%s">%s</span> <span class="bcount">%d rip%s</span></span>'
        '%s'
        '<span class="bookline">%s</span>'
        '<span class="bsamples">%s</span></span>'
        '<span class="bchev">\u25be</span></button></h2>'
        % (gh, esca(b["book"]), esc(_bt), len(bcards), "" if len(bcards) == 1 else "s",
           _bauthor, esc(b["bookline"]), esc(samples)))
    parts.append('<div class="cards">')
    thesis_open = b["genre"] == "Thesis"  # one book = one card: skip the second click
    for c in bcards:
        n_ = c["id"]  # permanent id, frozen 2026-09-24; display order never renumbers
        search = " ".join([c["title"], c["steal"], c["why"], c["uw"]]).lower()
        pv = c["steal"]
        if len(pv) > 90:
            pv = pv[:90].rsplit(" ", 1)[0] + "\u2026"
        kicker_rip = '<div class="kicker">' + RIP_SVG + '<span class="ktext">Ripped from</span></div>'
        kicker_use = '<div class="kicker">' + RIP_SVG + '<span class="ktext">Use when</span></div>'
        parts.append(
            '<article class="card%s" id="c%d" data-n="%d" '
            'data-book="%s" data-genre="%s" data-type="%s" data-status="%s" data-search="%s">'
            '<h3 class="ch"><button type="button" class="cardhead" aria-expanded="%s">'
            '<span class="num">%d</span>'
            '<span class="ctext"><span class="ctitle">%s</span><span class="pv">%s</span></span>'
            '<span class="pill %s">%s</span></button></h3>'
            '<div class="cardbody">'
            '%s'
            '<p class="steal">%s</p>'
            '<p class="why"><span class="k">Why it matters:</span> %s</p>'
            '%s'
            '<p class="uw">%s</p>'
            '<div class="actions"><button type="button" data-copy="steal">Copy steal</button>'
            '<button type="button" data-copy="uw">Copy use-when</button>'
            '<button type="button" data-copy="link">Copy link</button></div>'
            '</div></article>'
            % (" open" if thesis_open else "", n_, n_, esca(c["book"]), esca(b["genre"]), esca(c["type"]), c.get("status", "keeper"), esca(search),
               "true" if thesis_open else "false",
               n_, esc(c["title"]), esc(pv), esca(c["type"]), esc(c["type"]),
               kicker_rip, esc(c["steal"]), esc(c["why"]), kicker_use, esc(c["uw"])))
    parts.append('</div></section>')
    return "\n".join(parts)

def fb_chapter_detail(ch):
    """Rich chapter section: thesis, key events, causes/consequences, evidence,
    the author's reading. Falls back to the old one-line layout for chapters
    without enriched data."""
    unit = esc(ch.get("unit", ""))
    summ = esc(ch.get("summary", ""))
    if not ch.get("thesis") and not ch.get("key_events"):
        return '<dl class="fbchaps"><dt>%s</dt><dd>%s</dd></dl>' % (unit, summ)
    p = ['<details class="fbchap"><summary><span class="fbchapunit">%s</span>'
         ' <span class="fbchapsum">%s</span></summary>' % (unit, summ)]
    if ch.get("thesis"):
        p.append('<p class="fbthesis"><span class="k">Chapter thesis:</span> %s</p>' % esc(ch["thesis"]))
    evs = ch.get("key_events") or []
    if evs:
        p.append('<p class="fbclab">Key events</p><div class="twrap">'
                 '<table class="fbtable fbevents"><tr><th>What</th><th>When</th><th>Who</th></tr>')
        for e in evs:
            p.append('<tr><td>%s</td><td>%s</td><td>%s</td></tr>'
                     % (esc(e.get("what", "")), esc(e.get("when", "")), esc(e.get("who", ""))))
        p.append('</table></div>')
    ca = ch.get("causes") or []
    cq = ch.get("consequences") or []
    if ca or cq:
        p.append('<div class="fbcols"><div><p class="fbclab">Causes</p><ul class="fblist">')
        for c in ca:
            p.append('<li>%s</li>' % esc(c))
        p.append('</ul></div><div><p class="fbclab">Consequences</p><ul class="fblist">')
        for c in cq:
            p.append('<li>%s</li>' % esc(c))
        p.append('</ul></div></div>')
    ed = ch.get("evidence") or []
    if ed:
        p.append('<p class="fbclab">Evidence</p><ul class="fblist">')
        for e in ed:
            p.append('<li>%s</li>' % esc(e))
        p.append('</ul>')
    if ch.get("reading"):
        p.append('<p class="fbreading"><span class="k">The author\'s reading:</span> %s</p>' % esc(ch["reading"]))
    p.append('</details>')
    return "\n".join(p)

def fullbook_block(fb):
    """Standalone deep-dive entry: argument map, themes, timeline, author-vs-fact,
    synthesis, the full card deck, and chapter summaries. Cards reuse rip
    card visuals but carry data-fb so rip search/count/hash logic skips them."""
    parts = ['<section class="fbook collapsed" id="fb-%s">' % esca(fb["id"])]
    blurb = fb["author"]
    if fb.get("publisher"):
        blurb += " (%s)" % fb["publisher"]
    if fb.get("lens"):
        blurb += " \u2014 " + fb["lens"]
    parts.append(
        '<h2 class="bh"><button type="button" class="fbookhead" aria-expanded="false">'
        '<span class="chip" style="background:var(--amber)"></span>'
        '<span class="bmain"><span class="btitle">%s <span class="bcount">full-book brief \u00b7 %d cards</span></span>'
        '<span class="bookline">%s</span></span>'
        '<span class="bchev">\u25be</span></button></h2>'
        % (esc(fb["title"]), len(fb["cards"]), esc(blurb)))
    parts.append('<div class="fbookbody">')
    am = fb.get("argument_map", {})
    if am:
        parts.append('<h3 class="fbsub">The argument</h3><div class="amap">')
        for lab, key in (("Because", "because"), ("This led to", "led_to"),
                         ("However", "however"), ("Therefore", "therefore")):
            if am.get(key):
                parts.append('<div class="amstep"><span class="amlab">%s</span><p>%s</p></div>'
                             % (lab, esc(am[key])))
        parts.append('</div>')
    if fb.get("themes"):
        parts.append('<h3 class="fbsub">Recurring themes</h3>')
        for t in fb["themes"]:
            parts.append('<p class="fbtheme"><strong>%s</strong> %s</p>'
                         % (esc(t.get("title", "")), esc(t.get("body", ""))))
    if fb.get("timeline"):
        parts.append('<h3 class="fbsub">Turning points</h3><div class="twrap"><table class="fbtable">'
                     '<tr><th>Date</th><th>Cause</th><th>What changed</th><th>Pace</th></tr>')
        for r in fb["timeline"]:
            parts.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
                         % (esc(r.get("date", "")), esc(r.get("cause", "")),
                            esc(r.get("changed", "")), esc(r.get("pace", ""))))
        parts.append('</table></div>')
    if fb.get("author_vs_fact"):
        parts.append('<h3 class="fbsub">Author vs. the evidence</h3><div class="twrap"><table class="fbtable">'
                     '<tr><th>Claim</th><th>Anchored in</th><th>Status</th></tr>')
        for r in fb["author_vs_fact"]:
            parts.append('<tr><td>%s</td><td>%s</td><td>%s</td></tr>'
                         % (esc(r.get("claim", "")), esc(r.get("anchored", "")),
                            esc(r.get("status", ""))))
        parts.append('</table></div>')
    sy = fb.get("synthesis", {})
    if sy:
        parts.append('<h3 class="fbsub">Synthesis</h3>')
        if sy.get("five_sentences"):
            parts.append('<p>%s</p>' % esc(sy["five_sentences"]))
        if sy.get("biggest_ideas"):
            parts.append('<p><strong>The three biggest ideas:</strong></p><ol class="fbideas">')
            for idea in sy["biggest_ideas"]:
                parts.append('<li>%s</li>' % esc(idea))
            parts.append('</ol>')
        if sy.get("turning_points"):
            parts.append('<p><strong>Major turning points:</strong> %s</p>' % esc(sy["turning_points"]))
        ass = sy.get("assessment", {})
        if ass:
            parts.append('<dl class="fbassess">')
            for lab, key in (("Explains well", "explains_well"),
                             ("Evidence relied on", "evidence_relied_on"),
                             ("Remains uncertain", "remains_uncertain"),
                             ("Another historian might dispute", "another_historian_might_dispute")):
                if ass.get(key):
                    parts.append('<dt>%s</dt><dd>%s</dd>' % (lab, esc(ass[key])))
            parts.append('</dl>')
    parts.append('<h3 class="fbsub">The %d cards</h3><div class="fbcards">' % len(fb["cards"]))
    for c in fb["cards"]:
        pv = c["steal"]
        if len(pv) > 90:
            pv = pv[:90].rsplit(" ", 1)[0] + "\u2026"
        meta = " \u00b7 ".join(x for x in (c.get("chapter"), c.get("period")) if x)
        parts.append(
            '<article class="fbcard card" data-fb="1">'
            '<h3 class="ch"><button type="button" class="cardhead" aria-expanded="false">'
            '<span class="fbnum">%d</span>'
            '<span class="ctext"><span class="ctitle">%s</span><span class="pv">%s</span></span>'
            '<span class="pill %s">%s</span></button></h3>'
            '<div class="cardbody">'
            '<p class="steal">%s</p>'
            '<p class="why"><span class="k">Why it matters:</span> %s</p>'
            '<p class="uw">%s</p>'
            '%s'
            '<div class="actions"><button type="button" data-copy="steal">Copy steal</button>'
            '<button type="button" data-copy="uw">Copy use-when</button></div>'
            '</div></article>'
            % (c["n"], esc(c["title"]), esc(pv), esca(c.get("type", "")), esc(c.get("type", "")),
               esc(c["steal"]), esc(c["why_it_matters"]), esc(c["use_when"]),
               '<p class="fbmeta">%s</p>' % esc(meta) if meta else ""))
    parts.append('</div>')
    if fb.get("chapter_summaries"):
        parts.append('<h3 class="fbsub">Chapter by chapter</h3>')
        for ch in fb["chapter_summaries"]:
            parts.append(fb_chapter_detail(ch))
    parts.append('</div></section>')
    return "\n".join(parts)

import re
def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

genre_of = {b["book"]: b["genre"] for b in books}
sections = []
for g in genre_order:
    gbooks = books_in_genre(g)
    if not gbooks:
        continue
    gcount = sum(1 for c in cards if genre_of[c["book"]] == g)
    gunit = "theses" if g == "Thesis" else "books"
    sections.append('<h2 class="genre" data-genre="%s" id="g-%s">%s <span class="gcount">%d cards · %d %s</span></h2>'
                    % (esca(g), slugify(g), esc(g), gcount, len(gbooks), gunit))
    for b in gbooks:
        sections.append(book_block(b))

if fbooks:
    fb_cards = sum(len(fb["cards"]) for fb in fbooks)
    sections.append('<h2 class="genre fbshelf">Full Books <span class="gcount">%d deep %s &middot; %d cards</span></h2>'
                    % (len(fbooks), "dive" if len(fbooks) == 1 else "dives", fb_cards))
    for fb in fbooks:
        sections.append(fullbook_block(fb))

# genre index: one compact link per genre (label + mono card count)
_gcounts = {g: sum(1 for c in cards if genre_of[c["book"]] == g) for g in genre_order}
gindex = "\n".join(
    '<a class="gix" href="#g-%s" data-genre="%s">%s · <span class="gixc">%d</span></a>'
    % (slugify(g), esca(g), esc(g), _gcounts[g])
    for g in genre_order if _gcounts[g])
# jump scents: the 12 most recently added books (highest max card id)
def _maxid(b):
    return max(c["id"] for c in cards if c["book"] == b["book"])
scents = sorted(books, key=_maxid, reverse=True)[:12]
chips = "\n".join(
    '<a class="bchip" href="#b-%s" data-genre="%s" title="%s">%s</a>'
    % (slugify(b["book"]), esca(b["genre"]), esca(b["book"]), esc(b["book"]))
    for b in scents)

genre_opts = "\n".join('<option value="%s">%s</option>' % (esca(g), esc(g)) for g in genre_order)
book_opts = "\n".join('<option value="%s">%s</option>' % (esca(b["book"]), esc(b["book"])) for b in books)
type_counts = {t2: sum(1 for c in cards if c["type"] == t2) for t2 in types}
type_checks = "\n".join(
    '<label class="tcheck"><input type="checkbox" name="ftype" value="%s"/> %s <span class="tn">(%d)</span></label>'
    % (esca(t2), esc(t2), type_counts[t2]) for t2 in types)

CSS = """

/* ===== Phase 4 identity (Billy lock 2026-09-24, option A: cards repainted for paper) =====
   Rule: aggression lives in the frame (--surface-frame), readability lives in
   the content (--surface-paper). Every color, type size, and spacing value
   below comes from a :root custom property. No hardcoded values elsewhere,
   except 0/auto keywords and the two wordmark attribute selectors (which must
   match the original SVG's own attributes to recolor it). */
:root{
  /* identity tokens (required) */
  --surface-frame:#0E0E0E;
  --ink-frame:#F2F0EB;
  --accent-rip:#E5322A;
  --surface-paper:#FAF7F2;
  --ink-body:#111111;
  --ink-structure:#706960;   /* nearest passing warm gray for TEXT on paper (5.07:1; spec #8C8478 was 3.46:1) */
  --mark-highlight:#FFE066;
  --link:#1F3D6E;
  /* derived tokens (all still :root properties) */
  --surface-frame-raised:#1C1C1B;  /* inputs, chips, toast on the frame */
  --ink-structure-frame:#8C8478;   /* text on the frame (5.23:1); too light for text on paper */
  --line-frame:#3B3936;            /* borders on the frame */
  --line-structure:#8C8478;        /* dividers on paper only (3.46:1, never text) */
  --line-card:#B7AB90;             /* card hairline on paper (decorative) */
  --accent-mechanism:#7A5A10;      /* mechanism pill on paper (5.96:1) */
  --accent-mechanism-line:#A8873A; /* mechanism border on paper */
  --print-ink:#000;                /* print only: black text on white */
  --print-paper:#fff;              /* print only */
  /* type */
  --font-mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  --font-serif:"Spectral",Georgia,"Iowan Old Style","Source Serif 4",serif;
  --fs-xs:.72rem;
  --fs-sm:.8rem;
  --fs-md:.9rem;
  --fs-base:1rem;
  --fs-lg:1.03rem;
  --fs-xl:1.15rem;
  --fs-2xl:1.7rem;
  --lh-body:1.6;
  --lh-tight:1.35;
  /* spacing scale */
  --space-3xs:.125rem;
  --space-2xs:.25rem;
  --space-xs:.5rem;
  --space-sm:.75rem;
  --space-md:1rem;
  --space-lg:1.5rem;
  --space-xl:2.5rem;
  --space-2xl:3rem;
  --page-gutter:1.25rem;
  --page-max:1180px;
  --page-narrow:920px;
  --wordmark-max:330px;
  --search-min:200px;
  --chip-max:12rem;
  --num-min:2.2rem;
  --count-min:18ch;
  --select-max:11rem;
  --measure:60rem;
  --scroll-mt:4.5rem;
  --scroll-mt-mobile:8rem;
  --radius-sm:6px;
  --radius-md:8px;
  --radius-lg:10px;
  --radius-pill:999px;
}
*{box-sizing:border-box}
html{font-size:100%}
body{margin:0;font-family:var(--font-serif);font-size:var(--fs-base);line-height:var(--lh-body);background:var(--surface-paper);color:var(--ink-body)}
/* ---------- frame: masthead ---------- */
header.masthead{max-width:none;padding:0;background:var(--surface-frame);color:var(--ink-frame);border-bottom:3px solid var(--accent-rip)}
.mast-inner{max-width:var(--page-max);margin:0 auto;padding:var(--space-md) var(--page-gutter) var(--space-md)}
.wordmark{max-width:var(--wordmark-max);margin:0}
.wordmark svg{display:block;width:100%;height:auto}
/* existing mark, presented in frame ink: shapes untouched, fills remapped */
.wordmark svg [fill="#14110c"]{fill:var(--ink-frame)}
.wordmark svg [stroke="#d92b1f"]{stroke:var(--accent-rip)}
.print-title{display:none}
.mast-sub{margin:var(--space-sm) 0 0;font-family:var(--font-mono);font-size:var(--fs-xs);font-weight:400;letter-spacing:.24em;text-transform:uppercase;color:var(--ink-frame)}
.mast-meta{margin:var(--space-2xs) 0 0;font-family:var(--font-mono);font-size:var(--fs-sm);color:var(--ink-structure-frame)}
/* ---------- frame: controls ---------- */
.controls{position:sticky;top:0;z-index:20;background:var(--surface-frame);border-bottom:1px solid var(--line-frame);padding:var(--space-sm) 0}
.controls .inner{max-width:var(--page-max);margin:0 auto;padding:0 var(--page-gutter);display:flex;gap:var(--space-xs);flex-wrap:wrap;align-items:center}
.controls input[type=search]{flex:1 1 var(--search-min);background:var(--surface-frame-raised);border:1px solid var(--line-frame);color:var(--ink-frame);border-radius:var(--radius-md);padding:var(--space-xs) var(--space-sm);font-size:var(--fs-md);font-family:var(--font-mono)}
.controls select{background:var(--surface-frame-raised);border:1px solid var(--line-frame);color:var(--ink-frame);border-radius:var(--radius-md);padding:var(--space-xs) var(--space-xs);font-size:var(--fs-sm);font-family:var(--font-mono);max-width:var(--select-max)}
.controls button{background:transparent;border:1px solid var(--line-frame);color:var(--ink-frame);border-radius:var(--radius-md);padding:var(--space-2xs) var(--space-sm);font-size:var(--fs-sm);font-family:var(--font-mono);cursor:pointer}
.controls button:hover{border-color:var(--accent-rip)}
.count{color:var(--ink-structure-frame);font-size:var(--fs-sm);font-family:var(--font-mono);margin-left:auto;min-width:var(--count-min);text-align:right}
/* ---------- frame: type filter ---------- */
.typefilter{position:relative}
.typefilter>summary{cursor:pointer;list-style:none;background:var(--surface-frame-raised);border:1px solid var(--line-frame);color:var(--ink-frame);border-radius:var(--radius-md);padding:var(--space-xs) var(--space-xs);font-size:var(--fs-sm);font-family:var(--font-mono)}
.typefilter>summary::-webkit-details-marker{display:none}
.typefilter>summary::before{content:"▸  ";color:var(--accent-rip)}
.typefilter[open]>summary::before{content:"▾  "}
.typefilter fieldset{border:1px solid var(--line-frame);border-radius:var(--radius-md);padding:var(--space-sm) var(--space-md);margin:var(--space-xs) 0 0;display:flex;flex-wrap:wrap;gap:var(--space-2xs) var(--space-md);flex:1 1 100%;background:var(--surface-frame-raised)}
.typefilter legend{font-size:var(--fs-sm);font-family:var(--font-mono);color:var(--ink-structure-frame);padding:0 var(--space-2xs)}
.tcheck{display:inline-flex;align-items:center;gap:var(--space-2xs);font-size:var(--fs-sm);font-family:var(--font-mono);cursor:pointer;color:var(--ink-frame)}
.tcheck input{accent-color:var(--accent-rip);width:var(--space-md);height:var(--space-md)}
.tn{color:var(--ink-structure-frame);font-size:var(--fs-sm)}
.tcount{background:transparent;border:1px solid var(--accent-rip);color:var(--ink-frame);border-radius:var(--radius-pill);font-size:var(--fs-xs);font-weight:700;padding:var(--space-3xs) var(--space-xs);margin-left:var(--space-2xs);font-family:var(--font-mono)}
#cleartypes{background:transparent;border:1px solid var(--line-frame);color:var(--ink-frame);border-radius:var(--radius-sm);padding:var(--space-2xs) var(--space-sm);font-size:var(--fs-sm);font-family:var(--font-mono);cursor:pointer}
#cleartypes:hover{border-color:var(--accent-rip)}
/* ---------- frame: TOC jump chips ---------- */
.jumpchips{max-width:none;background:var(--surface-frame);border-bottom:1px solid var(--line-frame);margin:0;padding:var(--space-xs) var(--page-gutter);display:flex;gap:var(--space-2xs);overflow-x:auto;scrollbar-width:thin}
.jumpchips a{flex:none;max-width:var(--chip-max);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;background:var(--surface-frame-raised);border:1px solid var(--line-frame);color:var(--ink-frame);border-radius:var(--radius-pill);padding:var(--space-2xs) var(--space-sm);font-size:var(--fs-xs);font-family:var(--font-mono);cursor:pointer;text-decoration:none}
.jumpchips a:hover{border-color:var(--accent-rip)}
.jumpchips{align-items:center}
.gindex{flex:none;display:flex;flex-wrap:wrap;gap:var(--space-3xs) var(--space-sm);align-items:center;padding:var(--space-3xs) var(--space-sm) var(--space-3xs) 0;border-right:1px solid var(--line-frame);margin-right:var(--space-2xs)}
.gindex a{flex:none;max-width:none;background:none;border:0;border-radius:0;padding:0;font-family:var(--font-mono);font-size:.75rem;color:var(--ink-structure-frame);white-space:nowrap}
.gindex a:hover{color:var(--ink-frame);border-color:transparent}
.gindex .gixc{font-variant-numeric:tabular-nums}
.scents{flex:1;min-width:0;display:flex;gap:var(--space-2xs);overflow-x:auto;scrollbar-width:thin;padding:var(--space-3xs) 0}
/* ---------- frame: footer ---------- */
footer{background:var(--surface-frame);color:var(--ink-frame);font-family:var(--font-mono);font-size:var(--fs-sm);padding:var(--space-xl) var(--page-gutter);border-top:3px solid var(--accent-rip);text-align:center}
footer .fmeta{margin:0;color:var(--ink-structure-frame)}
/* ---------- reading zone ---------- */
#intro{max-width:var(--page-narrow);margin:0 auto;padding:var(--space-md) var(--page-gutter) 0;color:var(--ink-body);font-size:var(--fs-base)}
#intro p{margin:var(--space-xs) 0;max-width:var(--measure)}
#intro strong{color:var(--ink-body);font-weight:700}
.intromore{margin:var(--space-xs) 0}
.intromore summary{cursor:pointer;color:var(--ink-structure);font-size:var(--fs-sm)}
main{max-width:var(--page-narrow);margin:0 auto;padding:var(--space-md) var(--page-gutter) var(--space-2xl)}
main a{color:var(--link)}
.genre{margin:var(--space-xl) 0 var(--space-sm);font-size:1.4rem;font-weight:400;color:var(--ink-body);border-bottom:2px solid var(--accent-rip);padding-bottom:var(--space-2xs);line-height:var(--lh-tight)}
.gcount{color:var(--ink-structure);font-size:var(--fs-sm);font-weight:400;font-family:var(--font-mono)}
.book,.fbook{margin-bottom:var(--space-lg);scroll-margin-top:var(--scroll-mt)}
/* ---------- book strip ---------- */
.bh,.ch{margin:0;font-size:var(--fs-base);font-weight:400}
.bookhead,.fbookhead,.cardhead{font:inherit;color:inherit;background:none;border:0;padding:0;text-align:left;width:100%;cursor:pointer}
.bookhead{display:flex;align-items:center;gap:var(--space-sm);margin:var(--space-md) 0 var(--space-3xs)}
button::-moz-focus-inner{border:0;padding:0}
:focus-visible{outline:3px solid var(--accent-rip);outline-offset:2px}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}
.chip{display:inline-block;width:var(--space-sm);height:var(--space-sm);border-radius:var(--radius-sm);flex:none}
.bookhead .bmain,.fbookhead .bmain{flex:1;min-width:0}
.btitle{display:block;font-weight:400;font-size:1.125rem;color:var(--ink-body);line-height:var(--lh-tight)}
.btitle .bcount{color:var(--ink-structure);font-size:.75rem;font-weight:400;margin-left:var(--space-xs);font-family:var(--font-mono);font-variant-numeric:tabular-nums}
.bauthor{display:block;color:var(--ink-structure);font-size:.8125rem;margin-top:var(--space-3xs)}
.bookline{display:block;color:var(--ink-structure);font-size:var(--fs-sm);margin:var(--space-3xs) 0 var(--space-3xs)}
.bsamples{display:block;color:var(--ink-structure);font-size:var(--fs-sm);font-style:italic;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin:0 0 var(--space-2xs)}
.book[data-genre="Thesis"] .btitle{display:flex;min-width:0;align-items:baseline}
.book[data-genre="Thesis"] .bttext{flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bchev{margin-left:auto;color:var(--ink-structure);flex:none}
.book.collapsed .bchev{transform:rotate(-90deg)}
.book .cards{margin-top:var(--space-xs)}
.book.collapsed .cards{display:none}
/* ---------- cards (repainted for paper, option A) ---------- */
.card{background:var(--surface-paper);border:1px solid var(--line-card);border-left:3px solid var(--accent-mechanism-line);border-radius:var(--radius-lg);padding:var(--space-sm) var(--space-md);margin:var(--space-xs) 0;position:relative}
.cardhead{display:flex;align-items:baseline;gap:var(--space-sm)}
.num{color:var(--ink-structure);font-size:var(--fs-sm);font-family:var(--font-mono);flex:none;min-width:var(--num-min)}
.ctext{flex:1;min-width:0}
.ctitle{display:block;font-size:var(--fs-lg);color:var(--ink-body);line-height:var(--lh-tight)}
.pv{display:block;color:var(--ink-structure);font-size:var(--fs-sm);font-weight:400;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card.open .pv{display:none}
.pill{flex:none;display:inline-block;padding:var(--space-3xs) var(--space-xs);border-radius:var(--radius-pill);border:1px solid var(--line-structure);font-size:var(--fs-xs);font-family:var(--font-mono);color:var(--ink-structure)}
.pill.mechanism{color:var(--accent-mechanism);border-color:var(--accent-mechanism-line)}
.cardbody{display:none;padding-top:var(--space-2xs)}
.card.open .cardbody{display:block}
.kicker{display:flex;align-items:center;gap:var(--space-xs);margin:var(--space-sm) 0 var(--space-3xs);font-family:var(--font-mono);font-size:var(--fs-xs);font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:var(--ink-structure)}
.kicker .ripmark{width:var(--space-lg);height:auto;flex:none}
.kicker .ripmark polyline{stroke:var(--accent-rip)}
.kicker .ktext{border-bottom:2px solid var(--accent-rip);padding-bottom:var(--space-3xs)}
.card .steal{margin:var(--space-xs) 0;font-style:italic;font-size:var(--fs-lg);line-height:var(--lh-body);color:var(--ink-body)}
.why{margin:var(--space-xs) 0;font-size:var(--fs-base);line-height:var(--lh-body);color:var(--ink-body)}
.why .k{display:block;font-family:var(--font-mono);font-size:var(--fs-xs);font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-body);margin-bottom:var(--space-2xs)}
.card .uw{color:var(--ink-structure);font-size:var(--fs-base);line-height:var(--lh-body);margin:var(--space-xs) 0 0}
.actions{margin-top:var(--space-xs);display:flex;gap:var(--space-xs);flex-wrap:wrap}
.actions button{background:transparent;border:1px solid var(--line-structure);color:var(--ink-structure);border-radius:var(--radius-sm);padding:var(--space-2xs) var(--space-sm);font-size:var(--fs-sm);font-family:var(--font-mono);cursor:pointer}
.actions button:hover{color:var(--ink-body);border-color:var(--accent-rip)}
.card.deeplink{outline:3px solid var(--accent-rip);outline-offset:3px}
.hidden{display:none!important}
/* ---------- search ---------- */
mark{background:var(--mark-highlight);color:var(--ink-body);font-weight:400;border-radius:2px;padding:0 .1em}
.noresults{color:var(--ink-structure);text-align:center;padding:var(--space-xl) 0;font-size:var(--fs-base)}
.noresults button{background:transparent;border:1px solid var(--line-structure);color:var(--ink-structure);border-radius:var(--radius-md);padding:var(--space-xs) var(--space-sm);font-size:var(--fs-sm);font-family:var(--font-mono);cursor:pointer;margin-left:var(--space-xs)}
.noresults button:hover{color:var(--ink-body);border-color:var(--accent-rip)}
#toast{position:fixed;left:50%;bottom:var(--space-lg);transform:translateX(-50%) translateY(8px);background:var(--surface-frame-raised);border:1px solid var(--accent-rip);color:var(--ink-frame);border-radius:var(--radius-md);padding:var(--space-xs) var(--space-md);font-size:var(--fs-sm);font-family:var(--font-mono);opacity:0;pointer-events:none;z-index:50}
#toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
/* ---------- full-book deep dives (reading zone) ---------- */
.fbookhead{display:flex;align-items:center;gap:var(--space-sm);margin:var(--space-md) 0 var(--space-3xs)}
.fbookhead .bchev{margin-left:auto;color:var(--ink-structure);flex:none}
.fbook.collapsed .bchev{transform:rotate(-90deg)}
.fbookbody{padding:var(--space-2xs) 0 var(--space-md)}
.fbook.collapsed .fbookbody{display:none}
.fbsub{color:var(--ink-body);font-size:var(--fs-lg);margin:var(--space-lg) 0 var(--space-xs);font-weight:400}
.amstep{background:var(--surface-paper);border:1px solid var(--line-card);border-radius:var(--radius-md);padding:var(--space-xs) var(--space-md);margin:var(--space-xs) 0}
.amstep p{margin:var(--space-3xs) 0 0}
.amlab{color:var(--ink-body);font-weight:700;font-size:var(--fs-xs);font-family:var(--font-mono);text-transform:uppercase;letter-spacing:.05em}
.fbtheme{margin:var(--space-xs) 0}
.fbtheme strong{color:var(--ink-body)}
.twrap{overflow-x:auto}
.fbtable{width:100%;border-collapse:collapse;font-size:var(--fs-sm);margin:var(--space-xs) 0}
.fbtable th{text-align:left;color:var(--ink-body);font-weight:700;padding:var(--space-xs) var(--space-xs);border-bottom:1px solid var(--line-structure);white-space:nowrap}
.fbtable td{padding:var(--space-xs) var(--space-xs);border-bottom:1px solid var(--line-card);vertical-align:top}
.fbtable td:first-child{white-space:nowrap}
.fbideas{margin:var(--space-2xs) 0 var(--space-sm);padding-left:var(--space-lg)}
.fbideas li{margin:var(--space-2xs) 0}
.fbassess dt{color:var(--ink-body);font-weight:700;font-size:var(--fs-sm);margin-top:var(--space-xs)}
.fbassess dd{margin:var(--space-3xs) 0 var(--space-2xs);color:var(--ink-structure)}
.fbchaps dt{font-weight:700;font-size:var(--fs-sm);margin-top:var(--space-xs)}
.fbchaps dd{margin:var(--space-3xs) 0 var(--space-2xs);color:var(--ink-structure)}
.fbchap{border:1px solid var(--line-card);border-radius:var(--radius-md);margin:var(--space-xs) 0;background:var(--surface-paper)}
.fbchap>summary{cursor:pointer;padding:var(--space-xs) var(--space-md);list-style:none;display:block}
.fbchap>summary::-webkit-details-marker{display:none}
.fbchap>summary::before{content:"▸  ";color:var(--accent-mechanism)}
.fbchap[open]>summary::before{content:"▾  "}
.fbchapunit{font-weight:700;font-size:var(--fs-md)}
.fbchapsum{color:var(--ink-structure);font-size:var(--fs-sm)}
.fbthesis{margin:var(--space-xs) var(--space-md);font-size:var(--fs-md)}
.fbthesis .k,.fbreading .k{color:var(--ink-body);font-weight:700}
.fbclab{color:var(--ink-body);font-size:var(--fs-sm);font-weight:700;font-family:var(--font-mono);text-transform:uppercase;letter-spacing:.05em;margin:var(--space-sm) var(--space-md) var(--space-2xs)}
.fblist{margin:var(--space-3xs) var(--space-md) var(--space-xs) var(--space-lg);font-size:var(--fs-sm);color:var(--ink-body)}
.fblist li{margin:var(--space-2xs) 0}
.fbcols{display:grid;grid-template-columns:1fr 1fr;gap:0 var(--space-sm)}
.fbreading{margin:var(--space-sm) var(--space-md) var(--space-md);font-size:var(--fs-md);border-left:2px solid var(--accent-mechanism-line);padding-left:var(--space-sm)}
.fbevents td:first-child{white-space:normal}
.fbmeta{color:var(--ink-structure);font-size:var(--fs-sm);margin:var(--space-xs) 0 0;font-family:var(--font-mono)}
.cardhead .fbnum{color:var(--ink-structure);font-size:var(--fs-sm);font-family:var(--font-mono);flex:none;min-width:var(--num-min)}
/* ---------- responsive ---------- */
@media(min-width:1000px){
main{max-width:var(--page-max)}
.controls .inner,#intro{max-width:var(--page-max)}
.book:not(.collapsed) .cards{display:grid;grid-template-columns:1fr 1fr;gap:var(--space-sm);align-items:start}
.book:not(.collapsed) .card{margin:0}
.fbook:not(.collapsed) .fbcards{display:grid;grid-template-columns:1fr 1fr;gap:var(--space-sm);align-items:start}
.fbook:not(.collapsed) .fbcards .card{margin:0}
}
@media(max-width:700px){
.bsamples{display:none}
.controls input[type=search]{flex:1 1 100%}
.typefilter{flex:1 1 100%}
.typefilter>summary{width:100%}
.book,.fbook{scroll-margin-top:var(--scroll-mt-mobile)}
.controls{padding-top:env(safe-area-inset-top,0px)}
}
@media (prefers-reduced-motion: reduce){*,*::before,*::after{transition:none!important;animation:none!important}}
/* ---------- print: no frame, no red, black on white ---------- */
@media print{
  .controls,.jumpchips,.gindex,#toast,.actions,.noresults button{display:none!important}
  body{background:var(--print-paper);color:var(--print-ink)}
  header.masthead{background:var(--print-paper);border-bottom:2px solid var(--print-ink)}
  .mast-inner{padding:var(--space-sm) 0}
  .wordmark svg,.mast-sub,.mast-meta{display:none!important}
  .print-title{display:block!important;font-family:var(--font-serif);font-size:var(--fs-xl);font-weight:700;color:var(--print-ink);margin:0}
  main,#intro{max-width:none;padding-left:0;padding-right:0}
  #intro{color:var(--print-ink)}
  #intro strong{color:var(--print-ink)}
  .genre{color:var(--print-ink);border-bottom:2px solid var(--print-ink)}
  .gcount{color:var(--print-ink)}
  .chip,.bchev,.pv,.tcount{display:none!important}
  .bookhead,.fbookhead,.cardhead{cursor:default;color:var(--print-ink)}
  .bh,.ch,.btitle{font-weight:700;color:var(--print-ink)}
  .btitle .bcount,.bookline,.bsamples{color:var(--print-ink)}
  .book.collapsed .cards,.fbook.collapsed .fbookbody{display:block!important}
  .cardbody{display:block!important}
  .card{background:var(--print-paper);border:1px solid var(--print-ink);break-inside:avoid;margin:var(--space-xs) 0}
  .num,.kicker,.pill,.card .uw{color:var(--print-ink)}
  .pill{border-color:var(--print-ink)}
  .pill.mechanism{color:var(--print-ink);border-color:var(--print-ink)}
  .kicker .ripmark{display:none}
  .kicker .ktext{border-bottom-color:var(--print-ink)}
  .card .steal,.why{color:var(--print-ink)}
  .why .k{color:var(--print-ink)}
  mark{background:none;color:var(--print-ink);font-weight:700}
  main a{color:var(--print-ink);text-decoration:none}
  footer{background:var(--print-paper);color:var(--print-ink);border-top:2px solid var(--print-ink)}
  footer .fmeta{color:var(--print-ink)}
  .amstep,.fbchap{background:var(--print-paper);border-color:var(--print-ink)}
  *{box-shadow:none!important;text-shadow:none!important}
}
"""

JS = r"""
(function(){
var q=document.getElementById('q'),gs=document.getElementById('fgenre'),
    bs=document.getElementById('fbook'),
    tboxes=document.querySelectorAll('input[name=ftype]'),
    count=document.getElementById('count'),nores=document.getElementById('noresults'),
    toastEl=document.getElementById('toast'),
    total=document.querySelectorAll('.card:not([data-fb])').length,
    manual={},toastT=null,RM=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
function toast(msg,ms){
  toastEl.textContent=msg;toastEl.classList.add('show');
  clearTimeout(toastT);toastT=setTimeout(function(){toastEl.classList.remove('show');},ms||1500);
}
function jesc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function setBook(book,expand){
  book.classList.toggle('collapsed',!expand);
  manual[book.id]=expand;
  var hd=book.querySelector('.bookhead');
  if(hd)hd.setAttribute('aria-expanded',expand?'true':'false');
}
function checkedTypes(){
  var v=[];
  for(var i=0;i<tboxes.length;i++)if(tboxes[i].checked)v.push(tboxes[i].value);
  return v;
}
function updateTypeUI(){
  var n=checkedTypes().length,tc=document.getElementById('tcount'),cl=document.getElementById('cleartypes');
  if(n){tc.textContent=n;tc.hidden=false;}else{tc.hidden=true;}
  cl.hidden=!n;
}
function setHash(h){
  if(history.replaceState){try{history.replaceState(null,'',location.pathname+location.search+h);}catch(_){}}
}
function syncURL(){
  if(!history.replaceState)return;
  var p,term=q.value.trim(),tvs=checkedTypes();
  try{p=new URLSearchParams(location.search);}catch(_){p=new URLSearchParams();}
  if(term)p.set('q',term);else p.delete('q');
  if(tvs.length)p.set('type',tvs.join(','));else p.delete('type');
  if(gs.value)p.set('g',gs.value);else p.delete('g');
  if(bs.value)p.set('b',bs.value);else p.delete('b');
  var qs=p.toString();
  try{history.replaceState(null,'',location.pathname+(qs?'?'+qs:'')+location.hash);}catch(_){}
}
function apply(fromInput){
  var term=q.value.trim().toLowerCase(),
      gv=gs.value,bv=bs.value,tvs=checkedTypes(),
      filtering=!!(term||gv||bv||tvs.length);
  document.querySelectorAll('.card:not([data-fb])').forEach(function(c){
    var ok=true;
    if(term&&c.dataset.search.indexOf(term)<0)ok=false;
    if(gv&&c.dataset.genre!==gv)ok=false;
    if(bv&&c.dataset.book!==bv)ok=false;
    if(tvs.length&&tvs.indexOf(c.dataset.type)<0)ok=false;
    c.classList.toggle('hidden',!ok);
    if(fromInput)c.classList.toggle('open',!!term&&ok||(!term&&ok&&c.dataset.genre==='Thesis'));
  });
  document.querySelectorAll('.book').forEach(function(b){
    var vis=!!b.querySelector('.card:not(.hidden)');
    b.classList.toggle('hidden',!vis);
    if(vis){
      if(filtering){b.classList.remove('collapsed');}
      else{b.classList.toggle('collapsed',!manual[b.id]);}
      var hd=b.querySelector('.bookhead');
      if(hd)hd.setAttribute('aria-expanded',b.classList.contains('collapsed')?'false':'true');
    }
  });
  /* full-book deep dives stand alone: the rip hunt box hides the shelf */
  document.querySelectorAll('.fbook').forEach(function(b){
    b.classList.toggle('hidden',filtering);
  });
  document.querySelectorAll('.genre').forEach(function(g){
    if(g.classList.contains('fbshelf')){
      g.classList.toggle('hidden',filtering||!document.querySelector('.fbook:not(.hidden)'));
      return;
    }
    var show=false,next=g.nextElementSibling;
    while(next&&!next.classList.contains('genre')){
      if(next.classList.contains('book')&&!next.classList.contains('hidden')){show=true;break;}
      next=next.nextElementSibling;
    }
    g.classList.toggle('hidden',!show);
  });
  document.querySelectorAll('#jumpchips a').forEach(function(ch){
    ch.classList.toggle('hidden',!!gv&&ch.dataset.genre!==gv);
  });
  var vis=document.querySelectorAll('.card:not([data-fb]):not(.hidden)').length;
  count.textContent='showing '+vis+' of '+total;
  nores.hidden=vis>0;
  if(!nores.hidden){
    var msg='No rips match',tm=q.value.trim(),tn=checkedTypes();
    if(tm)msg+=' &ldquo;'+jesc(tm)+'&rdquo;';
    if(tn.length)msg+=(tm?' with':'')+' type &ldquo;'+tn.map(jesc).join(', ')+'&rdquo;';
    if(!tm&&!tn.length&&(gv||bv))msg+=' the current filters';
    msg+='. <button type="button" id="clearall">Clear search and filters</button>';
    nores.innerHTML=msg;
    var ca=document.getElementById('clearall');
    if(ca)ca.addEventListener('click',function(){
      q.value='';gs.value='';bs.value='';
      for(var i=0;i<tboxes.length;i++)tboxes[i].checked=false;
      apply(true);q.focus();
    });
  }
  updateTypeUI();
  syncURL();
  scheduleHighlight(term);
}
function clearMarks(root){
  var marks=root.querySelectorAll('mark'),i,m,p;
  for(i=0;i<marks.length;i++){
    m=marks[i];p=m.parentNode;
    while(m.firstChild)p.insertBefore(m.firstChild,m);
    p.removeChild(m);
    p.normalize();
  }
}
function markTerm(el,term){
  var walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT,null,false),nodes=[],nd,i,t,low,idx,last,frag,mk;
  while(nd=walker.nextNode()){
    if(nd.parentNode&&nd.parentNode.className==='k')continue;
    nodes.push(nd);
  }
  for(i=0;i<nodes.length;i++){
    t=nodes[i];low=t.nodeValue.toLowerCase();idx=low.indexOf(term);
    if(idx<0)continue;
    frag=document.createDocumentFragment();last=0;
    while((idx=low.indexOf(term,last))>=0){
      if(idx>last)frag.appendChild(document.createTextNode(t.nodeValue.slice(last,idx)));
      mk=document.createElement('mark');
      mk.textContent=t.nodeValue.slice(idx,idx+term.length);
      frag.appendChild(mk);
      last=idx+term.length;
    }
    frag.appendChild(document.createTextNode(t.nodeValue.slice(last)));
    t.parentNode.replaceChild(frag,t);
  }
}
var hlT=null;
function scheduleHighlight(term){
  clearTimeout(hlT);
  hlT=setTimeout(function(){
    document.querySelectorAll('.card:not([data-fb])').forEach(function(c){clearMarks(c);});
    if(term){
      document.querySelectorAll('.card:not([data-fb]):not(.hidden)').forEach(function(c){
        ['.ctitle','.steal','.why','.uw'].forEach(function(sel){
          var el=c.querySelector(sel);if(el)markTerm(el,term);
        });
      });
    }
  },term?150:0);
}
var liveT=null;
function announceLive(){
  var el=document.getElementById('countlive');
  if(el)el.textContent=count.textContent;
}
function scheduleLive(){clearTimeout(liveT);liveT=setTimeout(announceLive,400);}
q.addEventListener('input',function(){apply(true);scheduleLive();});
q.addEventListener('change',function(){apply(false);});
[gs,bs].forEach(function(el){
  el.addEventListener('input',function(){apply(true);announceLive();});
  el.addEventListener('change',function(){apply(false);announceLive();});
});
for(var ti=0;ti<tboxes.length;ti++){
  tboxes[ti].addEventListener('change',function(){apply(true);announceLive();});
}
document.getElementById('cleartypes').addEventListener('click',function(){
  for(var i=0;i<tboxes.length;i++)tboxes[i].checked=false;
  apply(true);announceLive();
});
q.addEventListener('keydown',function(e){
  if(e.key==='Escape'){q.value='';apply(true);}
});
function toggleCard(card,open){
  var will=open===undefined?!card.classList.contains('open'):open;
  card.classList.toggle('open',will);
  var chd=card.querySelector('.cardhead');
  if(chd)chd.setAttribute('aria-expanded',will?'true':'false');
  if(will&&card.dataset.n)setHash('#c'+card.dataset.n);
}
document.querySelectorAll('.cardhead').forEach(function(h){
  h.addEventListener('click',function(){toggleCard(h.closest('.card'));});
});
document.querySelectorAll('.bookhead').forEach(function(h){
  function t(){var b=h.closest('section');setBook(b,b.classList.contains('collapsed'));}
  h.addEventListener('click',t);
});
/* full-book shelf: own toggle, outside rip expand/collapse-all */
document.querySelectorAll('.fbookhead').forEach(function(h){
  function t(){var b=h.closest('section'),exp=b.classList.contains('collapsed');
    b.classList.toggle('collapsed',!exp);
    h.setAttribute('aria-expanded',exp?'true':'false');}
  h.addEventListener('click',t);
});
document.getElementById('expand').addEventListener('click',function(){
  document.querySelectorAll('.book:not(.hidden)').forEach(function(b){
    setBook(b,true);
    b.querySelectorAll('.card:not(.hidden)').forEach(function(c){c.classList.add('open');});
  });
});
document.getElementById('collapse').addEventListener('click',function(){
  document.querySelectorAll('.book').forEach(function(b){
    setBook(b,false);
    b.querySelectorAll('.card.open').forEach(function(c){c.classList.remove('open');});
  });
});
document.querySelectorAll('[data-copy]').forEach(function(btn){
  btn.addEventListener('click',function(e){
    e.stopPropagation();
    var card=btn.closest('.card'),kind=btn.dataset.copy,txt;
    if(kind==='steal')txt=card.querySelector('.steal').textContent;
    else if(kind==='uw')txt=card.querySelector('.uw').textContent;
    else txt=location.origin+location.pathname+'#c'+card.dataset.n;
    function done(ok){
      if(ok){toast(kind==='link'?'Link copied':'Copied');return;}
      try{var rng=document.createRange();rng.selectNodeContents(card);
        var sel=getSelection();sel.removeAllRanges();sel.addRange(rng);}catch(_){}
      toast('Copy failed \u2014 press Ctrl+C (Cmd+C on Mac) to copy the selected text',4000);
    }
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt).then(function(){done(true);},function(){done(false);});}
    else{var ta=document.createElement('textarea');ta.value=txt;document.body.appendChild(ta);ta.select();try{document.execCommand('copy');done(true);}catch(_){done(false);}document.body.removeChild(ta);}
  });
});
document.querySelectorAll('#jumpchips a').forEach(function(ch){
  ch.addEventListener('click',function(e){
    var b=document.getElementById(ch.getAttribute('href').slice(1));
    if(b){e.preventDefault();if(b.classList.contains('book'))setBook(b,true);
      b.scrollIntoView({behavior:RM?'auto':'smooth',block:'start'});
      setHash(ch.getAttribute('href'));}
  });
});
function openHash(){
  var m=/^#c(\d+)$/.exec(location.hash),c;
  if(m&&(c=document.getElementById('c'+m[1]))){
    var b=c.closest('.book');setBook(b,true);c.classList.add('open');c.classList.add('deeplink');
    var oh=c.querySelector('.cardhead');
    if(oh){oh.setAttribute('aria-expanded','true');try{oh.focus({preventScroll:true});}catch(_){}}
    setTimeout(function(){c.scrollIntoView({behavior:RM?'auto':'smooth',block:'center'});},60);return true;
  }
  m=/^#b-([a-z0-9-]+)$/.exec(location.hash);
  if(m){var bk=document.getElementById('b-'+m[1]);
    if(bk){setBook(bk,true);setTimeout(function(){bk.scrollIntoView({behavior:RM?'auto':'smooth',block:'start'});},60);return true;}}
  m=/^#g-([a-z0-9-]+)$/.exec(location.hash);
  if(m){var gn=document.getElementById('g-'+m[1]);
    if(gn){setTimeout(function(){gn.scrollIntoView({behavior:RM?'auto':'smooth',block:'start'});},60);return true;}}
  return false;
}
openHash();
(function restoreURL(){
  var p,qq,tt,gg,bb,want,i;
  try{p=new URLSearchParams(location.search);}catch(_){return;}
  qq=p.get('q');if(qq)q.value=qq;
  tt=p.get('type');
  if(tt){want={};tt.split(',').forEach(function(t){want[t]=1;});
    for(i=0;i<tboxes.length;i++)tboxes[i].checked=!!want[tboxes[i].value];}
  gg=p.get('g');if(gg)gs.value=gg;
  bb=p.get('b');if(bb)bs.value=bb;
  if(tt){var d=document.getElementById('typefilter');if(d)d.open=true;}
})();
var restoredQ=q.value.trim()!=='';
apply(restoredQ);
openHash();
})();

"""

fb_intro = ""
fb_footer = ""
if fbooks:
    fb_intro = ("<p><strong>Full Books:</strong> below the shelves \u2014 standalone deep-dives "
                "(the argument, turning points, every card) for books too rich to shred into rips.</p>")
    fb_footer = " &middot; %d full-book brief%s" % (len(fbooks), "" if len(fbooks) == 1 else "s")

page = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&family=Spectral:ital,wght@0,400;1,400&display=swap"/>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&family=Spectral:ital,wght@0,400;1,400&display=swap"/>
<title>Idea Ripper - the idea-hunting library</title>
<link rel="icon" type="image/svg+xml" href="brand/r-mark.svg"/>
<link rel="icon" type="image/png" sizes="32x32" href="brand/r-mark-32.png"/>
<link rel="apple-touch-icon" href="brand/apple-touch-icon.png"/>
<style>%s</style><noscript><style>.book.collapsed .cards,.fbook.collapsed .fbookbody{display:block!important}.cardbody{display:block!important}</style></noscript>
</head>
<body>

<header class="masthead"><div class="mast-inner">
<h1 class="wordmark"><span class="sr-only">Idea Ripper</span>%s</h1>
<p class="print-title">Idea Ripper \u2014 the idea-hunting library</p>
<p class="mast-sub">the idea-hunting library</p>
<p class="mast-meta">%d rips &middot; %d books &middot; %d theses &middot; curated %s</p>
</div></header>
<section id="intro">
<p><strong>What this is:</strong> a hunting library of ideas ripped by hand from books worth stealing from. Every rip is one stealable mechanism — the exact lines worth keeping, plus when to use them.</p>
<details class="intromore"><summary>How to hunt</summary>
<p><strong>How to hunt:</strong> tap a book to open its rips, tap a card for the full steal, copy anything you want. Search hunts titles, steals, and use-whens all at once.</p>
%s
</details>
</section>
<div class="controls"><div class="inner">
<input type="search" id="q" placeholder="Search titles, steals, use-when&hellip;" aria-label="Search cards"/>
<select id="fgenre" aria-label="Filter by genre"><option value="">All genres</option>
%s</select>
<select id="fbook" aria-label="Filter by book"><option value="">All books</option>
%s</select>
<details class="typefilter" id="typefilter">
<summary>Filter by type <span class="tcount" id="tcount" hidden></span></summary>
<fieldset>
<legend>Filter by type</legend>
%s
<button type="button" id="cleartypes" hidden>Clear type filters</button>
</fieldset>
</details>
<button type="button" id="expand">Expand all</button>
<button type="button" id="collapse">Collapse all</button>
<span class="count" id="count"></span><span id="countlive" class="sr-only" aria-live="polite"></span>
</div></div>
<nav class="jumpchips" id="jumpchips" aria-label="Jump to a genre or book"><span class="gindex">%s</span><span class="scents">%s</span></nav>
<main>
%s
<p class="noresults" id="noresults" hidden>No rips match — try a mechanism word (interlock, delay, patronage).</p>
</main>
<footer><p class="fmeta">Last curated %s &middot; %d books &middot; %d theses &middot; %d rips%s &middot; ripped with the Idea Ripper pipeline</p></footer>
<script>%s</script>
<div id="toast" role="status"></div>
</body>
</html>""" % (CSS, WORDMARK_SVG, n, n_books, n_theses, curated, fb_intro, genre_opts, book_opts, type_checks, gindex, chips,
              "\n\n".join(sections), curated_long, n_books, n_theses, n, fb_footer, JS)

open(os.path.join(BASE, "index.html"), "w", encoding="utf-8").write(page)
print("built: %d cards, %d books, %d theses, %d genres" % (n, n_books, n_theses, len(genre_order)))
