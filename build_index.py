#!/usr/bin/env python3
"""Rebuild index.html: genre pills + search + genre filter + sorting.

Reads the existing index.html rows, applies GENRES, and writes a new
index.html with controls. Idempotent: keeps title/author/date/cards/grades.
"""
import re, html, os

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")

GENRES = {
    "all-about-love-bell-hooks.html": "Self-Help & Psychology",
    "the-anxious-generation-jonathan-haidt.html": "Parenting & Family",
    "bad-law-elie-mystal.html": "History & Politics",
    "bitter-honey-lol-k-nm-d.html": "Fiction",
    "the-body-keeps-the-score.html": "Self-Help & Psychology",
    "bread-of-angels-patti-smith.html": "Memoir & Biography",
    "the-calamity-club-kathryn-stockett.html": "Fiction",
    "cancel-me-if-you-can-dave-portnoy.html": "Memoir & Biography",
    "collected-fictions-borges.html": "Fiction",
    "communion-jd-vance.html": "Philosophy & Spirituality",
    "cool-machine-colson-whitehead.html": "Mystery & Thriller",
    "the-correspondent-virginia-evans.html": "Fiction",
    "the-country-road-murders-james-patterson-and-mike-lupica.html": "Mystery & Thriller",
    "cursed-daughters-oyinkan-braithwaite.html": "Fiction",
    "the-day-after-brian-tyler-cohen.html": "History & Politics",
    "the-deal-elle-kennedy.html": "Romance",
    "dogs-boys-and-other-things-ive-cried-about-isabel-klee.html": "Memoir & Biography",
    "dungeon-crawler-carl-matt-dinniman.html": "Sci-Fi & Fantasy",
    "the-eleventh-hour-a-quintet-of-salman-rushdie.html": "Fiction",
    "the-everlasting-alix-e-harrow.html": "Sci-Fi & Fantasy",
    "famesick-lena-dunham.html": "Memoir & Biography",
    "the-five-star-weekend-elin-hilderbrand.html": "Romance",
    "a-forsaken-prophecy-stacey-mcewan.html": "Sci-Fi & Fantasy",
    "fun-for-the-whole-family-a-nov-jennifer-e-smith.html": "Fiction",
    "gene-wolfes-the-book-of-the-new-sun-a-chapter-guide-michael-andre-driu.html": "Sci-Fi & Fantasy",
    "gilgamesh-helle-2021.html": "Poetry & Essays",
    "gilgamesh-lombardo.html": "Poetry & Essays",
    "gilgamesh-mitchell-2005.html": "Poetry & Essays",
    "great-big-beautiful-life-emily-henry.html": "Romance",
    "heartwood-a-read-with-jenna-pi-amity-gaige.html": "Fiction",
    "the-history-of-money-by-david-mcwilliams.html": "Business & Money",
    "dup-the-king-in-yellow-robert-w-chambers.html": "Mystery & Thriller",
    "the-land-and-its-people-david-sedaris.html": "Poetry & Essays",
    "like-family-a-novel-erin-o-white.html": "Fiction",
    "london-falling-patrick-radden-keefe.html": "History & Politics",
    "mad-mabel-sally-hepworth.html": "Fiction",
    "a-marriage-at-sea-sophie-elmhirst.html": "Memoir & Biography",
    "matriarch-tina-knowles.html": "Memoir & Biography",
    "murder-at-gulls-nest-a-novel-jess-kidd-us.html": "Mystery & Thriller",
    "no-more-tears-the-dark-secrets-gardiner-harris.html": "History & Politics",
    "theosophy-trust-the-origins-of-self-consciousness-in-the-secret-doctri.html": "Philosophy & Spirituality",
    "project-hail-mary-andy-weir.html": "Sci-Fi & Fantasy",
    "ransom-daniel-silva.html": "Mystery & Thriller",
    "regime-change-maggie-haberman-and-jonathan-swan.html": "History & Politics",
    "the-shampoo-effect-jenny-jackson.html": "Fiction",
    "simultaneous-eric-heisserer.html": "Sci-Fi & Fantasy",
    "strangers-belle-burden.html": "Memoir & Biography",
    "theo-of-golden-allen-levi.html": "Fiction",
    "h-p-blavatsky-the-theosophical-glossary.html": "Philosophy & Spirituality",
    "this-is-the-plan-ben-wikler.html": "History & Politics",
    "tilt-emma-pattee.html": "Fiction",
    "the-traitors-circle-jonathan-freedland.html": "History & Politics",
    "twist-a-novel-colum-mccann.html": "Fiction",
    "h-p-blavatsky-the-voice-of-the-silence.html": "Philosophy & Spirituality",
    "when-the-going-was-good-graydon-carter.html": "Memoir & Biography",
    "when-we-ride-rex-ogle.html": "Fiction",
    "where-the-axe-is-buried-ray-nayler.html": "Sci-Fi & Fantasy",
    "whistler-ann-patchett.html": "Fiction",
    "the-white-octopus-hotel-alexandra-bell.html": "Sci-Fi & Fantasy",
    "yesteryear-caro-claire-burke.html": "Fiction",
}

