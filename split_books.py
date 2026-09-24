#!/usr/bin/env python3
"""One-shot P1 splitter: cards.json -> books/*.md + shelf.yaml.

Run once from the lib dir. After this, books/*.md + shelf.yaml are the
source of truth; cards.json is a build artifact produced by compile.py.

Safety: refuses to overwrite an existing books/ dir unless --force.
"""
import json
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
CARDS_JSON = os.path.join(HERE, "cards.json")
BOOKS_DIR = os.path.join(HERE, "books")
SHELF = os.path.join(HERE, "shelf.yaml")

BODY_SECTIONS = (("steal", "Steal"), ("why", "Why it matters"), ("uw", "Use when"))


def slugify(book_key):
    s = book_key.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "book"


def jval(v):
    """Emit a frontmatter value as JSON (quoted strings stay strings on load)."""
    return json.dumps(v, ensure_ascii=False)


def emit_card_block(fm, sections):
    """fm: dict with id, title, field_order + extra keys. sections: {Steal, Why it matters, Use when}."""
    ordered = {}
    for k in ("id", "title", "field_order"):
        if k in fm:
            ordered[k] = fm[k]
    for k, v in fm.items():
        if k not in ordered:
            ordered[k] = v
    lines = ["--- card"]
    for k, v in ordered.items():
        lines.append("%s: %s" % (k, jval(v)))
    lines.append("---")
    for field, heading in BODY_SECTIONS:
        lines.append("## %s" % heading)
        lines.append("")
        lines.append(sections[heading])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main():
    force = "--force" in sys.argv
    ds = json.load(open(CARDS_JSON, encoding="utf-8"))
    books, cards, genre_order = ds["books"], ds["cards"], ds["genre_order"]

    if os.path.exists(BOOKS_DIR) and not force:
        sys.exit("books/ exists; pass --force to re-split")
    os.makedirs(BOOKS_DIR, exist_ok=True)

    # guard: no body text may contain our delimiters
    for c in cards:
        for field, heading in BODY_SECTIONS:
            for line in c[field].split("\n"):
                s = line.strip()
                assert s != "---", "card %r has --- line" % c.get("title")
                assert not line.startswith("## "), "card %r has ## line" % c.get("title")
                assert not line.startswith("--- card"), "card %r has --- card line" % c.get("title")

    cards_by_book = {}
    for c in cards:
        cards_by_book.setdefault(c["book"], []).append(c)

    seen_slugs = {}
    shelf_books = []
    card_order = [c["id"] for c in cards]
    for b in books:
        slug = slugify(b["book"])
        if slug in seen_slugs:
            i = 2
            while "%s-%d" % (slug, i) in seen_slugs:
                i += 1
            slug = "%s-%d" % (slug, i)
        seen_slugs[slug] = b["book"]

        clines = ["---"]
        clines.append("book: %s" % jval(b["book"]))
        clines.append("genre: %s" % jval(b["genre"]))
        clines.append("bookline: %s" % jval(b["bookline"]))
        clines.append("---")
        clines.append("")
        for c in cards_by_book.get(b["book"], []):
            fm = {}
            for k in ("id", "title"):
                fm[k] = c[k]
            fm["field_order"] = list(c.keys())
            for k in c.keys():
                if k not in ("book", "steal", "why", "uw", "id", "title"):
                    fm[k] = c[k]
            sections = {"Steal": c["steal"], "Why it matters": c["why"], "Use when": c["uw"]}
            clines.append(emit_card_block(fm, sections))
        path = os.path.join(BOOKS_DIR, slug + ".md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(clines).rstrip() + "\n")
        shelf_books.append({"key": slug, "genre": b["genre"],
                            "bookline": b["bookline"],
                            "field_order": list(b.keys())})

    shelf = {"curated": ds["curated"], "genre_order": genre_order,
             "books": shelf_books, "card_order": card_order}
    with open(SHELF, "w", encoding="utf-8") as fh:
        yaml.safe_dump(shelf, fh, sort_keys=False, allow_unicode=True)

    print("split: %d books -> books/, shelf.yaml (%d cards)" % (len(books), len(cards)))


if __name__ == "__main__":
    main()
