#!/usr/bin/env python3
"""Renders Report 2's insight cards from parts/insights.json.

parts/insights.json:
  {"sections": [{"id": "value", "title": "...", "intro": "...", "items": [ITEM, ...]}, ...],
   "tested": [{"id": "i1", "was": "old title", "decision": "Revised", "now": "n3", "change": "one sentence"}, ...]}
ITEM:
  {"id": "v1", "title": "...", "confidence": "High", "origin": "i1" or "new",
   "observed": "...", "link": {"href": "competitive-networks.html#portals", "label": "The portals, compared"},
   "evidence": ["visa-164", ...], "means": [{"surface": "Value proposition", "text": "..."}],
   "limit": "...", "objection": "...", "resolution": "..."}

Writes parts/insights.html (the cards, one h3 per section) and parts/tested.html (what the pressure test changed)."""
import json, os, html
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(ROOT, 'parts', 'insights.json')))
S = {r['id'] for r in json.load(open(os.path.join(ROOT, 'sources.json')))}
def e(s): return html.escape(str(s or ''), quote=False)
missing, out = [], []
for sec in D['sections']:
    out.append(f'<h3 class="doc-s" id="{sec["id"]}">{e(sec["title"])}</h3>')
    if sec.get('intro'): out.append(f'<p class="gn-prose">{e(sec["intro"])}</p>')
    for it in sec['items']:
        for i in it['evidence']:
            if i not in S: missing.append(f'{it["id"]}: {i}')
        origin = 'New in the second pass' if it.get('origin') == 'new' else f'Tested from {it["origin"]}'
        link = f' <a class="gn-link" href="{e(it["link"]["href"])}">{e(it["link"]["label"])}</a>' if it.get('link') else ''
        means = ' '.join(f'<b>{e(m["surface"])}.</b> {e(m["text"])}' for m in it['means'])
        ev = ' · '.join('{{ref:' + i + '}}' for i in it['evidence'])
        out.append(
            f'<section class="rs-insight" id="{it["id"]}"><div class="rs-insight-h"><span class="k">{it["id"]}</span><b>{e(it["title"])}</b>'
            f'<span class="gn-status is-quiet">{e(it["confidence"])} confidence</span></div>\n'
            f'<div class="rs-insight-g"><b>Observed</b><div>{e(it["observed"])}{link}</div>\n'
            f'<b>Evidence</b><div>{ev}</div>\n'
            f'<b>What it means</b><div>{means}</div>\n'
            f'<b>Challenged</b><div>{e(it["objection"])} {e(it["resolution"])}</div>\n'
            f'<b>Limit</b><div>{e(it["limit"])}</div>\n'
            f'<b>Origin</b><div>{origin}</div></div></section>\n')
open(os.path.join(ROOT, 'parts', 'insights.html'), 'w').write('\n'.join(out))
rows = ''.join(f'<tr><td>{e(t["id"])}</td><td>{e(t["was"])}</td><td>{e(t["decision"])}</td><td>'
               + (f'<a class="gn-link" href="#{e(t["now"])}">{e(t["now"])}</a>' if t.get('now') else 'None') + f'</td><td>{e(t["change"])}</td></tr>' for t in D['tested'])
open(os.path.join(ROOT, 'parts', 'tested.html'), 'w').write(
    '<div class="gn-table-wrap"><table class="gn-table gn-table--dense"><thead><tr><th>Was</th><th>First version</th><th>Decision</th><th>Now</th><th>What changed</th></tr></thead>'
    f'<tbody>{rows}</tbody></table></div>\n')
n = sum(len(s['items']) for s in D['sections'])
print(f'{n} insights in {len(D["sections"])} sections, {len(D["tested"])} tested rows')
if missing: print('evidence ids not in sources.json:', ', '.join(missing))
