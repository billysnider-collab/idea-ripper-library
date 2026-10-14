#!/usr/bin/env python3
"""Phase 1 redesign builder for idearipper.com (2026-10-14).

Runs AFTER the legacy gate (compile -> verify_ids -> build_site ->
build_index). Gate order wired by rip/safe-deploy:
  compile -> verify_ids -> build_pages --ensure-slugs -> verify_slugs
  -> build_pages -> site_guard -> deploy

Emits, into the lib root (the served root):
  index.html                  new paper homepage (command bar, latest, shelves)
  c/<id>-<slug>/index.html    one canonical page per card (slug from the lock)
  c/<id>/index.html           redirect stub (meta refresh + canonical + noindex)
  ledger/index.html           dense all-cards index, per-genre anchors
  search-index.json           merged index: new short keys {i,s,l,u,b} per rip
                              PLUS the legacy Next-app fields, so the existing
                              /books/, /search/, /collections/ pages keep working
  sitemap.xml                 sitemap index
  sitemap-cards.xml           canonical card URLs only (never stubs)
  sitemap-books.xml           /, /ledger/, and the existing /books/<key>/ pages
  assets/paper.<hash>.css     the Archive Paper stylesheet
  404.html, 404/index.html    one-time #cN hash-redirect injection (idempotent)

Field mapping (cards.json schema: steal/why/uw/title/type/book):
  The Line = steal; Use When = uw; Why It Matters = why; Title = title.
  Book string is "Title — Author" (em dash); author may be absent.
VERBATIM/SYNTHESIS pill: type == "passage" -> VERBATIM EXCERPT, else SYNTHESIS
(the steal of a passage-type card is the book's own text; every other type is
the ripper's distillation). Situation labels render only on cards whose data
carries a `situations` list (plain chips; situation pages are Phase 2).
"""
import argparse
import datetime as _dt
import hashlib
import html
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import slugs as slugs_lib  # noqa: E402
import compile as compiler  # noqa: E402

SITE = "https://idearipper.com"


def esc(s):
    return html.escape(str(s), quote=False)


def esca(s):
    return html.escape(str(s), quote=True)


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-") or "x"


def trunc(s, n):
    s = " ".join(str(s).split())
    if len(s) <= n:
        return s
    return s[:n].rsplit(" ", 1)[0] + "\u2026"


def split_book(book):
    if " \u2014 " in book:
        t, a = book.rsplit(" \u2014 ", 1)
        return t, a
    return book, ""


def book_key_map():
    """book string -> shelf key, from the source files (authoritative)."""
    shelf = compiler.load_shelf()
    out = {}
    for e in shelf["books"]:
        path = os.path.join(BASE, "books", e["key"] + ".md")
        if not os.path.exists(path):
            continue
        book_fm, _ = compiler.parse_book_file(path)
        out[book_fm["book"]] = e["key"]
    return out


