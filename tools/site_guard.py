#!/usr/bin/env python3
"""Site guard for idearipper.com (added 2026-09-30; guards rewritten for the
Archive Paper homepage, 2026-10-14).

Why: an automated "rip deploy" job keeps cached copies of the builders and
has pushed stale copies over the repo (164ec42 reverted the 5d35385 reskin
and two bug fixes). This script is the tripwire the CI workflow runs on
every push.

  python3 tools/site_guard.py check [--rev REV]   exit 1 if any guard fails
  python3 tools/site_guard.py last-good [--max N] print newest first-parent
                                                  ancestor of HEAD~1 that passes

Checks read index.html plus the external assets it references, and
build_pages.py, either from the working tree or from a git revision. The
data invariants (search index / card pages / stubs / sitemap) only run
against the working tree, where the built files exist.
Stdlib only.

Redesign note (2026-10-14): the homepage is now emitted by build_pages.py
(Phase 1 redesign). Guards welded to the retired build_site.py hunt-layer
homepage (toast, flushInitialScroll, _stext, hashed app/site assets, ...) were
replaced with guards on the new structure — marker, tokens, hash redirect,
command bar — plus data invariants the old guard never had. Nothing was
relaxed: deep links, search, canonical and the light-only rule are all
still guarded.
"""
import hashlib, json, re, subprocess, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(path, rev=None):
    if rev is None:
        p = os.path.join(ROOT, path)
        if not os.path.exists(p):
            return None
        with open(p, "rb") as f:
            return f.read()
    try:
        return subprocess.run(["git", "-C", ROOT, "show", "%s:%s" % (rev, path)],
                              check=True, capture_output=True).stdout
    except subprocess.CalledProcessError:
        return None


def site_text(rev=None):
    """index.html + every local assets/*.css|js it references (query string stripped)."""
    idx = _read("index.html", rev)
    if idx is None:
        return None, []
    html = idx.decode("utf-8", "replace")
    parts, missing = [html], []
    for ref in re.findall(r'(?:href|src)="/?(assets/[^"?#]+\.(?:css|js))(?:\?[^"]*)?"', html):
        b = _read(ref, rev)
        if b is None:
            missing.append(ref)
        else:
            parts.append(b.decode("utf-8", "replace"))
    return "\n".join(parts), missing


def _tpl_hash(tpl):
    return hashlib.sha256(tpl.replace(b"\r\n", b"\n")).hexdigest()[:12]


# (name, test(site, html, tpl_bytes) -> bool). tpl_bytes is build_pages.py.
GUARDS = [
    ("no Google Fonts hotlinks", lambda s, h, t: "fonts.googleapis" not in s and "fonts.gstatic" not in s),
    ("color-scheme light meta", lambda s, h, t: '<meta name="color-scheme" content="light"' in h),
    ("build marker matches build_pages.py", lambda s, h, t: t is not None and
        ('<meta name="build" content="pages-%s' % _tpl_hash(t)) in h),
    ("archive paper tokens", lambda s, h, t: "--bg-canvas:#F4F1EA" in s and "--bg-card:#FAF8F5" in s and "--accent-signal:#C83E2B" in s),
    ("zero border-radius rule", lambda s, h, t: "border-radius:0" in s),
    ("hashed paper stylesheet referenced", lambda s, h, t: bool(re.search(r'href="/assets/paper\.[0-9a-f]{10}\.css"', h))),
    ("#cN hash redirect on homepage", lambda s, h, t: "ir-hash-redirect" in h and "location.replace" in h),
    ("command bar wired to /search-index.json", lambda s, h, t: 'id="commandbar"' in h and 'id="cb-input"' in h and 'fetch("/search-index.json")' in s),
    ("random card button present", lambda s, h, t: "randomcard" in h),
    ("canonical + WebSite JSON-LD", lambda s, h, t: '<link rel="canonical" href="https://idearipper.com/"' in h and '"@type":"WebSite"' in h),
    ("/dark preview page still present", lambda s, h, t: _read(os.path.join("dark", "index.html")) is not None),
]


