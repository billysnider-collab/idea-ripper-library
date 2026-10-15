#!/usr/bin/env python3
"""Seed/refresh book_dates.json: the date (America/Chicago) each book first
appeared in cards.json, from git history. Needs a full (non-shallow) clone.
Existing entries are never changed; build_pages.py stamps brand-new books
with the build date."""
import json, subprocess, os, datetime
from zoneinfo import ZoneInfo
os.chdir(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
TZ = ZoneInfo("America/Chicago")
try:
    dates = json.load(open("book_dates.json"))
except FileNotFoundError:
    dates = {}
log = subprocess.check_output(["git", "log", "--reverse", "--format=%H %ct", "--", "cards.json"], text=True).split("\n")
for line in filter(None, log):
    sha, ts = line.split()
    try:
        d = json.loads(subprocess.check_output(["git", "show", "%s:cards.json" % sha], stderr=subprocess.DEVNULL))
    except Exception:
        continue
    day = datetime.datetime.fromtimestamp(int(ts), TZ).strftime("%Y-%m-%d")
    cards = d.get("cards", d) if isinstance(d, dict) else d
    for c in cards if isinstance(cards, list) else []:
        b = c.get("book") if isinstance(c, dict) else None
        if b and b not in dates:
            dates[b] = day
json.dump(dict(sorted(dates.items())), open("book_dates.json", "w"), indent=1, ensure_ascii=False)
print(len(dates), "books dated")