PAPER_CSS = """
/* Idea Ripper — Archive Paper (redesign Phase 1, 2026-10-14).
   Argon spec tokens; zero border-radius; hard offset shadows; light only. */
:root{
  color-scheme:light;
  --bg-canvas:#F4F1EA;
  --bg-card:#FAF8F5;
  --bg-subtle:#E8E4DA;
  --text-primary:#141413;
  --text-secondary:#57554E;
  --border-strong:#141413;
  --border-subtle:#D0C9BC;
  --accent-signal:#C83E2B;
  --font-serif:"Newsreader","Source Serif 4","Iowan Old Style",Georgia,"Times New Roman",serif;
  --font-sans:"Inter",system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  --font-mono:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;
}
*{box-sizing:border-box;border-radius:0!important}
html{font-size:100%}
body{margin:0;background:var(--bg-canvas);color:var(--text-primary);font-family:var(--font-sans);font-size:1rem;line-height:1.6}
a{color:var(--accent-signal)}
a:hover{color:var(--text-primary)}
:focus-visible{outline:2px solid var(--accent-signal);outline-offset:2px}
.wrap{max-width:68rem;margin:0 auto;padding:0 1.25rem 3rem}
.wrap-narrow{max-width:55rem;margin:0 auto;padding:0 1.25rem 3rem}
/* status bar */
.statusbar{display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;background:var(--text-primary);color:var(--bg-canvas);font-family:var(--font-mono);font-size:.72rem;letter-spacing:.12em;padding:.45rem 1.25rem;text-transform:uppercase}
.statusbar .live{color:#F0B429}
/* brand + mission */
.brandrow{padding:1.5rem 0 0}
.wordmark{max-width:330px}
.wordmark svg{display:block;width:100%;height:auto}
h1.mission{font-family:var(--font-serif);font-weight:600;font-size:2rem;line-height:1.25;margin:1rem 0 .25rem}
.sub{color:var(--text-secondary);font-size:1.05rem;margin:.25rem 0 1.5rem;max-width:44rem}
/* command bar */
.cmdbar{border:1.5px solid var(--border-strong);background:var(--bg-card);box-shadow:5px 5px 0 var(--border-strong);padding:1rem;margin:0 0 1rem}
.cmdbar label{display:block;font-family:var(--font-mono);font-size:.72rem;font-weight:700;letter-spacing:.18em;text-transform:uppercase;margin-bottom:.5rem}
.cmdrow{display:flex;gap:.5rem}
.cmdrow input{flex:1;min-width:0;font-family:var(--font-mono);font-size:1rem;padding:.7rem .8rem;border:1.5px solid var(--border-strong);background:var(--bg-subtle);color:var(--text-primary)}
.btn{font-family:var(--font-mono);font-size:.85rem;font-weight:700;letter-spacing:.06em;background:var(--text-primary);color:var(--bg-canvas);border:1.5px solid var(--border-strong);padding:.7rem 1rem;cursor:pointer;text-decoration:none;display:inline-block}
.btn:hover{background:var(--accent-signal);color:#fff}
.btn.ghost{background:var(--bg-card);color:var(--text-primary)}
.btn.ghost:hover{background:var(--bg-subtle);color:var(--text-primary)}
.cb-results{margin-top:.5rem}
.cb-hit{display:flex;gap:.6rem;align-items:baseline;padding:.5rem .6rem;border:1px solid var(--border-subtle);background:var(--bg-canvas);text-decoration:none;color:var(--text-primary);margin-top:.4rem}
.cb-hit:hover{border-color:var(--border-strong)}
.cb-id{font-family:var(--font-mono);font-size:.75rem;font-weight:700;color:var(--accent-signal);flex:none}
.cb-line{flex:1;min-width:0}
.cb-book{font-family:var(--font-mono);font-size:.72rem;color:var(--text-secondary);flex:none;max-width:38%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cb-note{font-family:var(--font-mono);font-size:.78rem;color:var(--text-secondary);padding:.4rem 0 0}
.headrow{display:flex;gap:.5rem;flex-wrap:wrap;margin:0 0 2rem}
/* sections */
h2.sect{font-family:var(--font-mono);font-size:.85rem;font-weight:700;letter-spacing:.18em;text-transform:uppercase;border-bottom:2px solid var(--border-strong);padding-bottom:.35rem;margin:2.2rem 0 1rem}
h2.sect .cnt{color:var(--text-secondary);letter-spacing:.05em}
.pills{display:flex;flex-wrap:wrap;gap:.45rem}
.pill-link{font-family:var(--font-mono);font-size:.8rem;border:1px solid var(--border-strong);background:var(--bg-card);color:var(--text-primary);text-decoration:none;padding:.45rem .7rem;box-shadow:3px 3px 0 var(--border-subtle)}
.pill-link:hover{background:var(--bg-subtle);color:var(--text-primary)}
.pill-link .n{color:var(--accent-signal);font-weight:700}
/* preview + dossier cards */
.prevcard,.dossier{background:var(--bg-card);border:1.5px solid var(--border-strong);box-shadow:4px 4px 0 var(--border-strong);padding:1.1rem 1.25rem;margin:0 0 1.25rem;position:relative}
.pc-top{display:flex;justify-content:space-between;gap:.75rem;align-items:center;border-bottom:1px solid var(--border-subtle);padding-bottom:.55rem;margin-bottom:.8rem;flex-wrap:wrap}
.badge{font-family:var(--font-mono);font-weight:700;font-size:.8rem;letter-spacing:.1em}
.stamp{font-family:var(--font-mono);font-size:.68rem;color:var(--text-secondary);letter-spacing:.14em}
.vpill{margin-left:auto}
.vpill{font-family:var(--font-mono);font-size:.68rem;font-weight:700;letter-spacing:.12em;border:1px solid var(--border-strong);padding:.18rem .5rem;text-transform:uppercase}
.vpill.verbatim{background:var(--text-primary);color:var(--bg-canvas)}
blockquote.theline{font-family:var(--font-serif);font-size:1.55rem;line-height:1.4;margin:.4rem 0 .8rem;quotes:"\u201c" "\u201d"}
.dossier blockquote.theline{font-size:1.8rem}
.attr{font-family:var(--font-mono);font-size:.82rem;color:var(--text-secondary);margin:.4rem 0 .9rem}
.attr a{color:var(--text-primary)}
.meta-block{border-top:1px dashed var(--border-subtle);padding-top:.8rem;margin-top:.4rem}
.uwk{font-family:var(--font-mono);font-size:.75rem;font-weight:700;letter-spacing:.14em;color:var(--accent-signal);text-transform:uppercase}
.uw{font-size:1.02rem;margin:.25rem 0 .9rem}
.whyk{font-family:var(--font-mono);font-size:.75rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase}
.why{margin:.25rem 0 .4rem}
.sits{margin-top:.9rem;display:flex;gap:.4rem;flex-wrap:wrap;align-items:center}
.sits .slab{font-family:var(--font-mono);font-size:.7rem;font-weight:700;letter-spacing:.14em;color:var(--text-secondary);text-transform:uppercase}
.sitchip{font-family:var(--font-mono);font-size:.72rem;border:1px solid var(--border-subtle);background:var(--bg-subtle);padding:.2rem .55rem}
.openfile{font-family:var(--font-mono);font-size:.8rem;font-weight:700;text-decoration:none}
/* breadcrumb */
.crumb{font-family:var(--font-mono);font-size:.75rem;color:var(--text-secondary);letter-spacing:.08em;padding:1.1rem 0 .9rem;text-transform:uppercase}
.crumb a{color:var(--text-secondary)}
/* share + nav rows */
.sharerow{display:flex;gap:.5rem;flex-wrap:wrap;margin:0 0 1.5rem}
.sharerow .btn{flex:1;text-align:center;min-width:10rem}
.navrow{display:flex;gap:.5rem;justify-content:space-between;margin:0 0 2rem}
.navrow .btn{min-width:9rem;text-align:center}
.navrow .spacer{flex:1}
/* related */
.relgrid{display:grid;gap:.8rem}
@media(min-width:760px){.relgrid{grid-template-columns:1fr 1fr}}
.relcard{border:1px solid var(--border-strong);background:var(--bg-card);padding:.8rem .95rem;text-decoration:none;color:var(--text-primary);display:block;box-shadow:3px 3px 0 var(--border-subtle)}
.relcard:hover{background:var(--bg-subtle);color:var(--text-primary)}
.relcard .rid{font-family:var(--font-mono);font-size:.72rem;font-weight:700;color:var(--accent-signal)}
.relcard .rline{font-family:var(--font-serif);font-size:1.05rem;line-height:1.35;display:block;margin:.25rem 0}
.relcard .ruw{font-size:.85rem;color:var(--text-secondary);display:block}
/* shelves grid */
.shelfgrid{display:grid;gap:.8rem;grid-template-columns:1fr}
@media(min-width:640px){.shelfgrid{grid-template-columns:1fr 1fr}}
@media(min-width:1000px){.shelfgrid{grid-template-columns:1fr 1fr 1fr}}
.shelfbox{border:1.5px solid var(--border-strong);background:var(--bg-card);padding:.9rem 1rem;text-decoration:none;color:var(--text-primary);box-shadow:4px 4px 0 var(--border-subtle);display:block}
.shelfbox:hover{background:var(--bg-subtle);color:var(--text-primary)}
.shelfbox .sname{font-weight:700;font-size:1.02rem;display:block}
.shelfbox .scounts{font-family:var(--font-mono);font-size:.75rem;color:var(--text-secondary);letter-spacing:.08em;text-transform:uppercase}
/* ledger */
.ledwrap{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1.5px solid var(--border-strong);margin:0 0 1.5rem}
table.ledger{width:100%;min-width:620px;border-collapse:collapse;font-size:.85rem;background:var(--bg-card)}
table.ledger th{font-family:var(--font-mono);font-size:.7rem;letter-spacing:.14em;text-align:left;text-transform:uppercase;border-bottom:1.5px solid var(--border-strong);padding:.5rem .6rem}
table.ledger td{border-bottom:1px solid var(--border-subtle);padding:.42rem .6rem;vertical-align:top}
table.ledger td.lid{font-family:var(--font-mono);font-weight:700;white-space:nowrap}
table.ledger td.lid a{color:var(--accent-signal);text-decoration:none}
table.ledger td.lbook{color:var(--text-secondary);font-size:.8rem}
table.ledger td.lshelf{font-family:var(--font-mono);font-size:.72rem;color:var(--text-secondary);white-space:nowrap;text-transform:uppercase;letter-spacing:.06em}
/* footer */
footer.sitefoot{border-top:2px solid var(--border-strong);margin-top:2.5rem;padding:1.2rem 0 0;font-family:var(--font-mono);font-size:.78rem;color:var(--text-secondary)}
footer.sitefoot a{color:var(--text-primary)}
@media(max-width:560px){
  blockquote.theline{font-size:1.3rem}
  .dossier blockquote.theline{font-size:1.45rem}
  .prevcard,.dossier{box-shadow:3px 3px 0 var(--border-strong)}
  h1.mission{font-size:1.55rem}
  .cb-book{display:none}
}
@media print{.statusbar,.cmdbar,.headrow,.sharerow,.navrow{display:none!important}body{background:#fff}}
"""

