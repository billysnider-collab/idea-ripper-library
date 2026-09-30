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
_byid = {c["id"]: c for c in cards}  # phase 5: related-rip title lookup

def book_block(b):
    gh = ghue[b["genre"]]
    slug = book_slug(b)
    bcards = [c for c in cards if c["book"] == b["book"]]
    _bt, _ba = b["book"].rsplit(" — ", 1) if " — " in b["book"] else (b["book"], "")
    _bauthor = '<span class="bauthor">%s</span>' % esc(_ba) if _ba else ""
    samples = " · ".join("\u201c%s\u201d" % c["title"] for c in bcards[:2])
    parts = ['<section class="book collapsed" id="b-%s" data-book="%s" data-genre="%s">'
             % (slug, esca(b["book"]), esca(b["genre"]))]
    parts.append(
        '<h2 class="bh"><button type="button" class="bookhead" aria-expanded="false">'
        '<span class="chip" data-hue="%d"></span>'
        '<span class="bmain"><span class="btitle"><span class="bttext" title="%s">%s</span> <span class="bcount">%d rip%s</span></span>'
        '%s'
        '<span class="bookline">%s</span>'
        '<span class="bsamples">%s</span></span>'
        '<span class="bchev">\u25be</span></button><button type="button" class="xall" aria-expanded="false" aria-label="Expand or collapse all rips in this book">Expand all</button></h2>'
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
        _rel = c.get("related_ids") or []
        _rell = ['<a href="#c%d">%s</a>' % (_byid[r]["id"], esc(_byid[r]["title"])) for r in _rel if r in _byid]
        relhtml = ('<p class="rel"><span class="rk">Related rips:</span> ' + " \u00b7 ".join(_rell) + "</p>") if _rell else "" 
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
            '%s'
            '<div class="actions"><button type="button" data-copy="steal">Copy steal</button>'
            '<button type="button" data-copy="uw">Copy use-when</button>'
            '<button type="button" data-copy="link">Copy link</button>'
            '<button type="button" data-save="%d" aria-pressed="false">Save</button></div>'
            '</div></article>'
            % (" open" if thesis_open else "", n_, n_, esca(c["book"]), esca(b["genre"]), esca(c["type"]), c.get("status", "keeper"), esca(search),
               "true" if thesis_open else "false",
               n_, esc(c["title"]), esc(pv), esca(c["type"]), esc(c["type"]),
               kicker_rip, esc(c["steal"]), esc(c["why"]), kicker_use, esc(c["uw"]), relhtml, n_))
    parts.append('</div></section>')
    return "\n".join(parts)

# Phase 1 landing (2026-09-27): Start-here shelf - 5 hand-picked rips rendered
# in full above the library. Rendered as article.fcard (NOT article.card, and
# no span.num) so the build_index card-count/numbering gates keep counting
# library cards only. Each links down to its canonical #c<id> shelf card.
FEATURED_IDS = [623, 117, 470, 500, 149]
def featured_block():
    # 2026-09-30 (Billy): intro trim - the five hand-picked rips render as ONE
    # compact link card, not five full cards. Full cards live on the shelf.
    feats = [c for _fid in FEATURED_IDS for c in cards if c["id"] == _fid]
    assert len(feats) == len(FEATURED_IDS), "featured id missing from cards"
    fk = '<p class="fkicker">' + RIP_SVG + '<span class="ktext">Start here</span></p>'
    items = "".join(
        '<li><a href="#c%d"><span class="sht">%s</span> <span class="shb">%s</span></a></li>'
        % (c["id"], esc(c["title"]), esc(c["book"])) for c in feats)
    parts = ['<h2 class="genre" data-genre="Start here" id="g-start-here">Start here <span class="gcount">5 rips, hand-picked</span></h2>',
             '<section class="start-here-compact" aria-label="Start here: five featured rips">',
             '<article class="fcard shcard">%s<ul class="shlist">%s</ul></article>' % (fk, items),
             '</section>']
    return "\n".join(parts)


# Rip of the week (2026-09-27): one hand-picked card rendered as a hero above
# the Start-here shelf. Config lives in shelf.yaml as rip_of_the_week:
# {id: <card id>, week: "Sep 27 - Oct 4, 2026", note: "one-line editor note"}.
# Rendered as article.fcard (NOT article.card, no span.num) so the build_index
# gates keep counting library cards only. Rotate by changing the shelf entry.
def rotw_block():
    rotw = ds.get("rip_of_the_week") or {}
    rid = rotw.get("id")
    matches = [c for c in cards if c["id"] == rid]
    assert matches, "rip_of_the_week id %r not in cards" % (rid,)
    c = matches[0]
    fk = '<p class="fkicker">' + RIP_SVG + '<span class="ktext">Rip of the week</span></p>'
    kr = '<div class="kicker">' + RIP_SVG + '<span class="ktext">Ripped from</span></div>'
    ku = '<div class="kicker">' + RIP_SVG + '<span class="ktext">Use when</span></div>'
    parts = ['<section class="rotw" aria-label="Rip of the week">',
             '<article class="fcard rotw-card">',
             fk,
             '<h3 class="ftitle">%s</h3>' % esc(c["title"]),
             '<p class="fbook">%s &middot; <span class="pill %s">%s</span></p>'
             % (esc(c["book"]), esca(c["type"]), esc(c["type"])),
             kr,
             '<p class="steal">%s</p>' % esc(c["steal"]),
             '<p class="why"><span class="k">Why it matters:</span> %s</p>' % esc(c["why"]),
             ku,
             '<p class="uw">%s</p>' % esc(c["uw"])]
    week = rotw.get("week") or ""
    note = rotw.get("note") or ""
    if week or note:
        parts.append('<p class="rotw-meta">%s%s%s</p>'
                     % (esc(week), " &mdash; " if week and note else "", esc(note)))
    parts.append('<p class="fmore"><a href="#c%d">Find it on the shelf \u2193</a></p>' % c["id"])
    parts.append('</article>')
    parts.append('</section>')
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
        '<span class="chip chip-fb"></span>'
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


def book_slug(b):
    # per-book anchor override; falls back to slugified title (legacy behavior)
    return b.get("anchor") or slugify(b["book"])

genre_of = {b["book"]: b["genre"] for b in books}
sections = []
# recently ripped shelf: the N books with the highest max card id (theses excluded:
# theses are ideas, not books). Rendered first, above the genre sections, and excluded
# from their genre sections below so every card still renders exactly once.
sections.append(rotw_block())
sections.append(featured_block())
RECENT_N = ds.get("recent_first", 5)
def _book_maxid(bname):
    return max(c["id"] for c in cards if c["book"] == bname)
recent_books = sorted([b for b in books if b["genre"] != "Thesis"],
                      key=lambda b: _book_maxid(b["book"]), reverse=True)[:RECENT_N]
# 2026-09-30 (Billy): intro trim - recent books render as one compact link strip,
# not full book blocks. Each book still renders exactly once, in its genre shelf.
if recent_books:
    rlinks = "".join(
        '<a class="rchip" href="#b-%s">%s</a>' % (book_slug(b), esc(b["book"]))
        for b in recent_books)
    sections.append('<h2 class="genre" data-genre="Recently ripped" id="g-recently-ripped">Recently ripped <span class="gcount">%d books</span></h2>'
                    % len(recent_books))
    sections.append('<nav class="recent-strip" aria-label="Recently ripped books">%s</nav>' % rlinks)
for g in genre_order:
    _gb_all = books_in_genre(g)
    if not _gb_all:
        continue
    gbooks = _gb_all
    gcount = sum(1 for c in cards if genre_of[c["book"]] == g)
    gunit = "theses" if g == "Thesis" else "books"
    sections.append('<h2 class="genre" data-genre="%s" id="g-%s">%s <span class="gcount">%d cards · %d %s</span></h2>'
                    % (esca(g), slugify(g), esc(g), gcount, len(_gb_all), gunit))
    for b in gbooks:
        sections.append(book_block(b))

