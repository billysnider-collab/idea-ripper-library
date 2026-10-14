#!/usr/bin/env python3
"""Slug gate for the Idea Ripper redesign (Phase 1, 2026-10-14).

Gate order: compile -> verify_ids -> verify_slugs -> build pages.
Fails if: a card has no slug, a slug is duplicated or malformed, a lock id
disappeared without a tombstone, or a committed slug changed. Generation is
NOT done here (pure check): run `python3 build_pages.py --ensure-slugs`
first to append lock entries for new cards.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import slugs as slugs_lib


def main():
    ds = json.load(open(os.path.join(HERE, "cards.json"), encoding="utf-8"))
    cards = ds["cards"]
    fails = slugs_lib.verify(cards)
    if fails:
        for f in fails[:40]:
            print("FAIL: " + f)
        if len(fails) > 40:
            print("... and %d more" % (len(fails) - 40))
        sys.exit(1)
    lock = slugs_lib.load_lock()
    print("slugs OK: %d cards, %d locked slugs, %d tombstones"
          % (len(cards), len(lock["slugs"]), len(lock["tombstones"])))


if __name__ == "__main__":
    main()