HASH_SCRIPT = ("<script>/* ir-hash-redirect: legacy #cN links land on the card page */"
               "(function(){var m=/^#c(\\d+)$/.exec(location.hash);"
               "if(m)location.replace('/c/'+m[1]+'/');})();</script>")


def build_marker():
    h = hashlib.sha256(open(os.path.abspath(__file__), "rb").read()
                       .replace(b"\r\n", b"\n")).hexdigest()[:12]
    d = hashlib.sha256(open(os.path.join(BASE, "cards.json"), "rb").read()
                       .replace(b"\r\n", b"\n")).hexdigest()[:10]
    return "pages-%s data-%s" % (h, d)


def write_asset(text):
    data = text.encode("utf-8")
    name = "paper.%s.css" % hashlib.sha256(data).hexdigest()[:10]
    d = os.path.join(BASE, "assets")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name), "wb") as f:
        f.write(data)
    return "assets/" + name


def head(title, desc, canonical, marker, css_href, extra=""):
    return ("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\"/>\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"/>\n"
            "<meta name=\"color-scheme\" content=\"light\"/>\n"
            "<meta name=\"build\" content=\"%s\"/>\n"
            "<title>%s</title>\n"
            "<meta name=\"description\" content=\"%s\"/>\n"
            "<link rel=\"canonical\" href=\"%s\"/>\n"
            "<meta property=\"og:type\" content=\"article\"/>\n"
            "<meta property=\"og:site_name\" content=\"Idea Ripper\"/>\n"
            "<meta property=\"og:title\" content=\"%s\"/>\n"
            "<meta property=\"og:description\" content=\"%s\"/>\n"
            "<meta property=\"og:url\" content=\"%s\"/>\n"
            "<link rel=\"icon\" type=\"image/svg+xml\" href=\"/brand/r-mark.svg\"/>\n"
            "<link rel=\"stylesheet\" href=\"/%s\"/>\n%s\n</head>\n"
            % (marker, esca(title), esca(desc), esca(canonical),
               esca(title), esca(desc), esca(canonical), css_href, extra))


