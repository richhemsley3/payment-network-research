#!/usr/bin/env python3
"""One extra screenshot outside the station script, recorded as its own small walk record so it is citable.
usage: python3 tools/extra-shot.py <slug> <label> <url> "<note>" [w h]"""
import json, os, sys, subprocess, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
slug, label, url, note = sys.argv[1:5]; w, h = (sys.argv[5], sys.argv[6]) if len(sys.argv) > 6 else ('1440', '1000')
today = datetime.date.today().isoformat(); stamp = today.replace('-', '')
rec_path = os.path.join(ROOT, 'ledger', 'walks', f'{slug}-{label}.json')
rec = json.load(open(rec_path)) if os.path.exists(rec_path) else {'network': slug, 'seed': url, 'tier': 'shot', 'date': today, 'viewport': f'{w}x{h}', 'logged_out': True, 'stations': {'S0': {'final_url': url}, 'S1': {'title': note}}, 'visited': [{'url': url, 'why': 'extra shot'}], 'screenshots': [], 'errors': []}
n = len(rec['screenshots']) + 1; base = f'{slug}-{label}-s1-{n:02d}-{stamp}'; out = os.path.join(ROOT, 'assets', slug, base + '.webp')
env = dict(os.environ, NODE_PATH=os.path.join(ROOT, '..', 'node_modules'))
r = subprocess.run(['node', os.path.join(ROOT, 'tools', 'shoot-site.js'), url, out, w, h], cwd=ROOT, env=env, capture_output=True, text=True, timeout=150)
if not os.path.exists(out): print('failed', r.stdout[-200:], r.stderr[-300:]); sys.exit(1)
rec['screenshots'].append({'id': f'{slug}-{label}-s{n:02d}', 'station': 'S1', 'note': note, 'url': url, 'captured': today, 'file': f'assets/{slug}/{base}.webp', 'kb': round(os.path.getsize(out) / 1024)})
json.dump(rec, open(rec_path, 'w'), indent=1); print(rec['screenshots'][-1])