ROW_RE = re.compile(
    r'<tr><td><a href="books/([^"]+)">([^<]+)</a></td>'
    r'<td>([^<]*)</td><td>(\d+)</td><td>(.*?)</td></tr>'
)

with open(SRC, encoding="utf-8") as f:
    old = f.read()

rows = []
for m in ROW_RE.finditer(old):
    fname, label, date, cards, grades = m.groups()
    if " — " in label:
        title, author = label.split(" — ", 1)
    else:
        title, author = label, ""
    genre = GENRES.get(fname)
    if genre is None:
        raise SystemExit("MISSING GENRE for " + fname)
    rows.append({
        "fname": fname, "title": title, "author": author,
        "date": date, "cards": int(cards), "grades": grades, "genre": genre,
    })

total_cards = sum(r["cards"] for r in rows)
genres_sorted = sorted({r["genre"] for r in rows})

genre_options = "\n".join(
    '    <option value="{g}">{g}</option>'.format(g=html.escape(g))
    for g in genres_sorted
)

tbody = []
for r in rows:
    label = html.escape(r["title"]) + (" — " + html.escape(r["author"]) if r["author"] else "")
    tbody.append(
        '<tr data-title="{t}" data-author="{a}" data-genre="{g}" data-cards="{c}" data-date="{d}">'
        '<td><a href="books/{f}">{label}</a></td>'
        '<td><span class="pill genre">{g}</span></td>'
        '<td>{d}</td><td>{c}</td><td>{gr}</td></tr>'.format(
            t=html.escape(r["title"], quote=True), a=html.escape(r["author"], quote=True),
            g=html.escape(r["genre"], quote=True), c=r["cards"],
            d=html.escape(r["date"], quote=True), f=r["fname"],
            label=label, gr=r["grades"])
    )

page = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><title>Library · Idea Ripper</title><style>
:root{--bg:#0b1220;--panel:#121a2b;--fg:#f3f0e8;--muted:#8b97ad;--amber:#e8a54b;--border:#243049;--keep:#3d9a6a;--kill:#b44a4a;--rewrite:#c4a035}
*{box-sizing:border-box}body{margin:0;font-family:"Segoe UI",system-ui,sans-serif;background:var(--bg);color:var(--fg);line-height:1.45}
a{color:var(--amber);text-decoration:none}a:hover{text-decoration:underline}
header{padding:1.25rem 1.5rem;border-bottom:1px solid var(--border);display:flex;gap:1rem;align-items:baseline;flex-wrap:wrap}
header h1{margin:0;font-size:1.25rem;font-weight:600}header .sub{color:var(--muted);font-size:.95rem}
main{max-width:960px;margin:0 auto;padding:1.25rem 1.25rem 3rem}
.meta{color:var(--muted);font-size:.9rem;margin:.75rem 0}
.controls{display:flex;flex-wrap:wrap;gap:.6rem;margin:1rem 0;align-items:center}
.controls input[type=search]{flex:1 1 220px;background:var(--panel);border:1px solid var(--border);color:var(--fg);border-radius:8px;padding:.5rem .75rem;font:inherit}
.controls select{background:var(--panel);border:1px solid var(--border);color:var(--fg);border-radius:8px;padding:.5rem .6rem;font:inherit;max-width:100%}
.controls button{background:transparent;color:var(--muted);border:1px solid var(--border);border-radius:999px;padding:.4rem .9rem;cursor:pointer;font:inherit}
.controls button:hover{color:var(--bg);background:var(--amber);border-color:var(--amber)}
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;min-width:560px}th,td{text-align:left;padding:.65rem .5rem;border-bottom:1px solid var(--border)}
th{color:var(--muted);font-weight:500;font-size:.8rem;text-transform:uppercase;letter-spacing:.04em}
tbody tr:hover td{background:var(--panel)}
.pill{display:inline-block;padding:.1rem .45rem;border-radius:999px;border:1px solid var(--border);font-size:.75rem;color:var(--muted);white-space:nowrap}
.pill.keep{color:var(--keep);border-color:var(--keep)}.pill.kill{color:var(--kill);border-color:var(--kill)}.pill.rewrite{color:var(--rewrite);border-color:var(--rewrite)}
.pill.genre{color:var(--amber);border-color:var(--border)}
tr.empty td{color:var(--muted);text-align:center;padding:2rem}
footer{color:var(--muted);font-size:.8rem;padding:2rem 1.5rem;border-top:1px solid var(--border)}
</style></head><body><header><h1><a href="index.html">Idea Ripper</a></h1><div class="sub">Book → Deck → Decisions</div></header><main>
<div class="controls">
<input id="q" type="search" placeholder="Search title or author…" aria-label="Search title or author"/>
<select id="genre" aria-label="Filter by genre"><option value="">All genres</option>
__GENRE_OPTIONS__
</select>
<select id="sort" aria-label="Sort"><option value="title-asc">Title A–Z</option><option value="title-desc">Title Z–A</option><option value="cards-desc">Most cards first</option><option value="cards-asc">Fewest cards first</option><option value="date-desc">Newest ripped first</option><option value="date-asc">Oldest ripped first</option></select>
<button id="reset" type="button">Reset</button>
</div>
<p class="meta"><span id="count"></span> · __N__ decks · __C__ cards · public library</p>
<div class="table-wrap"><table><thead><tr><th>Book</th><th>Genre</th><th>Ripped</th><th>Cards</th><th>Grades</th></tr></thead><tbody id="rows">
__ROWS__
</tbody></table></div></main><footer>Static export · 2026-09-23 · Idea Ripper library</footer>
<script>
(function(){
var q=document.getElementById('q'),g=document.getElementById('genre'),s=document.getElementById('sort'),
    rows=Array.prototype.slice.call(document.getElementById('rows').querySelectorAll('tr')),
    count=document.getElementById('count');
function visible(r){
  var needle=q.value.trim().toLowerCase();
  if(needle){var hay=(r.dataset.title+' '+r.dataset.author).toLowerCase();if(hay.indexOf(needle)===-1)return false;}
  if(g.value&&r.dataset.genre!==g.value)return false;
  return true;
}
function cmp(a,b){
  switch(s.value){
    case 'title-desc':return b.dataset.title.localeCompare(a.dataset.title);
    case 'cards-desc':return (+b.dataset.cards)-(+a.dataset.cards);
    case 'cards-asc':return (+a.dataset.cards)-(+b.dataset.cards);
    case 'date-desc':return b.dataset.date.localeCompare(a.dataset.date);
    case 'date-asc':return a.dataset.date.localeCompare(b.dataset.date);
    default:return a.dataset.title.localeCompare(b.dataset.title);
  }
}
function apply(){
  var shown=0;
  rows.forEach(function(r){var v=visible(r);r.style.display=v?'':'none';if(v)shown++;});
  rows.sort(cmp).forEach(function(r){r.parentNode.appendChild(r);});
  count.textContent='Showing '+shown+' of '+rows.length+' decks';
  var empty=document.getElementById('emptyrow');
  if(shown===0&&!empty){var tr=document.createElement('tr');tr.id='emptyrow';tr.className='empty';
    tr.innerHTML='<td colspan="5">No books match. Try clearing the search or filters.</td>';
    document.getElementById('rows').appendChild(tr);}
  else if(shown>0&&empty){empty.remove();}
}
q.addEventListener('input',apply);g.addEventListener('change',apply);s.addEventListener('change',apply);
document.getElementById('reset').addEventListener('click',function(){q.value='';g.value='';s.value='title-asc';apply();});
apply();
})();
</script></body></html>
"""

page = (page
        .replace("__GENRE_OPTIONS__", genre_options)
        .replace("__ROWS__", "\n".join(tbody))
        .replace("__N__", str(len(rows)))
        .replace("__C__", str(total_cards)))

with open(SRC, "w", encoding="utf-8") as f:
    f.write(page)

print("wrote", SRC, len(rows), "decks,", total_cards, "cards,", len(genres_sorted), "genres")
