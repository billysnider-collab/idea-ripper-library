#!/usr/bin/env python3
"""Build the Cool Keepers hunt-layer page from cards.json.

Design: deduped book blurbs (once per book header), sticky search/filter bar,
collapsed cards (scan layer), book color chips, copy buttons, trust footer.
"""
import json, html, os

BASE = os.path.dirname(os.path.abspath(__file__))

def esc(s):
    return html.escape(s, quote=False)

def esca(s):
    return html.escape(s, quote=True)

ds = json.load(open(os.path.join(BASE, "cards.json"), encoding="utf-8"))
books = ds["books"]            # ordered by first appearance
cards = ds["cards"]
genre_order = ds["genre_order"]
curated = ds.get("curated", "")

# validation: every card has all four fields; every book has genre + blurb
for c in cards:
    for f in ("title", "steal", "why", "uw"):
        assert c.get(f) and c[f].strip(), "missing field %s in %r" % (f, c.get("title"))
bookset = {b["book"] for b in books}
for c in cards:
    assert c["book"] in bookset, "unknown book " + c["book"]
for b in books:
    assert b["genre"] in genre_order and b["bookline"].strip()

# book colors: deterministic hue rotation
hues = {}
for i, b in enumerate(books):
    hues[b["book"]] = (i * 47) % 360

types = sorted({c["type"] for c in cards})
n = len(cards)

def book_block(b):
    hue = hues[b["book"]]
    bcards = [c for c in cards if c["book"] == b["book"]]
    parts = ['<div class="book" data-book="%s" data-genre="%s">' % (esca(b["book"]), esca(b["genre"]))]
    parts.append('<div class="bookhead"><span class="chip" style="background:hsl(%d,45%%,55%%)"></span>'
                 '<span class="btitle">%s</span><span class="bcount">%d</span></div>'
                 % (hue, esc(b["book"]), len(bcards)))
    parts.append('<p class="bookline">%s</p>' % esc(b["bookline"]))
    for c in bcards:
        search = " ".join([c["title"], c["steal"], c["why"], c["uw"]]).lower()
        parts.append(
            '<article class="card" style="border-left-color:hsl(%d,45%%,55%%)" '
            'data-book="%s" data-genre="%s" data-type="%s" data-search="%s">'
            '<div class="cardhead" role="button" tabindex="0">'
            '<span class="num">%d</span><span class="ctitle">%s</span>'
            '<span class="pill %s">%s</span></div>'
            '<div class="cardbody">'
            '<p class="steal">%s</p>'
            '<p class="why"><span class="k">Why it matters:</span> %s</p>'
            '<p class="uw">%s</p>'
            '<div class="actions"><button type="button" data-copy="steal">Copy steal</button>'
            '<button type="button" data-copy="uw">Copy use-when</button></div>'
            '</div></article>'
            % (hue, esca(c["book"]), esca(b["genre"]), esca(c["type"]), esca(search),
               0, esc(c["title"]), esca(c["type"]), esc(c["type"]),
               esc(c["steal"]), esc(c["why"]), esc(c["uw"])))
    parts.append('</div>')
    return "\n".join(parts)

# number cards globally in render order
html_cards = []
counter = [0]
def numbered_block(b):
    s = book_block(b)
    def repl(m):
        counter[0] += 1
        return '<span class="num">%d</span>' % counter[0]
    return re.sub(r'<span class="num">0</span>', repl, s)

import re
genre_of = {b["book"]: b["genre"] for b in books}
sections = []
for g in genre_order:
    gbooks = [b for b in books if b["genre"] == g]
    if not gbooks:
        continue
    gcount = sum(1 for c in cards if genre_of[c["book"]] == g)
    sections.append('<h2 class="genre" data-genre="%s">%s <span class="gcount">%d cards · %d books</span></h2>'
                    % (esca(g), esc(g), gcount, len(gbooks)))
    for b in gbooks:
        sections.append(numbered_block(b))

genre_opts = "\n".join('<option value="%s">%s</option>' % (esca(g), esc(g)) for g in genre_order)
book_opts = "\n".join('<option value="%s">%s</option>' % (esca(b["book"]), esc(b["book"])) for b in books)
type_opts = "\n".join('<option value="%s">%s</option>' % (esca(t2), esc(t2)) for t2 in types)

