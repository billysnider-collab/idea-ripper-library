#!/usr/bin/env python3
"""P1 compiler: books/*.md + shelf.yaml -> cards.json.

Source of truth is the per-book markdown files plus shelf.yaml.
cards.json is a build artifact. Run: python3 compile.py

Rules (P0 freeze holds):
- Every card has a permanent int id. Existing ids are NEVER changed.
- Cards without an id get max(id)+1, in shelf order then file order.
- New ids are written back into the book md files so the next compile is stable.
"""
import json
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
BOOKS_DIR = os.path.join(HERE, "books")
SHELF = os.path.join(HERE, "shelf.yaml")
CARDS_JSON = os.path.join(HERE, "cards.json")

BODY_SECTIONS = (("steal", "Steal"), ("why", "Why it matters"), ("uw", "Use when"))
DEFAULT_ORDER = ["title", "book", "type", "steal", "why", "uw", "id"]
HEADING_BY_FIELD = dict(BODY_SECTIONS)


def slugify(book_key):
    s = book_key.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "book"


def load_shelf():
    return yaml.safe_load(open(SHELF, encoding="utf-8"))


def save_shelf(shelf):
    with open(SHELF, "w", encoding="utf-8") as fh:
        yaml.safe_dump(shelf, fh, sort_keys=False, allow_unicode=True)


def jval(v):
    return json.dumps(v, ensure_ascii=False)


