#!/usr/bin/env python3
"""Builds journey-map.html, the partner lifecycle journey map.

Reads ledger/journey/tasks.json (the calibrated task list), ledger/teardown/keymap.json and sources.json.
Resolves every id to a ledger id, embeds the tasks and the labels of every cited source as JSON,
and writes a page that draws the map in the browser. Fails on any unknown id or uncited friction."""
import json, os, re, sys, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from labels import compact
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = {r['id']: r for r in json.load(open(os.path.join(ROOT, 'sources.json')))}
KM = json.load(open(os.path.join(ROOT, 'ledger', 'teardown', 'keymap.json')))
D = json.load(open(os.path.join(ROOT, 'ledger', 'journey', 'tasks.json')))
problems, cited = [], set()
def res(ids, where):
    out = []
    for i in ids or []:
        k = i[4:] if i.startswith('new:') else i
        lid = KM.get(k) or (k if k in S else None)
        if not lid: problems.append(f'{where}: unknown id {i}'); continue
        out.append(lid)
    out = list(dict.fromkeys(out)); cited.update(out); return out
def walk(o, where):
    if isinstance(o, dict):
        if 'ids' in o: o['ids'] = res(o['ids'], where)
        for v in o.values(): walk(v, where)
    elif isinstance(o, list):
        for v in o: walk(v, where)
for t in D['tasks']:
    walk(t, t['id'])
    if t['friction']['level'] != 'none found' and not t['friction']['why'].get('ids'): problems.append(f'{t["id"]}: friction level uncited')
    for p in t['friction']['points']:
        if not p.get('ids'): problems.append(f'{t["id"]}: uncited friction point')
def lab(r): return re.sub(r'[,:;·\s]+(Version|Vol\.?|Rev\.?|Edition|Part)?\s*$', '', compact(r))
SRC = {i: {'l': lab(S[i]), 't': (S[i].get('title') or S[i].get('excerpt') or '')[:160], 'p': S[i].get('publisher') or S[i].get('platform') or S[i].get('channel') or '', 'c': S[i].get('confidence') or ('Reported' if S[i].get('kind') == 'quote' else '')} for i in sorted(cited)}
data = json.dumps({'tasks': D['tasks'], 'stages': D['stages'], 'phases': D['phases'], 'src': SRC}, ensure_ascii=False).replace('</', '<\\/')
tpl = open(os.path.join(ROOT, 'src', 'journey-map.html')).read()
out = tpl.replace('/*JOURNEY_DATA*/null', data)
n = len(D['tasks']); sev = sum(1 for t in D['tasks'] if t['friction']['level'] == 'severe'); dif = sum(1 for t in D['tasks'] if t['opportunity']['kind'] == 'differentiator')
out = out.replace('<!-- count:tasks -->', str(n)).replace('<!-- count:severe -->', str(sev)).replace('<!-- count:diff -->', str(dif)).replace('<!-- count:cited -->', f'{len(cited):,}')
open(os.path.join(ROOT, 'journey-map.html'), 'w').write(out)
print(f'{n} tasks, {sev} severe, {dif} differentiators, {len(cited)} sources cited')
if problems: print('\n'.join(problems[:30])); sys.exit(1)