CSS = """
:root{--bg:#0b1220;--panel:#121a2b;--fg:#f3f0e8;--muted:#8b97ad;--amber:#e8a54b;--border:#243049}
*{box-sizing:border-box}body{margin:0;font-family:"Segoe UI",system-ui,sans-serif;background:var(--bg);color:var(--fg);line-height:1.45}
header{padding:1.5rem 1.5rem 1rem;max-width:920px;margin:0 auto}
header h1{margin:0;font-size:1.7rem;font-weight:700}
.job{color:var(--fg);font-size:1.05rem;margin:.3rem 0 .3rem}
.purpose{color:var(--muted);font-size:.9rem;margin:0 0 .4rem;max-width:60rem}
.meta{color:var(--muted);font-size:.85rem;margin:0}
.controls{position:sticky;top:0;z-index:20;background:var(--bg);border-bottom:1px solid var(--border);padding:.6rem 0}
.controls .inner{max-width:920px;margin:0 auto;padding:0 1.25rem;display:flex;gap:.5rem;flex-wrap:wrap;align-items:center}
.controls input[type=search]{flex:1 1 200px;background:var(--panel);border:1px solid var(--border);color:var(--fg);border-radius:8px;padding:.45rem .7rem;font-size:.9rem}
.controls select{background:var(--panel);border:1px solid var(--border);color:var(--fg);border-radius:8px;padding:.45rem .5rem;font-size:.85rem;max-width:11rem}
.controls button{background:transparent;border:1px solid var(--border);color:var(--muted);border-radius:8px;padding:.4rem .7rem;font-size:.85rem;cursor:pointer}
.controls button:hover{color:var(--fg);border-color:var(--amber)}
.count{color:var(--muted);font-size:.85rem;margin-left:auto}
main{max-width:920px;margin:0 auto;padding:1rem 1.25rem 3rem}
.genre{margin:2rem 0 .8rem;font-size:1.15rem;color:var(--amber);border-bottom:1px solid var(--border);padding-bottom:.4rem}
.gcount{color:var(--muted);font-size:.85rem;font-weight:400}
.book{margin-bottom:1.5rem}
.bookhead{display:flex;align-items:center;gap:.6rem;margin:1.1rem 0 .1rem}
.chip{display:inline-block;width:12px;height:12px;border-radius:4px;flex:none}
.btitle{font-weight:600;font-size:1rem}
.bcount{color:var(--muted);font-size:.8rem}
.bookline{color:var(--muted);font-size:.85rem;margin:.1rem 0 .6rem}
.card{background:var(--panel);border:1px solid var(--border);border-left:3px solid var(--amber);border-radius:10px;padding:.65rem .9rem;margin:.5rem 0}
.cardhead{display:flex;align-items:baseline;gap:.6rem;cursor:pointer}
.cardhead .num{color:var(--amber);font-size:.85rem;flex:none;min-width:2.2rem}
.cardhead .ctitle{font-weight:600;font-size:.95rem;flex:1}
.cardhead .pill{flex:none}
.cardbody{display:none;padding-top:.4rem}
.card.open .cardbody{display:block}
.card .steal{margin:.4rem 0;font-style:italic}
.why{margin:.4rem 0}
.why .k{color:var(--amber);font-weight:600}
.card .uw{color:var(--muted);font-size:.88rem;margin:.4rem 0 0}
.actions{margin-top:.5rem;display:flex;gap:.5rem}
.actions button{background:transparent;border:1px solid var(--border);color:var(--muted);border-radius:6px;padding:.25rem .6rem;font-size:.78rem;cursor:pointer}
.actions button:hover{color:var(--amber);border-color:var(--amber)}
.pill{display:inline-block;padding:.1rem .45rem;border-radius:999px;border:1px solid var(--border);font-size:.72rem;color:var(--muted)}
.pill.mechanism{color:var(--amber);border-color:var(--amber)}
.hidden{display:none!important}
footer{color:var(--muted);font-size:.8rem;padding:2rem 1.5rem;border-top:1px solid var(--border);text-align:center}
"""

