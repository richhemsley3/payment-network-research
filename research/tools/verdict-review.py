#!/usr/bin/env python3
"""Lists agent verdicts that touch the prose: every qualified, unsupported, page-changed or not-fetched claim
cited in parts/, with the sentence that cites it and the verifier's qualification.
Usage: python3 tools/verdict-review.py ledger/verify/out/agent-07.json [...]"""
import json, re, sys, glob, html
res = {}
for f in sys.argv[1:]:
    for r in json.load(open(f)).get('results', []): res[r['id']] = r
for f in sorted(glob.glob('parts/**/*.html', recursive=True)):
    t = open(f).read()
    for m in re.finditer(r'\{\{(?:cite|ref):([\w+-]+)(?:\|[^}]*)?\}\}', t):
        ids = m.group(1).split('+')
        hit = [i for i in ids if i in res and res[i]['result'] != 'supports']
        if not hit: continue
        start = max(t.rfind('. ', 0, m.start()), t.rfind('>', 0, m.start()), 0)
        sent = re.sub(r'<[^>]+>|\{\{[^}]+\}\}', '', t[start:m.end()]).strip(' .>')
        for i in hit:
            r = res[i]
            print(f"{f} · {i} · {r['result']}\n  prose: {sent[-260:]}\n  verifier: {(r.get('qualification') or r.get('note') or '')[:400]}\n")
