#!/usr/bin/env python3
"""Validator for the Cool Keepers hunt-layer page (2026-09-22).

Dataset lives in cards.json; build_site.py renders index.html from it.
This script verifies both: the dataset (all four grounded fields on every
card, every book has genre + one bookline) and the rendered page
(sequential numbering, genre sections, one book header per book with the
blurb, sticky controls, copy buttons, trust footer).
"""
import re, os, json, html

HERE = os.path.dirname(os.path.abspath(__file__))

def main():
    ds = json.load(open(os.path.join(HERE, "cards.json"), encoding="utf-8"))
    cards, books = ds["cards"], ds["books"]
    nc, nbk = len(cards), len(books)
    assert nc > 0 and nbk > 0
    for c in cards:
        for f in ("title", "steal", "why", "uw"):
            assert c.get(f) and c[f].strip(), "card missing %s: %r" % (f, c.get("title"))
    bnames = [b["book"] for b in books]
    for c in cards:
        assert c["book"] in bnames, "unknown book " + c["book"]
    for b in books:
        assert b["genre"] in ds["genre_order"], "bad genre " + b["genre"]
        assert b["bookline"].strip(), "empty bookline " + b["book"]

    t = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
    found = re.findall(r'<article class="card(?:"| )', t)
    assert len(found) == nc, "page has %d cards, dataset has %d" % (len(found), nc)
    nums = re.findall(r'<span class="num">(\d+)</span>', t)
    assert [int(n) for n in nums] == list(range(1, nc + 1)), "numbering broken"
    for g in ds["genre_order"]:
        assert ('<h2 class="genre" data-genre="%s">' % html.escape(g, quote=True)) in t, "missing genre " + g
    for b in books:
        assert t.count('data-book="%s"' % html.escape(b["book"], quote=True)) >= 1, "missing book block " + b["book"]
        assert html.escape(b["bookline"], quote=False) in t, "missing bookline " + b["book"]
    for part in ('id="q"', 'id="fgenre"', 'id="fbook"', 'id="ftype"',
                 'id="expand"', 'id="collapse"', 'data-copy="steal"',
                 'data-copy="uw"', 'data-copy="link"', "Last curated", 'id="splash"',
                 'id="floatfield"', 'id="dive"', 'id="jumpchips"',
                 'id="noresults"', 'id="toast"', 'id="intro"', 'class="book collapsed"',
                 'class="pv"'):
        assert part in t, "page missing " + part
    # each rendered card keeps the grounded fields
    bodies = re.findall(r'<article class="card".*?</article>', t, re.S)
    for i, c in enumerate(bodies, 1):
        for part in ('class="cardhead"', 'class="cardbody"', 'class="steal"',
                     'class="why"', 'class="uw"'):
            assert part in c, "card %d missing %s" % (i, part)
    print("keepers page OK: %d cards, %d books, %d genres, numbered 1-%d"
          % (nc, nbk, len(ds["genre_order"]), nc))

if __name__ == "__main__":
    main()
