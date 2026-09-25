#!/usr/bin/env python3
"""Assembles the reports from src/<name>.html templates.
Markers:  <!-- include:parts/visa-portal.html -->   pastes a part
          <!-- table:register -->                    the source register from sources.json
          <!-- table:register:visa -->               one network's register rows
          <!-- figs:visa-dev:S1,S4 -->               captioned figures from a walk record's screenshots
Citations in prose are written as {{cite:visa-014}} or {{cite:visa-014|Visa quick start}} and rendered as the citation link from sources.json."""
import json, os, re, sys, html
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = {r['id']: r for r in json.load(open(os.path.join(ROOT, 'sources.json')))}
NAMES = json.load(open(os.path.join(ROOT, 'tools', 'names.json'))) if os.path.exists(os.path.join(ROOT, 'tools', 'names.json')) else {}
def esc(s): return html.escape(str(s or ''), quote=True)
def month(d):
    m = re.match(r'(\d{4})-(\d{2})(?:-(\d{2}))?', d or '')
    if not m: return d or 'n.d.'
    names = ['January','February','March','April','May','June','July','August','September','October','November','December']
    return (f"{names[int(m.group(2))-1]} {int(m.group(3))}, {m.group(1)}" if m.group(3) else f"{names[int(m.group(2))-1]} {m.group(1)}")
def cite(match):
    ids = match.group(1).split('+'); label = match.group(2)
    parts = []
    for i, sid in enumerate(ids):
        r = S.get(sid.strip())
        if not r: return f'<span class="rs-cite">[missing {esc(sid)}]</span>'
        lab = label if (label and i == 0) else (r.get('publisher') or r.get('title') or sid)
        title = f"Accessed {month(r.get('accessed'))} · {r.get('confidence')}" if r.get('kind') == 'source' else f"{r.get('channel','')} · {r.get('confidence','')}"
        parts.append(f'<a class="rs-src" data-src="{esc(sid)}" href="{esc(r.get("url"))}" title="{esc(title)}">{esc(lab)}</a>')
    return '<span class="rs-cite">(' + ' · '.join(parts) + ')</span>'
def register(slug=None):
    rows = [r for r in S.values() if r['kind'] in ('source', 'video') and (slug is None or r['network'] == slug)]
    rows.sort(key=lambda r: (r['network'], r['kind'] != 'source', int(re.sub(r'\D', '', r['id'].split('-')[-1]) or 0)))
    out = ['<div class="gn-table-wrap"><table class="gn-table gn-table--dense rs-register"><thead><tr><th>Id</th><th>Source</th><th>Publisher</th><th>Published</th><th>Accessed</th><th>Confidence</th></tr></thead><tbody>']
    for r in rows:
        title = r.get('title') if r['kind'] == 'source' else r.get('title')
        pub = r.get('publisher') if r['kind'] == 'source' else r.get('channel')
        out.append(f'<tr id="src-{esc(r["id"])}"><td>{esc(r["id"])}</td><td><a class="rs-src" data-src="{esc(r["id"])}" href="{esc(r.get("url"))}">{esc(title)}</a></td><td>{esc(pub)}</td><td>{esc(r.get("published") or "n.d.")}</td><td>{esc(r.get("accessed"))}</td><td>{esc(r.get("confidence"))}</td></tr>')
    out.append('</tbody></table></div>')
    return '\n'.join(out)
def figs(walk, stations):
    p = os.path.join(ROOT, 'ledger', 'walks', walk + '.json'); d = json.load(open(p))
    want = stations.split(','); shots = [s for s in d['screenshots'] if (s['station'] in want) or any(s['id'].endswith('-' + w) for w in want)]
    caps = json.load(open(os.path.join(ROOT, 'parts', 'captions.json'))) if os.path.exists(os.path.join(ROOT, 'parts', 'captions.json')) else {}
    out = [f'<div class="rs-shots{" rs-shots--1" if len(shots) == 1 else ""}">']
    for s in shots:
        key = os.path.basename(s['file']); c = caps.get(key, {}); lead = c.get('lead', s['note']); text = c.get('text', '')
        out.append(f'<figure class="rs-shot" data-src="{esc(s["id"])}"><img src="{esc(s["file"])}" alt="{esc(lead)}" width="1400" loading="lazy"><figcaption><b>{esc(lead)}</b> {text} {esc(s["url"].replace("https://", "").split("/")[0])} · {month(s["captured"])}</figcaption></figure>')
    out.append('</div>'); return '\n'.join(out)
def build(name):
    src = os.path.join(ROOT, 'src', name); t = open(src).read()
    t = re.sub(r'<!-- include:([^ ]+) -->', lambda m: open(os.path.join(ROOT, m.group(1))).read(), t)
    t = re.sub(r'<!-- table:register(?::(\w+))? -->', lambda m: register(m.group(1)), t)
    t = re.sub(r'<!-- figs:([\w-]+):([\w,]+) -->', lambda m: figs(m.group(1), m.group(2)), t)
    t = re.sub(r'\{\{cite:([\w+-]+)(?:\|([^}]+))?\}\}', cite, t)
    open(os.path.join(ROOT, name), 'w').write(t); print(f'rendered {name}: {len(t)//1024} KB')
for n in (sys.argv[1:] or ['competitive-networks.html', 'prototype-insights.html']):
    if os.path.exists(os.path.join(ROOT, 'src', n)): build(n)
