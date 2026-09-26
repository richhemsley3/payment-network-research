#!/usr/bin/env python3
"""Takes new evidence rows from an insight workflow's output into the ledger.

Usage: python3 tools/insights-ingest.py <round-name> <rows.json>
rows.json is a list of evidence rows: {network, claim, quote, url, title, publisher, published, label, fetch, [ledger_id]}.
Rows that carry a ledger_id, or whose URL and claim are already in the ledger, are skipped.
The rest go to ledger/raw/<slug>/insights-<round>.json, one file per network, for tools/ledger-build.py."""
import json, os, re, sys, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLUGS = set('amex visa mastercard dgn diners pulse star accel nyce shazam culiance jeanie affn interlink plus maestro cirrus jcb unionpay interac eftpos rupay cb girocard elo cross'.split())
ALIAS = {'discover': 'dgn', 'discover global network': 'dgn', 'capital one': 'dgn', 'capitalone': 'dgn', 'capital-one': 'dgn',
         'american express': 'amex', 'american-express': 'amex', 'diners club': 'diners', 'diners-club': 'diners',
         'cartes bancaires': 'cb', 'cartes-bancaires': 'cb', 'ap+': 'eftpos', 'applus': 'eftpos', 'ap-plus': 'eftpos',
         'npci': 'rupay', 'upi': 'unionpay', 'fiserv': 'star', 'fis': 'nyce', 'worldpay': 'jeanie', 'multiple': 'cross', 'all': 'cross'}
def cell(s): return re.sub(r'\s+', ' ', '' if s is None else str(s)).replace('|', '\\|').strip()
def norm_url(u):
    u = (u or '').strip(); u = re.sub(r'#.*$', '', u); u = re.sub(r'[?&](utm_[^&]*|ref=[^&]*)', '', u)
    return u.rstrip('/').lower()
def slug(n):
    n = (n or '').strip().lower()
    return n if n in SLUGS else ALIAS.get(n, 'cross')
round_name, path = sys.argv[1], sys.argv[2]
DEFAULT = sys.argv[3] if len(sys.argv) > 3 else '2026-09-25'
def acc(r):
    m = re.search(r'20\d\d-\d\d-\d\d', (r.get('fetch') or '') + ' ' + (r.get('note') or ''))
    return m.group(0) if m and m.group(0) >= '2026-09-20' else DEFAULT
rows = json.load(open(path))
reg = json.load(open(os.path.join(ROOT, 'ledger', 'ids.json')))
known = {k for d in reg.values() for k in d}
by = collections.defaultdict(list); skipped = 0
for r in rows:
    if r.get('ledger_id') or not r.get('url') or not r.get('claim'): skipped += 1; continue
    s = slug(r.get('network'))
    if norm_url(r['url']) + '\t' + cell(r['claim'])[:80] in known: skipped += 1; continue
    by[s].append({'dimension': 'insights', 'claim': r['claim'], 'quote': r.get('quote', ''), 'url': r['url'], 'title': r.get('title', ''),
                  'publisher': r.get('publisher', ''), 'published': r.get('published', ''), 'label': r.get('label', 'Reported'),
                  'fetch': r.get('fetch', ''), 'accessed': acc(r), 'note': f'Added by the insight work ({round_name}), accessed {acc(r)}. ' + (r.get('note') or '')})
for s, cl in by.items():
    d = os.path.join(ROOT, 'ledger', 'raw', s); os.makedirs(d, exist_ok=True)
    f = os.path.join(d, f'insights-{round_name}.json')
    old = json.load(open(f))['claims'] if os.path.exists(f) else []
    seen = {(norm_url(c['url']), cell(c['claim'])[:80]) for c in old}
    old += [c for c in cl if (norm_url(c['url']), cell(c['claim'])[:80]) not in seen]
    json.dump({'network': s, 'dimension': 'insights', 'accessed': '2026-09-25', 'claims': old}, open(f, 'w'), indent=1, ensure_ascii=False)
print(f'{sum(len(v) for v in by.values())} rows added across {len(by)} networks, {skipped} skipped as already in the ledger')
