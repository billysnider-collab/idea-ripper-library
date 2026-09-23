#!/usr/bin/env python3
"""Build the Idea Ripper library index from the graded (public) book pages.

Source of truth: the 19 shipped books below. For each book page, counts are
read from the actual <article data-status="keep|rewrite"> blocks, so the
index can never drift from the pages again. Grade pills are only rendered
for nonzero counts; ungraded/killed cards are not public and not counted.

Usage: python3 build_index.py   (run from the idea-ripper-lib directory)
"""
import os, re, json, html as htmlmod
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
BOOKS_DIR = os.path.join(HERE, "books")

# (slug, title, author, genre) — the public, graded set
BOOKS = [
    ("a-marriage-at-sea-sophie-elmhirst", "A Marriage at Sea", "Sophie Elmhirst", "Memoir & Biography"),
    ("cancel-me-if-you-can-dave-portnoy", "Cancel Me If You Can", "Dave Portnoy", "Memoir & Biography"),
    ("cool-machine-colson-whitehead", "Cool Machine", "Colson Whitehead", "Sci-Fi & Fantasy"),
    ("dogs-boys-and-other-things-ive-cried-about-isabel-klee", "Dogs, Boys, and Other Things I've Cried About", "Isabel Klee", "Memoir & Biography"),
    ("dungeon-crawler-carl-matt-dinniman", "Dungeon Crawler Carl", "Matt Dinniman", "Sci-Fi & Fantasy"),
    ("the-king-in-yellow-robert-w-chambers", "The King in Yellow", "Robert W. Chambers", "Sci-Fi & Fantasy"),
    ("gilgamesh-lombardo", "Gilgamesh (Lombardo translation)", "Stanley Lombardo", "Poetry & Essays"),
    ("gilgamesh-mitchell-2005", "Gilgamesh (Mitchell translation)", "Stephen Mitchell", "Poetry & Essays"),
    ("project-hail-mary-andy-weir", "Project Hail Mary", "Andy Weir", "Sci-Fi & Fantasy"),
    ("regime-change-maggie-haberman-and-jonathan-swan", "Regime Change", "Maggie Haberman and Jonathan Swan", "History & Politics"),
    ("simultaneous-eric-heisserer", "Simultaneous", "Eric Heisserer", "Sci-Fi & Fantasy"),
    ("strangers-belle-burden", "Strangers", "Belle Burden", "Memoir & Biography"),
    ("the-collected-stories-of-arthur-c-clarke", "The Collected Stories of Arthur C. Clarke", "Arthur C. Clarke", "Sci-Fi & Fantasy"),
    ("the-day-after-brian-tyler-cohen", "The Day After", "Brian Tyler Cohen", "History & Politics"),
    ("tilt-emma-pattee", "Tilt", "Emma Pattee", "Sci-Fi & Fantasy"),
    ("where-the-axe-is-buried-ray-nayler", "Where the Axe Is Buried", "Ray Nayler", "Sci-Fi & Fantasy"),
]

RIPPED = "2026-09-22"


def count_cards(slug):
    t = open(os.path.join(BOOKS_DIR, slug + ".html"), encoding="utf-8").read()
    keep = len(re.findall(r'data-status="keep"', t))
    rewrite = len(re.findall(r'data-status="rewrite"', t))
    return keep, rewrite


def esc(s):
    return htmlmod.escape(s, quote=True)


def main():
    rows = []
    total = 0
    for slug, title, author, genre in BOOKS:
        keep, rewrite = count_cards(slug)
        n = keep + rewrite
        total += n
        pills = '<span class="pill keep">%d keep</span>' % keep
        if rewrite:
            pills += ' <span class="pill rewrite">%d rewrite</span>' % rewrite
        rows.append(
            '<tr data-title="%s" data-author="%s" data-genre="%s" data-cards="%d" data-date="%s">'
            '<td><a href="books/%s.html">%s &mdash; %s</a></td>'
            '<td><span class="pill genre">%s</span></td>'
            '<td>%s</td><td>%d</td><td>%s</td></tr>'
            % (esc(title), esc(author), esc(genre), n, RIPPED, slug,
               esc(title), esc(author), esc(genre), RIPPED, n, pills)
        )

    tpl = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()
    head = tpl[:tpl.find('<div class="controls">')]
    head = head.replace("</style>",
        ".purpose{color:var(--fg);font-size:1.05rem;margin:.1rem 0 1rem;max-width:60rem}</style>")
    head = re.sub(r'<p class="purpose">.*?</p>\n', '', head)  # idempotent reruns
    head += ('<p class="purpose">Stealable ideas from books I actually graded. '
             'Every card below survived a human keep-or-rewrite verdict.</p>\n')

    genres = sorted({g for _, _, _, g in BOOKS})
    genre_opts = '<option value="">All genres</option>\n' + "\n".join(
        '    <option value="%s">%s</option>' % (esc(g), esc(g)) for g in genres)

    body = (
        '<div class="controls">\n'
        '<input id="q" type="search" placeholder="Search title or author\u2026" aria-label="Search title or author"/>\n'
        '<select id="genre" aria-label="Filter by genre">%s</select>\n'
        '<select id="sort" aria-label="Sort"><option value="title-asc">Title A\u2013Z</option>'
        '<option value="title-desc">Title Z\u2013A</option>'
        '<option value="cards-desc">Most cards first</option>'
        '<option value="cards-asc">Fewest cards first</option>'
        '<option value="date-desc">Newest ripped first</option>'
        '<option value="date-asc">Oldest ripped first</option></select>\n'
        '<button id="reset" type="button">Reset</button>\n</div>\n'
        '<p class="meta"><span id="count"></span> &middot; %d decks &middot; %d stealable ideas &middot; graded library</p>\n'
        '<div class="table-wrap"><table><thead><tr><th>Book</th><th>Genre</th><th>Ripped</th><th>Cards</th><th>Grades</th></tr></thead>\n'
        '<tbody id="rows">\n%s\n</tbody></table></div>\n'
        % (genre_opts, len(BOOKS), total, "\n".join(rows))
    )
    script = tpl[tpl.find("<script>"):]
    open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(head + body + script)

    manifest = {
        "decks": len(BOOKS),
        "cards": total,
        "generated_at": date.today().isoformat(),
        "note": "Public set: graded books only (keep + rewrite cards). Full 61-book export archived locally.",
    }
    open(os.path.join(HERE, "export-manifest.json"), "w", encoding="utf-8").write(
        json.dumps(manifest, indent=2) + "\n")
    print("index rebuilt: %d decks, %d cards" % (len(BOOKS), total))


if __name__ == "__main__":
    main()
