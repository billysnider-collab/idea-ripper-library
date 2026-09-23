#!/usr/bin/env python3
"""Remove the splash (floaters hero) from build_site.py — one-shot."""
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_site.py")
s = open(P, encoding="utf-8").read()

def cut(start_anchor, end_anchor, inclusive_end=True, name=""):
    global s
    i = s.find(start_anchor)
    assert i != -1, "start not found: " + name
    j = s.find(end_anchor, i)
    assert j != -1, "end not found: " + name
    j_end = j + len(end_anchor) if inclusive_end else j
    s = s[:i] + s[j_end:]
    print("cut:", name or start_anchor[:40])

# 1) floaters_json computation (keep _ordered/_n stamping above it)
i = s.find("floaters_json = json.dumps(")
assert i != -1
j = s.find("ensure_ascii=False)", i)
assert j != -1
k = s.find("\n", j)
s = s[:i] + s[k + 1:]
print("cut: floaters_json block")

# 2) splash + floater CSS
cut("#splash{position:relative;",
    "@media (prefers-reduced-motion:reduce){.floater{animation:none}}",
    name="splash CSS")
# eat the trailing newline left behind
s = s.replace("@media (prefers-reduced-motion:reduce){.floater{animation:none}}\n",
              "@media (prefers-reduced-motion:reduce){.floater{animation:none}}")

for mq in ["@media (max-width:700px){.floater{display:none}}\n",
           "@media (max-height:500px){.floater{display:none}}\n",
           "@media (min-width:701px) and (max-width:900px){.floater{max-width:180px;font-size:.72rem}}\n"]:
    assert mq in s, "mq missing: " + mq[:30]
    s = s.replace(mq, "")
print("cut: floater media queries")

# 3) floater JS block + dive handler
i = s.find("var field=document.getElementById('floatfield');")
assert i != -1
j = s.find("var dive=document.getElementById('dive');")
assert j != -1
s = s[:i] + s[j:]
print("cut: floater JS")
i = s.find("var dive=document.getElementById('dive');")
j = s.find("\n", s.find("scrollIntoView", i))
s = s[:i] + s[j + 1:]
print("cut: dive handler")

# 4) splash HTML section
cut('<section id="splash">', "</section>", name="splash HTML")

# 5) FLOATERS script tag + tuple arg
tag = "<script>var FLOATERS=%s;</script>\n"
assert tag in s
s = s.replace(tag, "")
print("cut: FLOATERS script tag")
old_tuple = "fb_footer, floaters_json, JS)"
assert old_tuple in s
s = s.replace(old_tuple, "fb_footer, JS)")
print("cut: tuple arg")

open(P, "w", encoding="utf-8").write(s)
print("done")