if fbooks:
    fb_cards = sum(len(fb["cards"]) for fb in fbooks)
    sections.append('<h2 class="genre fbshelf">Full Books <span class="gcount">%d deep %s &middot; %d cards</span></h2>'
                    % (len(fbooks), "dive" if len(fbooks) == 1 else "dives", fb_cards))
    for fb in fbooks:
        sections.append(fullbook_block(fb))

# collide (2026-09-27): empty shell at the top of main; JS populates the pair
# on button click. No static article.card markup, so build_index's card gates
# keep counting library cards only.
collide_section = ("<section class=\"collideshelf\" id=\"collide\" aria-label=\"Collide\" hidden>"
    "<h2 class=\"collidehead\">Collide <span class=\"gcount\">two rips, different worlds</span></h2>"
    "<p class=\"collideframe\">Two rips from different worlds. The collision is the point &mdash; your move.</p>"
    "<div class=\"collidepair\" id=\"collidepair\"></div>"
    "<div class=\"savedactions\"><button type=\"button\" id=\"collideagain\">Collide again</button></div>"
    "</section>")
sections.insert(0, collide_section)

# genre index: one compact link per genre (label + mono card count)
_gcounts = {g: sum(1 for c in cards if genre_of[c["book"]] == g) for g in genre_order}
gindex = "\n".join(
    '<a class="gix" href="#g-%s" data-genre="%s"><span class="gdot"></span>%s <span class="gixc">%d</span></a>'
    % (slugify(g), esca(g), esc(g), _gcounts[g])
    for g in genre_order if _gcounts[g])
# phase 5: saved-rips chip (count filled by JS)
gindex = ('<a class="gix" id="savedchip" href="#saved"><span class="gdot"></span>\u2605 Saved (0)</a>\n' + gindex)
# jump scents: the 12 most recently added books (highest max card id)
def _maxid(b):
    return max(c["id"] for c in cards if c["book"] == b["book"])
scents = sorted(books, key=_maxid, reverse=True)[:12]
chips = "\n".join(
    '<a class="bchip" href="#b-%s" data-genre="%s" title="%s">%s</a>'
    % (book_slug(b), esca(b["genre"]), esca(b["book"]), esc(b["book"]))
    for b in scents)
