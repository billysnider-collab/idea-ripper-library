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

# chip colors: one hue per genre so chips mean something (genre color)
ghue = {g: int(i * 360 / len(genre_order)) for i, g in enumerate(genre_order)}

types = sorted({c["type"] for c in cards})
n = len(cards)

# render order (genre -> book -> card); stamp global card numbers 1..N
_ordered = []
for _g in genre_order:
    for _b in books:
        if _b["genre"] != _g:
            continue
        for _c in cards:
            if _c["book"] == _b["book"]:
                _ordered.append(_c)
for _i, _c in enumerate(_ordered):
    _c["_n"] = _i + 1
floaters_json = json.dumps(
    [{"n": i + 1, "title": c["title"], "steal": c["steal"],
      "book": c["book"], "type": c["type"]}
     for i, c in enumerate(_ordered)],
    ensure_ascii=False).replace("</", "<\\/")

def book_block(b):
    gh = ghue[b["genre"]]
    slug = slugify(b["book"])
    bcards = [c for c in cards if c["book"] == b["book"]]
    samples = " · ".join("\u201c%s\u201d" % c["title"] for c in bcards[:2])
    parts = ['<section class="book collapsed" id="b-%s" data-book="%s" data-genre="%s">'
             % (slug, esca(b["book"]), esca(b["genre"]))]
    parts.append(
        '<div class="bookhead" role="button" tabindex="0" aria-expanded="false">'
        '<span class="chip" style="background:hsl(%d,45%%,55%%)"></span>'
        '<span class="bmain"><span class="btitle">%s <span class="bcount">%d keeper%s</span></span>'
        '<span class="bookline">%s</span>'
        '<span class="bsamples">%s</span></span>'
        '<span class="bchev">\u25be</span></div>'
        % (gh, esc(b["book"]), len(bcards), "" if len(bcards) == 1 else "s",
           esc(b["bookline"]), esc(samples)))
    parts.append('<div class="cards">')
    thesis_open = b["genre"] == "Thesis"  # one book = one card: skip the second click
    for c in bcards:
        n_ = c["_n"]
        search = " ".join([c["title"], c["steal"], c["why"], c["uw"]]).lower()
        pv = c["steal"]
        if len(pv) > 90:
            pv = pv[:90].rsplit(" ", 1)[0] + "\u2026"
        parts.append(
            '<article class="card%s" id="c%d" data-n="%d" '
            'data-book="%s" data-genre="%s" data-type="%s" data-search="%s">'
            '<div class="cardhead" role="button" tabindex="0">'
            '<span class="num">%d</span>'
            '<span class="ctext"><span class="ctitle">%s</span><span class="pv">%s</span></span>'
            '<span class="pill %s">%s</span></div>'
            '<div class="cardbody">'
            '<p class="steal">%s</p>'
            '<p class="why"><span class="k">Why it matters:</span> %s</p>'
            '<p class="uw">%s</p>'
            '<div class="actions"><button type="button" data-copy="steal">Copy steal</button>'
            '<button type="button" data-copy="uw">Copy use-when</button>'
            '<button type="button" data-copy="link">Copy link</button></div>'
            '</div></article>'
            % (" open" if thesis_open else "", n_, n_, esca(c["book"]), esca(b["genre"]), esca(c["type"]), esca(search),
               n_, esc(c["title"]), esc(pv), esca(c["type"]), esc(c["type"]),
               esc(c["steal"]), esc(c["why"]), esc(c["uw"])))
    parts.append('</div></section>')
    return "\n".join(parts)

import re
def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

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
        sections.append(book_block(b))

