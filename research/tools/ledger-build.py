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
VER = {}
_vdir = os.path.join(ROOT, 'ledger', 'verify', 'out')
if os.path.isdir(_vdir):
    _files = sorted(os.listdir(_vdir), key=lambda f: (0 if f.startswith('auto') else 1, f))
    for _f in _files:
        if not _f.endswith('.json'): continue
        try:
            for _r in json.load(open(os.path.join(_vdir, _f))).get('results', []): VER[_r['id']] = _r
        except Exception: pass
ALLROWS = []
REG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ledger', 'ids.json')
REG = json.load(open(REG_PATH)) if os.path.exists(REG_PATH) else {}
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
    raws = sorted(glob.glob(os.path.join(RAW, slug, '*.json'))) + ([f for f in glob.glob(os.path.join(RAW, 'cross', 'demos-*.json'))] if slug != 'cross' else [])
    walks = sorted(glob.glob(os.path.join(WALKS, slug + '*.json')))
    if not raws and not walks: return None
    out = os.path.join(LEDGER, slug + '.md'); existing = load_existing(out)
    claims, notfound, contradictions, gated, seen, demos = [], [], [], [], set(), []
    for f in raws:
        try: d = json.load(open(f))
        except Exception as e: print(f'  skip {f}: {e}'); continue
        if os.path.basename(f).startswith('demos'):
            AL = {'npci': 'rupay', 'ap-plus': 'eftpos', 'applus': 'eftpos', 'upi': 'unionpay', 'fiserv': 'star', 'worldpay': 'jeanie', 'fis': 'nyce'}
            demos += [k for k in d.get('kept', []) if not k.get('network') or AL.get(k.get('network'), k.get('network')) == slug]; continue
        dim = d.get('dimension', '')
        for c in d.get('claims', []):
            key = (norm_url(c.get('url')), cell(c.get('claim'))[:80])
            if key in seen: continue
            seen.add(key); c = dict(c); c.setdefault('dimension', dim.split('-')[0] if '-' in dim and not c.get('dimension') else dim); c['_key'] = key; claims.append(c)
        notfound += d.get('not_found', []); contradictions += d.get('contradictions', []); gated += d.get('gated_surfaces', [])
    # ids come from ledger/ids.json, which only grows: an id is assigned once and never reused,
    # whether its claim is kept, moved to the unverified list or dropped. A claim whose URL was
    # re-pointed keeps its id through a match on the claim text alone.
    reg = REG.setdefault(slug, {})
    by_claim = {}
    for k, v in reg.items(): by_claim.setdefault(k.split('\t', 1)[1], set()).add(v)
    used = set(reg.values())
    n = max([int(v.rsplit('-', 1)[1]) for v in used] or [0])
    taken = set()
    def assign(c):
        nonlocal n
        k = c['_key'][0] + '\t' + c['_key'][1]
        i = reg.get(k)
        if not i:
            cand = sorted(by_claim.get(c['_key'][1], set()) - taken)
            if len(cand) == 1: i = cand[0]; reg[k] = i
        if not i or i in taken:
            n += 1; i = f'{slug}-{n:03d}'; reg[k] = i
        taken.add(i); return i
    for c in claims: c['id'] = assign(c)
    claims.sort(key=lambda c: int(c['id'].split('-')[-1]))
    by_label = collections.Counter(c.get('label', '') for c in claims)
    lines = [f"# {NAME.get(slug, slug)}", '', f"Kind {KIND.get(slug, '')} · Accessed {min([c.get('accessed') or '2026-09-25' for c in claims] or ['2026-09-25'])} to {max([c.get('accessed') or '2026-09-25' for c in claims] or ['2026-09-25'])} · Viewport 1440 by 1000 · Logged out unless the note says otherwise · {len(claims)} claims: {by_label.get('Verified', 0)} Verified, {by_label.get('Reported', 0)} Reported, {by_label.get('Vendor', 0)} Vendor", '',
             '## Sources', '', '| Id | Claim | Dimension | Title | Publisher | URL | Published | Accessed | Confidence | Archive | Note |', '|---|---|---|---|---|---|---|---|---|---|---|']
    unverified = []
    kept_claims = []
    for c in claims:
        v = VER.get(c['id'])
        ALLROWS.append({'id': c['id'], 'claim': c.get('claim'), 'quote': c.get('quote'), 'url': c.get('url'), 'title': c.get('title'), 'publisher': c.get('publisher'), 'confidence': c.get('label'), 'auto': (v or {}).get('result'), 'auto_note': (v or {}).get('note')})
        if v and v.get('result') in ('unsupported', 'page-changed') and not v.get('archive_url'):
            unverified.append(f"- {c['id']} · {cell(c.get('claim'))} · {v['result']} · {cell(v.get('note'))} · {cell(c.get('url'))}"); continue
        if v and v.get('result') == 'not-fetched' and not v.get('archive_url'):
            unverified.append(f"- {c['id']} · {cell(c.get('claim'))} · could not be re-read by any method on 2026-09-25 · {cell(v.get('note'))} · {cell(c.get('url'))}")
        c['_ver'] = v; kept_claims.append(c)
    claims = kept_claims
    for c in claims:
        note = cell(c.get('note', '')); q = cell(c.get('quote', ''))
        if q: note = (f'Quote: "{q}"' + (' · ' + note if note else ''))
        if c.get('fetch') and c['fetch'] != 'webfetch': note += (' · ' if note else '') + f"fetch {c['fetch']}"
        if c.get('networks'): note += (' · ' if note else '') + 'networks ' + ','.join(c['networks'])
        v = c.get('_ver'); arch = ''
        if v:
            arch = cell(v.get('archive_url') or '')
            vd = v.get('date') or '2026-09-25'
            tag = {'supports': 'verified ' + vd, 'qualified': 'verified with qualification: ' + cell(v.get('qualification')), 'unsupported': 'quote not found on the live page, archived copy kept', 'page-changed': 'page changed, archived copy kept', 'not-fetched': 'not re-read, blocked on ' + vd}.get(v.get('result'), '')
            if tag: note += (' · ' if note else '') + tag
        lines.append(f"| {c['id']} | {cell(c.get('claim'))} | {cell(c.get('dimension'))} | {cell(c.get('title'))} | {cell(c.get('publisher'))} | {cell(c.get('url'))} | {cell(c.get('published') or 'n.d.')} | {cell(c.get('accessed') or '2026-09-25')} | {cell(c.get('label'))} | {arch} | {note} |")
    # walk records become citable observations, one row per walk, ids stable by walk name
    shots = []
    for w in walks:
        try: d = json.load(open(w))
        except Exception: continue
        for s in d.get('screenshots', []): shots.append((d.get('seed', ''), s))
        wname = os.path.basename(w)[:-5]; label = wname[len(slug):].lstrip('-') or 'site'
        S0 = (d.get('stations') or {}).get('S0') or {}; S1 = (d.get('stations') or {}).get('S1') or {}
        if d.get('tier') == 'shot':
            lines.append(f"| {slug}-w-{label} | Screenshot of {cell(d.get('seed'))} on {cell(d.get('date'))}, logged out at 1440 by 1000 | shot | {cell(S1.get('title') or d.get('seed'))} | This research, observed in the browser | {cell(S0.get('final_url') or d.get('seed'))} | {cell(d.get('date'))} | {cell(d.get('date'))} | Verified | | record ledger/walks/{wname}.json |")
        else:
            lines.append(f"| {slug}-w-{label} | Station walk of {cell(d.get('seed'))} on {cell(d.get('date'))}: {len(d.get('visited', []))} pages visited logged out at 1440 by 1000, {len(d.get('screenshots', []))} screenshots | walk | {cell(S1.get('title') or d.get('seed'))} | This research, observed in the browser | {cell(S0.get('final_url') or d.get('seed'))} | {cell(d.get('date'))} | {cell(d.get('date'))} | Verified | | record ledger/walks/{wname}.json |")
    lines += ['', '## Screenshots', '', '| Id | Step | URL | Captured | File | Width | KB |', '|---|---|---|---|---|---|---|']
    for i, (seed, s) in enumerate(shots, 1):
        lines.append(f"| {cell(s.get('id') or f'{slug}-s{i:02d}')} | {cell(s.get('station'))} {cell(s.get('note'))} | {cell(s.get('url'))} | {cell(s.get('captured'))} | {cell(s.get('file'))} | 1400 | {s.get('kb', '')} |")
    lines += ['', '## Demonstrations', '', '| Id | Title | Channel | Official | Published | Duration | URL | Accessed | What it shows | Confidence | Excerpts | Frames |', '|---|---|---|---|---|---|---|---|---|---|---|---|']
    for i, v in enumerate(demos, 1):
        conf = 'Verified' if v.get('official') else 'Reported'
        lines.append(f"| {slug}-v{i:02d} | {cell(v.get('title'))} | {cell(v.get('channel_or_publisher'))} | {'yes' if v.get('official') else 'no'} | {cell(v.get('published') or 'n.d.')} | {cell(v.get('duration_s'))} | {cell(v.get('url'))} | 2026-09-25 | {cell(v.get('what_it_shows'))} · priority {cell(v.get('priority'))} | {conf} |  |  |")
    lines += ['', '## Sentiment', '', '| Id | Platform | Date | Audience | Stance | Topic | Author as shown | Excerpt | URL | Archive |', '|---|---|---|---|---|---|---|---|---|---|']
    sfiles = sorted(glob.glob(os.path.join(RAW, slug, 'sentiment*.json'))) + (sorted(glob.glob(os.path.join(RAW, 'cross', 'sentiment-*.json'))) if slug != 'cross' else [])
    items, seen_i = [], set()
    for f in sfiles:
        try: d = json.load(open(f))
        except Exception: continue
        for it in d.get('items', []):
            net = it.get('network') or d.get('network')
            if net != slug and not (os.path.dirname(f).endswith(slug)): continue
            if os.path.dirname(f).endswith('cross') and net != slug: continue
            k = (norm_url(it.get('url')), cell(it.get('excerpt'))[:60])
            if k in seen_i: continue
            seen_i.add(k); items.append(it)
    items.sort(key=lambda it: (it.get('date') or ''), reverse=True)
    for i, it in enumerate(items, 1):
        old_tag = ' (older)' if it.get('older') else ''
        lines.append(f"| {slug}-q{i:02d} | {cell(it.get('platform'))} | {cell(it.get('date'))}{old_tag} | {cell(it.get('audience'))} | {cell(it.get('stance'))} | {cell(it.get('topic'))} | {cell(it.get('author_as_shown'))} | {cell(it.get('excerpt'))} | {cell(it.get('url'))} | {cell(it.get('archive_url') or '')} |")
    lines += ['', '## Gated surfaces named', '']
    seen_g = set()
    for g in gated:
        k = (cell(g.get('name')).lower(), norm_url(g.get('url')))
        if k in seen_g or not k[0]: continue
        seen_g.add(k); lines.append(f"- {cell(g.get('name'))}{' · ' + cell(g.get('url')) if g.get('url') else ''} (named at {cell(g.get('named_at'))})")
    lines += ['', '## Contradictions', '']
    for x in contradictions: lines.append(f"- {cell(x.get('a'))} · versus · {cell(x.get('b'))} · {' · '.join(cell(u) for u in x.get('urls', []))}")
    lines += ['', '## Claims this research could not verify', '']
    lines += unverified or ['- None.']
    lines += ['', '## Not established', '']
    seen_q = set()
    for q in notfound:
        k = cell(q.get('query')).lower()
        if k in seen_q or not k: continue
        seen_q.add(k); lines.append(f"- {cell(q.get('query'))} · searched {cell(q.get('where'))} · {cell(q.get('date'))}")
    open(out, 'w').write('\n'.join(lines) + '\n')
    return dict(slug=slug, quotes=len(items), unverified=len(unverified), claims=len(claims), shots=len(shots), demos=len(demos), gated=len(seen_g), notfound=len(seen_q), labels=dict(by_label))
slugs = [x for x in (sys.argv[1:] or sorted({os.path.basename(p) for p in glob.glob(os.path.join(RAW, '*')) if os.path.isdir(p)} | {re.sub(r'-.*$', '', os.path.basename(p)[:-5]) for p in glob.glob(os.path.join(WALKS, '*.json'))})) if x != 'rungs']
for s in slugs:
    r = build(s)
    if r: print(r)
json.dump(REG, open(REG_PATH, 'w'), indent=0, ensure_ascii=False, sort_keys=True)
if not sys.argv[1:]: json.dump(ALLROWS, open(os.path.join(ROOT, 'ledger', 'verify', 'all-rows.json'), 'w'), indent=1, ensure_ascii=False)
