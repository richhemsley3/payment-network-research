#!/usr/bin/env python3
"""Runs tools/walk.js over every property in tools/properties.txt, four at a time. Logs to the scratchpad."""
import os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIST = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'tools', 'properties.txt')
LOG = '/private/tmp/claude-501/-Users-richhemsley-Desktop-Claude/a7b17a35-5948-40cb-a79f-825d4720b44b/scratchpad/walks'
os.makedirs(LOG, exist_ok=True)
env = dict(os.environ, NODE_PATH=os.path.join(ROOT, '..', 'story', 'brightline-story', 'node_modules'))
rows = [l.strip().split('|') for l in open(LIST) if l.strip() and not l.startswith('#') and '|' in l]
def run(row):
    slug, url, tier = row[0], row[1], row[2] if len(row) > 2 and row[2] else 'A'
    label = row[3] if len(row) > 3 and row[3] else ''
    name = slug + ('-' + label if label else '')
    t0 = time.time(); out = os.path.join(LOG, name + '.log')
    with open(out, 'w') as f:
        p = subprocess.run(['node', os.path.join(ROOT, 'tools', 'walk.js'), slug, url, tier] + ([label] if label else []), cwd=ROOT, env=env, stdout=f, stderr=subprocess.STDOUT, timeout=900)
    tail = open(out).read().strip().splitlines()
    summary = next((l for l in reversed(tail) if l.startswith('{')), tail[-1] if tail else '')
    return f"{name:22s} exit {p.returncode} {int(time.time()-t0):4d}s  {summary[:160]}"
with ThreadPoolExecutor(max_workers=4) as ex:
    for line in ex.map(run, rows): print(line, flush=True)
print('all done')
