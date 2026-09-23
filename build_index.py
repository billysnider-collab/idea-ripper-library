#!/usr/bin/env python3
"""Validator for the Ten Cool Keepers page (2026-09-22).

The library is now Billy's hand-curated keepers list, not a generated
book index. New keepers are appended as <article class="card"> blocks in
index.html (copy the existing pattern, keep the numbering sequential).
This script only verifies the page: card count, sequential numbering,
and that every card has a title, source, steal, and use-when.
"""
import re, os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")

def main():
    t = open(P, encoding="utf-8").read()
    cards = re.findall(r'<article class="card">(.*?)</article>', t, re.S)
    nums = re.findall(r'<span class="num">(\d+)</span>', t)
    assert [int(n) for n in nums] == list(range(1, len(cards) + 1)), "numbering broken: %s" % nums
    for i, c in enumerate(cards, 1):
        for part in ("<h3>", 'class="src"', 'class="steal"', 'class="uw"'):
            assert part in c, "card %d missing %s" % (i, part)
    print("keepers page OK: %d cards, numbered 1-%d" % (len(cards), len(cards)))

if __name__ == "__main__":
    main()