# phase 2: browse-all-books expander list (theses excluded: ideas, not books)
_bbrowse = [b for b in books if b["genre"] != "Thesis"]
n_btotal = len(_bbrowse)
blist = "\n".join(
    '<a class="blist-item" href="#b-%s" data-book="%s"><span class="bt">%s</span><span class="bc">%d</span></a>'
    % (book_slug(b), esca(b["book"]), esc(b["book"]),
       sum(1 for c in cards if c["book"] == b["book"]))
    for b in _bbrowse)

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
  /* "Oxblood on paper" (Billy lock 2026-09-29, re-applied 2026-09-30 after 164ec42).
     Light only, no dark mode. The accent is the ONLY saturated color: Copy
     buttons, links, and the keep marker (Save / Saved). Everything else is
     ink, muted, or line. */
  color-scheme:light; /* one deliberate palette: the OS never re-themes this page */
  --paper:#F5EFE3;           /* bg: cream paper */
  --surface:#FCFAF4;         /* cards */
  --ink:#1D1913;             /* text: 16.8:1 on surface */
  --ink-muted:#6C6355;       /* secondary text: 5.2:1 on paper, 5.7:1 on surface */
  --line:#E4DCC9;            /* hairline borders */
  --line-strong:#CFC4AE;     /* neutral outline / hover rule (no hue) */
  --accent:#A03B2A;          /* oxblood */
  --accent-deep:#7E2E20;     /* oxblood hover / pressed */
  /* legacy token names, remapped onto the paper palette */
  --surface-frame:var(--paper);
  --surface-base:var(--paper);
  --surface-paper:var(--surface);
  --surface-raised:var(--surface);
  --ink-frame:var(--ink);
  --accent-rip:var(--ink);   /* rules + rip marks are ink now, not red */
  --ink-body:var(--ink);
  --ink-structure:var(--ink-muted);
  --mark-highlight:#E9DDC0;  /* search-hit ground: darker paper, no hue */
  --link:var(--accent);
  --surface-frame-raised:var(--surface);
  --ink-structure-frame:var(--ink-muted);
  --line-frame:var(--line);
  --line-structure:var(--line-strong);
  --line-card:var(--line);
  --accent-mechanism:var(--ink-muted);
  --accent-mechanism-line:var(--line-strong);
  --accent-rust:var(--line-strong); /* title rules + chrome hover: neutral */
  --accent-rust-hi:var(--accent-deep); /* link hover */
  --accent-rust-hover:var(--ink);
  --amber:var(--ink-muted);
  --type-mechanism:var(--ink);      /* type pills: ink/muted outlines, told apart by label + weight */
  --type-argument:var(--ink-muted);
  --type-concept:var(--ink-muted);
  --type-passage:var(--ink-muted);
  --type-definition:var(--ink-muted);
  --type-evidence:var(--ink-muted);
  --type-contradiction:var(--ink);
  --type-question:var(--ink-muted);
  --type-prediction:var(--ink-muted);
  --print-ink:#000;                /* print only: black text on white */
  --print-paper:#fff;              /* print only */
  /* type */
  --font-mono:ui-monospace,SFMono-Regular,"Cascadia Code",Menlo,Consolas,monospace;
  --font-serif:"Iowan Old Style","Source Serif 4","Source Serif Pro",Georgia,"Times New Roman",serif;
  --font-sans:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  --font-read:var(--font-serif);
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
  --radius-sm:3px;
  --radius-md:4px;
  --radius-lg:4px;
  --radius-pill:3px;   /* catalog tags read square, not bubbly */
}
*{box-sizing:border-box}
html{font-size:100%}
body{margin:0;font-family:var(--font-sans);font-size:var(--fs-base);line-height:var(--lh-body);background:var(--surface-base);color:var(--ink-body)}
:focus-visible{outline:2px solid var(--accent-rust);outline-offset:2px}
body::before{content:"";position:fixed;inset:0;z-index:100;pointer-events:none;opacity:.035;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='160' height='160' filter='url(%23n)'/%3E%3C/svg%3E")}
/* ---------- frame: masthead ---------- */
header.masthead{max-width:none;padding:0;background:var(--surface-frame);color:var(--ink-frame);border-bottom:2px solid var(--ink)}
.mast-inner{max-width:var(--page-max);margin:0 auto;padding:var(--space-md) var(--page-gutter) var(--space-md)}
.wordmark{max-width:var(--wordmark-max);margin:0}
.wordmark svg{display:block;width:100%;height:auto}
/* existing mark, presented in frame ink: shapes untouched, fills remapped */
.wordmark svg [fill="#1D1913"]{fill:var(--ink-frame)}
.wordmark svg [stroke="#A03B2A"]{stroke:var(--accent-rip)}
.print-title{display:none}
.mast-sub{margin:var(--space-sm) 0 0;font-family:var(--font-mono);font-size:var(--fs-xs);font-weight:400;letter-spacing:.24em;text-transform:uppercase;color:var(--ink-frame)}
.mast-meta{margin:var(--space-2xs) 0 0;font-family:var(--font-mono);font-size:var(--fs-sm);color:var(--ink-structure-frame)}
.mast-inner{position:relative}
.rip-request{position:absolute;top:var(--space-md);right:var(--page-gutter);font-family:var(--font-mono);font-size:var(--fs-xs);letter-spacing:.14em;text-transform:uppercase;color:var(--ink-frame);border:1px solid var(--ink-frame);border-radius:999px;padding:.5em 1.1em;text-decoration:none;white-space:nowrap}
.rip-request:hover{border-color:var(--accent-rust);color:var(--accent-rust-hi)}
@media (max-width:560px){.rip-request{position:static;display:inline-block;margin-top:var(--space-sm);font-size:11px;padding:.45em .9em}}
/* ---------- start-here shelf (phase 1, 2026-09-27) ---------- */
.start-here{display:grid;gap:var(--space-md);margin:0 0 var(--space-xl)}
.fcard{background:var(--surface-paper);border:1px solid var(--line-card);border-radius:var(--radius-lg);padding:var(--space-md) var(--space-lg);position:relative}
.fcard:hover{border-color:var(--line-structure)}
.fkicker{display:flex;align-items:center;gap:var(--space-xs);margin:0 0 var(--space-xs);font-family:var(--font-mono);font-size:var(--fs-xs);font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:var(--ink-structure)}
.fkicker .ripmark{width:var(--space-lg);height:auto;flex:none}
.fkicker .ripmark polyline{stroke:var(--accent-rip)}
.fkicker .ktext{border-bottom:2px solid var(--accent-rip);padding-bottom:var(--space-3xs)}
.ftitle{margin:0 0 var(--space-2xs);font-size:var(--fs-xl);line-height:var(--lh-tight);color:var(--ink-body);border-bottom:2px solid var(--accent-rust);padding-bottom:var(--space-3xs)}
.fbook{margin:0 0 var(--space-sm);font-family:var(--font-mono);font-size:var(--fs-sm);color:var(--ink-structure)}
.fcard .steal{font-size:var(--fs-lg)}
.fmore{margin:var(--space-sm) 0 0;font-family:var(--font-mono);font-size:var(--fs-xs)}
.fmore a{color:var(--link)}
@media(min-width:900px){.start-here{grid-template-columns:1fr 1fr}.fcard:first-child{grid-column:1/-1}}

/* ---------- rip of the week (2026-09-27) ---------- */
.rotw{margin:0 0 var(--space-xl)}
.rotw-card{border:2px solid var(--accent-rip)}
.rotw-meta{margin:var(--space-sm) 0 0;font-family:var(--font-mono);font-size:var(--fs-sm);color:var(--ink-structure)}
/* ---------- intro trim (2026-09-30): one compact start-here card + recent strip ---------- */
.start-here-compact{margin:0 0 var(--space-xl)}
.shcard{padding:var(--space-md)}
.shlist{list-style:none;margin:var(--space-sm) 0 0;padding:0;display:grid;gap:var(--space-2xs)}
.shlist a{display:flex;justify-content:space-between;align-items:center;gap:var(--space-sm);text-decoration:none;color:var(--ink-body);padding:var(--space-2xs) var(--space-xs);border-radius:var(--radius-sm);min-height:44px}
.shlist a:hover{background:var(--surface-frame-raised);color:var(--ink-frame)}
.shlist .sht{font-weight:600}
.shlist .shb{font-family:var(--font-mono);font-size:var(--fs-xs);color:var(--ink-structure);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:40%}
.shlist a:hover .shb{color:var(--ink-frame)}
.recent-strip{display:flex;flex-wrap:wrap;gap:var(--space-2xs);margin:0 0 var(--space-xl)}
.rchip{display:inline-block;padding:var(--space-2xs) var(--space-sm);border:1px solid var(--line-card);border-radius:var(--radius-md);background:var(--surface-paper);color:var(--ink-body);text-decoration:none;font-size:var(--fs-sm);font-family:var(--font-mono)}
.rchip:hover{background:var(--surface-frame-raised);color:var(--ink-frame);border-color:var(--surface-frame-raised)}

/* ---------- collide (2026-09-27) ---------- */
.collideshelf{margin:0 0 var(--space-xl);scroll-margin-top:var(--scroll-mt)}
.collidehead{margin:0 0 var(--space-2xs);font-size:1.4rem;font-weight:400;color:var(--ink-body);border-bottom:2px solid var(--accent-rust);padding-bottom:var(--space-2xs);line-height:var(--lh-tight)}
.collidehead .gcount{color:var(--ink-structure);font-size:var(--fs-sm);font-weight:400;font-family:var(--font-mono)}
.collideframe{margin:var(--space-xs) 0 var(--space-md);font-family:var(--font-mono);font-size:var(--fs-sm);color:var(--ink-structure)}
.collidepair{display:grid;gap:var(--space-md);margin:0 0 var(--space-md)}
@media(min-width:900px){.collidepair{grid-template-columns:1fr 1fr}}
@media(max-width:700px){.collideshelf{scroll-margin-top:var(--scroll-mt-mobile)}}

/* ---------- frame: controls ---------- */
.controls{position:sticky;top:0;z-index:20;background:var(--surface-frame);border-bottom:1px solid var(--line-frame);padding:var(--space-sm) 0}
.controls .inner{max-width:var(--page-max);margin:0 auto;padding:0 var(--page-gutter);display:flex;gap:var(--space-xs);flex-wrap:wrap;align-items:center}
.controls input[type=search]{flex:1 1 var(--search-min);background:var(--surface-frame-raised);border:1px solid var(--line-frame);color:var(--ink-frame);border-radius:var(--radius-md);padding:var(--space-xs) var(--space-sm);font-size:var(--fs-md);font-family:var(--font-mono)}
.controls select{background:var(--surface-frame-raised);border:1px solid var(--line-frame);color:var(--ink-frame);border-radius:var(--radius-md);padding:var(--space-xs) var(--space-xs);font-size:var(--fs-sm);font-family:var(--font-mono);max-width:var(--select-max)}
.controls button{background:transparent;border:1px solid var(--line-frame);color:var(--ink-frame);border-radius:var(--radius-md);padding:var(--space-2xs) var(--space-sm);font-size:var(--fs-sm);font-family:var(--font-mono);cursor:pointer}
.controls button:hover{border-color:var(--accent-rust)}
.count{color:var(--ink-structure-frame);font-size:var(--fs-sm);font-family:var(--font-mono);margin-left:auto;min-width:var(--count-min);text-align:right}
/* ---------- frame: type filter ---------- */
.typefilter{position:relative}
.typefilter>summary{cursor:pointer;list-style:none;background:var(--surface-frame-raised);border:1px solid var(--line-frame);color:var(--ink-frame);border-radius:var(--radius-md);padding:var(--space-xs) var(--space-xs);font-size:var(--fs-sm);font-family:var(--font-mono)}
.typefilter>summary::-webkit-details-marker{display:none}
.typefilter>summary::before{content:"▸  ";color:var(--accent-rust)}
.typefilter[open]>summary::before{content:"▾  "}
.typefilter fieldset{border:1px solid var(--line-frame);border-radius:var(--radius-md);padding:var(--space-sm) var(--space-md);margin:var(--space-xs) 0 0;display:flex;flex-wrap:wrap;gap:var(--space-2xs) var(--space-md);flex:1 1 100%;background:var(--surface-frame-raised)}
.typefilter legend{font-size:var(--fs-sm);font-family:var(--font-mono);color:var(--ink-structure-frame);padding:0 var(--space-2xs)}
.tcheck{display:inline-flex;align-items:center;gap:var(--space-2xs);font-size:var(--fs-sm);font-family:var(--font-mono);cursor:pointer;color:var(--ink-frame)}
.tcheck input{accent-color:var(--accent-rust);width:var(--space-md);height:var(--space-md)}
.tn{color:var(--ink-structure-frame);font-size:var(--fs-sm)}
.tcount{background:transparent;border:1px solid var(--accent-rust);color:var(--ink-frame);border-radius:var(--radius-pill);font-size:var(--fs-xs);font-weight:700;padding:var(--space-3xs) var(--space-xs);margin-left:var(--space-2xs);font-family:var(--font-mono)}
#cleartypes{background:transparent;border:1px solid var(--line-frame);color:var(--ink-frame);border-radius:var(--radius-sm);padding:var(--space-2xs) var(--space-sm);font-size:var(--fs-sm);font-family:var(--font-mono);cursor:pointer}
#cleartypes:hover{border-color:var(--accent-rust)}
/* ---------- frame: TOC jump chips ---------- */
.jumpchips{max-width:none;background:var(--surface-frame);border-bottom:1px solid var(--line-frame);margin:0;padding:var(--space-xs) var(--page-gutter);display:flex;gap:var(--space-2xs);overflow-x:auto;scrollbar-width:thin}
.jumpchips a{flex:none;max-width:var(--chip-max);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;background:var(--surface-frame-raised);border:1px solid var(--line-frame);color:var(--ink-frame);border-radius:var(--radius-pill);padding:var(--space-2xs) var(--space-sm);font-size:var(--fs-xs);font-family:var(--font-mono);cursor:pointer;text-decoration:none}
.jumpchips a:hover{border-color:var(--accent-rust)}
.jumpchips{align-items:center}
/* phase 2: genre tiles */
.gindex{flex:none;display:flex;flex-wrap:wrap;gap:var(--space-2xs);align-items:stretch;padding:var(--space-3xs) var(--space-sm) var(--space-3xs) 0;border-right:1px solid var(--line-frame);margin-right:var(--space-2xs)}
.gix{flex:none;display:flex;align-items:center;gap:var(--space-2xs);background:var(--surface-frame-raised);border:1px solid var(--line-frame);border-top:2px solid var(--line-frame);color:var(--ink-frame);border-radius:4px 4px 2px 2px;padding:var(--space-2xs) var(--space-sm);font-family:var(--font-mono);font-size:var(--fs-sm);white-space:nowrap;min-height:44px;text-decoration:none}
.gix:hover{border-color:var(--accent-rust)}
.gix .gdot{width:.7em;height:.7em;border-radius:50%;flex:none}
.gix .gixc{color:var(--ink-structure-frame);font-variant-numeric:tabular-nums}
.scents{flex:1;min-width:0;display:flex;gap:var(--space-2xs);overflow-x:auto;scrollbar-width:thin;padding:var(--space-3xs) 0}
/* ---------- phase 2: browse-all-books + crumbs ---------- */
.bookbrowser{max-width:var(--page-max);margin:0 auto;padding:var(--space-xs) var(--page-gutter) 0}
.bookbrowser summary{cursor:pointer;font-family:var(--font-mono);font-size:var(--fs-sm);color:var(--ink-body);padding:var(--space-2xs) 0;list-style:none;min-height:44px;display:flex;align-items:center}
.bookbrowser summary::-webkit-details-marker{display:none}
.bookbrowser summary::before{content:"\u25b8";color:var(--accent-rust);margin-right:var(--space-2xs)}
.bookbrowser[open] summary::before{content:"\u25be"}
.bookbrowser .btotal{color:var(--ink-structure)}
.blist-filter{width:100%;max-width:var(--measure);margin:var(--space-2xs) 0 var(--space-xs);padding:var(--space-2xs) var(--space-sm);font-family:var(--font-mono);font-size:var(--fs-sm);border:1px solid var(--line-card);border-radius:var(--radius-md);background:var(--surface-paper);color:var(--ink-body)}
.blist{display:grid;grid-template-columns:repeat(auto-fill,minmax(16rem,1fr));gap:var(--space-3xs) var(--space-sm);padding-bottom:var(--space-md)}
.blist-item{display:flex;justify-content:space-between;align-items:center;gap:var(--space-sm);padding:var(--space-2xs) var(--space-xs);border-radius:var(--radius-sm);text-decoration:none;color:var(--ink-body);font-size:var(--fs-sm);min-height:44px}
.blist-item:hover{background:var(--surface-frame-raised);color:var(--ink-frame)}
.blist-item:hover .bc{color:var(--ink-frame)}
.blist-item .bt{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.blist-item .bc{flex:none;font-family:var(--font-mono);font-size:var(--fs-xs);color:var(--ink-structure)}
.crumbs{max-width:var(--page-max);margin:0 auto;padding:var(--space-xs) var(--page-gutter) 0;font-family:var(--font-mono);font-size:var(--fs-xs);color:var(--ink-structure);display:flex;align-items:center;flex-wrap:wrap;gap:var(--space-2xs)}
.crumbs a{color:var(--link);text-decoration:none}
.crumbs a:hover{color:var(--accent-rust-hi);text-decoration:underline}
.ccur{min-width:0;overflow-wrap:anywhere}
.csep{color:var(--ink-structure)}
.ccur{color:var(--ink-body)}
/* ---------- frame: footer ---------- */
footer{background:var(--surface-frame);color:var(--ink-frame);font-family:var(--font-mono);font-size:var(--fs-sm);padding:var(--space-xl) var(--page-gutter);border-top:2px solid var(--ink);text-align:center}
footer .fmeta{margin:0;color:var(--ink-structure-frame)}
/* ---------- reading zone ---------- */
#intro{max-width:var(--page-narrow);margin:0 auto;padding:var(--space-md) var(--page-gutter) 0;color:var(--ink-body);font-size:var(--fs-base)}
#intro p{margin:var(--space-xs) 0;max-width:var(--measure)}
#intro strong{color:var(--ink-body);font-weight:700}
.intromore{margin:var(--space-xs) 0}
.intromore summary{cursor:pointer;color:var(--ink-structure);font-size:var(--fs-sm)}
main{max-width:var(--page-narrow);margin:0 auto;padding:var(--space-md) var(--page-gutter) var(--space-2xl)}
main a{color:var(--link)}
main a:hover,.fmore a:hover{color:var(--accent-rust-hi)}
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
.bh{display:flex;align-items:center;gap:var(--space-sm)}
.bh .bookhead{flex:1;min-width:0;width:auto}
.xall{flex:none;font-family:var(--font-mono);font-size:.75rem;line-height:1;color:var(--ink-structure);background:transparent;border:1px solid var(--line-structure);border-radius:var(--radius-sm);padding:0 var(--space-sm);min-height:44px;cursor:pointer;white-space:nowrap}
.xall:hover{color:var(--ink-body);border-color:var(--accent-rust)}
/* ---------- cards (repainted for paper, option A) ---------- */
.card{background:var(--surface-paper);border:1px solid var(--line-card);border-radius:var(--radius-lg);padding:var(--space-sm) var(--space-md);margin:var(--space-xs) 0;position:relative}
.card:hover{border-color:var(--line-structure)}
.cardhead{display:flex;align-items:baseline;gap:var(--space-sm)}
.num{color:var(--ink-structure);font-size:var(--fs-sm);font-family:var(--font-mono);flex:none;min-width:var(--num-min)}
.ctext{flex:1;min-width:0}
.ctitle{display:block;font-size:var(--fs-lg);color:var(--ink-body);line-height:var(--lh-tight);border-bottom:2px solid var(--accent-rust);padding-bottom:var(--space-3xs);margin-bottom:var(--space-3xs)}
.pv{display:block;color:var(--ink-structure);font-size:var(--fs-sm);font-weight:400;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card.open .pv{display:none}
.pill{flex:none;display:inline-block;padding:var(--space-3xs) var(--space-xs);border-radius:var(--radius-pill);border:1px solid var(--line-structure);font-size:var(--fs-xs);font-family:var(--font-mono);color:var(--ink-structure)}
.pill.mechanism{color:var(--type-mechanism);border-color:var(--type-mechanism)}
.pill.argument{color:var(--type-argument);border-color:var(--type-argument)}
.pill.concept{color:var(--type-concept);border-color:var(--type-concept)}
.pill.passage{color:var(--type-passage);border-color:var(--type-passage)}
.pill.definition{color:var(--type-definition);border-color:var(--type-definition)}
.pill.evidence{color:var(--type-evidence);border-color:var(--type-evidence)}
.pill.contradiction{color:var(--type-contradiction);border-color:var(--type-contradiction)}
.pill.question{color:var(--type-question);border-color:var(--type-question)}
.pill.prediction{color:var(--type-prediction);border-color:var(--type-prediction)}
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
.actions button{background:transparent;border:1px solid var(--line-structure);color:var(--accent-rip);border-radius:var(--radius-sm);padding:var(--space-2xs) var(--space-sm);font-size:var(--fs-sm);font-family:var(--font-mono);cursor:pointer}
.actions button:hover{color:var(--accent-rip);border-color:var(--accent-rip);background:#A03B2A0F}
.card.deeplink{outline:3px solid var(--accent-rip);outline-offset:3px}
.hidden{display:none!important}
/* ---------- search ---------- */
mark{background:var(--mark-highlight);color:var(--ink-body);font-weight:400;border-radius:2px;padding:0 .1em}
.noresults{color:var(--ink-structure);text-align:center;padding:var(--space-xl) 0;font-size:var(--fs-base)}
.noresults button{background:transparent;border:1px solid var(--line-structure);color:var(--ink-structure);border-radius:var(--radius-md);padding:var(--space-xs) var(--space-sm);font-size:var(--fs-sm);font-family:var(--font-mono);cursor:pointer;margin-left:var(--space-xs)}
.noresults button:hover{color:var(--ink-body);border-color:var(--accent-rust)}
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
.book:not(.collapsed) .cards{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:var(--space-sm);align-items:start}
.book:not(.collapsed) .card{margin:0}
.fbook:not(.collapsed) .fbcards{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:var(--space-sm);align-items:start}
.fbook:not(.collapsed) .fbcards .card{margin:0}
}
/* phase 5: saved shelf + related rips */
.savedshelf{margin:var(--space-xl) 0}
.savehead{font-family:var(--font-read);font-weight:600;font-size:var(--fs-xl);color:var(--ink-body);border-bottom:2px solid var(--accent-rust);padding-bottom:var(--space-2xs);margin:0 0 var(--space-sm)}
.savenote{color:var(--ink-structure);font-size:var(--fs-sm);margin:var(--space-2xs) 0}
.savedlist{display:grid;gap:var(--space-2xs);margin:var(--space-sm) 0}
.sitem{display:flex;gap:var(--space-sm);align-items:baseline;flex-wrap:wrap;background:var(--surface-raised);border:1px solid var(--line-card);border-radius:var(--radius-md);padding:var(--space-2xs) var(--space-sm)}
.sitem a{color:var(--link);font-weight:600;text-decoration:none}
.sitem a:hover{text-decoration:underline}
.sitem .smeta{color:var(--ink-structure);font-size:var(--fs-xs);font-family:var(--font-mono)}
.savedactions{display:flex;gap:var(--space-sm);margin-top:var(--space-sm);flex-wrap:wrap}
.savedactions button{font-family:var(--font-mono);font-size:var(--fs-sm);background:var(--surface-frame-raised);border:1px solid var(--line-frame);color:var(--ink-frame);border-radius:var(--radius-md);padding:var(--space-2xs) var(--space-md);min-height:44px;cursor:pointer}
.savedactions button:hover:not(:disabled){border-color:var(--ink-frame);color:var(--ink-frame)}
.savedactions button:disabled{opacity:.4;cursor:default}
.actions button[aria-pressed="true"]{color:var(--accent-rip);border-color:var(--accent-rip)}
.rel{margin:var(--space-sm) 0 0;font-size:var(--fs-sm);color:var(--ink-structure)}
.rel .rk{font-family:var(--font-mono);font-size:var(--fs-xs);text-transform:uppercase;letter-spacing:.08em}
.rel a{color:var(--link);text-decoration:none}
.rel a:hover{text-decoration:underline}
@media(max-width:700px){
.bsamples{display:none}
.controls input[type=search]{flex:1 1 100%}
.typefilter{flex:1 1 100%}
.typefilter>summary{width:100%}
.book,.fbook{scroll-margin-top:var(--scroll-mt-mobile)}
.controls{padding-top:env(safe-area-inset-top,0px)}
/* phase 4: touch targets >=44px */
.controls button,.controls input[type=search],#cleartypes{min-height:44px}
.typefilter>summary{min-height:44px;display:flex;align-items:center}
.tcheck{min-height:44px}
.actions button{min-height:44px}
.jumpchips a{min-height:44px;display:inline-flex;align-items:center}
.blist-filter{min-height:44px}
.rip-request{min-height:44px;display:inline-flex;align-items:center}
/* phase 4: text density - a little more breathing room on narrow screens */
.card{padding:var(--space-md)}
.fcard{padding:var(--space-md)}
}
@media (prefers-reduced-motion: reduce){*,*::before,*::after{transition:none!important;animation:none!important}}
/* ---------- print: no frame, no red, black on white ---------- */
@media print{
  .controls,.jumpchips,.gindex,#toast,.actions,.savedactions,.collideshelf,.noresults button{display:none!important}
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
  .chip,.bchev,.pv,.tcount,.xall{display:none!important}
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
/* ---------- oxblood on paper (2026-09-29): headline serif, quiet rules, accent only where it earns it ---------- */
.genre,.collidehead,.btitle,.ctitle,.ftitle,.fbsub,.savehead,.print-title{font-family:var(--font-serif)}
.genre,.collidehead{font-weight:600}
.ctitle,.ftitle{border-bottom:1px solid var(--line);font-weight:600}
.btitle{font-weight:600}
.card .steal{font-family:var(--font-serif)}
.chip{background:var(--line-strong)}
.chip.chip-fb{background:transparent;box-shadow:inset 0 0 0 2px var(--ink)}
.gix,.gix:hover{border-top-color:var(--ink-muted)}
.gix .gdot{background:var(--ink-muted)}
.pill.mechanism,.pill.contradiction{font-weight:700}
.pill.question,.pill.prediction{border-style:dashed}
.rotw-card{border:2px solid var(--ink)}
.controls{border-bottom:1px solid var(--line-strong)}
.rip-request:hover{border-color:var(--ink);color:var(--ink);background:var(--surface)}
/* non-accent action buttons stay ink; hover is a neutral paper wash */
.actions button{color:var(--ink-muted);border-color:var(--line-strong)}
.actions button:hover{color:var(--ink);border-color:var(--ink);background:var(--paper)}
/* Copy buttons: oxblood outline */
.actions button[data-copy]{color:var(--accent);border-color:var(--accent)}
.actions button[data-copy]:hover{color:var(--surface);background:var(--accent);border-color:var(--accent)}
/* keep marker: Save / Saved */
.actions button[data-save]{color:var(--accent);border-color:var(--accent)}
.actions button[aria-pressed="true"]{color:var(--surface);background:var(--accent);border-color:var(--accent)}
#savedchip{border-top-color:var(--accent)}
#savedchip .gdot{background:var(--accent)}
.savehead{border-bottom:2px solid var(--accent)}
.tcheck input,.blist-filter{accent-color:var(--ink)}
#toast{border-color:var(--ink)}
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
  /* #toast is rendered after this script: look it up lazily (was null -> Save/Copy threw) */
  toastEl=toastEl||document.getElementById('toast');if(!toastEl)return;
  toastEl.textContent=msg;toastEl.classList.add('show');
  clearTimeout(toastT);toastT=setTimeout(function(){toastEl.classList.remove('show');},ms||1500);
}
function jesc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
var crumbs=document.getElementById('crumbs');
function updateCrumbs(){
  var open=document.querySelectorAll('.book:not(.collapsed):not(.hidden)'),b=open.length?open[open.length-1]:null;
  var h='<a href="#" data-crumb="root">All books</a>';
  if(b){
    var g=b.getAttribute('data-genre'),gh=document.querySelector('h2.genre[data-genre="'+g+'"]');
    h+='<span class="csep"> \u203a </span>'+(gh?'<a href="#'+gh.id+'">'+jesc(g)+'</a>':jesc(g))+'<span class="csep"> \u203a </span><span class="ccur">'+jesc(b.getAttribute('data-book'))+'</span>';
  }
  crumbs.innerHTML=h;
}
crumbs.addEventListener('click',function(e){
  var r=e.target.closest('[data-crumb="root"]');
  if(r){e.preventDefault();window.scrollTo({top:0,behavior:RM?'auto':'smooth'});}
});
function setBook(book,expand){
  book.classList.toggle('collapsed',!expand);
  manual[book.id]=expand;
  var hd=book.querySelector('.bookhead');
  if(hd)hd.setAttribute('aria-expanded',expand?'true':'false');
  updateCrumbs();
}
/* phase 4: on narrow screens books behave as an accordion - opening one
   closes the others, so the page stays a tidy scan list */
var MOBQ=window.matchMedia?matchMedia('(max-width:700px)'):null;
function accordionize(except){
  if(!(MOBQ&&MOBQ.matches))return;
  document.querySelectorAll('.book:not(.collapsed)').forEach(function(b){
    if(b!==except)setBook(b,false);
  });
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
      syncXall(b);
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
  function t(){var b=h.closest('section'),exp=b.classList.contains('collapsed');setBook(b,exp);if(exp)accordionize(b);}
  h.addEventListener('click',t);
});
function syncXall(b){
  var x=b.querySelector('.xall');if(!x)return;
  var cards=b.querySelectorAll('.card:not(.hidden)'),anyClosed=false,i;
  for(i=0;i<cards.length;i++)if(!cards[i].classList.contains('open')){anyClosed=true;break;}
  x.setAttribute('aria-expanded',anyClosed?'false':'true');
  x.textContent=anyClosed?'Expand all':'Collapse all';
}
document.querySelectorAll('.xall').forEach(function(x){
  x.addEventListener('click',function(e){
    e.stopPropagation();
    var b=x.closest('section.book');if(!b)return;
    if(b.classList.contains('collapsed')){setBook(b,true);accordionize(b);}
    var cards=b.querySelectorAll('.card:not(.hidden)'),anyClosed=false,i;
    for(i=0;i<cards.length;i++)if(!cards[i].classList.contains('open')){anyClosed=true;break;}
    for(i=0;i<cards.length;i++){
      cards[i].classList.toggle('open',anyClosed);
      var h=cards[i].querySelector('.cardhead');
      if(h)h.setAttribute('aria-expanded',anyClosed?'true':'false');
    }
    syncXall(b);
  });
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
    if(b){e.preventDefault();if(b.classList.contains('book')){setBook(b,true);accordionize(b);}
      b.scrollIntoView({behavior:RM?'auto':'smooth',block:'start'});
      setHash(ch.getAttribute('href'));}
  });
});
/* phase 2: browse-all-books expander */
(function(){
  var bb=document.getElementById('bookbrowser');if(!bb)return;
  var bf=bb.querySelector('.blist-filter');
  bf.addEventListener('input',function(){
    var t=bf.value.toLowerCase();
    bb.querySelectorAll('.blist-item').forEach(function(a){
      a.classList.toggle('hidden',!!t&&a.textContent.toLowerCase().indexOf(t)<0);
    });
  });
  bb.querySelectorAll('.blist-item').forEach(function(a){
    a.addEventListener('click',function(e){
      e.preventDefault();
      bs.value=a.getAttribute('data-book');apply(true);announceLive();
      var sec=document.getElementById(a.getAttribute('href').slice(1));
      if(sec){setBook(sec,true);accordionize(sec);sec.scrollIntoView({behavior:RM?'auto':'smooth',block:'start'});setHash(a.getAttribute('href'));}
      bb.open=false;bf.value='';bf.dispatchEvent(new Event('input'));
    });
  });
})();
function openHash(){
  var m=/^#c(\d+)$/.exec(location.hash),c;
  if(m&&(c=document.getElementById('c'+m[1]))){
    var b=c.closest('.book');setBook(b,true);accordionize(b);c.classList.add('open');c.classList.add('deeplink');
    var oh=c.querySelector('.cardhead');
    if(oh){oh.setAttribute('aria-expanded','true');try{oh.focus({preventScroll:true});}catch(_){}}
    setTimeout(function(){c.scrollIntoView({behavior:RM?'auto':'smooth',block:'center'});},60);return true;
  }
  m=/^#b-([a-z0-9-]+)$/.exec(location.hash);
  if(m){var bk=document.getElementById('b-'+m[1]);
    if(bk){setBook(bk,true);accordionize(bk);setTimeout(function(){bk.scrollIntoView({behavior:RM?'auto':'smooth',block:'start'});},60);return true;}}
  m=/^#g-([a-z0-9-]+)$/.exec(location.hash);
  if(m){var gn=document.getElementById('g-'+m[1]);
    if(gn){setTimeout(function(){gn.scrollIntoView({behavior:RM?'auto':'smooth',block:'start'});},60);return true;}}
  return false;
}
var _dlTakeover=false;
["touchstart","wheel","keydown"].forEach(function(ev){window.addEventListener(ev,function(){_dlTakeover=true;},{once:true,passive:true});});
function deepLink(){
  var h=location.hash;
  if(!openHash())return;
  var n=0;
  var iv=setInterval(function(){
    if(_dlTakeover||location.hash!==h||++n>3){clearInterval(iv);return;}
    openHash();
  },800);
}
deepLink();
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
updateCrumbs();
/* phase 5: saved rips (localStorage), export, random rip, related/saved link opens */
var SVKEY='idearipper.saved.v1';
function getSaved(){try{var v=JSON.parse(localStorage.getItem(SVKEY)||'[]');if(!Array.isArray(v))return[];var out=[],seen={},i,id;for(i=0;i<v.length;i++){id=+v[i];if(id&&!seen[id]){seen[id]=1;out.push(id);}}return out;}catch(_){return[];}}
function setSaved(a){try{localStorage.setItem(SVKEY,JSON.stringify(a));}catch(_){}}
function mainCard(id){return document.querySelector('.card:not([data-fb])#c'+id);}
function cleanTitle(t){return t.replace(/^\d+\s*/,'').trim();}
function stripPrefix(t,lab){return t.indexOf(lab)===0?t.slice(lab.length).trim():t;}
function bookAuthor(bk){var p=(bk||'').split(' \u2014 ');if(p.length<2)return{b:bk,a:''};var a=p.pop();return{b:p.join(' \u2014 '),a:a};}
function openRip(id){
  var c=mainCard(id);if(!c)return false;
  var b=c.closest('.book');if(b&&b.classList.contains('collapsed')){setBook(b,true);accordionize(b);}
  c.classList.add('open');var h=c.querySelector('.cardhead');if(h)h.setAttribute('aria-expanded','true');
  if(b)syncXall(b);
  setTimeout(function(){c.scrollIntoView({behavior:RM?'auto':'smooth',block:'center'});},60);
  if(c.dataset.n)setHash('#c'+c.dataset.n);
  return true;
}
function renderSaved(){
  var s=getSaved(),list=document.getElementById('savedlist'),note=document.getElementById('savenote'),i,id,c,t,bk;
  if(!list)return;
  list.innerHTML='';
  if(note)note.hidden=s.length>0;
  for(i=0;i<s.length;i++){id=s[i];c=mainCard(id);if(!c)continue;
    t=c.querySelector('.ctitle');bk=c.getAttribute('data-book')||'';
    var d=document.createElement('div');d.className='sitem';
    var a=document.createElement('a');a.href='#c'+id;a.textContent=cleanTitle(t?t.textContent:('Rip #'+id));
    var m=document.createElement('span');m.className='smeta';m.textContent=bk+' \u00b7 '+(c.getAttribute('data-type')||'');
    d.appendChild(a);d.appendChild(m);list.appendChild(d);}
  var ex=document.getElementById('exportSaved');if(ex)ex.disabled=!s.length;
  var sc=document.getElementById('savedcount');if(sc)sc.textContent=s.length;
  var chip=document.getElementById('savedchip');if(chip)chip.textContent='\u2605 Saved ('+s.length+')';
}
function syncSaveButtons(){
  var s=getSaved(),has={},i;for(i=0;i<s.length;i++)has[s[i]]=1;
  document.querySelectorAll('[data-save]').forEach(function(b){
    var on=!!has[+b.getAttribute('data-save')];
    b.setAttribute('aria-pressed',on?'true':'false');
    b.textContent=on?'Saved \u2713':'Save';
  });
}
document.querySelectorAll('[data-save]').forEach(function(b){
  b.addEventListener('click',function(e){
    e.stopPropagation();
    var id=+b.getAttribute('data-save'),s=getSaved(),i=s.indexOf(id);
    /* persist first, then update UI, then toast: a toast problem can never lose a save */
    var was=i>=0;if(was)s.splice(i,1);else s.push(id);
    setSaved(s);syncSaveButtons();renderSaved();
    toast(was?'Removed from saved':'Saved');
  });
});
document.querySelectorAll('.rel a').forEach(function(a){
  a.addEventListener('click',function(e){e.preventDefault();openRip(+a.getAttribute('href').slice(2));});
});
/* "Find it on the shelf" links (featured shelves + collide clones): open the
   canonical shelf card instead of a bare hash jump. Delegated so dynamically
   added collide clones are covered too. */
