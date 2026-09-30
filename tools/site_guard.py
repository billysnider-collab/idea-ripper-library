#!/usr/bin/env python3
"""Site guard for idearipper.com (added 2026-09-30).

Why: an automated "rip deploy" job keeps a cached copy of build_site.py and has
pushed stale copies over the repo (164ec42 reverted the 5d35385 reskin and two
bug fixes). This script is the tripwire the CI workflow runs on every push.

  python3 tools/site_guard.py check [--rev REV]   exit 1 if any guard fails
  python3 tools/site_guard.py last-good [--max N] print newest first-parent
                                                  ancestor of HEAD~1 that passes

Checks read index.html plus the external assets it references, and
build_site.py, either from the working tree or from a git revision.
Stdlib only.
"""
import hashlib, re, subprocess, sys, os

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


# (name, test(site, html, tpl_bytes) -> bool). Add a line per guarded fix.
def _tpl_hash(tpl):
    return hashlib.sha256(tpl.replace(b"\r\n", b"\n")).hexdigest()[:12]


GUARDS = [
    ("no Google Fonts hotlinks", lambda s, h, t: "fonts.googleapis" not in s and "fonts.gstatic" not in s),
    ("color-scheme light meta", lambda s, h, t: '<meta name="color-scheme" content="light"' in h),
    ("lazy #toast lookup (Save/Copy fix)", lambda s, h, t: "toastEl=toastEl||document.getElementById('toast')" in s),
    ("minmax(0,1fr) 2-col grid (desktop overflow fix)", lambda s, h, t: "grid-template-columns:minmax(0,1fr) minmax(0,1fr)" in s),
    ("build marker matches committed build_site.py", lambda s, h, t: t is not None and
        ('<meta name="build" content="tpl-%s' % _tpl_hash(t)) in h),
]
# Guards added with later fixes live in this list so a stale template trips them too.
GUARDS += [
    ("oxblood paper tokens", lambda s, h, t: "--paper:#F5EFE3" in s and "--accent:#A03B2A" in s),
    ("phone overflow: .shlist .sht min-width:0", lambda s, h, t: ".shlist .sht{font-weight:600;min-width:0" in s and ".bookline,.bauthor{overflow-wrap:anywhere}" in s),
    ("canonical + WebSite JSON-LD", lambda s, h, t: '<link rel="canonical" href="https://idearipper.com/"' in h and '"@type":"SearchAction"' in h),
    ("search: AND + stemmed prefix", lambda s, h, t: "function qStems(term)" in s and "searchMode='any'" in s),
    ("perf: content-visibility on .book", lambda s, h, t: ".book,.fbook{content-visibility:auto" in s),
    ("perf: CSS rip mark (no inline SVGs)", lambda s, h, t: 'class="ripmark"' not in h and ".kicker::before,.fkicker::before" in s),
    ("perf: no duplicated data-search text", lambda s, h, t: "data-search=" not in h and "var _stext={}" in s),
    ("perf: external hashed CSS/JS", lambda s, h, t: bool(re.search(r'href="assets/site\.[0-9a-f]{10}\.css"', h)) and bool(re.search(r'src="assets/app\.[0-9a-f]{10}\.js"', h))),
    ("Save persists before toast", lambda s, h, t: "setSaved(s);syncSaveButtons();renderSaved();\n    toast(" in s),
]


def check(rev=None, quiet=False):
    site, missing = site_text(rev)
    if site is None:
        if not quiet:
            print("FAIL index.html missing")
        return False
    html = _read("index.html", rev).decode("utf-8", "replace")
    tpl = _read("build_site.py", rev)
    ok = True
    if missing:
        ok = False
        if not quiet:
            print("FAIL referenced assets missing: %s" % ", ".join(missing))
    for name, fn in GUARDS:
        try:
            r = bool(fn(site, html, tpl))
        except Exception as e:  # a guard that crashes is a failed guard
            r = False
        ok &= r
        if not quiet:
            print("%s %s" % ("ok  " if r else "FAIL", name))
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
