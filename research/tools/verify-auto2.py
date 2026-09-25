#!/usr/bin/env python3
"""Second automatic pass over the verification residue: refetch through the browser's network stack (tools/fetch-browser.js),
extract PDF text with pypdf, and re-check quotes. Writes ledger/verify/out/auto2.json (later files override earlier ones)."""
import json, os, re, sys, subprocess, html, collections, urllib.parse, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = '/private/tmp/claude-501/-Users-richhemsley-Desktop-Claude/a7b17a35-5948-40cb-a79f-825d4720b44b/scratchpad'
CACHE = os.path.join(SP, 'pages2'); os.makedirs(CACHE, exist_ok=True)
env = dict(os.environ, NODE_PATH=os.path.join(ROOT, '..', 'story', 'brightline-story', 'node_modules'))
S = {r['id']: r for r in json.load(open(os.path.join(ROOT, 'sources.json')))}
prev = {r['id']: r for r in json.load(open(os.path.join(ROOT, 'ledger', 'verify', 'out', 'auto.json')))['results']}
skip_hosts = set(sys.argv[1:])  # hosts to leave for another method
def norm(s): return re.sub(r'[^a-z0-9]+', ' ', html.unescape(s or '').lower()).strip()
def quote_of(r):
    m = re.search(r'Quote: "(.*?)"(?: ·|$)', r.get('note') or ''); return m.group(1) if m else ''
def key(u): return re.sub(r'[^A-Za-z0-9]+', '_', u)[:150]
def fetch(url):
    p = os.path.join(CACHE, key(url) + '.txt')
    if os.path.exists(p): return open(p).read()
    raw = os.path.join(CACHE, key(url) + '.bin'); text = ''; method = 'none'
    try:
        r = subprocess.run(['node', os.path.join(ROOT, 'tools', 'fetch-browser.js'), url, raw], cwd=ROOT, env=env, capture_output=True, text=True, timeout=200)
        info = json.loads(r.stdout.strip().splitlines()[-1]) if r.stdout.strip() else {}
        body = open(raw, 'rb').read() if os.path.exists(raw) else b''
        if body[:5] == b'%PDF-':
            rr = subprocess.run([os.path.join(SP, 'venv', 'bin', 'python'), '-c', f"import pypdf; r=pypdf.PdfReader({raw!r}); print('\\n'.join((pg.extract_text() or '') for pg in r.pages[:1600]))"], capture_output=True, text=True, timeout=600)
            text, method = rr.stdout, f"browser-pdf-{info.get('status')}"
        elif info.get('status') == 200:
            t = body.decode('utf-8', 'ignore'); t = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', t, flags=re.S); text, method = html.unescape(re.sub(r'<[^>]+>', ' ', t)), f"browser-html-{info.get('status')}"
        else: method = f"browser-{info.get('status')}"
    except Exception as e: method = 'error'
    open(p, 'w').write(method + '\n' + text); return method + '\n' + text
residue = [rid for rid, r in prev.items() if r['result'] != 'supports' and rid in S]
by_url = collections.defaultdict(list)
for rid in residue:
    u = S[rid]['url']
    if urllib.parse.urlparse(u).netloc in skip_hosts: continue
    by_url[u].append(rid)
out = []; t0 = time.time()
for i, (u, ids) in enumerate(by_url.items()):
    text = fetch(u); method, body = text.split('\n', 1) if '\n' in text else ('none', ''); nb = norm(body)
    for rid in ids:
        q = norm(quote_of(S[rid])); w = q.split(); ok = False
        if q and len(nb) >= 200: ok = (q in nb) or (len(w) >= 6 and any(' '.join(w[j:j+6]) in nb for j in range(0, len(w) - 5)))
        res = 'supports' if ok else ('not-fetched' if len(nb) < 200 else 'unsupported')
        out.append({'id': rid, 'result': res, 'fetch': method, 'archive_url': prev[rid].get('archive_url'), 'note': f"auto2: quote {'found' if ok else 'not found'} via {method}, page {len(nb)} chars"})
    if i % 10 == 0: print(f'{i}/{len(by_url)} urls, {int(time.time()-t0)}s', flush=True)
json.dump({'results': out}, open(os.path.join(ROOT, 'ledger', 'verify', 'out', 'auto2.json'), 'w'), indent=1)
c = collections.Counter(r['result'] for r in out); print(dict(c), 'over', len(out), 'claims,', len(by_url), 'urls')
