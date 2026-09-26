#!/usr/bin/env python3
"""Assembles the reports from src/<name>.html templates.
Markers:  <!-- include:parts/visa-portal.html -->   pastes a part
          <!-- table:register -->                    the source register from sources.json
          <!-- table:register:visa -->               one network's register rows
          <!-- figs:visa-dev:S1,S4 -->               captioned figures from a walk record's screenshots
Citations in prose are written as {{cite:visa-014}} or {{cite:visa-014|Visa quick start}} and rendered as the citation link from sources.json."""
import json, os, re, sys, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from labels import label as short_label, compact as compact_label
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
    ids = match.group(2).split('+'); label = match.group(3); tight = match.group(1) == 'citet'
    parts = []; seen = {}
    for i, sid in enumerate(ids):
        r = S.get(sid.strip())
        if not r: return f'<span class="rs-cite">[missing {esc(sid)}]</span>'
        key = (r.get('url'), short_label(r))
        if key in seen and not (label and i == 0):
            j = seen[key]; parts[j] = parts[j].replace(' data-also="', f' data-also="{esc(sid)} ', 1) if ' data-also="' in parts[j] else parts[j].replace(' href=', f' data-also="{esc(sid)}" href=', 1)
            continue
        seen[key] = len(parts)
        base = compact_label(r) if tight else short_label(r)
        if label in ('Reported', 'Vendor', 'Verified'): label = None
        lab = (label if (label and i == 0) else base).replace(';', ',')
        title = f"{r.get('title')} · {r.get('publisher')} · accessed {month(r.get('accessed'))} · {r.get('confidence')}" if r.get('kind') == 'source' else (f"{r.get('author','')} · {r.get('date','')} · Reported" if r.get('kind') == 'quote' else f"{r.get('channel','')} · {r.get('confidence','')}")
        parts.append(f'<a class="rs-src" data-src="{esc(sid)}" href="{esc(r.get("url"))}" title="{esc(title)}">{esc(lab)}</a>')
    return '<span class="rs-cite">(' + ' · '.join(parts) + ')</span>'