def parse_book_file(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise ValueError("%s: missing book frontmatter" % path)
    book_fm = yaml.safe_load(m.group(1)) or {}
    rest = text[m.end():]
    chunks = re.split(r"^--- card\s*$", rest, flags=re.M)
    cards = []
    for chunk in chunks[1:]:
        lines = chunk.split("\n")
        try:
            end = next(i for i, l in enumerate(lines) if l.strip() == "---")
        except StopIteration:
            raise ValueError("%s: card block missing closing ---" % path)
        fm = yaml.safe_load("\n".join(lines[:end])) or {}
        body = "\n".join(lines[end + 1:])
        parts = re.split(r"^## (.+?)\s*$", body, flags=re.M)
        sections = {}
        for i in range(1, len(parts), 2):
            sections[parts[i].strip()] = parts[i + 1].strip()
        cards.append((fm, sections))
    return book_fm, cards


def emit_card_block(fm, sections):
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
        if heading not in sections:
            raise ValueError("card %r missing section %s" % (fm.get("title"), heading))
        lines.append("## %s" % heading)
        lines.append("")
        lines.append(sections[heading])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def emit_book_file(book_fm, cards):
    lines = ["---"]
    for k in ("book", "genre", "bookline"):
        lines.append("%s: %s" % (k, jval(book_fm[k])))
    lines.append("---")
    lines.append("")
    for fm, sections in cards:
        lines.append(emit_card_block(fm, sections))
    return "\n".join(lines).rstrip() + "\n"


def build_card(fm, sections, book_key):
    fo = fm.get("field_order") or DEFAULT_ORDER
    card = {}
    for k in fo:
        if k == "book":
            card["book"] = book_key
        elif k in HEADING_BY_FIELD:
            heading = HEADING_BY_FIELD[k]
            if heading not in sections:
                raise ValueError("card %r missing section %s" % (fm.get("title"), heading))
            card[k] = sections[heading]
        elif k in fm:
            card[k] = fm[k]
        else:
            raise ValueError("card %r: field_order key %r not in frontmatter" % (fm.get("title"), k))
    if "id" not in card:
        raise ValueError("card %r has no id after assignment" % (fm.get("title"),))
    return card


def add_book(slug, book_key, genre, bookline):
    """Create books/<slug>.md scaffold + shelf entry. Idempotent on same book key."""
    shelf = load_shelf()
    for e in shelf["books"]:
        if e["key"] == slug:
            return slug
    base, i = slug, 2
    while os.path.exists(os.path.join(BOOKS_DIR, slug + ".md")):
        slug = "%s-%d" % (base, i)
        i += 1
    os.makedirs(BOOKS_DIR, exist_ok=True)
    book_fm = {"book": book_key, "genre": genre, "bookline": bookline}
    with open(os.path.join(BOOKS_DIR, slug + ".md"), "w", encoding="utf-8") as fh:
        fh.write(emit_book_file(book_fm, []))
    shelf["books"].append({"key": slug, "genre": genre, "bookline": bookline,
                          "field_order": ["book", "genre", "bookline"]})
    save_shelf(shelf)
    return slug


def add_card(slug, fields, sections):
    """Append one id-less card block to books/<slug>.md. fields: title/type/extras."""
    path = os.path.join(BOOKS_DIR, slug + ".md")
    book_fm, cards = parse_book_file(path)
    fm = dict(fields)
    fm.pop("id", None)
    fm.pop("field_order", None)
    cards.append((fm, sections))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(emit_book_file(book_fm, cards))


def shelf_book_keys(shelf):
    """key -> book frontmatter, for dedup lookups."""
    out = {}
    for e in shelf["books"]:
        book_fm, _ = parse_book_file(os.path.join(BOOKS_DIR, e["key"] + ".md"))
        out[e["key"]] = book_fm
    return out


def run():
    shelf = load_shelf()
    books_out = []
    # parse everything first
    parsed = {}
    for e in shelf["books"]:
        key = e["key"]
        path = os.path.join(BOOKS_DIR, key + ".md")
        if not os.path.exists(path):
            raise ValueError("shelf lists %s but %s is missing" % (key, path))
        book_fm, cards = parse_book_file(path)
        for k in ("book", "genre", "bookline"):
            if book_fm.get(k) != e.get(k) and k in e:
                raise ValueError("%s: md %s != shelf %s" % (key, k, k))
        if e["genre"] not in shelf["genre_order"]:
            raise ValueError("%s: bad genre %r" % (key, e["genre"]))
        parsed[key] = (book_fm, cards)

    # id assignment: existing ids are sacred; new cards get max+1
    have_ids = [fm["id"] for _, cards in parsed.values() for fm, _ in cards
                if isinstance(fm.get("id"), int)]
    if len(have_ids) != len(set(have_ids)):
        raise ValueError("duplicate card id in books/*.md")
    next_id = max(have_ids) + 1 if have_ids else 1
    dirty_files = set()
    new_ids = []
    for e in shelf["books"]:
        key = e["key"]
        book_fm, cards = parsed[key]
        for fm, _ in cards:
            if not isinstance(fm.get("id"), int):
                fm["id"] = next_id
                next_id += 1
                if "field_order" not in fm:
                    fo = list(DEFAULT_ORDER)
                    for k in fm.keys():
                        if k not in fo:
                            fo.append(k)
                    fm["field_order"] = fo
                new_ids.append(fm["id"])
                dirty_files.add(key)
    for key in dirty_files:
        book_fm, cards = parsed[key]
        with open(os.path.join(BOOKS_DIR, key + ".md"), "w", encoding="utf-8") as fh:
            fh.write(emit_book_file(book_fm, cards))
    if new_ids:
        shelf.setdefault("card_order", []).extend(new_ids)
        save_shelf(shelf)
    elif dirty_files:
        save_shelf(shelf)

    # build cards.json: books in shelf order, cards in shelf card_order
    books_out = []
    for e in shelf["books"]:
        book_fm = parsed[e["key"]][0]
        fo = e.get("field_order") or ["book", "genre", "bookline"]
        bvals = {"book": book_fm["book"], "genre": book_fm["genre"],
                 "bookline": book_fm["bookline"]}
        books_out.append({k: bvals[k] for k in fo})
    by_id = {}
    for key, (_, cards) in parsed.items():
        for fm, sections in cards:
            if fm["id"] in by_id:
                raise ValueError("duplicate id %r" % fm["id"])
            by_id[fm["id"]] = (key, fm, sections)
    cards_out = []
    in_order = set()
    for cid in shelf.get("card_order", []):
        if cid not in by_id:
            raise ValueError("shelf card_order lists id %r not found in books/*.md" % (cid,))
        key, fm, sections = by_id[cid]
        book_fm = parsed[key][0]
        cards_out.append(build_card(fm, sections, book_fm["book"]))
        in_order.add(cid)
    for key, (_, cards) in parsed.items():
        for fm, _ in cards:
            if fm["id"] not in in_order:
                raise ValueError("books/%s.md has id %r missing from shelf card_order"
                                 % (key, fm["id"]))

    ds = {"curated": shelf["curated"], "genre_order": shelf["genre_order"],
          "books": books_out, "cards": cards_out}
    with open(CARDS_JSON, "w", encoding="utf-8") as fh:
        json.dump(ds, fh, indent=1, ensure_ascii=False)
    print("compiled: %d books, %d cards -> cards.json" % (len(books_out), len(cards_out)))
    return ds


def main():
    run()


if __name__ == "__main__":
    main()
