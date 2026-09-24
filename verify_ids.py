#!/usr/bin/env python3
"""P0 golden test (2026-09-24): card ids are permanent.
Fails if an existing id was remapped, dropped, or had its book/title changed.
New ids (max+1 appends) are fine. Run after any cards.json edit, before build.
"""
import json, os, sys
BASE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(BASE, "cards.json"), encoding="utf-8"))
cards = d["cards"]
ids = [c.get("id") for c in cards]
assert all(isinstance(i, int) for i in ids), "FAIL: card missing int id"
assert len(ids) == len(set(ids)), "FAIL: duplicate card id"
idset = set(ids)
for c in cards:
    for r in c.get("related_ids", []):
        assert r in idset, f"FAIL: card {c['id']} references missing id {r}"
golden = json.load(open(os.path.join(BASE, ".card_id_golden.json"), encoding="utf-8"))
for gid, (book, title) in golden.items():
    cur = next((c for c in cards if c["id"] == int(gid)), None)
    assert cur is not None, f"FAIL: golden id {gid} is gone"
    assert [cur["book"], cur["title"]] == [book, title], f"FAIL: id {gid} remapped/changed"
print(f"ids OK: {len(cards)} cards, {len(golden)} golden ids intact, related refs valid")