JS = """
(function(){
var q=document.getElementById('q'),gs=document.getElementById('fgenre'),
    bs=document.getElementById('fbook'),ts=document.getElementById('ftype'),
    count=document.getElementById('count'),total=document.querySelectorAll('.card').length;
function apply(autoOpen){
  var term=q.value.trim().toLowerCase();
  document.querySelectorAll('.card').forEach(function(c){
    var ok=true;
    if(term&&c.dataset.search.indexOf(term)<0)ok=false;
    if(gs.value&&c.dataset.genre!==gs.value)ok=false;
    if(bs.value&&c.dataset.book!==bs.value)ok=false;
    if(ts.value&&c.dataset.type!==ts.value)ok=false;
    c.classList.toggle('hidden',!ok);
    if(autoOpen)c.classList.toggle('open',!!term&&ok);
  });
  document.querySelectorAll('.book').forEach(function(b){
    b.classList.toggle('hidden',!b.querySelector('.card:not(.hidden)'));
  });
  document.querySelectorAll('.genre').forEach(function(g){
    var show=false,next=g.nextElementSibling;
    while(next&&!next.classList.contains('genre')){
      if(next.classList.contains('book')&&!next.classList.contains('hidden')){show=true;break;}
      next=next.nextElementSibling;
    }
    g.classList.toggle('hidden',!show);
  });
  var vis=document.querySelectorAll('.card:not(.hidden)').length;
  count.textContent='showing '+vis+' of '+total;
}
[q,gs,bs,ts].forEach(function(el){el.addEventListener('input',function(){apply(true);});el.addEventListener('change',function(){apply(false);});});
document.querySelectorAll('.cardhead').forEach(function(h){
  function t(){h.parentElement.classList.toggle('open');}
  h.addEventListener('click',t);
  h.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();t();}});
});
document.getElementById('expand').addEventListener('click',function(){
  document.querySelectorAll('.card:not(.hidden)').forEach(function(c){c.classList.add('open');});});
document.getElementById('collapse').addEventListener('click',function(){
  document.querySelectorAll('.card.open').forEach(function(c){c.classList.remove('open');});});
document.querySelectorAll('[data-copy]').forEach(function(btn){
  btn.addEventListener('click',function(e){
    e.stopPropagation();
    var card=btn.closest('.card');
    var txt=btn.dataset.copy==='steal'?card.querySelector('.steal').textContent:card.querySelector('.uw').textContent;
    function done(){btn.textContent='Copied';setTimeout(function(){btn.textContent=btn.dataset.copy==='steal'?'Copy steal':'Copy use-when';},1200);}
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt).then(done,done);}
    else{var ta=document.createElement('textarea');ta.value=txt;document.body.appendChild(ta);ta.select();try{document.execCommand('copy');}catch(_){}document.body.removeChild(ta);done();}
  });
});
apply(false);
})();
"""

page = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Cool Keepers - Idea Ripper</title>
<style>%s</style>
</head>
<body>
<header>
<h1>Cool Keepers</h1>
<p class="job">Stealable mechanisms from books worth stealing from.</p>
<p class="purpose">Hand-picked rips. No self-help, no love stories. The list grows as the ripping gets better.</p>
<p class="meta">%d keepers &middot; %d books &middot; curated %s</p>
</header>
<div class="controls"><div class="inner">
<input type="search" id="q" placeholder="Search titles, steals, use-when&hellip;" aria-label="Search cards"/>
<select id="fgenre" aria-label="Filter by genre"><option value="">All genres</option>
%s</select>
<select id="fbook" aria-label="Filter by book"><option value="">All books</option>
%s</select>
<select id="ftype" aria-label="Filter by type"><option value="">All types</option>
%s</select>
<button type="button" id="expand">Expand all</button>
<button type="button" id="collapse">Collapse all</button>
<span class="count" id="count"></span>
</div></div>
<main>
%s
</main>
<footer>Last curated September 22, 2026 &middot; %d books &middot; %d keepers &middot; ripped with the Idea Ripper pipeline</footer>
<script>%s</script>
</body>
</html>""" % (CSS, n, len(books), curated, genre_opts, book_opts, type_opts,
              "\n\n".join(sections), len(books), n, JS)

open(os.path.join(BASE, "index.html"), "w", encoding="utf-8").write(page)
print("built: %d cards, %d books, %d genres" % (n, len(books), len(genre_order)))
