#!/usr/bin/env python3
"""Third automatic pass: for residue claims on hosts that block every direct fetch, read the Wayback Machine capture
(the research agents' own route) and re-check quotes. Writes ledger/verify/out/auto3.json."""
import json, os, re, sys, subprocess, html, collections, urllib.parse, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SP = '/private/tmp/claude-501/-Users-richhemsley-Desktop-Claude/a7b17a35-5948-40cb-a79f-825d4720b44b/scratchpad'
CACHE = os.path.join(SP, 'pages3'); os.makedirs(CACHE, exist_ok=True)
hosts = set(sys.argv[1:]) or {'www.mastercard.com', 'www.mastercard.us'}
S = {r['id']: r for r in json.load(open(os.path.join(ROOT, 'sources.json')))}
prev = {}
for f in sorted(os.listdir(os.path.join(ROOT, 'ledger', 'verify', 'out'))):
    if f.startswith('auto') and f.endswith('.json'):
        for r in json.load(open(os.path.join(ROOT, 'ledger', 'verify', 'out', f)))['results']: prev[r['id']] = r
def norm(s): return re.sub(r'[^a-z0-9]+', ' ', html.unescape(s or '').lower()).strip()
def quote_of(r):
    m = re.search(r'Quote: "(.*?)"(?: ·|$)', r.get('note') or ''); return m.group(1) if m else ''
def key(u): return re.sub(r'[^A-Za-z0-9]+', '_', u)[:150]
def fetch(url, archive):
    p = os.path.join(CACHE, key(url) + '.txt')
    if os.path.exists(p): return open(p).read()
    cands = ([archive] if archive else []) + [f'https://web.archive.org/web/2026id_/{url}', f'https://web.archive.org/web/2025id_/{url}']
    text, method = '', 'none'
    for c in cands:
        raw = os.path.join(CACHE, key(url) + '.bin')
        try:
            r = subprocess.run(['curl', '-sL', '--max-time', '180', '-A', 'Mozilla/5.0 research', '-o', raw, '-w', '%{http_code} %{content_type}', c], capture_output=True, text=True, timeout=200)
            code = r.stdout.split(' ')[0]; body = open(raw, 'rb').read() if os.path.exists(raw) else b''
            if code != '200' or len(body) < 500: continue
            if body[:5] == b'%PDF-':
                rr = subprocess.run([os.path.join(SP, 'venv', 'bin', 'python'), '-c', f"import pypdf; r=pypdf.PdfReader({raw!r}); print('\\n'.join((pg.extract_text() or '') for pg in r.pages[:1700]))"], capture_output=True, text=True, timeout=900)
                text, method = rr.stdout, 'wayback-pdf'
            else:
                t = body.decode('utf-8', 'ignore'); t = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', t, flags=re.S); text, method = html.unescape(re.sub(r'<[^>]+>', ' ', t)), 'wayback-html'
            if len(norm(text)) > 500: break
        except Exception: continue
        time.sleep(1)
    open(p, 'w').write(method + '\n' + text); return method + '\n' + text
by_url = collections.defaultdict(list)
for rid, r in prev.items():
    if r['result'] == 'supports' or rid not in S: continue
    u = S[rid]['url']
    if urllib.parse.urlparse(u).netloc in hosts: by_url[u].append(rid)
out = []; t0 = time.time()
for i, (u, ids) in enumerate(by_url.items()):
    arch = next((prev[r].get('archive_url') for r in ids if prev[r].get('archive_url')), None)
    text = fetch(u, arch); method, body = text.split('\n', 1) if '\n' in text else ('none', ''); nb = norm(body)
    for rid in ids:
        q = norm(quote_of(S[rid])); w = q.split(); ok = False
        if q and len(nb) >= 200: ok = (q in nb) or (len(w) >= 6 and any(' '.join(w[j:j+6]) in nb for j in range(0, len(w) - 5)))
        res = 'supports' if ok else ('not-fetched' if len(nb) < 200 else 'unsupported')
        out.append({'id': rid, 'result': res, 'fetch': method, 'archive_url': arch or (f'https://web.archive.org/web/2026id_/{u}' if method != 'none' else None), 'note': f"auto3: quote {'found' if ok else 'not found'} via {method}, page {len(nb)} chars"})
    print(f'{i+1}/{len(by_url)} {u[:80]} {method} {len(nb)}', flush=True)
json.dump({'results': out}, open(os.path.join(ROOT, 'ledger', 'verify', 'out', 'auto3.json'), 'w'), indent=1)
c = collections.Counter(r['result'] for r in out); print(dict(c), 'over', len(out), 'claims,', len(by_url), 'urls in', int(time.time()-t0), 's')
