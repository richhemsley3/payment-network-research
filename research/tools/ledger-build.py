#!/usr/bin/env python3
"""Builds ledger/<slug>.md from ledger/raw/<slug>/*.json and ledger/walks/<slug>*.json.
Ids are assigned once and kept: an existing ledger's id→url+claim map is honoured, new rows get the next number.
usage: python3 tools/ledger-build.py [slug ...]   (default: every slug with raw or walk files)"""
import json, os, re, sys, glob, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW, WALKS, LEDGER = (os.path.join(ROOT, 'ledger', d) for d in ('raw', 'walks', ''))
LEDGER = os.path.join(ROOT, 'ledger')
KIND = {'amex': 'global card', 'visa': 'global card', 'mastercard': 'global card', 'dgn': 'global card', 'diners': 'global card', 'pulse': 'US debit and ATM',
        'star': 'US debit and ATM', 'accel': 'US debit and ATM', 'nyce': 'US debit and ATM', 'shazam': 'US debit and ATM', 'culiance': 'US debit and ATM', 'jeanie': 'US debit and ATM', 'affn': 'US debit and ATM',
        'interlink': 'US debit and ATM', 'plus': 'US debit and ATM', 'maestro': 'US debit and ATM', 'cirrus': 'US debit and ATM',
        'jcb': 'domestic scheme', 'unionpay': 'domestic scheme', 'interac': 'domestic scheme', 'eftpos': 'domestic scheme', 'rupay': 'domestic scheme', 'cb': 'domestic scheme', 'girocard': 'domestic scheme', 'elo': 'domestic scheme', 'cross': 'cross-cutting'}
NAME = {'amex': 'American Express', 'visa': 'Visa', 'mastercard': 'Mastercard', 'dgn': 'Discover Global Network', 'diners': 'Diners Club International', 'pulse': 'PULSE', 'star': 'STAR', 'accel': 'Accel', 'nyce': 'NYCE', 'shazam': 'SHAZAM', 'culiance': 'CULIANCE', 'jeanie': 'Jeanie', 'affn': 'AFFN', 'interlink': 'Interlink', 'plus': 'Plus', 'maestro': 'Maestro', 'cirrus': 'Cirrus', 'jcb': 'JCB', 'unionpay': 'UnionPay International', 'interac': 'Interac', 'eftpos': 'eftpos', 'rupay': 'RuPay', 'cb': 'Cartes Bancaires', 'girocard': 'girocard', 'elo': 'Elo', 'cross': 'Cross-cutting sources'}
def cell(s):
    s = '' if s is None else str(s)
    return re.sub(r'\s+', ' ', s).replace('|', '\\|').strip()
def norm_url(u):
    u = (u or '').strip(); u = re.sub(r'#.*$', '', u); u = re.sub(r'[?&](utm_[^&]*|ref=[^&]*)', '', u)
    return u.rstrip('/').lower()
def load_existing(path):
    ids = {}
    if not os.path.exists(path): return ids
    for line in open(path):
        m = re.match(r'^\| (\w+-\d{3}) \| (.*?) \| .*? \| .*? \| .*? \| (\S+) \|', line)
        if m: ids[(norm_url(m.group(3)), m.group(2)[:80])] = m.group(1)
    return ids
