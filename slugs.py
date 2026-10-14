#!/usr/bin/env python3
"""Slug lock for Idea Ripper card pages (redesign Phase 1, 2026-10-14).

Card ids are permanent (P0 freeze); slugs join them. Each card gets exactly
one slug, generated ONCE from its title (4-6 content words), written to
slugs.lock.json in the lib root, and never regenerated or changed afterwards
(a copy edit to books/*.md must never move a URL). Deliberate renames are
out of band: move the old slug to "tombstones" here and emit a redirect.

Lock shape:
  {"version": 1,
   "slugs":     {"<card id>": "<slug>", ...},
   "tombstones": {"<card id>": "<retired slug>", ...}}

Used by verify_slugs.py (pure gate) and build_pages.py (generation + build).
"""
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
LOCK_PATH = os.path.join(HERE, "slugs.lock.json")
CARDS_JSON = os.path.join(HERE, "cards.json")

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
STOPWORDS = {
    "a", "an", "the", "of", "to", "in", "on", "for", "and", "or", "vs",
    "with", "from", "how", "why", "what", "when", "is", "it", "as", "at",
    "by", "into", "over", "under", "about", "after", "before",
}


def load_lock(path=LOCK_PATH):
    if not os.path.exists(path):
        return {"version": 1, "slugs": {}, "tombstones": {}}
    with open(path, encoding="utf-8") as fh:
        lock = json.load(fh)
    lock.setdefault("version", 1)
    lock.setdefault("slugs", {})
    lock.setdefault("tombstones", {})
    return lock


def save_lock(lock, path=LOCK_PATH):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(lock, fh, indent=1, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, path)


def derive_slug(card, taken):
    """Deterministic 4-6 word slug from the card title (fallback: use-when).

    `taken` maps slug -> id for slugs already claimed; a collision gets a
    one-time "-<id>" suffix so the result is unique. Generation happens once;
    the lock is the record, so this function never re-runs for a locked card.
    """
    def words(text):
        out = []
        for w in re.findall(r"[a-z0-9]+", (text or "").lower()):
            if w not in STOPWORDS and len(w) > 1:
                out.append(w)
        return out

    ws = words(card.get("title"))
    if len(ws) < 3:
        ws = ws + [w for w in words(card.get("uw")) if w not in ws]
    slug = "-".join(ws[:5]) or "rip"
    if len(slug) > 64:
        slug = slug[:64].rsplit("-", 1)[0]
    if taken.get(slug, card["id"]) != card["id"]:
        slug = "%s-%d" % (slug, card["id"])
    return slug


def ensure_slugs(cards, path=LOCK_PATH):
    """Append lock entries for cards that lack one. Returns (lock, added ids).

    Iterates in ascending id order so generation is deterministic. Existing
    entries are NEVER modified.
    """
    lock = load_lock(path)
    slugs = lock["slugs"]
    taken = {s: int(i) for i, s in slugs.items()}
    taken.update({s: int(i) for i, s in lock["tombstones"].items()})
    added = []
    for card in sorted(cards, key=lambda c: c["id"]):
        cid = str(card["id"])
        if cid in slugs:
            continue
        slug = derive_slug(card, taken)
        slugs[cid] = slug
        taken[slug] = card["id"]
        added.append(card["id"])
    if added:
        save_lock(lock, path)
    return lock, added


def _head_lock(path=LOCK_PATH):
    """The slugs.lock.json committed at HEAD, or None if not committed yet."""
    try:
        out = subprocess.run(
            ["git", "-C", HERE, "show", "HEAD:slugs.lock.json"],
            capture_output=True, text=True, timeout=20)
        if out.returncode != 0:
            return None
        return json.loads(out.stdout)
    except Exception:
        return None


def verify(cards, path=LOCK_PATH):
    """Gate checks. Returns a list of failure strings (empty == pass)."""
    fails = []
    if not os.path.exists(path):
        return ["slugs.lock.json missing (run: python3 build_pages.py --ensure-slugs)"]
    lock = load_lock(path)
    slugs = lock["slugs"]
    tombs = lock["tombstones"]
    card_ids = {c["id"] for c in cards}

    for cid in sorted(card_ids):
        if str(cid) not in slugs:
            fails.append("card %d has no slug" % cid)
    seen = {}
    for sid, slug in slugs.items():
        if not SLUG_RE.match(slug or "") or not (3 <= len(slug) <= 72):
            fails.append("bad slug format for id %s: %r" % (sid, slug))
        if slug in seen:
            fails.append("duplicate slug %r for ids %s and %s" % (slug, seen[slug], sid))
        seen[slug] = sid
        if sid in tombs:
            fails.append("id %s is both live and tombstoned" % sid)
    for sid in slugs:
        if int(sid) not in card_ids:
            fails.append("lock id %s has no card and is not a tombstone" % sid)
    for sid, slug in tombs.items():
        if slug in seen:
            fails.append("tombstoned slug %r still in use by id %s" % (slug, seen[slug]))

    head = _head_lock(path)
    if head is None:
        print("note: slugs.lock.json not committed at HEAD yet; "
              "immutability-vs-HEAD check skipped")
    else:
        hslugs = head.get("slugs", {})
        for sid, slug in hslugs.items():
            if sid in slugs and slugs[sid] != slug:
                fails.append("slug for id %s changed: %r -> %r" % (sid, slug, slugs[sid]))
            if sid not in slugs and sid not in tombs:
                fails.append("slug for id %s vanished without a tombstone" % sid)
    return fails
