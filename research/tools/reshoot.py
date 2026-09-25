#!/usr/bin/env python3
"""Re-shoots the landing (S1) and mobile (S11) screenshots for every walk record with banner clearing, then builds a contact sheet."""
import json, glob, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = dict(os.environ, NODE_PATH=os.path.join(ROOT, '..', 'story', 'brightline-story', 'node_modules'))
jobs = []
for f in sorted(glob.glob(os.path.join(ROOT, 'ledger', 'walks', '*.json'))):
    if f.endswith('rungs.json'): continue
    d = json.load(open(f))
    for s in d.get('screenshots', []):
        if s['station'] in ('S1', 'S11'):
            w, h = ('390', '844') if s['station'] == 'S11' else ('1440', '1000')
            jobs.append((os.path.basename(f)[:-5], s['station'], s['url'], os.path.join(ROOT, s['file']), w, h))
def run(j):
    name, st, url, out, w, h = j
    r = subprocess.run(['node', os.path.join(ROOT, 'tools', 'shoot-site.js'), url, out, w, h], cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
    return f"{name} {st}: {r.stdout.strip()[-120:] or r.stderr.strip()[-120:]}"
with ThreadPoolExecutor(max_workers=4) as ex:
    for line in ex.map(run, jobs): print(line, flush=True)
# contact sheet of every S1
from PIL import Image, ImageDraw
tiles = [(n, o) for (n, st, u, o, w, h) in jobs if st == 'S1' and os.path.exists(o)]
TW, TH, COLS = 320, 224, 5
sheet = Image.new('RGB', (COLS * TW, ((len(tiles) + COLS - 1) // COLS) * (TH + 20)), 'white'); dr = ImageDraw.Draw(sheet)
for i, (n, o) in enumerate(tiles):
    im = Image.open(o).convert('RGB'); im.thumbnail((TW - 8, TH - 8)); x, y = (i % COLS) * TW, (i // COLS) * (TH + 20)
    sheet.paste(im, (x + 4, y + 4)); dr.text((x + 6, y + TH + 2), n, fill='black')
sp = '/private/tmp/claude-501/-Users-richhemsley-Desktop-Claude/a7b17a35-5948-40cb-a79f-825d4720b44b/scratchpad/contact-s1.png'
sheet.save(sp); print('contact sheet', sp, len(tiles), 'tiles')
