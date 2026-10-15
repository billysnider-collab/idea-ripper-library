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
  books/index.html            Wave 4: every book by shelf + theses/reports archive
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

Wave 1 (2026-10-14, ripping-method program): honest quote styling (synthesis
steals render as plain paragraphs labeled "In our words", never blockquotes);
source classification (book / thesis / military report, from shelf genre +
bookline institution) driving a books-only homepage feed, an Archives shelf,
source pills, a ledger source filter, and a `src` key in search-index.json;
a compact Start Here block; corrected command-bar ID hint (#c1-#c<max>);
problem-word search placeholder + shelf links on zero results.

Wave 2 (2026-10-14, ripping-method program): situations become the front
door (S1) — situation pages at /situations/ and /situations/<slug>/ built
from the cards' `situations` data (they did not exist before Wave 2; the
homepage strip that wore the situation label linked to genre anchors).
Situation DISPLAY names are felt friction (SIT_DISPLAY below); the data
labels in books/*.md and the page slugs (slugified data labels) never
change. Card pages end with two exit ramps (S7): "Same situation, different
book" and "Card N of M from this book" with in-book prev/next. The ledger
gains a client-side "Sample the stack" sampler + "Surprise me" jump (S8),
fed by data-title / data-book / data-sit row attributes.

Wave 4 (2026-10-14, Billy): findability. The redesign's front door hid the
two lists a browser actually navigates by, so both are restored: a
"Recently Added" list on the homepage (the newest books, ordered by each
book's highest permanent card id — the only recency signal in the data)
and a /books/ index page (every book grouped by shelf, with the theses
and military reports in their own separated archive section). "Books"
joins the top-level nav surfaces. Presentation only: no library data,
card id, or slug changes.
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


def uw_disp(s):
    """DISPLAY ONLY: strip a leading 'Use when:' that some card data carries,
    so the label never doubles ('Use when: Use when ...'). Data untouched."""
    t = re.sub(r"^\s*use when\s*:?\s*", "", s or "", flags=re.I)
    return (t[:1].upper() + t[1:]) if t else t


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
.theline{font-family:var(--font-serif);font-size:1.55rem;line-height:1.4;margin:.4rem 0 .8rem}
blockquote.theline{quotes:"\u201c" "\u201d"}
.dossier .theline{font-size:1.8rem}
.srcpill{font-family:var(--font-mono);font-size:.66rem;font-weight:700;letter-spacing:.12em;border:1px solid var(--border-subtle);color:var(--text-secondary);background:var(--bg-subtle);padding:.16rem .45rem;text-transform:uppercase;white-space:nowrap}
.relcard .srcpill{display:inline-block;margin-left:.45rem}
td .srcpill{margin-left:.4rem}
.cb-src .srcpill{margin-left:.2rem}
.starthere{border:1.5px solid var(--border-strong);background:var(--bg-subtle);padding:.85rem 1rem;margin:0 0 1.25rem}
.starthere .shk{font-family:var(--font-mono);font-size:.72rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--accent-signal);display:block;margin-bottom:.3rem}
.starthere p{margin:0;font-size:.99rem}
.srcfilter{display:flex;gap:.5rem;flex-wrap:wrap;margin:0 0 1.25rem}
.sfilter.on{background:var(--text-primary);color:var(--bg-canvas)}
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
/* Wave 4: Recently Added (homepage) + Books index rows */
.recentlist,.booklist{list-style:none;margin:0 0 1.25rem;padding:0}
.rbook{border-bottom:1px solid var(--border-subtle);margin:0;padding:0}
.rbook a.rlink{display:flex;flex-direction:column;justify-content:center;gap:.15rem;min-height:44px;padding:.65rem .5rem;color:var(--text-primary);text-decoration:none;border-radius:2px}
.rbook a.rlink:hover{background:var(--bg-subtle)}
.rbook a.rlink:hover .rtitle{text-decoration:underline;text-underline-offset:3px}
.rbook a.rlink:focus-visible{outline:3px solid #1a4fd6;outline-offset:2px;background:var(--bg-subtle)}
.rbook .rtitle{font-family:var(--font-serif);font-size:1.15rem;font-weight:600;line-height:1.3;color:#1c1a17}
.rbook .rmeta{font-size:1rem;line-height:1.4;color:#4a4540}
.rbook .rmeta>span{white-space:nowrap}
.rbook .rmeta .sep{padding:0 .35rem;color:#6b645c}
.rbook .srcpill{font-size:.75rem}
.seeall{display:inline-flex;align-items:center;min-height:44px;padding:0 .9rem;margin:0 0 1.5rem;border:1.5px solid var(--border-strong);font-size:1rem;font-weight:600;color:#1c1a17;text-decoration:none;background:var(--bg-card)}
.seeall:hover{background:var(--bg-subtle)}
.seeall:focus-visible{outline:3px solid #1a4fd6;outline-offset:2px}
h2.recenthead{font-family:var(--font-serif);font-size:1.5rem;font-weight:700;letter-spacing:0;text-transform:none;margin:2rem 0 .25rem}
p.recentnote{font-size:1rem;color:#4a4540;margin:0 0 .5rem}
h3.archsub{font-family:var(--font-mono);font-size:.78rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--text-secondary);margin:1.4rem 0 .4rem}
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
  .theline{font-size:1.3rem}
  .dossier .theline{font-size:1.45rem}
  .prevcard,.dossier{box-shadow:3px 3px 0 var(--border-strong)}
  h1.mission{font-size:1.55rem}
  .cb-book{display:none}
}
@media print{.statusbar,.cmdbar,.headrow,.sharerow,.navrow{display:none!important}body{background:#fff}}
/* Wave 2: situation chip links, exit ramps, ledger sampler */
a.sitchip{color:var(--text-primary);text-decoration:none}
a.sitchip:hover{background:var(--bg-canvas);border-color:var(--border-strong);color:var(--text-primary)}
.relcard .rbook{font-family:var(--font-mono);font-size:.72rem;color:var(--text-secondary);display:block;margin-top:.2rem;letter-spacing:.05em}
.booknav{align-items:center}
.bookpos{font-family:var(--font-mono);font-size:.78rem;color:var(--text-secondary);text-align:center;letter-spacing:.05em;padding:0 .5rem}
.sampler{margin:0 0 1.5rem}
.samplegrid{margin-top:.9rem}
/* Fix pass 2026-10-14: paper book pages, connections toggle, request link */
.bookhead{border:1.5px solid var(--border-strong);background:var(--bg-card);box-shadow:5px 5px 0 var(--border-strong);padding:1.1rem 1.25rem;margin:0 0 1.5rem}
.bookhead .bauthor{font-family:var(--font-serif);font-size:1.15rem;color:var(--text-secondary);margin:0 0 .4rem}
.bookhead .bline{margin:.4rem 0 0}
.bookhead .bcounts{font-family:var(--font-mono);font-size:.75rem;letter-spacing:.08em;text-transform:uppercase;color:var(--text-secondary)}
.cardacts{display:flex;gap:.5rem;margin:.9rem 0 0}
.cardacts .btn{padding:.45rem .8rem;font-size:.78rem}
details.conn{margin-top:.9rem;border-top:1px dashed var(--border-subtle);padding-top:.6rem}
details.conn summary{cursor:pointer;font-family:var(--font-mono);font-size:.78rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase}
details.conn .relgrid{margin-top:.7rem}
.topnav{display:flex;justify-content:space-between;align-items:center;gap:1rem}
.rip-request{font-family:var(--font-mono);font-size:.75rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase}
.rip-request .rr-short{display:none}
@media(max-width:560px){.rip-request .rr-long{display:none}.rip-request .rr-short{display:inline}}
"""

HASH_SCRIPT = ("<script>/* ir-hash-redirect: legacy #cN links land on the card page */"
               "(function(){var m=/^#c(\\d+)$/.exec(location.hash);"
               "if(m)location.replace('/c/'+m[1]+'/');})();</script>")


SLUG_SCRIPT = ("<script>/* ir-slug-redirect: /c/<id>-<wrong-slug>/ lands on the card */"
               "(function(){var m=/^\\/c\\/(\\d+)(?:-[^\\/]*)?\\/?$/.exec(location.pathname);"
               "if(m&&location.pathname!=='/c/'+m[1]+'/')location.replace('/c/'+m[1]+'/');})();</script>")


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


def id_note(n, maxid):
    """Card count vs ID range: IDs are permanent and never reused, so the
    highest ID runs ahead of the card count when cards are retired."""
    return ("%d cards \u00b7 IDs run #c1\u2013#c%d (highest ID; %d IDs retired, never reused)"
            % (n, maxid, maxid - n))


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
        if key:
            return "/books/%s/" % key  # fix pass: every keyed book gets a paper page
        anchor = key or slugify(book)
        return "/ledger/#book-%s" % anchor

    def pill(card):
        return "verbatim" if card["type"] == "passage" else "synthesis"

    def pill_label(card):
        return "Verbatim excerpt" if card["type"] == "passage" else "Synthesis"

    # Source classification (Wave 1, 2026-10-14): a card's source is a BOOK
    # unless its shelf genre is Thesis; a thesis from a military institution
    # (bookline carries the institution) is a MILITARY REPORT, else a THESIS.
    MIL_INST = ("Naval Postgraduate School", "Joint Advanced Warfighting School",
                "National Defense University", "Command and General Staff College",
                "Air University", "School of Advanced Air and Space Studies",
                "Air Force Institute of Technology")

    def src_kind(b):
        if b["genre"] != "Thesis":
            return "book"
        bl = b.get("bookline", "")
        return "report" if any(m in bl for m in MIL_INST) else "thesis"

    src_of = {b["book"]: src_kind(b) for b in books}
    SRC_LABEL = {"thesis": "Thesis", "report": "Military report"}

    def src_pill(card):
        k = src_of[card["book"]]
        if k == "book":
            return ""
        return '<span class="srcpill">%s</span>' % SRC_LABEL[k]

    def line_el(c):
        """The steal, honestly framed: blockquote only for verbatim quotes."""
        if pill(c) == "verbatim":
            return '<blockquote class="theline">%s</blockquote>' % esc(c["steal"])
        return '<p class="theline inwords">%s</p>' % esc(c["steal"])

    def attr_html(c, bt, ba):
        inner = '<a href="%s">%s</a>%s' % (esca(book_url(c["book"])), esc(bt),
                                           (" (%s)" % esc(ba)) if ba else "")
        if pill(c) == "verbatim":
            return '<p class="attr">\u2014 Source: %s</p>' % inner
        return '<p class="attr">\u2014 In our words \u00b7 Source: %s</p>' % inner

    # Wave 2 (S1): situation DISPLAY names are felt friction — the moment a
    # reader recognizes from their own week — written from each situation's
    # actual use-when lines. DISPLAY ONLY: the data labels in books/*.md /
    # cards.json and the page slugs (slugified data labels) never change, so
    # no URL moves and no source file is touched.
    SIT_DISPLAY = {
        "Persuading": "When you need a yes and they\u2019re not there yet",
        "Hiring and leading": "When the team is looking to you to lead",
        "Negotiating": "When the other side has more leverage",
        "Making things": "When you\u2019re building the thing, not just planning it",
        "Seeing clearly": "When your picture of things might be wrong",
        "Deciding under uncertainty": "When you must decide and the facts aren\u2019t in",
        "Starting something": "When it\u2019s day one and nothing exists yet",
        "Strategy and competition": "When a rival\u2019s move changes your game",
        "Technology and AI": "When new tech lands in your work",
        "Stuck or burned out": "When you\u2019re stuck and running on empty",
        "Understanding power": "When you need to know who really decides",
    }

    def sit_slug(label):
        return slugify(label)

    def sit_name(label):
        return SIT_DISPLAY.get(label, label)

    def sit_url(label):
        return "/situations/%s/" % sit_slug(label)

    sit_cards = {}
    for c in cards:
        for s in (c.get("situations") or []):
            sit_cards.setdefault(s, []).append(c["id"])
    sit_labels = sorted(sit_cards, key=lambda s: -len(sit_cards[s]))
    book_cards = {}
    for c in cards:
        book_cards.setdefault(c["book"], []).append(c["id"])

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
        url = SITE + canon(cid)
        book_ld = {"@type": "Book", "name": bt}
        if ba:
            book_ld["author"] = {"@type": "Person", "name": ba}
        if pill(c) == "verbatim":
            # verbatim excerpt: a real quotation, attributed to the author
            title = '"%s\u2026" \u2014 %s (#c%d) | Idea Ripper' % (words, ba or bt, cid)
            desc = trunc('"%s" \u2014 From %s by %s. Use when: %s. Why it matters: %s.'
                         % (line, bt, ba, uw_disp(c["uw"]), c["why"]), 300)
            ld = {"@context": "https://schema.org", "@type": "Quotation",
                  "text": line, "isPartOf": book_ld,
                  "mainEntity": {"@type": "DefinedTerm", "name": trunc(c["title"], 120),
                                 "description": uw_disp(c["uw"])}}
        else:
            # synthesis ("In our words"): never attributed to the author as a quote
            title = '%s \u2014 Idea Ripper on %s (#c%d)' % (trunc(c["title"], 80), bt, cid)
            desc = trunc('Idea Ripper synthesis of %s: %s Use when: %s'
                         % (bt, line.rstrip(), uw_disp(c["uw"])), 300)
            ld = {"@context": "https://schema.org", "@type": "Article",
                  "headline": trunc(c["title"], 110), "abstract": line,
                  "author": {"@type": "Organization", "name": "Idea Ripper"},
                  "about": book_ld, "url": url,
                  "genre": "Synthesis (in our words)"}
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
            chips = "".join('<a class="sitchip" href="%s">%s</a>'
                            % (sit_url(s), esc(sit_name(s))) for s in c["situations"])
            sits = ('<div class="sits"><span class="slab">Filed under situations:</span>%s</div>' % chips)
        page.append(
            '<article class="dossier">'
            '<div class="pc-top"><span class="badge">Card #c%d</span>'
            '<span class="stamp">IR // #c%d</span>'
            '<span class="vpill %s">%s</span>%s</div>'
            '%s'
            '%s'
            '<div class="meta-block">'
            '<span class="uwk">[Use when]</span><p class="uw">%s</p>'
            '<span class="whyk">[Why it matters]</span><p class="why">%s</p>'
            '%s</div></article>'
            % (cid, cid, pill(c), esc(pill_label(c)), src_pill(c),
               line_el(c), attr_html(c, bt, ba), esc(uw_disp(c["uw"])), esc(c["why"]), sits))
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
                page.append('<a class="relcard" href="%s"><span class="rid">#c%d</span>%s'
                            '<span class="rline">%s</span><span class="ruw">%s</span></a>'
                            % (canon(r), r, src_pill(rc), esc(trunc(rc["steal"], 140)), esc(trunc(uw_disp(rc["uw"]), 110))))
            page.append('</div>')
        sibs = [o for o in cards if o["book"] == c["book"] and o["id"] != cid]
        sibs.sort(key=lambda o: o["id"])
        if sibs:
            page.append('<h2 class="sect">More from %s</h2><div class="relgrid">' % esc(bt))
            for rc in sibs[:3]:
                page.append('<a class="relcard" href="%s"><span class="rid">#c%d</span>%s'
                            '<span class="rline">%s</span><span class="ruw">%s</span></a>'
                            % (canon(rc["id"]), rc["id"], src_pill(rc), esc(trunc(rc["steal"], 140)),
                               esc(trunc(uw_disp(rc["uw"]), 110))))
            page.append('</div>')
        # Wave 2 exit ramps (S7): the page never ends on a dead end. Ramp 1
        # fires only when cross-book cards share a situation with this one;
        # ramp 2 only when the book holds more than this one card. In-book
        # order is the curated cards.json order for the book.
        own_sits = c.get("situations") or []
        if own_sits:
            scored = {}
            for s in own_sits:
                for oid in sit_cards.get(s, []):
                    if oid != cid and by_id[oid]["book"] != c["book"]:
                        scored[oid] = scored.get(oid, 0) + 1
            top = sorted(scored, key=lambda o: (-scored[o], -o))[:4]
            if top:
                page.append('<h2 class="sect">Same situation, different book</h2><div class="relgrid">')
                for r in top:
                    rc = by_id[r]
                    rbt, _rba = split_book(rc["book"])
                    page.append('<a class="relcard" href="%s"><span class="rid">#c%d</span>%s'
                                '<span class="rline">%s</span><span class="ruw">%s</span>'
                                '<span class="rbook">From %s</span></a>'
                                % (canon(r), r, src_pill(rc), esc(rc["title"]),
                                   esc(trunc(uw_disp(rc["uw"]), 110)), esc(rbt)))
                page.append('</div>')
        sib_ids = book_cards[c["book"]]
        if len(sib_ids) > 1:
            pos = sib_ids.index(cid)
            p_btn = ('<a class="btn ghost" href="%s">&lt;- Prev in this book</a>'
                     % canon(sib_ids[pos - 1])) if pos > 0 else '<span></span>'
            nx_btn = ('<a class="btn ghost" href="%s">Next in this book -&gt;</a>'
                      % canon(sib_ids[pos + 1])) if pos < len(sib_ids) - 1 else '<span></span>'
            page.append('<nav class="navrow booknav">%s'
                        '<span class="bookpos">Card %d of %d from %s</span>%s</nav>'
                        % (p_btn, pos + 1, len(sib_ids), esc(bt), nx_btn))
        page.append('<footer class="sitefoot"><a href="/">Idea Ripper archive</a> \u00b7 '
                    '<a href="/ledger/">Full ledger</a> \u00b7 Card #c%d of %d \u00b7 '
                    'Machine-assisted, hand-curated</footer>' % (cid, n))
        page.append('</div>')
        if pill(c) == "verbatim":
            copy_text = '"%s"\n\u2014 %s, %s\nidearipper.com/c/%d' % (
                " ".join(line.split()), ba, bt, cid)
        else:
            copy_text = '%s\n\u2014 Idea Ripper, in our words, on %s%s\nidearipper.com/c/%d' % (
                " ".join(line.split()), bt, (" (%s)" % ba) if ba else "", cid)
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

    # Wave 4: one book row (title, author, card count, link), shared by the
    # homepage Recently Added list and the /books/ index. The link is the
    # site's own pattern (book_url): the full-book page when one exists,
    # else the book's ledger anchor.
    _w4_book_cards = {}
    for c in cards:
        _w4_book_cards[c["book"]] = _w4_book_cards.get(c["book"], 0) + 1

    # Recently Added (2026-10-14, Billy): plain-words "date added" per book,
    # seeded from git history by tools/book_dates.py; books new to this
    # build are stamped with today's date (America/Chicago) and saved.
    try:
        _bd = json.load(open(os.path.join(BASE, "book_dates.json"), encoding="utf-8"))
    except (OSError, ValueError):
        _bd = {}
    import datetime as _dtm
    try:
        from zoneinfo import ZoneInfo as _ZI
        _today = _dtm.datetime.now(_ZI("America/Chicago")).strftime("%Y-%m-%d")
    except Exception:
        _today = _dtm.date.today().isoformat()
    _bd_new = False
    for c in cards:
        if c["book"] not in _bd:
            _bd[c["book"]] = _today
            _bd_new = True
    if _bd_new:
        with open(os.path.join(BASE, "book_dates.json"), "w", encoding="utf-8") as fh:
            json.dump(dict(sorted(_bd.items())), fh, indent=1, ensure_ascii=False)

    def _plain_date(iso):
        d = _dtm.date.fromisoformat(iso)
        return "%s %d, %d" % (d.strftime("%B"), d.day, d.year)

    def book_li(b, with_pill=False):
        bt, ba = split_book(b["book"])
        pill = (' <span class="srcpill">%s</span>'
                % SRC_LABEL[src_of[b["book"]]]) if with_pill else ""
        n_c = _w4_book_cards.get(b["book"], 0)
        meta = []
        if ba:
            meta.append('<span class="rauthor">by %s</span>' % esc(ba))
        meta.append('<span class="rcount">%d card%s</span>' % (n_c, "" if n_c == 1 else "s"))
        iso = _bd.get(b["book"])
        if iso:
            meta.append('<span class="rdate">Added <time datetime="%s">%s</time></span>'
                        % (iso, _plain_date(iso)))
        return ('<li class="rbook"><a class="rlink" href="%s"><span class="rtitle">%s</span>'
                '<span class="rmeta">%s%s</span></a></li>'
                % (esca(book_url(b["book"])), esc(bt),
                   '<span class="sep" aria-hidden="true">\u00b7</span>'.join(meta), pill))

    # ---------------- homepage ----------------
    def prev_card(c):
        bt, ba = split_book(c["book"])
        return (
            '<article class="prevcard"><div class="pc-top"><span class="badge">Card #c%d</span>'
            '<span class="vpill %s">%s</span>%s</div>'
            '%s'
            '%s'
            '<span class="uwk">[Use when]</span><p class="uw">%s</p>'
            '<a class="openfile" href="%s">[Open file #c%d -&gt;]</a></article>'
            % (c["id"], pill(c), esc(pill_label(c)), src_pill(c),
               line_el(c), attr_html(c, bt, ba),
               esc(uw_disp(c["uw"])), canon(c["id"]), c["id"]))

    # Wave 1 feed rule: the homepage feed carries BOOKS ONLY; the latest
    # non-book cards (theses + military reports) get the Archives shelf.
    latest = [by_id[i] for i in ids_sorted[::-1]
              if src_of[by_id[i]["book"]] == "book"][:6]
    archive_latest = [by_id[i] for i in ids_sorted[::-1]
                      if src_of[by_id[i]["book"]] != "book"][:6]
    prev_html = [prev_card(c) for c in latest]
    sample = None
    _row = ds.get("rip_of_the_week") or {}
    if isinstance(_row.get("id"), int) and _row["id"] in by_id \
            and src_of[by_id[_row["id"]]["book"]] == "book":
        sample = by_id[_row["id"]]
    if sample is None and latest:
        sample = latest[0]
    # Wave 2 (S1): this strip wore the situation label over genre pills
    # until now; it carries the real situations, under felt-friction names.
    # Genres keep their own surface in "Browse by shelf" below.
    pills = []
    for s in sit_labels:
        pills.append('<a class="pill-link" href="%s">%s <span class="n">%d</span></a>'
                     % (sit_url(s), esc(sit_name(s)), len(sit_cards[s])))
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
    home.append('<p class="stamp">%s</p>' % id_note(n, ids_sorted[-1]))
    if sample is not None:
        home.append(
            '<section class="starthere" id="start-here"><span class="shk">Start here</span>'
            '<p>New here? Idea Ripper pulls one usable idea out of a book: the line '
            'worth keeping, why it matters, and the moment you would use it. The '
            'fastest way in is by situation, so pick the situation below that '
            'matches your problem, or open one card now: <a href="%s">Card #c%d, from '
            '%s</a>.</p></section>'
            % (canon(sample["id"]), sample["id"],
               esc(split_book(sample["book"])[0])))
    home.append(
        '<form class="cmdbar" id="commandbar" action="#" method="get">'
        '<label for="cb-input">Direct access // Enter a card ID (highest: #c%d) or keyword</label>'
        '<div class="cmdrow"><input id="cb-input" type="text" autocomplete="off" '
        'placeholder="Search a problem (\u201cfiring\u201d, \u201cenvy\u201d, '
        '\u201cpricing\u201d) or a book\u2026"/>'
        '<button class="btn" type="submit">[Go -&gt;]</button></div>'
        '<div class="cb-results" id="cb-results" hidden></div></form>'
        % ids_sorted[-1])
    home.append('<div class="headrow"><button type="button" class="btn ghost randomcard">'
                '[Random card \u21bb]</button>'
                '<a class="btn ghost" href="/books/">[Books]</a>'
                '<a class="btn ghost" href="/ledger/">[Full ledger]</a></div>')
    home.append('<h2 class="sect" id="situations">Field-tested by situation:</h2><div class="pills">%s'
                '<a class="pill-link" href="/situations/">All situations -&gt;</a></div>'
                % "".join(pills))
    home.append('<h2 class="sect">Latest dispatches <span class="cnt">// last 6 additions, from books</span></h2>')
    home.extend(prev_html)
    if archive_latest:
        home.append('<h2 class="sect">From the Archives: Field Reports &amp; Theses '
                    '<span class="cnt">// last %d non-book additions</span></h2>'
                    % len(archive_latest))
        home.extend(prev_card(c) for c in archive_latest)
    # Wave 4 (Billy): Recently Added — the newest BOOKS in the library.
    # Recency = each book's permanent card ids: ids are permanent and
    # issued in adoption order, so ranking by highest card id descending
    # ranks the books by adoption. No dates are printed; the ordering
    # carries the recency. One refinement: the books of the newest
    # adoption event occupy mutually contiguous ranges at the head of the
    # id space (each book starts where the previous one ends); inside
    # that block the list follows adoption order (first card id
    # ascending) — the order the books were ripped in — instead of
    # last-card order, so a same-day batch reads the way it happened.
    _w4_maxid, _w4_minid = {}, {}
    for c in cards:
        if c["id"] > _w4_maxid.get(c["book"], 0):
            _w4_maxid[c["book"]] = c["id"]
        if c["id"] < _w4_minid.get(c["book"], 1 << 30):
            _w4_minid[c["book"]] = c["id"]
    _ranked = sorted(
        [b for b in books if src_of[b["book"]] == "book"],
        key=lambda b: _w4_maxid[b["book"]], reverse=True)
    _head = []
    for b in _ranked:
        if _head and _w4_maxid[b["book"]] != _w4_minid[_head[-1]["book"]] - 1:
            break
        _head.append(b)
    _head.sort(key=lambda b: _w4_minid[b["book"]])
    recent_books = (_head + _ranked[len(_head):])[:10]
    if recent_books:
        home.append('<section aria-labelledby="recent-head">'
                    '<h2 class="recenthead" id="recent-head">Recently added books</h2>'
                    '<p class="recentnote">The %d newest books in the library, newest first.</p>'
                    % len(recent_books))
        home.append('<ul class="recentlist">%s</ul>'
                    % "".join(book_li(b) for b in recent_books))
        home.append('<a class="seeall" href="/books/">See all books \u2192</a></section>')
    home.append('<h2 class="sect">Browse by shelf</h2><div class="shelfgrid">%s</div>'
                % "".join(shelf_boxes))
    home.append('<footer class="sitefoot"><a href="/books/">Books</a> &#183; '
                '<a href="/ledger/">Full ledger</a> \u00b7 '
                '<a href="https://x.com/IdeaRipper">@IdeaRipper on X</a> \u00b7 '
                '%d cards \u00b7 Machine-assisted, hand-curated with the Idea Ripper pipeline</footer>' % n)
    home.append('</div>')
    _shelf_js = sorted(((sum(1 for c in cards if genre_of[c["book"]] == g), g)
                        for g in genre_order), reverse=True)[:3]
    home.append('<script>var SHELVES=%s,MAXID=%d;</script>'
                % (json.dumps([[slugify(g), g] for _cnt, g in _shelf_js]), ids_sorted[-1]))
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
        '+\'<span class="cb-line"></span><span class="cb-book"></span><span class="cb-src"></span></a>\';});'
        'if(note)h+=\'<p class="cb-note">\'+note+\'</p>\';res.innerHTML=h;'
        'var rows=res.querySelectorAll(".cb-hit");list.forEach(function(e,k){'
        'rows[k].querySelector(".cb-line").textContent=e.l;'
        'rows[k].querySelector(".cb-book").textContent=e.b;'
        'var sp=rows[k].querySelector(".cb-src");'
        'if(e.src&&e.src!=="book"){sp.innerHTML=\'<span class="srcpill">\'+'
        '(e.src==="report"?"Military report":"Thesis")+\'</span>\';}});}'
        'function zeroNote(q){var links=(window.SHELVES||[]).map(function(s){'
        'return \'<a href="/ledger/#genre-\'+s[0]+\'">\'+s[1]+\'</a>\';}).join(" \u00b7 ");'
        'return "No cards match \u201c"+q.replace(/[<>&]/g,"")+"\u201d. Try one plain word (\u201cpricing\u201d, \u201cfear\u201d), a book title, or a card ID like c402. Or browse a shelf: "+links+'
        '" \u00b7 or <a href=\'/ledger/\'>open the full ledger</a>.";}'
        'function search(q){q=q.trim().toLowerCase();if(!idx||q.length<2){render([]);return;}'
        'var ws=q.split(/\\s+/),out=[];'
        'for(var k=0;k<idx.length&&out.length<6;k++){var e=idx[k],'
        't=(e.l+" "+e.u+" "+e.b+" "+(e.title||"")).toLowerCase(),ok=true;'
        'for(var j=0;j<ws.length;j++){if(t.indexOf(ws[j])<0){ok=false;break;}}'
        'if(ok)out.push(e);}'
        'render(out,out.length?"":zeroNote(q));}'
        'inp.addEventListener("input",function(){var v=inp.value.trim();'
        'var m=/^#?c?(\\d+)$/i.exec(v);'
        'if(m&&idx){var id=+m[1],hit=null;for(var k=0;k<idx.length;k++)if(idx[k].i===id){hit=idx[k];break;}'
        'render(hit?[hit]:[],hit?"":(id>MAXID?"No card #c"+id+" yet \u2014 the highest ID is #c"+MAXID+".":"Card #c"+id+" was retired or merged (IDs are never reused). Try a keyword, or <a href=\'/ledger/\'>open the ledger</a>."));return;}'
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
    led.append('<nav class="crumb"><a href="/">Archive</a> / Ledger &#183; '
               '<a href="/books/">Books</a></nav>')
    led.append('<h1 class="mission">The ledger</h1>')
    led.append('<p class="sub">Every card in the archive \u2014 %d \u2014 in shelf order. '
               'Each row opens the full file.</p>' % n)
    led.append('<div class="srcfilter" role="group" aria-label="Filter the ledger by source">'
               '<button type="button" class="btn ghost sfilter on" data-f="all">All</button>'
               '<button type="button" class="btn ghost sfilter" data-f="book">Books</button>'
               '<button type="button" class="btn ghost sfilter" data-f="archive">'
               'Reports &amp; Theses</button></div>')
    # Wave 2 (S8): sample the stack — five random cards, or one blind jump,
    # served entirely from the rows already on this page.
    led.append('<div class="sampler"><button type="button" class="btn" id="sample-btn">'
               '[Sample the stack \u21bb]</button> '
               '<button type="button" class="btn ghost" id="surprise-btn">[Surprise me]</button>'
               '<div class="relgrid samplegrid" id="sample-out" hidden></div></div>')
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
                csits = c.get("situations") or []
                led.append('<tr%s data-src="%s" data-title="%s" data-book="%s" data-sit="%s">'
                           '<td class="lid"><a href="%s">#c%d</a></td>'
                           '<td><a href="%s">%s</a></td><td class="lbook">%s%s</td>'
                           '<td class="lshelf">%s</td></tr>'
                           % (idattr, src_of[c["book"]], esca(c["title"]), esca(bt),
                              esca(sit_name(csits[0])) if csits else "",
                              canon(c["id"]), c["id"], canon(c["id"]),
                              esc(trunc(c["steal"], 60)), esc(bt), src_pill(c), esc(g)))
        led.append('</tbody></table></div>')
    led.append('<footer class="sitefoot"><a href="/">Idea Ripper archive</a> \u00b7 '
               '%d cards \u00b7 Machine-assisted, hand-curated</footer>' % n)
    led.append(
        '<script>(function(){'
        'var btns=document.querySelectorAll(".sfilter");'
        'function apply(f){btns.forEach(function(b){'
        'b.classList.toggle("on",b.getAttribute("data-f")===f);});'
        'document.querySelectorAll("table.ledger tbody tr").forEach(function(tr){'
        'var s=tr.getAttribute("data-src");'
        'var show=f==="all"||s===f||(f==="archive"&&(s==="thesis"||s==="report"));'
        'tr.style.display=show?"":"none";});'
        'document.querySelectorAll("h2.sect").forEach(function(h){'
        'var w=h.nextElementSibling;'
        'if(!w||!w.classList.contains("ledwrap"))return;'
        'var any=false;'
        'w.querySelectorAll("tbody tr").forEach(function(tr){'
        'if(tr.style.display!=="none")any=true;});'
        'h.style.display=any?"":"none";w.style.display=any?"":"none";});}'
        'btns.forEach(function(b){b.addEventListener("click",function(){'
        'apply(b.getAttribute("data-f"));});});'
        '})();</script>')
    led.append(
        '<script>(function(){'
        'var rows=[].slice.call(document.querySelectorAll("table.ledger tbody tr"));'
        'var out=document.getElementById("sample-out");'
        'if(!rows.length||!out)return;'
        'function hrefOf(tr){var a=tr.querySelector("td.lid a");'
        'return a?a.getAttribute("href"):"/ledger/";}'
        'function idOf(tr){var a=tr.querySelector("td.lid a");'
        'return a?a.textContent:"";}'
        'function pick(k){var seen={},res=[];'
        'while(res.length<k&&res.length<rows.length){'
        'var i=Math.floor(Math.random()*rows.length);'
        'if(!seen[i]){seen[i]=1;res.push(rows[i]);}}return res;}'
        'document.getElementById("sample-btn").addEventListener("click",function(){'
        'var sel=pick(5);out.hidden=false;'
        'out.innerHTML=sel.map(function(){return \'<a class="relcard"><span class="rid"></span>\''
        '+\'<span class="rline"></span><span class="ruw"></span></a>\';}).join("");'
        'var els=out.querySelectorAll(".relcard");'
        'sel.forEach(function(tr,k){var el=els[k];'
        'el.setAttribute("href",hrefOf(tr));'
        'el.querySelector(".rid").textContent=idOf(tr);'
        'el.querySelector(".rline").textContent=tr.getAttribute("data-title")||"";'
        'var meta=tr.getAttribute("data-book")||"";'
        'var sit=tr.getAttribute("data-sit");'
        'if(sit)meta+=" \u00b7 "+sit;'
        'el.querySelector(".ruw").textContent=meta;});});'
        'document.getElementById("surprise-btn").addEventListener("click",function(){'
        'location.assign(hrefOf(rows[Math.floor(Math.random()*rows.length)]));});'
        '})();</script>')
    led.append('</div></body></html>')
    os.makedirs(os.path.join(BASE, "ledger"), exist_ok=True)
    with open(os.path.join(BASE, "ledger", "index.html"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(led))

    # ---------------- situations (Wave 2, S1) ----------------
    # Built from the cards' `situations` data. These pages did not exist
    # before Wave 2: the redesign deferred them ("situation pages are
    # Phase 2") and the homepage strip that wore the label linked to genre
    # anchors. One system, in this builder: an index plus one page per
    # situation, rows = card title + use-when line (the "that's me" scan).
    def sit_relcard(rc):
        rbt, _rba = split_book(rc["book"])
        return ('<a class="relcard" href="%s"><span class="rid">#c%d</span>%s'
                '<span class="rline">%s</span><span class="ruw">%s</span>'
                '<span class="rbook">From %s</span></a>'
                % (canon(rc["id"]), rc["id"], src_pill(rc), esc(rc["title"]),
                   esc(trunc(uw_disp(rc["uw"]), 140)), esc(rbt)))

    os.makedirs(os.path.join(BASE, "situations"), exist_ok=True)
    sit_total = sum(len(v) for v in sit_cards.values())
    six = [head("Browse by situation | Idea Ripper",
                "Start from the moment you are in: %d situations, %d filed cards. "
                "Every card states the moment you would use it." % (len(sit_labels), sit_total),
                SITE + "/situations/", marker, css_href)]
    six.append("<body>")
    six.append(statusbar(n, build_date))
    six.append('<div class="wrap">')
    six.append('<nav class="crumb"><a href="/">Archive</a> / Situations</nav>')
    six.append('<h1 class="mission">Start from the moment you are in</h1>')
    six.append('<p class="sub">Cards here are filed by the situation they are '
               'for, not by subject. Find the line that sounds like your week; '
               'every card under it names what to do, and when.</p>')
    six.append('<div class="shelfgrid">')
    for s in sit_labels:
        sbooks = len({by_id[i]["book"] for i in sit_cards[s]})
        six.append('<a class="shelfbox" href="%s"><span class="sname">%s</span>'
                   '<span class="scounts">%d cards \u00b7 %d books \u00b7 filed as %s</span></a>'
                   % (sit_url(s), esc(sit_name(s)), len(sit_cards[s]), sbooks, esc(s)))
    six.append('</div>')
    six.append('<footer class="sitefoot"><a href="/">Idea Ripper archive</a> \u00b7 '
               '<a href="/books/">Books</a> \u00b7 '
               '<a href="/ledger/">Full ledger</a> \u00b7 %d situations \u00b7 '
               'Machine-assisted, hand-curated</footer>' % len(sit_labels))
    six.append('</div></body></html>')
    with open(os.path.join(BASE, "situations", "index.html"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(six))
    for s in sit_labels:
        name = sit_name(s)
        members = sorted(sit_cards[s], reverse=True)
        sbooks = len({by_id[i]["book"] for i in sit_cards[s]})
        sp = [head("%s | Idea Ripper" % name,
                   trunc("Cards for the moment: %s. %d field-tested ideas from %d books, "
                         "each with the line and when to use it."
                         % (name, len(members), sbooks), 300),
                   SITE + sit_url(s), marker, css_href)]
        sp.append("<body>")
        sp.append(statusbar(n, build_date))
        sp.append('<div class="wrap">')
        sp.append('<nav class="crumb"><a href="/">Archive</a> / '
                  '<a href="/situations/">Situations</a> / Filed as %s</nav>' % esc(s))
        sp.append('<h1 class="mission">%s</h1>' % esc(name))
        sp.append('<p class="sub">%d cards from %d books, filed under \u201c%s\u201d. '
                  'Newest first; every row is the card\u2019s title and the moment '
                  'you would use it.</p>' % (len(members), sbooks, esc(s)))
        sp.append('<div class="relgrid">')
        for mid in members:
            sp.append(sit_relcard(by_id[mid]))
        sp.append('</div>')
        sp.append('<footer class="sitefoot"><a href="/">Idea Ripper archive</a> \u00b7 '
                  '<a href="/situations/">All situations</a> \u00b7 '
                  '<a href="/ledger/">Full ledger</a> \u00b7 Machine-assisted, '
                  'hand-curated</footer>')
        sp.append('</div></body></html>')
        sd2 = os.path.join(BASE, "situations", sit_slug(s))
        os.makedirs(sd2, exist_ok=True)
        with open(os.path.join(sd2, "index.html"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(sp))

    # ---------------- book pages (fix pass 2026-10-14) ----------------
    # Every keyed book gets /books/<key>/ in the paper design. Replaces the
    # old Next.js export at the SAME URL (no URL changes) and creates pages
    # for books that only had a /ledger/#book-... anchor. One card anatomy
    # (same as the card page), actions cut to Copy + Link, and related rips
    # folded into a single "Explore connections (N)" toggle per card.
    bl_of = {b["book"]: b.get("bookline", "") for b in books}
    book_pages = 0
    for b in books:
        key = key_of.get(b["book"])
        if not key:
            continue
        bt, ba = split_book(b["book"])
        ids = book_cards.get(b["book"], [])
        bsits = []
        for i in ids:
            for st in (by_id[i].get("situations") or []):
                if st not in bsits:
                    bsits.append(st)
        burl = SITE + "/books/%s/" % key
        bdesc = trunc("%s%s. %d Idea Ripper cards: the line worth keeping and when to use it. %s"
                      % (bt, (" by %s" % ba) if ba else "", len(ids), bl_of[b["book"]]), 300)
        ld = {"@context": "https://schema.org", "@type": "Book", "name": bt, "url": burl}
        if ba:
            ld["author"] = {"@type": "Person", "name": ba}
        extra = '<script type="application/ld+json">%s</script>' % json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")
        if os.path.exists(os.path.join(BASE, "og", "og-%s.png" % key)):
            extra += '\n<meta property="og:image" content="%s/og/og-%s.png"/>' % (SITE, key)
        bp = [head("%s%s \u2014 Idea Ripper" % (bt, (" by %s" % ba) if ba else ""),
                   bdesc, burl, marker, css_href, extra)]
        bp.append("<body>")
        bp.append(statusbar(n, build_date))
        bp.append('<div class="wrap-narrow">')
        bp.append('<div class="topnav"><nav class="crumb"><a href="/">Archive</a> / '
                  '<a href="/books/">Books</a> / Shelf: <a href="/ledger/#genre-%s">%s</a></nav>'
                  '<a class="rip-request" aria-label="Request a rip" href="mailto:billysnider@gmail.com'
                  '?subject=Rip%%20request&amp;body=Book%%20title%%20and%%20author%%3A">'
                  '<span class="rr-long">Request a rip</span>'
                  '<span class="rr-short" aria-hidden="true">Request</span></a></div>'
                  % (slugify(b["genre"]), esc(b["genre"])))
        chips = "".join('<a class="sitchip" href="%s">%s</a>' % (sit_url(st), esc(sit_name(st)))
                        for st in bsits)
        bp.append('<header class="bookhead"><h1 class="mission">%s</h1>%s'
                  '<span class="bcounts">%d cards%s</span>%s%s</header>'
                  % (esc(bt), ('<p class="bauthor">by %s</p>' % esc(ba)) if ba else "",
                     len(ids), (' \u00b7 ' + SRC_LABEL[src_of[b["book"]]]) if src_of[b["book"]] != "book" else "",
                     ('<p class="bline">%s</p>' % esc(bl_of[b["book"]])) if bl_of[b["book"]] else "",
                     ('<div class="sits"><span class="slab">Situations:</span>%s</div>' % chips) if chips else ""))
        for cid in ids:
            c = by_id[cid]
            # hand-picked related_ids first, then the card page's own
            # "same situation, different book" ranking fills to 5
            rel = [r for r in (c.get("related_ids") or []) if r in by_id and r != cid]
            scored = {}
            for st in (c.get("situations") or []):
                for oid in sit_cards.get(st, []):
                    if oid != cid and by_id[oid]["book"] != c["book"]:
                        scored[oid] = scored.get(oid, 0) + 1
            for oid in sorted(scored, key=lambda o: (-scored[o], -o)):
                if len(rel) >= 5:
                    break
                if oid not in rel:
                    rel.append(oid)
            conn = ""
            if rel:
                conn = ('<details class="conn"><summary>Explore connections (%d)</summary>'
                        '<div class="relgrid">%s</div></details>'
                        % (len(rel), "".join(
                            '<a class="relcard" href="%s"><span class="rid">#c%d</span>%s'
                            '<span class="rline">%s</span><span class="rbook">From %s</span></a>'
                            % (canon(r), r, src_pill(by_id[r]), esc(by_id[r]["title"]),
                               esc(split_book(by_id[r]["book"])[0])) for r in rel)))
            bp.append(
                '<article class="dossier" id="c%d">'
                '<div class="pc-top"><span class="badge"><a href="%s">Card #c%d</a></span>'
                '<span class="vpill %s">%s</span>%s</div>'
                '<h2 class="whyk" style="margin:0 0 .2rem">%s</h2>'
                '%s%s'
                '<div class="meta-block">'
                '<span class="uwk">[Use when]</span><p class="uw">%s</p>'
                '<span class="whyk">[Why it matters]</span><p class="why">%s</p></div>'
                '<div class="cardacts"><button type="button" class="btn ghost bcopy" data-id="%d">Copy</button>'
                '<a class="btn ghost" href="%s">Link</a></div>%s</article>'
                % (cid, canon(cid), cid, pill(c), esc(pill_label(c)), src_pill(c),
                   esc(c["title"]), line_el(c), attr_html(c, bt, ba),
                   esc(uw_disp(c["uw"])), esc(c["why"]), cid, canon(cid), conn))
        copies = {}
        for cid in ids:
            c = by_id[cid]
            if pill(c) == "verbatim":
                copies[cid] = '"%s"\n\u2014 %s, %s\nidearipper.com/c/%d' % (" ".join(c["steal"].split()), ba, bt, cid)
            else:
                copies[cid] = '%s\n\u2014 Idea Ripper, in our words, on %s%s\nidearipper.com/c/%d' % (
                    " ".join(c["steal"].split()), bt, (" (%s)" % ba) if ba else "", cid)
        bp.append('<footer class="sitefoot"><a href="/">Idea Ripper archive</a> \u00b7 '
                  '<a href="/books/">All books</a> \u00b7 <a href="/ledger/">Full ledger</a> '
                  '\u00b7 Machine-assisted, hand-curated</footer></div>')
        bp.append('<script>(function(){var T=%s;'
                  'document.querySelectorAll(".bcopy").forEach(function(b){b.addEventListener("click",function(){'
                  'var t=T[b.getAttribute("data-id")];function done(){b.textContent="Copied";setTimeout(function(){b.textContent="Copy";},1400);}'
                  'if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(done,function(){});}'
                  '});});})();</script>' % json.dumps({str(k): v for k, v in copies.items()}, ensure_ascii=False).replace("</", "<\\/"))
        bp.append("</body></html>")
        bd = os.path.join(BASE, "books", key)
        os.makedirs(bd, exist_ok=True)
        with open(os.path.join(bd, "index.html"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(bp))
        book_pages += 1
    print("book pages: %d written (paper template)" % book_pages)

    # ---------------- books index (Wave 4) ----------------
    # /books/: every book in the library, grouped by shelf in the site's
    # genre order; then the theses and military reports (ideas, not books)
    # in their own clearly separated archive section. Rows link through
    # book_url, the site's existing pattern (full-book page when one
    # exists, else the book's ledger anchor). Presentation only.
    _w4_books = [b for b in books if src_of[b["book"]] == "book"]
    _w4_arch = [b for b in books if src_of[b["book"]] != "book"]
    bkp = [head("Books — every book in the library | Idea Ripper",
                "Every book ripped in the Idea Ripper library: %d books by "
                "shelf, plus %d theses and military reports in the archive."
                % (len(_w4_books), len(_w4_arch)),
                SITE + "/books/", marker, css_href)]
    bkp.append("<body>")
    bkp.append(statusbar(n, build_date))
    bkp.append('<div class="wrap">')
    bkp.append('<nav class="crumb"><a href="/">Archive</a> / Books</nav>')
    bkp.append('<h1 class="mission">Books</h1>')
    bkp.append('<p class="sub">Every book in the library, shelf by shelf. '
               '%d books, %d cards. The theses and military reports are '
               'filed in their own archive at the bottom.</p>'
               % (len(_w4_books),
                  sum(_w4_book_cards.get(b["book"], 0) for b in _w4_books)))
    for g in genre_order:
        gb = [b for b in _w4_books if b["genre"] == g]
        if not gb:
            continue
        bkp.append('<h2 class="sect">%s <span class="cnt">// %d books</span></h2>'
                   % (esc(g), len(gb)))
        bkp.append('<ul class="booklist">%s</ul>'
                   % "".join(book_li(b) for b in gb))
    bkp.append('<h2 class="sect">Theses &amp; Reports <span class="cnt">// the '
               'archive — ideas, not books</span></h2>')
    for g in genre_order:
        ga = [b for b in _w4_arch if b["genre"] == g]
        if not ga:
            continue
        bkp.append('<h3 class="archsub">%s <span class="cnt">// %d</span></h3>'
                   % (esc(g), len(ga)))
        bkp.append('<ul class="booklist">%s</ul>'
                   % "".join(book_li(b, with_pill=True) for b in ga))
    bkp.append('<footer class="sitefoot"><a href="/">Idea Ripper archive</a> \u00b7 '
               '<a href="/ledger/">Full ledger</a> \u00b7 '
               '<a href="/situations/">Situations</a> \u00b7 %d books \u00b7 '
               'Machine-assisted, hand-curated</footer>' % len(_w4_books))
    bkp.append('</div></body></html>')
    with open(os.path.join(BASE, "books", "index.html"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(bkp))
    print("books page: %d books, %d archive entries"
          % (len(_w4_books), len(_w4_arch)))

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
            "l": trunc(c["steal"], 200), "u": trunc(uw_disp(c["uw"]), 160), "b": bt,
            "kind": "rip", "id": cid, "title": c["title"], "steal": c["steal"],
            "why": c["why"], "uw": c["uw"], "type": c["type"], "book": bt,
            "src": src_of[c["book"]],
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
    book_urls = [(SITE + "/", "daily", "1.0"), (SITE + "/ledger/", "weekly", "0.8"),
                 (SITE + "/books/", "weekly", "0.8"),
                 (SITE + "/situations/", "weekly", "0.8")]
    book_urls += [(SITE + sit_url(s), "monthly", "0.6") for s in sit_labels]
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
        if "ir-slug-redirect" not in t and "</body>" in t:
            t = t.replace("</body>", SLUG_SCRIPT + "</body>", 1)
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(t)
            print("404: injected wrong-slug redirect into %s" % rel)
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