def register(slug=None):
    if slug is None:
        nets = sorted({r['network'] for r in S.values() if r['kind'] in ('source', 'video', 'quote')})
        return '\n'.join(f'<h3 class="doc-s" id="register-{n}">{n}</h3>\n' + register(n) for n in nets)
    rows = [r for r in S.values() if r['kind'] in ('source', 'video', 'quote') and r['network'] == slug]
    rows.sort(key=lambda r: (r['network'], r['kind'] != 'source', int(re.sub(r'\D', '', r['id'].split('-')[-1]) or 0)))
    out = ['<div class="gn-table-wrap"><table class="gn-table gn-table--dense rs-register"><thead><tr><th>Id</th><th>Source</th><th>Publisher</th><th>Published</th><th>Accessed</th><th>Confidence</th></tr></thead><tbody>']
    for r in rows:
        title = r.get('title') if r['kind'] != 'quote' else f"{r.get('author','')}: {r.get('excerpt','')}"
        pub = r.get('publisher') if r['kind'] == 'source' else (r.get('channel') if r['kind'] == 'video' else r.get('platform'))
        if r['kind'] == 'quote': r = dict(r, published=r.get('date'), accessed='2026-09-25', confidence='Reported')
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
    for _ in range(4): t = re.sub(r'<!-- include:([^ ]+) -->', lambda m: open(os.path.join(ROOT, m.group(1))).read(), t)
    def srcline(m):
        slug = m.group(1); rows = [r for r in S.values() if r['kind'] == 'source' and r['network'] == slug and '-w-' not in r['id']]
        c = {k: sum(1 for r in rows if r.get('confidence') == k) for k in ('Verified', 'Reported', 'Vendor')}
        walks = sum(1 for r in S.values() if r['kind'] == 'source' and r['network'] == slug and '-w-' in r['id'])
        if not rows: return f'<p class="rs-sources">Sources · cited under the parent network and the cross-cutting rows · {walks} browser walks · <a class="gn-link" href="#register">register</a></p>'
        return f'<p class="rs-sources">Sources · {len(rows)} ledger rows for this network · {c["Verified"]} Verified · {c["Reported"]} Reported · {c["Vendor"]} Vendor · {walks} browser walks · <a class="gn-link" href="#register-{slug}">register</a></p>'
    t = re.sub(r'<!-- sources:(\w+) -->', srcline, t)
    srcs = [r for r in S.values() if r['kind'] == 'source' and '-w-' not in r['id']]
    def walked(r):
        m = re.search(r'ledger/walks/([\w-]+)\.json', r.get('note') or '')
        if not m: return True
        d = json.load(open(os.path.join(ROOT, 'ledger', 'walks', m.group(1) + '.json')))
        return d.get('stations', {}).get('S0', {}).get('wall') != 'bot'
    walks = [r for r in S.values() if r['kind'] == 'source' and '-w-' in r['id'] and r.get('dimension') == 'walk' and walked(r)]
    vids = [r for r in S.values() if r['kind'] == 'video']
    ver = sum(1 for r in srcs if r.get('confidence') == 'Verified')
    rechecked = sum(1 for r in srcs if 'verified 2026-09-25' in (r.get('note') or '') or 'verified with qualification' in (r.get('note') or ''))
    C = {'sources': f"{len(srcs):,}", 'walks': str(len(walks)), 'videos': str(len(vids)), 'verified_pct': f"{round(100*ver/max(1,len(srcs)))} percent", 'verified_pc': f"{round(100*ver/max(1,len(srcs)))}%", 'rechecked_pct': f"{round(100*rechecked/max(1,len(srcs)))} percent", 'shots': str(sum(1 for r in S.values() if r['kind']=='shot'))}
    unv = 0
    for lf in __import__('glob').glob(os.path.join(ROOT, 'ledger', '*.md')):
        txt = open(lf).read()
        if '## Claims this research could not verify' in txt:
            sec = txt.split('## Claims this research could not verify', 1)[1].split('\n## ', 1)[0]
            unv += sum(1 for l in sec.splitlines() if l.startswith('- ') and l != '- None.')
    C['unverified'] = str(unv)
    C['quotes'] = str(sum(1 for r in S.values() if r['kind'] == 'quote'))
    t = re.sub(r'<!-- count:(\w+) -->', lambda m: C.get(m.group(1), '?'), t)
    t = re.sub(r'<!-- table:register(?::(\w+))? -->', lambda m: register(m.group(1)), t)
    t = re.sub(r'<!-- figs:([\w-]+):([\w,]+) -->', lambda m: figs(m.group(1), m.group(2)), t)
    def observed(m):
        row = m.group(0); ids = [i for g in re.findall(r'\{\{cite:([\w+-]+)', row) for i in g.split('+')]
        ok = bool(ids) and all((S.get(i) or {}).get('confidence') == 'Verified' for i in ids)
        row = re.sub(r'class="gn-doc-r(?: is-observed)?"', 'class="gn-doc-r is-observed"' if ok else 'class="gn-doc-r"', row, count=1)
        return row
    t = re.sub(r'<div class="gn-doc-r(?: is-observed)?">.*?</div>', observed, t, flags=re.S)
    for _ in range(4): t = re.sub(r'\{\{cite:([\w+-]+)(\|[^}]+)?\}\}\s+\{\{cite:([\w+-]+)\}\}', lambda m: '{{cite:' + m.group(1) + '+' + m.group(3) + (m.group(2) or '') + '}}', t)
    t = re.sub(r'<td\b[^>]*>.*?</td>', lambda m: m.group(0).replace('{{cite:', '{{citet:'), t, flags=re.S)
    t = re.sub(r'\{\{(cite|citet):([\w+-]+)(?:\|([^}]+))?\}\}', cite, t)
    def ref(m):
        out = []
        for sid in m.group(1).split('+'):
            r = S.get(sid)
            if not r: out.append(f'[missing {esc(sid)}]'); continue
            lab = short_label(r).replace(';', ',')
            out.append(f'<a class="rs-src" href="competitive-networks.html#src-{esc(sid)}" title="{esc(r.get("claim") or "")}">{esc(lab)}</a> <span class="gn-status is-quiet">{esc(r.get("confidence") or "")}</span>')
        return ' · '.join(out)
    t = re.sub(r'\{\{ref:([\w+-]+)\}\}', ref, t)
    open(os.path.join(ROOT, name), 'w').write(t); print(f'rendered {name}: {len(t)//1024} KB')
for n in (sys.argv[1:] or ['competitive-networks.html', 'prototype-insights.html']):
    if os.path.exists(os.path.join(ROOT, 'src', n)): build(n)