chips = "\n".join(
    '<button type="button" data-target="b-%s" data-genre="%s" title="%s">%s</button>'
    % (slugify(b["book"]), esca(b["genre"]), esca(b["book"]), esc(b["book"]))
    for b in books)

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
#splash{position:relative;min-height:92vh;overflow:hidden;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:3rem 1.25rem 4rem}
#splash h1{font-size:2.6rem;margin:0 0 .4rem;position:relative;z-index:2}
#splash .tag{color:var(--muted);font-size:1rem;max-width:34rem;position:relative;z-index:2;margin:0 0 1.4rem}
#floatfield{position:absolute;inset:0;z-index:1;pointer-events:none}
.floater{position:absolute;max-width:250px;background:rgba(18,26,43,.85);border:1px solid var(--border);border-radius:10px;padding:.5rem .7rem;font-size:.78rem;text-align:left;pointer-events:auto;cursor:pointer;animation:drift ease-in-out infinite}
.floater .ft{font-weight:600;color:var(--fg);display:block;margin-bottom:.15rem;font-size:.8rem}
.floater .fs{color:var(--muted);font-style:italic;display:block}
.floater:hover{border-color:var(--amber)}
@keyframes drift{0%,100%{transform:translateY(-10px) rotate(var(--rot,0deg))}50%{transform:translateY(12px) rotate(var(--rot,0deg))}}
#splash .dive{position:relative;z-index:2;background:transparent;border:1px solid var(--amber);color:var(--amber);border-radius:999px;padding:.55rem 1.4rem;font-size:.9rem;cursor:pointer}
#splash .dive:hover{background:var(--amber);color:#0b1220}
@media (prefers-reduced-motion:reduce){.floater{animation:none}}
/* v2: collapsed books, steal previews, chips, toast, jump chips */
.bookhead{cursor:pointer}
.bookhead .bmain{flex:1;min-width:0}
.btitle{font-weight:600;font-size:1rem}
.btitle .bcount{color:var(--muted);font-size:.78rem;font-weight:400;margin-left:.5rem}
.bookline{color:var(--muted);font-size:.85rem;margin:.15rem 0 .1rem .35rem}
.bsamples{color:var(--muted);font-size:.78rem;font-style:italic;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin:0 0 .2rem}
.bchev{margin-left:auto;color:var(--muted);flex:none;transition:transform .15s}
.book.collapsed .bchev{transform:rotate(-90deg)}
.book .cards{margin-top:.4rem}
.book.collapsed .cards{display:none}
.ctext{flex:1;min-width:0}
.ctitle{display:block}
.pv{display:block;color:var(--muted);font-size:.8rem;font-weight:400;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card.open .pv{display:none}
.card .steal{font-family:Georgia,'Iowan Old Style','Source Serif 4',serif;font-size:1.03rem}
.card .uw{color:#a7b2c7}
.noresults{color:var(--muted);text-align:center;padding:2.5rem 0}
.jumpchips{max-width:920px;margin:0 auto;padding:.55rem 1.25rem 0;display:flex;gap:.35rem;overflow-x:auto;scrollbar-width:thin}
.jumpchips button{flex:none;max-width:12rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;background:var(--panel);border:1px solid var(--border);color:var(--muted);border-radius:999px;padding:.22rem .65rem;font-size:.75rem;cursor:pointer}
.jumpchips button:hover{color:var(--amber);border-color:var(--amber)}
#toast{position:fixed;left:50%;bottom:1.5rem;transform:translateX(-50%) translateY(8px);background:var(--panel);border:1px solid var(--amber);color:var(--fg);border-radius:8px;padding:.5rem 1rem;font-size:.85rem;opacity:0;pointer-events:none;transition:opacity .2s,transform .2s;z-index:50}
#toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
.hrow{display:flex;align-items:baseline;gap:.8rem;flex-wrap:wrap}
.hrow strong{font-size:1.3rem}
@media (max-width:700px){.floater{display:none}}
@media(min-width:1000px){
main{max-width:1180px}
.controls .inner,.jumpchips,header{max-width:1180px}
.book:not(.collapsed) .cards{display:grid;grid-template-columns:1fr 1fr;gap:.6rem;align-items:start}
.book:not(.collapsed) .card{margin:0}
}
#intro{max-width:920px;margin:0 auto;padding:1rem 1.25rem 0;color:var(--muted);font-size:.9rem}
#intro p{margin:.45rem 0;max-width:60rem}
#intro strong{color:var(--fg);font-weight:600}
@media (max-width:700px){.bsamples{display:none}}
@media(min-width:1000px){#intro{max-width:1180px}}
"""

JS = r"""
(function(){
var q=document.getElementById('q'),gs=document.getElementById('fgenre'),
    bs=document.getElementById('fbook'),ts=document.getElementById('ftype'),
    count=document.getElementById('count'),nores=document.getElementById('noresults'),
    toastEl=document.getElementById('toast'),
    total=document.querySelectorAll('.card').length,
    manual={},toastT=null;
function toast(msg){
  toastEl.textContent=msg;toastEl.classList.add('show');
  clearTimeout(toastT);toastT=setTimeout(function(){toastEl.classList.remove('show');},1500);
}
function setBook(book,expand){
  book.classList.toggle('collapsed',!expand);
  manual[book.id]=expand;
  var hd=book.querySelector('.bookhead');
  if(hd)hd.setAttribute('aria-expanded',expand?'true':'false');
}
function apply(fromInput){
  var term=q.value.trim().toLowerCase(),
      gv=gs.value,bv=bs.value,tv=ts.value,
      filtering=!!(term||gv||bv||tv);
  document.querySelectorAll('.card').forEach(function(c){
    var ok=true;
    if(term&&c.dataset.search.indexOf(term)<0)ok=false;
    if(gv&&c.dataset.genre!==gv)ok=false;
    if(bv&&c.dataset.book!==bv)ok=false;
    if(tv&&c.dataset.type!==tv)ok=false;
    c.classList.toggle('hidden',!ok);
    if(fromInput)c.classList.toggle('open',!!term&&ok||(!term&&ok&&c.dataset.genre==='Thesis'));
  });
  document.querySelectorAll('.book').forEach(function(b){
    var vis=!!b.querySelector('.card:not(.hidden)');
    b.classList.toggle('hidden',!vis);
    if(vis){
      if(filtering){b.classList.remove('collapsed');}
      else{b.classList.toggle('collapsed',!manual[b.id]);}
      var hd=b.querySelector('.bookhead');
      if(hd)hd.setAttribute('aria-expanded',b.classList.contains('collapsed')?'false':'true');
    }
  });
  document.querySelectorAll('.genre').forEach(function(g){
    var show=false,next=g.nextElementSibling;
    while(next&&!next.classList.contains('genre')){
      if(next.classList.contains('book')&&!next.classList.contains('hidden')){show=true;break;}
      next=next.nextElementSibling;
    }
    g.classList.toggle('hidden',!show);
  });
  document.querySelectorAll('#jumpchips button').forEach(function(ch){
    ch.classList.toggle('hidden',!!gv&&ch.dataset.genre!==gv);
  });
  var vis=document.querySelectorAll('.card:not(.hidden)').length;
  count.textContent='showing '+vis+' of '+total;
  nores.hidden=vis>0;
}
[q,gs,bs,ts].forEach(function(el){
  el.addEventListener('input',function(){apply(true);});
  el.addEventListener('change',function(){apply(false);});
});
function toggleCard(card,open){
  var will=open===undefined?!card.classList.contains('open'):open;
  card.classList.toggle('open',will);
  if(will&&history.replaceState){try{history.replaceState(null,'','#c'+card.dataset.n);}catch(_){}}
}
document.querySelectorAll('.cardhead').forEach(function(h){
  h.addEventListener('click',function(){toggleCard(h.parentElement);});
  h.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();toggleCard(h.parentElement);}});
});
document.querySelectorAll('.bookhead').forEach(function(h){
  function t(){var b=h.parentElement;setBook(b,b.classList.contains('collapsed'));}
  h.addEventListener('click',t);
  h.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();t();}});
});
document.getElementById('expand').addEventListener('click',function(){
  document.querySelectorAll('.book:not(.hidden)').forEach(function(b){
    setBook(b,true);
    b.querySelectorAll('.card:not(.hidden)').forEach(function(c){c.classList.add('open');});
  });
});
document.getElementById('collapse').addEventListener('click',function(){
  document.querySelectorAll('.book').forEach(function(b){
    setBook(b,false);
    b.querySelectorAll('.card.open').forEach(function(c){c.classList.remove('open');});
  });
});
document.querySelectorAll('[data-copy]').forEach(function(btn){
  btn.addEventListener('click',function(e){
    e.stopPropagation();
    var card=btn.closest('.card'),kind=btn.dataset.copy,txt;
    if(kind==='steal')txt=card.querySelector('.steal').textContent;
    else if(kind==='uw')txt=card.querySelector('.uw').textContent;
    else txt=location.origin+location.pathname+'#c'+card.dataset.n;
    function done(ok){toast(ok?(kind==='link'?'Link copied':'Copied'):'Copy failed');}
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt).then(function(){done(true);},function(){done(false);});}
    else{var ta=document.createElement('textarea');ta.value=txt;document.body.appendChild(ta);ta.select();try{document.execCommand('copy');done(true);}catch(_){done(false);}document.body.removeChild(ta);}
  });
});
document.querySelectorAll('#jumpchips button').forEach(function(ch){
  ch.addEventListener('click',function(){
    var b=document.getElementById(ch.dataset.target);
    if(b){setBook(b,true);b.scrollIntoView({behavior:'smooth',block:'start'});}
  });
});
function openHash(){
  var m=/^#c(\d+)$/.exec(location.hash),c;
  if(m&&(c=document.getElementById('c'+m[1]))){
    var b=c.closest('.book');setBook(b,true);c.classList.add('open');
    setTimeout(function(){c.scrollIntoView({block:'center'});},60);return true;
  }
  m=/^#b-([a-z0-9-]+)$/.exec(location.hash);
  if(m){var bk=document.getElementById('b-'+m[1]);
    if(bk){setBook(bk,true);setTimeout(function(){bk.scrollIntoView({block:'start'});},60);return true;}}
  return false;
}
var field=document.getElementById('floatfield');
if(field&&window.FLOATERS){
  var pool=window.FLOATERS.slice(),picks=[],K=Math.min(6,pool.length),i;
  for(i=0;i<K;i++){picks.push(pool.splice(Math.floor(Math.random()*pool.length),1)[0]);}
  var cards=document.querySelectorAll('.card');
  picks.forEach(function(p){
    var d=document.createElement('div');
    d.className='floater';
    d.style.left=(4+Math.random()*72).toFixed(1)+'%';
    d.style.top=(6+Math.random()*68).toFixed(1)+'%';
    d.style.animationDuration=(9+Math.random()*9).toFixed(1)+'s';
    d.style.animationDelay=(-Math.random()*12).toFixed(1)+'s';
    d.style.setProperty('--rot',(Math.random()*6-3).toFixed(1)+'deg');
    var t=document.createElement('span');t.className='ft';t.textContent=p.title;
    var s=document.createElement('span');s.className='fs';
    s.textContent=p.steal.length>110?p.steal.slice(0,110)+'…':p.steal;
    d.appendChild(t);d.appendChild(s);
    d.title=p.book+' — click to open card '+p.n;
    d.addEventListener('click',function(){
      var c=cards[p.n-1];
      if(c){var b=c.closest('.book');setBook(b,true);c.classList.add('open');
        c.scrollIntoView({behavior:'smooth',block:'center'});
        if(history.replaceState){try{history.replaceState(null,'','#c'+p.n);}catch(_){}}}
    });
    field.appendChild(d);
  });
}
var dive=document.getElementById('dive');
if(dive){dive.addEventListener('click',function(){document.getElementById('intro').scrollIntoView({behavior:'smooth'});});}
var firstBook=document.querySelector('.book');
if(firstBook)manual[firstBook.id]=true;
apply(false);
if(!openHash()&&firstBook){
  var fc=firstBook.querySelector('.card');
  if(fc){fc.classList.add('open');if(history.replaceState){try{history.replaceState(null,'','#c'+fc.dataset.n);}catch(_){}}}
}
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
<section id="splash">
<div id="floatfield" aria-hidden="true"></div>
<h1>Cool Keepers</h1>
<p class="tag">Stealable mechanisms from books worth stealing from. The list grows as the ripping gets better.</p>
<button type="button" class="dive" id="dive">Dive into the library ↓</button>
</section>
<header>
<div class="hrow"><strong>Cool Keepers</strong><span class="meta">%d keepers &middot; %d books &middot; curated %s</span></div>
</header>
<section id="intro">
<p><strong>What this is:</strong> a hunting library of ideas ripped by hand from books worth stealing from. Every keeper is one stealable mechanism — the exact lines worth keeping, plus when to use them.</p>
<p><strong>How to hunt:</strong> tap a book to open its keepers, tap a card for the full steal, copy anything you want. Search hunts titles, steals, and use-whens all at once.</p>
</section>
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
<nav class="jumpchips" id="jumpchips" aria-label="Jump to a book">%s</nav>
<main>
%s
<p class="noresults" id="noresults" hidden>No keepers match — try a mechanism word (interlock, delay, patronage).</p>
</main>
<footer>Last curated September 22, 2026 &middot; %d books &middot; %d keepers &middot; ripped with the Idea Ripper pipeline</footer>
<script>var FLOATERS=%s;</script>
<script>%s</script>
<div id="toast" role="status"></div>
</body>
</html>""" % (CSS, n, len(books), curated, genre_opts, book_opts, type_opts, chips,
              "\n\n".join(sections), len(books), n, floaters_json, JS)

open(os.path.join(BASE, "index.html"), "w", encoding="utf-8").write(page)
print("built: %d cards, %d books, %d genres" % (n, len(books), len(genre_order)))