document.addEventListener('click',function(e){
  var a=e.target&&e.target.closest?e.target.closest('.fcard .fmore a[href^="#c"]'):null;
  if(!a)return;e.preventDefault();openRip(+a.getAttribute('href').slice(2));
});
var _slist=document.getElementById('savedlist');
if(_slist)_slist.addEventListener('click',function(e){
  var a=e.target.closest('a');if(!a)return;e.preventDefault();openRip(+a.getAttribute('href').slice(2));
});
var _ex=document.getElementById('exportSaved');
if(_ex)_ex.addEventListener('click',function(){
  var s=getSaved();if(!s.length)return;
  var out=['# Saved rips \u2014 Idea Ripper',''],i,id,c,t,st,wh,uw,ba;
  for(i=0;i<s.length;i++){id=s[i];c=mainCard(id);if(!c)continue;
    t=c.querySelector('.ctitle');st=c.querySelector('.steal');wh=c.querySelector('.why');uw=c.querySelector('.uw');
    ba=bookAuthor(c.getAttribute('data-book'));
    out.push('## '+cleanTitle(t?t.textContent:('Rip #'+id)));
    out.push('_'+ba.b+(ba.a?' \u2014 '+ba.a:'')+'_ \u00b7 #c'+id);
    out.push('');
    if(st){out.push('**Steal:** '+st.textContent.trim());out.push('');}
    if(wh){out.push('**Why it matters:** '+stripPrefix(wh.textContent.trim(),'Why it matters:'));out.push('');}
    if(uw){out.push('**Use when:** '+stripPrefix(uw.textContent.trim(),'Use when:'));out.push('');}
    out.push('---');out.push('');}
  var blob=new Blob([out.join('\n')],{type:'text/markdown'});
  var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='idea-ripper-saved.md';
  document.body.appendChild(a);a.click();
  setTimeout(function(){URL.revokeObjectURL(a.href);a.remove();},800);
  toast('Exported '+s.length+' saved rips');
});
var _cs=document.getElementById('clearSaved');
if(_cs)_cs.addEventListener('click',function(){setSaved([]);syncSaveButtons();renderSaved();toast('Saved rips cleared');});
var _rr=document.getElementById('randomrip');
if(_rr)_rr.addEventListener('click',function(){
  var pool=[],i,cs=document.querySelectorAll('.card:not([data-fb]):not(.hidden)');
  for(i=0;i<cs.length;i++)pool.push(cs[i]);
  if(!pool.length){toast('No rips visible \u2014 clear search first');return;}
  openRip(+pool[Math.floor(Math.random()*pool.length)].dataset.n);
});
/* collide (phase 1, 2026-09-27): two rips from different worlds, side by
   side. Deliberately no machine-written synthesis: the collision is the
   product, the user's brain writes the synthesis. */
