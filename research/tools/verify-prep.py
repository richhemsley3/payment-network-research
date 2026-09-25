#!/usr/bin/env python3
"""Prepares verification batches and the high-stakes list from sources.json.
Writes ledger/verify/batches.json  [{batch, slug, ids:[...]}]  (15 claims each)
and    ledger/verify/highstakes.json [{id, claim, network}]     (figures, dates, fees, ownership, absence claims)"""
import json, os, re, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = [r for r in json.load(open(os.path.join(ROOT, 'sources.json'))) if r['kind'] == 'source' and '-w-' not in r['id']]
by = collections.defaultdict(list)
for r in S: by[r['network']].append(r['id'])
batches = []
for slug, ids in sorted(by.items()):
    ids.sort(key=lambda i: int(re.sub(r'\D', '', i.split('-')[-1]) or 0))
    for i in range(0, len(ids), 15): batches.append({'batch': f'{slug}-{i//15+1:02d}', 'slug': slug, 'ids': ids[i:i+15]})
json.dump(batches, open(os.path.join(ROOT, 'ledger', 'verify', 'batches.json'), 'w'), indent=1)
HS = re.compile(r'\b\d[\d,.]*\s*(?:%|percent|million|billion|bn|m\b|k\b|countries|ATMs|cards|merchants|members|institutions|products|repositories|bps|basis points|business days|weeks|months|days)|\$\s?\d|€\s?\d|£\s?\d|\b(?:19|20)\d\d\b|\bowned by|\bacquired|\bacquisition|\bcompleted|\bclosed|\bno (?:public|published|portal|status|changelog|test cards|timeline|generic|sdk|cli)|\bnot published|\bnot found|\bdoes not (?:offer|publish|have|ship)|\bonly\b|\bfirst\b|\blargest|\bfee|\binterchange|\bpricing|\bcost', re.I)
hs = [{'id': r['id'], 'network': r['network'], 'claim': r['claim']} for r in S if HS.search(r['claim'] or '')]
json.dump(hs, open(os.path.join(ROOT, 'ledger', 'verify', 'highstakes.json'), 'w'), indent=1)
print(f'{len(S)} claims in {len(batches)} batches; {len(hs)} high-stakes claims ({len(hs)*100//max(1,len(S))}%)')
