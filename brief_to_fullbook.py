#!/usr/bin/env python3
"""Convert a research-brief-packet markdown file into fullbooks.json entries.

Input format: the ANGLO-SAXONS-MORRIS-BRIEF style packet:
  - ## Argument map (Morris's main thesis) with **Because**/**This led to**/**However**/**Therefore**
  - ## Three recurring themes (numbered list)
  - ## Turning-point timeline (samples) (markdown table)
  - ## Author-vs-fact table (samples) (markdown table)
  - ## One-page synthesis (### subsections)
  - ## Flat 25-card deck (full fields) with ## Card N: Title + "- key: value" lines
  - ## Appendix: Condensed chapter one-sentence summaries (markdown table)

Usage: python3 brief_to_fullbook.py IN.md [OUT.json]
Appends/merges the book into OUT.json (default: fullbooks.json next to the script).
"""
import json, re, sys, os

def parse_table(lines):
    rows = []
    for ln in lines:
        ln = ln.strip()
        if not ln.startswith('|'):
            continue
        cells = [c.strip() for c in ln.strip('|').split('|')]
        if all(re.fullmatch(r':?-+:?', c) for c in cells):
            continue
        rows.append(cells)
    if not rows:
        return []
    header, data = rows[0], rows[1:]
    return [dict(zip(header, r)) for r in data]

def main():
    inp = sys.argv[1]
    outp = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'fullbooks.json')
    text = open(inp, encoding='utf-8').read()
    lines = text.split('\n')

    # ---- book header ----
    m = re.search(r'##\s+(.+?)\s+[—–-]\s+\*(.+?)\*\s*\((.+?)\)', text)
    author, title, publisher = (m.group(1).strip(), m.group(2).strip(),
                               m.group(3).strip()) if m else ('', '', '')
    m = re.search(r'\*\*Central lens:\*\*\s*(.+)', text)
    lens = m.group(1).strip() if m else ''
    m = re.search(r'\*\*Date:\*\*\s*([0-9-]+)', text)
    date = m.group(1) if m else ''

    # ---- argument map ----
    am = {}
    sec = re.search(r'## Argument map.*?\n(.*?)(?=\n## )', text, re.S)
    if sec:
        body = sec.group(1)
        for key, pat in [('because', r'\*\*Because\*\*'),
                         ('led_to', r'\*\*This led to\*\*'),
                         ('however', r'\*\*However\*\*'),
                         ('therefore', r'\*\*Therefore\*\*')]:
            mm = re.search(pat + r'\s*(.*?)(?=\n\*\*|\Z)', body, re.S)
            if mm:
                am[key] = re.sub(r'\s+', ' ', mm.group(1)).strip(' ,')

    # ---- themes ----
    themes = []
    sec = re.search(r'## Three recurring themes\n(.*?)(?=\n## )', text, re.S)
    if sec:
        for ln in sec.group(1).strip().split('\n'):
            mm = re.match(r'\d+\.\s+\*\*(.+?)\*\*\s*(.*)', ln.strip())
            if mm:
                themes.append({'title': mm.group(1), 'body': mm.group(2)})

    # ---- timeline ----
    timeline = []
    sec = re.search(r'## Turning-point timeline.*?\n(.*?)(?=\n## )', text, re.S)
    if sec:
        for r in parse_table(sec.group(1).split('\n')):
            timeline.append({
                'date': r.get('Date', ''),
                'cause': r.get('Cause', ''),
                'changed': r.get('What changed', ''),
                'pace': re.sub(r'\*+', '', r.get('Immediate vs gradual', '')),
            })

    # ---- author vs fact ----
    avf = []
    sec = re.search(r'## Author-vs-fact table.*?\n(.*?)(?=\n## )', text, re.S)
    if sec:
        for r in parse_table(sec.group(1).split('\n')):
            avf.append({
                'claim': r.get('Claim / emphasis (Morris)', ''),
                'anchored': r.get('Anchored in', ''),
                'status': r.get('Status / dispute space', ''),
            })

    # ---- synthesis ----
    synth = {}
    sec = re.search(r'## One-page synthesis\n(.*?)(?=\n## )', text, re.S)
    if sec:
        body = sec.group(1)
        mm = re.search(r'### The book in five sentences\n(.*?)(?=\n### )', body, re.S)
        if mm:
            synth['five_sentences'] = re.sub(r'\s+', ' ', mm.group(1)).strip()
        mm = re.search(r'### The three biggest ideas\n(.*?)(?=\n### )', body, re.S)
        if mm:
            ideas = []
            for ln in mm.group(1).strip().split('\n'):
                lm = re.match(r'\d+\.\s+\*\*(.+?)\*\*\s*(.*)', ln.strip())
                if lm:
                    ideas.append((lm.group(1) + ' ' + lm.group(2)).strip())
            synth['biggest_ideas'] = ideas
        mm = re.search(r'### The major turning points\n(.*?)(?=\n### )', body, re.S)
        if mm:
            synth['turning_points'] = re.sub(r'\s+', ' ', mm.group(1)).strip()
        mm = re.search(r'### Assessment\n(.*)', body, re.S)
        if mm:
            assess = {}
            for ln in mm.group(1).strip().split('\n'):
                am_ = re.match(r'\*\*(.+?):\*\*\s*(.*)', ln.strip())
                if am_:
                    assess[am_.group(1).lower().replace(' ', '_')] = am_.group(2)
            synth['assessment'] = assess

    # ---- cards ----
    cards = []
    for cm in re.finditer(r'## Card (\d+):\s*(.+?)\n(.*?)(?=\n## Card |\n## Chapter coverage|\Z)',
                          text, re.S):
        num, ctitle, body = int(cm.group(1)), cm.group(2).strip(), cm.group(3)
        card = {'n': num, 'title': ctitle}
        for ln in body.strip().split('\n'):
            ln = ln.strip()
            if not ln.startswith('- '):
                continue
            kv = re.match(r'-\s+([\w_]+):\s*(.*)', ln)
            if kv:
                card[kv.group(1)] = kv.group(2).strip()
        cards.append(card)
    cards.sort(key=lambda c: c['n'])

    # ---- chapter summaries ----
    chaps = []
    sec = re.search(r'## Appendix: Condensed chapter one-sentence summaries\n(.*?)(?=\n## )',
                    text, re.S)
    if sec:
        for r in parse_table(sec.group(1).split('\n')):
            chaps.append({'unit': r.get('Unit', ''),
                          'summary': r.get('One-sentence summary', '')})

    book_id = re.sub(r'[^a-z0-9]+', '-', (author + ' ' + title).lower()).strip('-')
    entry = {
        'id': book_id,
        'author': author, 'title': title, 'publisher': publisher,
        'lens': lens, 'date': date,
        'argument_map': am, 'themes': themes, 'timeline': timeline,
        'author_vs_fact': avf, 'synthesis': synth,
        'cards': cards, 'chapter_summaries': chaps,
    }

    data = {'books': []}
    if os.path.exists(outp):
        data = json.load(open(outp, encoding='utf-8'))
    data['books'] = [b for b in data['books'] if b['id'] != book_id]
    data['books'].append(entry)
    json.dump(data, open(outp, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f'wrote {book_id}: {len(cards)} cards, {len(timeline)} timeline rows, '
          f'{len(avf)} avf rows, {len(chaps)} chapter summaries -> {outp}')

if __name__ == '__main__':
    main()