var _cb=document.getElementById('colliderip'),_csec=document.getElementById('collide'),
    _cpair=document.getElementById('collidepair'),_cagain=document.getElementById('collideagain'),
    _lastPair='';
function collideKicker(label){
  var p=document.createElement('p');p.className='fkicker';
  var src=document.querySelector('.fkicker .ripmark');
  if(src)p.appendChild(src.cloneNode(true));
  var s=document.createElement('span');s.className='ktext';s.textContent=label;
  p.appendChild(s);return p;
}
function collideCard(c){
  function tx(sel){var el=c.querySelector(sel);return el?el.textContent.trim():'';}
  var art=document.createElement('article');art.className='fcard';
  art.appendChild(collideKicker('Collision rip'));
  var h=document.createElement('h3');h.className='ftitle';h.textContent=tx('.ctitle');art.appendChild(h);
  var fb=document.createElement('p');fb.className='fbook';
  fb.textContent=(c.getAttribute('data-book')||'')+' \u00b7 ';
  var pill=document.createElement('span');pill.className='pill '+(c.getAttribute('data-type')||'');
  pill.textContent=c.getAttribute('data-type')||'';fb.appendChild(pill);art.appendChild(fb);
  art.appendChild(collideKicker('Ripped from'));
  var st=document.createElement('p');st.className='steal';st.textContent=tx('.steal');art.appendChild(st);
  var wy=document.createElement('p');wy.className='why';
  var k=document.createElement('span');k.className='k';k.textContent='Why it matters:';
  wy.appendChild(k);
  wy.appendChild(document.createTextNode(' '+tx('.why').replace(/^Why it matters:\s*/i,'')));
  art.appendChild(wy);
  art.appendChild(collideKicker('Use when'));
  var u=document.createElement('p');u.className='uw';
  u.textContent=tx('.uw').replace(/^Use when:\s*/i,'');art.appendChild(u);
  var fm=document.createElement('p');fm.className='fmore';
  var a=document.createElement('a');a.href='#c'+c.dataset.n;a.textContent='Find it on the shelf \u2193';
  fm.appendChild(a);art.appendChild(fm);
  return art;
}
function pickTwo(){
  var pool=[],i,cs=document.querySelectorAll('.card:not([data-fb])');
  for(i=0;i<cs.length;i++)pool.push(cs[i]);
  if(pool.length<2)return null;
  var a=null,b=null,tries,cand,key,rkey,att;
  for(att=0;att<3;att++){
    a=pool[(Math.random()*pool.length)|0];b=null;tries=0;
    while(tries<60){
      cand=pool[(Math.random()*pool.length)|0];tries++;
      if(cand===a||cand.getAttribute('data-book')===a.getAttribute('data-book'))continue;
      if(cand.getAttribute('data-genre')!==a.getAttribute('data-genre')||tries>20){b=cand;break;}
    }
    if(!b)continue;
    key=a.dataset.n+'|'+b.dataset.n;rkey=b.dataset.n+'|'+a.dataset.n;
    if(key!==_lastPair&&rkey!==_lastPair){_lastPair=key;return[a,b];}
  }
  return b?[a,b]:null;
}
function doCollide(){
  var pair=pickTwo();
  if(!pair){toast('Not enough rips to collide');return;}
  _cpair.innerHTML='';
  _cpair.appendChild(collideCard(pair[0]));
  _cpair.appendChild(collideCard(pair[1]));
  _csec.hidden=false;
  setTimeout(function(){_csec.scrollIntoView({behavior:RM?'auto':'smooth',block:'start'});},60);
}
if(_cb)_cb.addEventListener('click',doCollide);
if(_cagain)_cagain.addEventListener('click',doCollide);
syncSaveButtons();renderSaved();
})();