def _slug_of():
    p = os.path.join(ROOT, "slugs.lock.json")
    if not os.path.exists(p):
        return {}
    return json.load(open(p, encoding="utf-8")).get("slugs", {})


def data_checks(quiet=False):
    """Working-tree invariants over the Phase 1 outputs."""
    ok = True

    def rep(name, good):
        nonlocal ok
        ok &= bool(good)
        if not quiet:
            print("%s %s" % ("ok  " if good else "FAIL", name))

    cards_b = _read("cards.json")
    idx_b = _read("search-index.json")
    if cards_b is None or idx_b is None:
        rep("cards.json + search-index.json present", False)
        return False
    cards = json.loads(cards_b)["cards"]
    entries = json.loads(idx_b)
    rips = [e for e in entries if isinstance(e, dict) and isinstance(e.get("i"), int)]
    rep("search-index rip count == card count (%d)" % len(cards), len(rips) == len(cards))
    slugs = _slug_of()
    rep("slugs.lock.json covers every card", len(slugs) >= len(cards))
    miss_page = miss_stub = 0
    for c in cards:
        cid = c["id"]
        slug = slugs.get(str(cid))
        if not slug or not os.path.exists(os.path.join(ROOT, "c", "%d-%s" % (cid, slug), "index.html")):
            miss_page += 1
        sp = os.path.join(ROOT, "c", str(cid), "index.html")
        if not os.path.exists(sp):
            miss_stub += 1
    rep("every card has a canonical page", miss_page == 0)
    rep("every card has a redirect stub", miss_stub == 0)
    sm = _read("sitemap-cards.xml")
    nloc = sm.decode("utf-8", "replace").count("<loc>") if sm else 0
    rep("sitemap-cards.xml lists exactly the cards (%d)" % len(cards), nloc == len(cards))
    smi = _read("sitemap.xml")
    rep("sitemap.xml is an index over cards+books segments",
        bool(smi) and "sitemap-cards.xml" in smi.decode("utf-8", "replace")
        and "sitemap-books.xml" in smi.decode("utf-8", "replace"))
    led = _read(os.path.join("ledger", "index.html"))
    rep("ledger page present", led is not None and b'class="ledger"' in led)
    f404 = _read("404.html")
    rep("#cN hash redirect on 404.html", f404 is not None and b"ir-hash-redirect" in f404)
    return ok


def check(rev=None, quiet=False):
    site, missing = site_text(rev)
    if site is None:
        if not quiet:
            print("FAIL index.html missing")
        return False
    html = _read("index.html", rev).decode("utf-8", "replace")
    tpl = _read("build_pages.py", rev)
    ok = True
    if missing:
        ok = False
        if not quiet:
            print("FAIL referenced assets missing: %s" % ", ".join(missing))
    for name, fn in GUARDS:
        try:
            r = bool(fn(site, html, tpl))
        except Exception:
            r = False
        ok &= r
        if not quiet:
            print("%s %s" % ("ok  " if r else "FAIL", name))
    if rev is None:
        ok &= data_checks(quiet)
    return ok


def last_good(maxn=80):
    revs = subprocess.run(["git", "-C", ROOT, "rev-list", "--first-parent", "-n", str(maxn), "HEAD~1"],
                          check=True, capture_output=True, text=True).stdout.split()
    for r in revs:
        if check(r, quiet=True):
            return r
    return None


if __name__ == "__main__":
    a = sys.argv[1:]
    rev = a[a.index("--rev") + 1] if "--rev" in a else None
    if a and a[0] == "last-good":
        g = last_good()
        if not g:
            print("no passing ancestor found", file=sys.stderr)
            sys.exit(1)
        print(g)
    else:
        sys.exit(0 if check(rev) else 1)