def statusbar(n, build_date):
    return ('<div class="statusbar"><span>Idea Ripper // Archive</span>'
            '<span>Cards: %d <span class="live">[Live]</span> | Updated: %s</span></div>'
            % (n, build_date))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ensure-slugs", action="store_true",
                    help="only append missing slugs to slugs.lock.json, then exit")
    args = ap.parse_args()

    ds = json.load(open(os.path.join(BASE, "cards.json"), encoding="utf-8"))
    cards = ds["cards"]
    books = ds["books"]
    genre_order = ds["genre_order"]
    by_id = {c["id"]: c for c in cards}
    genre_of = {b["book"]: b["genre"] for b in books}
    key_of = book_key_map()

    lock, added = slugs_lib.ensure_slugs(cards)
    if added:
        print("slugs: appended %d new lock entries" % len(added))
    if args.ensure_slugs:
        return
    fails = slugs_lib.verify(cards)
    if fails:
        for f in fails[:20]:
            print("FAIL: " + f)
        sys.exit(1)
    slug_of = {int(i): s for i, s in lock["slugs"].items()}

    ids_sorted = sorted(by_id)
    prev_of, next_of = {}, {}
    for i, cid in enumerate(ids_sorted):
        if i > 0:
            prev_of[cid] = ids_sorted[i - 1]
        if i < len(ids_sorted) - 1:
            next_of[cid] = ids_sorted[i + 1]

    def canon(cid):
        return "/c/%d-%s/" % (cid, slug_of[cid])

    def book_url(book):
        key = key_of.get(book)
        if key and os.path.exists(os.path.join(BASE, "books", key, "index.html")):
            return "/books/%s/" % key
        anchor = key or slugify(book)
        return "/ledger/#book-%s" % anchor

    def pill(card):
        return "verbatim" if card["type"] == "passage" else "synthesis"

    def pill_label(card):
        return "Verbatim excerpt" if card["type"] == "passage" else "Synthesis"

    marker = build_marker()
    css_href = write_asset(PAPER_CSS)
    build_date = _dt.date.today().isoformat()
    n = len(cards)

    wm_path = os.path.join(BASE, "brand", "wordmark-inline.svg")
    wordmark = ""
    if os.path.exists(wm_path):
        wm = open(wm_path, encoding="utf-8").read()
        wm = wm.replace('role="img" aria-label="Idea Ripper"', 'aria-hidden="true"')
        wordmark = '<div class="wordmark" aria-hidden="true">%s</div>' % wm

    # ---------------- card pages + stubs ----------------
    for cid in ids_sorted:
        c = by_id[cid]
        bt, ba = split_book(c["book"])
        genre = genre_of[c["book"]]
        line = c["steal"]
        words = " ".join(line.split()[:8])
        title = '"%s\u2026" \u2014 %s (#c%d) | Idea Ripper' % (words, ba or bt, cid)
        desc = trunc('"%s" \u2014 From %s by %s. Use when: %s. Why it matters: %s.'
                     % (line, bt, ba, c["uw"], c["why"]), 300)
        url = SITE + canon(cid)
        ld = {
            "@context": "https://schema.org",
            "@type": "Quotation",
            "text": line,
            "isPartOf": {"@type": "Book", "name": bt,
                         "author": {"@type": "Person", "name": ba} if ba else bt},
            "mainEntity": {"@type": "DefinedTerm", "name": trunc(c["title"], 120),
                           "description": c["uw"]},
        }
        ld_json = json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")
        og_img = ""
        key = key_of.get(c["book"])
        if key and os.path.exists(os.path.join(BASE, "og", "og-%s.png" % key)):
            og_img = '<meta property="og:image" content="%s/og/og-%s.png"/>\n' % (SITE, key)
        page = [head(title, desc, url, marker, css_href,
                     '<script type="application/ld+json">%s</script>' % ld_json
                     + ("\n" + og_img if og_img else ""))]
        page.append("<body>")
        page.append(statusbar(n, build_date))
        page.append('<div class="wrap-narrow">')
        page.append('<nav class="crumb"><a href="/">Archive</a> / Shelf: '
                    '<a href="/ledger/#genre-%s">%s</a> / File #c%d</nav>'
                    % (slugify(genre), esc(genre), cid))
        prev_btn = ('<a class="btn ghost" href="%s">&lt;- Prev #c%d</a>' % (canon(prev_of[cid]), prev_of[cid])) if cid in prev_of else '<span></span>'
        next_btn = ('<a class="btn ghost" href="%s">Next #c%d -&gt;</a>' % (canon(next_of[cid]), next_of[cid])) if cid in next_of else '<span></span>'
        sits = ""
        if c.get("situations"):
            chips = "".join('<span class="sitchip">%s</span>' % esc(s) for s in c["situations"])
            sits = ('<div class="sits"><span class="slab">Filed under situations:</span>%s</div>' % chips)
        page.append(
            '<article class="dossier">'
            '<div class="pc-top"><span class="badge">Card #c%d</span>'
            '<span class="stamp">IR // #c%d</span>'
            '<span class="vpill %s">%s</span></div>'
            '<blockquote class="theline">%s</blockquote>'
            '<p class="attr">\u2014 Source: <a href="%s">%s</a>%s</p>'
            '<div class="meta-block">'
            '<span class="uwk">[Use when]</span><p class="uw">%s</p>'
            '<span class="whyk">[Why it matters]</span><p class="why">%s</p>'
            '%s</div></article>'
            % (cid, cid, pill(c), esc(pill_label(c)), esc(line),
               esca(book_url(c["book"])), esc(bt),
               (" (%s)" % esc(ba)) if ba else "", esc(c["uw"]), esc(c["why"]), sits))
        page.append(
            '<div class="sharerow">'
            '<button type="button" class="btn" id="copyx">Copy for X / Citation</button>'
            '<button type="button" class="btn ghost" id="copyid">Copy ID</button>'
            '<button type="button" class="btn ghost" id="share">Share card</button></div>')
        page.append('<nav class="navrow">%s<span class="spacer"></span>%s</nav>'
                    % (prev_btn, next_btn))
        rel = [r for r in (c.get("related_ids") or []) if r in by_id][:4]
        if rel:
            page.append('<h2 class="sect">Related principles</h2><div class="relgrid">')
            for r in rel:
                rc = by_id[r]
                page.append('<a class="relcard" href="%s"><span class="rid">#c%d</span>'
                            '<span class="rline">%s</span><span class="ruw">%s</span></a>'
                            % (canon(r), r, esc(trunc(rc["steal"], 140)), esc(trunc(rc["uw"], 110))))
            page.append('</div>')
        sibs = [o for o in cards if o["book"] == c["book"] and o["id"] != cid]
        sibs.sort(key=lambda o: o["id"])
        if sibs:
            page.append('<h2 class="sect">More from %s</h2><div class="relgrid">' % esc(bt))
            for rc in sibs[:3]:
                page.append('<a class="relcard" href="%s"><span class="rid">#c%d</span>'
                            '<span class="rline">%s</span><span class="ruw">%s</span></a>'
                            % (canon(rc["id"]), rc["id"], esc(trunc(rc["steal"], 140)),
                               esc(trunc(rc["uw"], 110))))
            page.append('</div>')
        page.append('<footer class="sitefoot"><a href="/">Idea Ripper archive</a> \u00b7 '
                    '<a href="/ledger/">Full ledger</a> \u00b7 Card #c%d of %d \u00b7 '
                    'Machine-assisted, hand-curated</footer>' % (cid, n))
        page.append('</div>')
        copy_text = '"%s"\n\u2014 %s, %s\nidearipper.com/c/%d' % (
            " ".join(line.split()), ba, bt, cid)
        page.append(
            '<script>(function(){'
            'var CT=%s,URL=%s,PREV=%s,NEXT=%s;'
            'function cp(t,b){function done(){var o=b.textContent;b.textContent="Copied";'
            'setTimeout(function(){b.textContent=o;},1400);}'
            'if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(done,function(){fb();});}'
            'else{fb();}function fb(){var ta=document.createElement("textarea");ta.value=t;'
            'document.body.appendChild(ta);ta.select();try{document.execCommand("copy");done();}catch(e){}'
            'document.body.removeChild(ta);}}'
            'var bx=document.getElementById("copyx");if(bx)bx.addEventListener("click",function(){cp(CT,bx);});'
            'var bi=document.getElementById("copyid");if(bi)bi.addEventListener("click",function(){cp("idearipper.com/c/"+%d,bi);});'
            'var bs=document.getElementById("share");if(bs)bs.addEventListener("click",function(){'
            'if(navigator.share){navigator.share({title:document.title,url:URL}).catch(function(){});}'
            'else{cp(URL,bs);}});'
            'document.addEventListener("keydown",function(e){'
            'if(e.target&&(e.target.tagName==="INPUT"||e.target.tagName==="TEXTAREA"))return;'
            'if(e.key==="ArrowLeft"&&PREV)location.href=PREV;'
            'if(e.key==="ArrowRight"&&NEXT)location.href=NEXT;});'
            '})();</script>'
            % (json.dumps(copy_text, ensure_ascii=False),
               json.dumps(url, ensure_ascii=False),
               json.dumps(canon(prev_of[cid])) if cid in prev_of else "null",
               json.dumps(canon(next_of[cid])) if cid in next_of else "null",
               cid))
        page.append("</body></html>")
        d = os.path.join(BASE, "c", "%d-%s" % (cid, slug_of[cid]))
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(page))
        sd = os.path.join(BASE, "c", str(cid))
        os.makedirs(sd, exist_ok=True)
        stub = ("<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"utf-8\"/>"
                "<meta name=\"robots\" content=\"noindex\"/>"
                "<link rel=\"canonical\" href=\"%s\"/>"
                "<meta http-equiv=\"refresh\" content=\"0; url=%s\"/>"
                "<title>Card #c%d \u2014 Idea Ripper</title></head>"
                "<body><p><a href=\"%s\">Card #c%d</a></p>"
                "<script>location.replace(%s);</script></body></html>"
                % (url, canon(cid), cid, canon(cid), cid, json.dumps(canon(cid))))
        with open(os.path.join(sd, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(stub)

    # ---------------- homepage ----------------
    latest = [by_id[i] for i in ids_sorted[-6:]][::-1]
    prev_html = []
    for c in latest:
        bt, ba = split_book(c["book"])
        prev_html.append(
            '<article class="prevcard"><div class="pc-top"><span class="badge">Card #c%d</span>'
            '<span class="vpill %s">%s</span></div>'
            '<blockquote class="theline">%s</blockquote>'
            '<p class="attr">\u2014 Source: <a href="%s">%s</a>%s</p>'
            '<span class="uwk">[Use when]</span><p class="uw">%s</p>'
            '<a class="openfile" href="%s">[Open file #c%d -&gt;]</a></article>'
            % (c["id"], pill(c), esc(pill_label(c)), esc(c["steal"]),
               esca(book_url(c["book"])), esc(bt), (" (%s)" % esc(ba)) if ba else "",
               esc(c["uw"]), canon(c["id"]), c["id"]))
    pills = []
    for g in genre_order:
        gc = sum(1 for c in cards if genre_of[c["book"]] == g)
        if gc:
            pills.append('<a class="pill-link" href="/ledger/#genre-%s">%s <span class="n">%d</span></a>'
                         % (slugify(g), esc(g), gc))
    shelf_boxes = []
    for g in genre_order:
        gb = [b for b in books if b["genre"] == g]
        gc = sum(1 for c in cards if genre_of[c["book"]] == g)
        if not gc:
            continue
        unit = "theses" if g == "Thesis" else "books"
        shelf_boxes.append(
            '<a class="shelfbox" href="/ledger/#genre-%s"><span class="sname">%s</span>'
            '<span class="scounts">%d cards \u00b7 %d %s</span></a>'
            % (slugify(g), esc(g), gc, len(gb), unit))
    home_desc = ("One idea from a book. The line, and when to use it. "
                 "%d battle-tested mental models, tactical quotes, and strategic "
                 "principles extracted from books." % n)
    home = [head("Idea Ripper \u2014 One idea from a book. The line, and when to use it.",
                 home_desc, SITE + "/", marker, css_href,
                 '<script type="application/ld+json">{"@context":"https://schema.org",'
                 '"@type":"WebSite","name":"Idea Ripper","url":"https://idearipper.com/"}</script>\n'
                 + HASH_SCRIPT)]
    home.append("<body>")
    home.append(statusbar(n, build_date))
    home.append('<div class="wrap">')
    home.append('<div class="brandrow">%s</div>' % wordmark)
    home.append('<h1 class="mission">One idea from a book. The line, and when to use it.</h1>')
    home.append('<p class="sub">%d battle-tested mental models, tactical quotes, and '
                'strategic principles extracted from books.</p>' % n)
    home.append(
        '<form class="cmdbar" id="commandbar" action="#" method="get">'
        '<label for="cb-input">Direct access // Enter card # or keyword</label>'
        '<div class="cmdrow"><input id="cb-input" type="text" autocomplete="off" '
        'placeholder="Type #402, \u201cnegotiation\u201d, \u201cGreene\u201d\u2026"/>'
        '<button class="btn" type="submit">[Go -&gt;]</button></div>'
        '<div class="cb-results" id="cb-results" hidden></div></form>')
    home.append('<div class="headrow"><button type="button" class="btn ghost randomcard">'
                '[Random card \u21bb]</button>'
                '<a class="btn ghost" href="/ledger/">[Full ledger]</a></div>')
    home.append('<h2 class="sect">Field-tested by situation:</h2><div class="pills">%s</div>'
                % "".join(pills))
    home.append('<h2 class="sect">Latest dispatches <span class="cnt">// last 6 additions</span></h2>')
    home.extend(prev_html)
    home.append('<h2 class="sect">Browse by shelf</h2><div class="shelfgrid">%s</div>'
                % "".join(shelf_boxes))
    home.append('<footer class="sitefoot"><a href="/ledger/">Full ledger</a> \u00b7 '
                '<a href="https://x.com/IdeaRipper">@IdeaRipper on X</a> \u00b7 '
                '%d cards \u00b7 Machine-assisted, hand-curated with the Idea Ripper pipeline</footer>' % n)
    home.append('</div>')
    home.append(
        '<script>(function(){'
        'var idx=null,loading=false;'
        'function loadIdx(cb){if(idx){cb&&cb(idx);return;}'
        'if(loading){setTimeout(function(){loadIdx(cb);},300);return;}loading=true;'
        'fetch("/search-index.json").then(function(r){return r.json();}).then(function(d){'
        'idx=d.filter(function(e){return e&&typeof e.i==="number";});loading=false;cb&&cb(idx);}'
        ').catch(function(){loading=false;});}'
        'function boot(){loadIdx();}'
        'if(window.requestIdleCallback){requestIdleCallback(boot,{timeout:2000});}'
        'else{window.addEventListener("load",function(){setTimeout(boot,1500);});}'
        'var form=document.getElementById("commandbar"),inp=document.getElementById("cb-input"),'
        'res=document.getElementById("cb-results");'
        'function canon(e){return "/c/"+e.i+"-"+e.s+"/";}'
        'function render(list,note){if(!list.length&&!note){res.hidden=true;res.innerHTML="";return;}'
        'res.hidden=false;var h="";list.forEach(function(e){'
        'h+=\'<a class="cb-hit" href="\'+canon(e)+\'"><span class="cb-id">#c\'+e.i+\'</span>\''
        '+\'<span class="cb-line"></span><span class="cb-book"></span></a>\';});'
        'if(note)h+=\'<p class="cb-note">\'+note+\'</p>\';res.innerHTML=h;'
        'var rows=res.querySelectorAll(".cb-hit");list.forEach(function(e,k){'
        'rows[k].querySelector(".cb-line").textContent=e.l;'
        'rows[k].querySelector(".cb-book").textContent=e.b;});}'
        'function search(q){q=q.trim().toLowerCase();if(!idx||q.length<2){render([]);return;}'
        'var ws=q.split(/\\s+/),out=[];'
        'for(var k=0;k<idx.length&&out.length<6;k++){var e=idx[k],'
        't=(e.l+" "+e.u+" "+e.b+" "+(e.title||"")).toLowerCase(),ok=true;'
        'for(var j=0;j<ws.length;j++){if(t.indexOf(ws[j])<0){ok=false;break;}}'
        'if(ok)out.push(e);}'
        'render(out,out.length?"":"No cards match \u201c"+q+"\u201d.");}'
        'inp.addEventListener("input",function(){var v=inp.value.trim();'
        'var m=/^#?c?(\\d+)$/i.exec(v);'
        'if(m&&idx){var id=+m[1],hit=null;for(var k=0;k<idx.length;k++)if(idx[k].i===id){hit=idx[k];break;}'
        'render(hit?[hit]:[],hit?"":"No card #c"+id+" in the archive.");return;}'
        'if(m){render([],"Loading the index\u2026");loadIdx(function(){inp.dispatchEvent(new Event("input"));});return;}'
        'if(!idx){render([],"Loading the index\u2026");loadIdx(function(){inp.dispatchEvent(new Event("input"));});return;}'
        'search(v);});'
        'form.addEventListener("submit",function(ev){ev.preventDefault();var v=inp.value.trim();'
        'var m=/^#?c?(\\d+)$/i.exec(v);if(m){location.assign("/c/"+m[1]+"/");return;}'
        'var hit=res.querySelector(".cb-hit");if(hit)location.assign(hit.getAttribute("href"));});'
        'inp.addEventListener("keydown",function(e){if(e.key==="Escape"){render([]);inp.value="";}});'
        'document.querySelectorAll(".randomcard").forEach(function(b){'
        'b.addEventListener("click",function(){function go(d){'
        'var e=d[Math.floor(Math.random()*d.length)];location.assign(canon(e));}'
        'if(idx)go(idx);else loadIdx(go);});});'
        '})();</script>')
    home.append("</body></html>")
    with open(os.path.join(BASE, "index.html"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(home))

    # ---------------- ledger ----------------
    led = [head("The Ledger \u2014 every card | Idea Ripper",
                "The full Idea Ripper ledger: all %d cards, by shelf." % n,
                SITE + "/ledger/", marker, css_href)]
    led.append("<body>")
    led.append(statusbar(n, build_date))
    led.append('<div class="wrap">')
    led.append('<nav class="crumb"><a href="/">Archive</a> / Ledger</nav>')
    led.append('<h1 class="mission">The ledger</h1>')
    led.append('<p class="sub">Every card in the archive \u2014 %d \u2014 in shelf order. '
               'Each row opens the full file.</p>' % n)
    books_by_genre = {}
    for b in books:
        books_by_genre.setdefault(b["genre"], []).append(b)
    for g in genre_order:
        gb = books_by_genre.get(g, [])
        gc = [c for b in gb for c in cards if c["book"] == b["book"]]
        if not gc:
            continue
        led.append('<h2 class="sect" id="genre-%s">%s <span class="cnt">// %d cards</span></h2>'
                   % (slugify(g), esc(g), len(gc)))
        led.append('<div class="ledwrap"><table class="ledger"><thead><tr><th>#ID</th><th>The line</th>'
                   '<th>Book</th><th>Shelf</th></tr></thead><tbody>')
        for b in gb:
            bc = sorted([c for c in cards if c["book"] == b["book"]], key=lambda c: c["id"])
            anchor = key_of.get(b["book"]) or slugify(b["book"])
            for j, c in enumerate(bc):
                idattr = ' id="book-%s"' % esca(anchor) if j == 0 else ""
                bt, _ba = split_book(c["book"])
                led.append('<tr%s><td class="lid"><a href="%s">#c%d</a></td>'
                           '<td><a href="%s">%s</a></td><td class="lbook">%s</td>'
                           '<td class="lshelf">%s</td></tr>'
                           % (idattr, canon(c["id"]), c["id"], canon(c["id"]),
                              esc(trunc(c["steal"], 60)), esc(bt), esc(g)))
        led.append('</tbody></table></div>')
    led.append('<footer class="sitefoot"><a href="/">Idea Ripper archive</a> \u00b7 '
               '%d cards \u00b7 Machine-assisted, hand-curated</footer>' % n)
    led.append('</div></body></html>')
    os.makedirs(os.path.join(BASE, "ledger"), exist_ok=True)
    with open(os.path.join(BASE, "ledger", "index.html"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(led))

    # ---------------- search-index.json (merged) ----------------
    legacy_books = []
    for src in (os.path.join(BASE, "search-index.json.pre-redesign-20261014"),
                os.path.join(BASE, "search-index.json")):
        if os.path.exists(src):
            try:
                old = json.load(open(src, encoding="utf-8"))
            except Exception:
                old = []
            legacy_books = [e for e in old if isinstance(e, dict) and e.get("kind") == "book"]
            if legacy_books:
                break
    entries = []
    for cid in ids_sorted:
        c = by_id[cid]
        bt, ba = split_book(c["book"])
        entries.append({
            "i": cid, "s": slug_of[cid],
            "l": trunc(c["steal"], 200), "u": trunc(c["uw"], 160), "b": bt,
            "kind": "rip", "id": cid, "title": c["title"], "steal": c["steal"],
            "why": c["why"], "uw": c["uw"], "type": c["type"], "book": bt,
            "author": ba, "slug": key_of.get(c["book"]) or slugify(c["book"]),
            "situations": c.get("situations") or [],
        })
    entries.extend(legacy_books)
    assert sum(1 for e in entries if isinstance(e.get("i"), int)) == n, \
        "search index rip count != card count"
    with open(os.path.join(BASE, "search-index.json"), "w", encoding="utf-8") as fh:
        json.dump(entries, fh, ensure_ascii=False)

    # ---------------- sitemaps ----------------
    today = _dt.date.today().isoformat()

    def urlset(urls):
        lines = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for loc, freq, pri in urls:
            lines.append("  <url><loc>%s</loc><lastmod>%s</lastmod>"
                         "<changefreq>%s</changefreq><priority>%s</priority></url>"
                         % (loc, today, freq, pri))
        lines.append("</urlset>")
        return "\n".join(lines) + "\n"

    card_urls = [(SITE + canon(cid), "monthly", "0.7") for cid in ids_sorted]
    with open(os.path.join(BASE, "sitemap-cards.xml"), "w", encoding="utf-8") as fh:
        fh.write(urlset(card_urls))
    book_urls = [(SITE + "/", "daily", "1.0"), (SITE + "/ledger/", "weekly", "0.8")]
    seen_books = set()
    for b in books:
        key = key_of.get(b["book"])
        if key and key not in seen_books and \
                os.path.exists(os.path.join(BASE, "books", key, "index.html")):
            seen_books.add(key)
            book_urls.append((SITE + "/books/%s/" % key, "monthly", "0.6"))
    with open(os.path.join(BASE, "sitemap-books.xml"), "w", encoding="utf-8") as fh:
        fh.write(urlset(book_urls))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
          '  <sitemap><loc>%s/sitemap-cards.xml</loc><lastmod>%s</lastmod></sitemap>' % (SITE, today),
          '  <sitemap><loc>%s/sitemap-books.xml</loc><lastmod>%s</lastmod></sitemap>' % (SITE, today),
          '</sitemapindex>']
    with open(os.path.join(BASE, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(sm) + "\n")

    # ---------------- 404 hash-redirect injection ----------------
    for rel in ("404.html", os.path.join("404", "index.html")):
        p = os.path.join(BASE, rel)
        if not os.path.exists(p):
            continue
        t = open(p, encoding="utf-8").read()
        if "ir-hash-redirect" in t:
            continue
        if "</body>" in t:
            t = t.replace("</body>", HASH_SCRIPT + "</body>", 1)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(t)
            print("404: injected #cN redirect into %s" % rel)

    print("pages built: %d cards, %d stubs, %d sitemap card urls, %d sitemap book urls"
          % (n, n, len(card_urls), len(book_urls)))
    print("search index: %d rip entries + %d legacy book entries"
          % (n, len(legacy_books)))


if __name__ == "__main__":
    main()