"""

# build marker (2026-09-30): tools/site_guard.py checks tpl-<hash> against the
# committed build_site.py, so an index.html built from a cached/stale template fails CI.
import hashlib as _hl
def _h(path):
    try:
        with open(path, "rb") as _f:
            return _hl.sha256(_f.read().replace(b"\r\n", b"\n")).hexdigest()[:12]
    except OSError:
        return "none"
BUILD_MARK = "tpl-%s data-%s" % (_h(os.path.abspath(__file__)), _h(os.path.join(BASE, "cards.json"))[:10])

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
<meta name="color-scheme" content="light"/>
<meta name="build" content="%s"/>
<title>Idea Ripper - the idea-hunting library</title>
<link rel="icon" type="image/svg+xml" href="brand/r-mark.svg"/>
<link rel="icon" type="image/png" sizes="32x32" href="brand/r-mark-32.png"/>
<link rel="apple-touch-icon" href="brand/apple-touch-icon.png"/>
<meta name="description" content="a hunting library of ideas ripped by hand from books worth stealing from. Every rip is one stealable mechanism \u2014 the exact lines worth keeping, plus when to use them."/>
<meta name="theme-color" content="#F5EFE3"/>
<meta property="og:type" content="website"/>
<meta property="og:site_name" content="Idea Ripper"/>
<meta property="og:title" content="Idea Ripper \u2014 the idea-hunting library"/>
<meta property="og:description" content="a hunting library of ideas ripped by hand from books worth stealing from. Every rip is one stealable mechanism \u2014 the exact lines worth keeping, plus when to use them."/>
<meta property="og:url" content="https://idearipper.com/"/>
<meta property="og:image" content="https://idearipper.com/brand/og-card.png"/>
<meta property="og:image:width" content="1200"/>
<meta property="og:image:height" content="630"/>
<meta property="og:image:alt" content="Idea Ripper \u2014 a hunting library of ideas ripped by hand from books worth stealing from."/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:title" content="Idea Ripper \u2014 the idea-hunting library"/>
<meta name="twitter:description" content="a hunting library of ideas ripped by hand from books worth stealing from. Every rip is one stealable mechanism \u2014 the exact lines worth keeping, plus when to use them."/>
<meta name="twitter:image" content="https://idearipper.com/brand/og-card.png"/>
<style>%s</style><noscript><style>.book.collapsed .cards,.fbook.collapsed .fbookbody{display:block!important}.cardbody{display:block!important}</style></noscript>
</head>
<body>

<header class="masthead"><div class="mast-inner">
<h1 class="wordmark"><span class="sr-only">Idea Ripper</span>%s</h1>
<p class="print-title">Idea Ripper \u2014 the idea-hunting library</p>
<p class="mast-sub">the idea-hunting library</p>
<p class="mast-meta">%d rips &middot; %d books &middot; %d theses &middot; curated %s</p>
<a class="rip-request" href="mailto:billysnider@gmail.com?subject=Rip%%20request&body=Book%%20title%%20and%%20author%%3A%%0A%%0AWhy%%20it%%27s%%20worth%%20ripping%%3A">Request a rip</a>
</div></header>
<section id="intro">
<p class="lede"><strong>What this is:</strong> a hunting library of ideas ripped by hand from books worth stealing from. Every rip is one stealable mechanism — the exact lines worth keeping, plus when to use them.</p>
<p class="value"><strong>Why it matters to you:</strong> farmer or professor, you came with a problem. Search it. Every rip is one usable mechanism from a book that solved a version of it, with the exact lines and when to use them.</p>\n<p class="howto"><strong>How to hunt:</strong> start from your problem &mdash; a negotiation, a hire, a stuck project &mdash; and search it. Tap a book to open its rips, tap a card for the full steal, copy anything you want.</p>
%s
</section>
<div class="controls"><div class="inner">
<input type="search" id="q" placeholder="Search titles, steals, use-when&hellip;" aria-label="Search cards"/>
<select id="fgenre" aria-label="Filter by genre"><option value="">All genres</option>
%s</select>
<select id="fbook" hidden aria-hidden="true" tabindex="-1" aria-label="Filter by book"><option value="">All books</option>
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
<button type="button" id="randomrip">Random rip</button>
<button type="button" id="colliderip">Collide</button>
<span class="count" id="count"></span><span id="countlive" class="sr-only" aria-live="polite"></span>
</div></div>
<nav class="jumpchips" id="jumpchips" aria-label="Jump to a genre or book"><span class="gindex">%s</span><span class="scents">%s</span></nav>
<details class="bookbrowser" id="bookbrowser"><summary>Browse all books <span class="btotal">%d</span></summary>
<input type="search" class="blist-filter" placeholder="Filter the book list&hellip;" aria-label="Filter the book list"/>
<div class="blist">
%s
</div></details>
<section class="savedshelf" id="saved" aria-label="Saved rips">
<h2 class="savehead">Saved rips <span class="gcount"><span id="savedcount">0</span> saved</span></h2>
<p class="savenote" id="savenote">Nothing saved yet \u2014 tap <b>Save</b> on any rip and it will wait for you here.</p>
<div class="savedlist" id="savedlist"></div>
<div class="savedactions"><button type="button" id="exportSaved">Export saved</button><button type="button" id="clearSaved">Clear saved</button></div>
</section>
<nav class="crumbs" id="crumbs" aria-label="Breadcrumb"><a href="#" data-crumb="root">All books</a></nav>
<main>
%s
<p class="noresults" id="noresults" hidden>No rips match — try a mechanism word (interlock, delay, patronage).</p>
</main>
<footer><p class="fmeta">Last curated %s &middot; %d books &middot; %d theses &middot; %d rips%s &middot; ripped with the Idea Ripper pipeline</p></footer>
<script>%s</script>
<div id="toast" role="status"></div>
<script>try{if(!sessionStorage.getItem("ir_c")){sessionStorage.setItem("ir_c","1");fetch("https://countapi.mileshilliard.com/api/v1/hit/idearipper-com",{mode:"no-cors",keepalive:true}).catch(function(){})}}catch(e){}</script>
</body>
</html>""" % (BUILD_MARK, CSS, WORDMARK_SVG, n, n_books, n_theses, curated, fb_intro, genre_opts, book_opts, type_checks, gindex, chips, n_btotal, blist,
              "\n\n".join(sections), curated_long, n_books, n_theses, n, fb_footer, JS)

