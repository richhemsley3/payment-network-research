#!/usr/bin/env python3
"""A labelled contact sheet of every screenshot in one walk record, for reading in one look.
usage: python3 tools/sheet.py <walk-name> [tile-width]  -> scratchpad/sheet-<walk>.png"""
import json, os, sys
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
name = sys.argv[1]; TW = int(sys.argv[2]) if len(sys.argv) > 2 else 700
d = json.load(open(os.path.join(ROOT, 'ledger', 'walks', name + '.json')))
shots = [s for s in d['screenshots'] if os.path.exists(os.path.join(ROOT, s['file']))]
ims = []
for s in shots:
    im = Image.open(os.path.join(ROOT, s['file'])).convert('RGB'); r = TW / im.width; im = im.resize((TW, int(im.height * r))); ims.append((s, im))
COLS = 2; rows = (len(ims) + 1) // 2
H = 0; heights = []
for i in range(rows): h = max(im.height for s, im in ims[i*2:i*2+2]); heights.append(h); H += h + 28
sheet = Image.new('RGB', (COLS * (TW + 12), H), 'white'); dr = ImageDraw.Draw(sheet); y = 0
for i in range(rows):
    for j, (s, im) in enumerate(ims[i*2:i*2+2]):
        x = j * (TW + 12); dr.text((x + 4, y + 4), f"{s['id']} · {s['station']} {s['note']} · {s['url'][:80]}", fill='black'); sheet.paste(im, (x, y + 22))
    y += heights[i] + 28
out = f'/private/tmp/claude-501/-Users-richhemsley-Desktop-Claude/a7b17a35-5948-40cb-a79f-825d4720b44b/scratchpad/sheet-{name}.png'; sheet.save(out); print(out, len(ims), 'shots', sheet.size)
