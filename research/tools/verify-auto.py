#!/usr/bin/env python3
"""First-pass verification without agents: fetch every cited URL (curl, then pypdf for PDFs, then a rendered page for script shells),
look for the ledger's verbatim quote, and look up an archive.org snapshot. Writes ledger/verify/out/auto.json and a residue list.
usage: python3 tools/verify-auto.py [--workers 6] [--only slug]"""
import json, os, re, sys, subprocess, html, time, collections, urllib.parse
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = '/private/tmp/claude-501/-Users-richhemsley-Desktop-Claude/a7b17a35-5948-40cb-a79f-825d4720b44b/scratchpad'
CACHE = os.path.join(SP, 'pages'); os.makedirs(CACHE, exist_ok=True)
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
workers = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 6
only = sys.argv[sys.argv.index('--only') + 1] if '--only' in sys.argv else None
S = [r for r in json.load(open(os.path.join(ROOT, 'sources.json'))) if r['kind'] == 'source' and '-w-' not in r['id'] and (only is None or r['network'] == only)]
def norm(s): return re.sub(r'[^a-z0-9]+', ' ', html.unescape(s or '').lower()).strip()
def quote_of(r):
    m = re.search(r'Quote: "(.*?)"(?: ·|$)', r.get('note') or ''); return m.group(1) if m else ''
def key(u): return re.sub(r'[^A-Za-z0-9]+', '_', u)[:150]
def fetch(url):
    p = os.path.join(CACHE, key(url) + '.txt')
    if os.path.exists(p): return open(p).read()
    text, method = '', None
    try:
        hdr = ['-H', 'User-Agent: ' + UA] if 'sec.gov' in url else ['-A', UA]
        r = subprocess.run(['curl', '-sL', '--compressed', '--max-time', '40'] + hdr + [url], capture_output=True, timeout=60)
        body = r.stdout
        if body[:5] == b'%PDF-' or url.lower().endswith('.pdf'):
            pp = os.path.join(CACHE, key(url) + '.pdf'); open(pp, 'wb').write(body)
            rr = subprocess.run([os.path.join(SP, 'venv', 'bin', 'python'), '-c', f"import pypdf,sys; r=pypdf.PdfReader({pp!r}); print('\\n'.join((pg.extract_text() or '') for pg in r.pages[:400]))"], capture_output=True, text=True, timeout=180)
            text, method = rr.stdout, 'pdf'
        else:
            t = body.decode('utf-8', 'ignore'); t = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', t, flags=re.S); t = html.unescape(re.sub(r'<[^>]+>', ' ', t)); text, method = t, 'curl'
    except Exception as e: text = ''
    if len(norm(text)) < 800:
        try:
            rr = subprocess.run(['node', os.path.join(ROOT, 'tools', 'text.js'), url], cwd=ROOT, env=dict(os.environ, NODE_PATH=os.path.join(ROOT, '..', 'story', 'brightline-story', 'node_modules')), capture_output=True, text=True, timeout=90)
            if len(norm(rr.stdout)) > len(norm(text)): text, method = rr.stdout, 'rendered'
        except Exception: pass
    open(p, 'w').write((method or 'none') + '\n' + text); return (method or 'none') + '\n' + text
def archive(url):
    try:
        r = subprocess.run(['curl', '-s', '--max-time', '20', 'https://archive.org/wayback/available?url=' + urllib.parse.quote(url, safe='')], capture_output=True, text=True, timeout=30)
        d = json.loads(r.stdout); c = (d.get('archived_snapshots') or {}).get('closest') or {}
        return c.get('url')
    except Exception: return None
by_url = collections.defaultdict(list)
for r in S: by_url[r['url']].append(r)
urls = list(by_url); results = {}; arch = {}
def work(u):
    text = fetch(u); method, body = text.split('\n', 1) if '\n' in text else ('none', ''); nb = norm(body); a = archive(u)
    out = []
    for r in by_url[u]:
        q = norm(quote_of(r)); res = 'not-fetched' if method == 'none' or len(nb) < 200 else 'unsupported'
        if q and len(nb) >= 200:
            w = q.split()
            if q in nb: res = 'supports'
            elif len(w) >= 6 and any(' '.join(w[i:i+6]) in nb for i in range(0, len(w) - 5)): res = 'supports'
            elif len(w) < 6 and q in nb: res = 'supports'
        out.append({'id': r['id'], 'result': res, 'fetch': method, 'archive_url': a, 'note': 'auto: quote ' + ('found' if res == 'supports' else 'not found') + f' via {method}, page {len(nb)} chars'})
    return out
t0 = time.time(); allres = []
with ThreadPoolExecutor(max_workers=workers) as ex:
    for i, out in enumerate(ex.map(work, urls)):
        allres += out
        if i % 50 == 0: print(f'{i}/{len(urls)} urls, {int(time.time()-t0)}s', flush=True)
json.dump({'results': allres}, open(os.path.join(ROOT, 'ledger', 'verify', 'out', 'auto.json'), 'w'), indent=1)
c = collections.Counter(r['result'] for r in allres); print(dict(c), f'{len(urls)} urls in {int(time.time()-t0)}s')
residue = [r['id'] for r in allres if r['result'] != 'supports']
json.dump(residue, open(os.path.join(ROOT, 'ledger', 'verify', 'residue.json'), 'w')); print(len(residue), 'claims for agent verification')