open(os.path.join(BASE, "index.html"), "w", encoding="utf-8").write(page)

# sitemap.xml — real URLs only (Google ignores #fragments); aids Search Console discovery
from datetime import date as _date
_today = _date.today().isoformat()
_sm_urls = [("https://idearipper.com/", "daily", "1.0"), ("https://idearipper.com/brand/", "monthly", "0.5")]
_sm_lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for _loc, _freq, _pri in _sm_urls:
    _sm_lines.append("  <url>")
    _sm_lines.append("    <loc>%s</loc>" % _loc)
    _sm_lines.append("    <lastmod>%s</lastmod>" % _today)
    _sm_lines.append("    <changefreq>%s</changefreq>" % _freq)
    _sm_lines.append("    <priority>%s</priority>" % _pri)
    _sm_lines.append("  </url>")
_sm_lines.append("</urlset>")
open(os.path.join(BASE, "sitemap.xml"), "w", encoding="utf-8").write(chr(10).join(_sm_lines) + chr(10))
# robots.txt — allow all, point crawlers at the sitemap
open(os.path.join(BASE, "robots.txt"), "w", encoding="utf-8").write(
    "User-agent: *" + chr(10) + "Allow: /" + chr(10) + chr(10) +
    "Sitemap: https://idearipper.com/sitemap.xml" + chr(10))
print("sitemap: %d urls -> sitemap.xml + robots.txt" % len(_sm_urls))
print("built: %d cards, %d books, %d theses, %d genres" % (n, n_books, n_theses, len(genre_order)))