def build(slug):
    raws = sorted(glob.glob(os.path.join(RAW, slug, '*.json')))
    walks = sorted(glob.glob(os.path.join(WALKS, slug + '*.json')))
    if not raws and not walks: return None
    out = os.path.join(LEDGER, slug + '.md'); existing = load_existing(out)
    claims, notfound, contradictions, gated, seen, demos = [], [], [], [], set(), []
    for f in raws:
        try: d = json.load(open(f))
        except Exception as e: print(f'  skip {f}: {e}'); continue
        if os.path.basename(f) == 'demos.json':
            demos = d.get('kept', []); continue
        dim = d.get('dimension', '')
        for c in d.get('claims', []):
            key = (norm_url(c.get('url')), cell(c.get('claim'))[:80])
            if key in seen: continue
            seen.add(key); c = dict(c); c.setdefault('dimension', dim.split('-')[0] if '-' in dim and not c.get('dimension') else dim); c['_key'] = key; claims.append(c)
        notfound += d.get('not_found', []); contradictions += d.get('contradictions', []); gated += d.get('gated_surfaces', [])
    # ids: keep existing, then next free
    used = set(existing.values()); n = 0
    def next_id():
        nonlocal n
        while True:
            n += 1; cand = f'{slug}-{n:03d}'
            if cand not in used: used.add(cand); return cand
    for c in claims: c['id'] = existing.get(c['_key']) or next_id()
    claims.sort(key=lambda c: int(c['id'].split('-')[-1]))
    by_label = collections.Counter(c.get('label', '') for c in claims)
    lines = [f"# {NAME.get(slug, slug)}", '', f"Kind {KIND.get(slug, '')} · Accessed 2026-09-25 · Viewport 1440 by 1000 · Logged out unless the note says otherwise · {len(claims)} claims: {by_label.get('Verified', 0)} Verified, {by_label.get('Reported', 0)} Reported, {by_label.get('Vendor', 0)} Vendor", '',
             '## Sources', '', '| Id | Claim | Dimension | Title | Publisher | URL | Published | Accessed | Confidence | Archive | Note |', '|---|---|---|---|---|---|---|---|---|---|---|']
    for c in claims:
        note = cell(c.get('note', '')); q = cell(c.get('quote', ''))
        if q: note = (f'Quote: "{q}"' + (' · ' + note if note else ''))
        if c.get('fetch') and c['fetch'] != 'webfetch': note += (' · ' if note else '') + f"fetch {c['fetch']}"
        if c.get('networks'): note += (' · ' if note else '') + 'networks ' + ','.join(c['networks'])
        lines.append(f"| {c['id']} | {cell(c.get('claim'))} | {cell(c.get('dimension'))} | {cell(c.get('title'))} | {cell(c.get('publisher'))} | {cell(c.get('url'))} | {cell(c.get('published') or 'n.d.')} | 2026-09-25 | {cell(c.get('label'))} |  | {note} |")
    # walk records become citable observations, one row per walk, ids stable by walk name
    shots = []
    for w in walks:
        try: d = json.load(open(w))
        except Exception: continue
        for s in d.get('screenshots', []): shots.append((d.get('seed', ''), s))
        wname = os.path.basename(w)[:-5]; label = wname[len(slug):].lstrip('-') or 'site'
        S0 = (d.get('stations') or {}).get('S0') or {}; S1 = (d.get('stations') or {}).get('S1') or {}
        lines.append(f"| {slug}-w-{label} | Station walk of {cell(d.get('seed'))} on {cell(d.get('date'))}: {len(d.get('visited', []))} pages visited logged out at 1440 by 1000, {len(d.get('screenshots', []))} screenshots | walk | {cell(S1.get('title') or d.get('seed'))} | This research, observed in the browser | {cell(S0.get('final_url') or d.get('seed'))} | {cell(d.get('date'))} | {cell(d.get('date'))} | Verified | | record ledger/walks/{wname}.json |")
    lines += ['', '## Screenshots', '', '| Id | Step | URL | Captured | File | Width | KB |', '|---|---|---|---|---|---|---|']
    for i, (seed, s) in enumerate(shots, 1):
        lines.append(f"| {cell(s.get('id') or f'{slug}-s{i:02d}')} | {cell(s.get('station'))} {cell(s.get('note'))} | {cell(s.get('url'))} | {cell(s.get('captured'))} | {cell(s.get('file'))} | 1400 | {s.get('kb', '')} |")
    lines += ['', '## Demonstrations', '', '| Id | Title | Channel | Official | Published | Duration | URL | Accessed | What it shows | Confidence | Excerpts | Frames |', '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for i, v in enumerate(demos, 1):
        conf = 'Verified' if v.get('official') else 'Reported'
        lines.append(f"| {slug}-v{i:02d} | {cell(v.get('title'))} | {cell(v.get('channel_or_publisher'))} | {'yes' if v.get('official') else 'no'} | {cell(v.get('published') or 'n.d.')} | {cell(v.get('duration_s'))} | {cell(v.get('url'))} | 2026-09-25 | {cell(v.get('what_it_shows'))} · priority {cell(v.get('priority'))} | {conf} |  |  |")
    lines += ['', '## Sentiment', '', '| Id | Platform | Date | Audience | Stance | Topic | Author as shown | Excerpt | URL | Archive |', '|---|---|---|---|---|---|---|---|---|---|']
    lines += ['', '## Gated surfaces named', '']
    seen_g = set()
    for g in gated:
        k = (cell(g.get('name')).lower(), norm_url(g.get('url')))
        if k in seen_g or not k[0]: continue
        seen_g.add(k); lines.append(f"- {cell(g.get('name'))}{' · ' + cell(g.get('url')) if g.get('url') else ''} (named at {cell(g.get('named_at'))})")
    lines += ['', '## Contradictions', '']
    for x in contradictions: lines.append(f"- {cell(x.get('a'))} · versus · {cell(x.get('b'))} · {' · '.join(cell(u) for u in x.get('urls', []))}")
    lines += ['', '## Not established', '']
    seen_q = set()
    for q in notfound:
        k = cell(q.get('query')).lower()
        if k in seen_q or not k: continue
        seen_q.add(k); lines.append(f"- {cell(q.get('query'))} · searched {cell(q.get('where'))} · {cell(q.get('date'))}")
    open(out, 'w').write('\n'.join(lines) + '\n')
    return dict(slug=slug, claims=len(claims), shots=len(shots), demos=len(demos), gated=len(seen_g), notfound=len(seen_q), labels=dict(by_label))
slugs = [x for x in (sys.argv[1:] or sorted({os.path.basename(p) for p in glob.glob(os.path.join(RAW, '*')) if os.path.isdir(p)} | {re.sub(r'-.*$', '', os.path.basename(p)[:-5]) for p in glob.glob(os.path.join(WALKS, '*.json'))})) if x != 'rungs']
for s in slugs:
    r = build(s)
    if r: print(r)
