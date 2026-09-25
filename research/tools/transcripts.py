#!/usr/bin/env python3
"""Pulls captions (never video) for every kept YouTube item in ledger/raw/<slug>/demos.json.
Writes <scratchpad>/transcripts/<slug>/<id>.txt with one line per caption cue: "[m:ss] text", plus an index.json per slug.
usage: python3 tools/transcripts.py [slug ...] [--priority high,medium]"""
import json, os, re, sys, glob, subprocess, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'ledger', 'raw')
SCRATCH = '/private/tmp/claude-501/-Users-richhemsley-Desktop-Claude/a7b17a35-5948-40cb-a79f-825d4720b44b/scratchpad'
OUT = os.path.join(SCRATCH, 'transcripts'); VENV = os.path.join(SCRATCH, 'venv', 'bin')
args = [a for a in sys.argv[1:] if not a.startswith('--')]
prio = next((a.split('=')[1].split(',') for a in sys.argv[1:] if a.startswith('--priority=')), ['high', 'medium', 'low'])
def yt_id(item):
    u = item.get('url', '') or ''; i = item.get('id', '') or ''
    m = re.search(r'(?:v=|youtu\.be/|shorts/|embed/)([\w-]{11})', u) or re.search(r'^([\w-]{11})$', i)
    return m.group(1) if m else None
def fmt(s):
    s = int(s); return f'{s//60}:{s%60:02d}'
def pull(vid, dst):
    # 1. youtube-transcript-api
    try:
        code = f"""
from youtube_transcript_api import YouTubeTranscriptApi
import json
api = YouTubeTranscriptApi()
tl = api.list('{vid}')
try:
    tr = tl.find_transcript(['en','en-US','en-GB'])
except Exception:
    tr = next(iter(tl))
data = tr.fetch()
print(json.dumps([{{'start': x.start, 'text': x.text}} for x in data]))
"""
        r = subprocess.run([os.path.join(VENV, 'python'), '-c', code], capture_output=True, text=True, timeout=90, env=dict(os.environ, PYTHONWARNINGS='ignore'))
        if r.returncode == 0 and r.stdout.strip().startswith('['):
            cues = json.loads(r.stdout)
            open(dst, 'w').write('\n'.join(f"[{fmt(c['start'])}] {c['text'].strip()}" for c in cues if c['text'].strip()))
            return 'youtube-transcript-api', len(cues)
    except Exception as e:
        pass
    # 2. yt-dlp auto captions (vtt), captions only
    try:
        tmp = dst + '.tmp'
        r = subprocess.run([os.path.join(VENV, 'yt-dlp'), '--skip-download', '--write-auto-sub', '--write-sub', '--sub-lang', 'en.*,en', '--sub-format', 'vtt', '-o', tmp, f'https://www.youtube.com/watch?v={vid}'], capture_output=True, text=True, timeout=120, env=dict(os.environ, PYTHONWARNINGS='ignore'))
        vtts = glob.glob(tmp + '*.vtt')
        if vtts:
            cues, last = [], None
            for line in open(vtts[0], encoding='utf-8', errors='ignore'):
                m = re.match(r'(\d+):(\d+):(\d+)\.\d+ --> ', line)
                if m: last = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)); continue
                t = re.sub(r'<[^>]+>', '', line).strip()
                if t and last is not None and not t.startswith(('WEBVTT', 'Kind:', 'Language:')) and (not cues or cues[-1][1] != t): cues.append((last, t))
            for v in vtts: os.remove(v)
            open(dst, 'w').write('\n'.join(f'[{fmt(s)}] {t}' for s, t in cues))
            return 'yt-dlp-autosub', len(cues)
    except Exception:
        pass
    return None, 0
slugs = args or sorted({os.path.basename(os.path.dirname(p)) for p in glob.glob(os.path.join(RAW, '*', 'demos*.json'))})
for slug in slugs:
    files = sorted(glob.glob(os.path.join(RAW, slug, 'demos*.json')))
    if not files: print(slug, 'no demos file'); continue
    d = {'kept': []}
    for f in files: d['kept'] += json.load(open(f)).get('kept', [])
    os.makedirs(os.path.join(OUT, slug), exist_ok=True)
    idx_path = os.path.join(OUT, slug, 'index.json'); idx = json.load(open(idx_path)) if os.path.exists(idx_path) else {}
    kept = [k for k in d.get('kept', []) if (k.get('priority') or 'low') in prio]
    got = 0
    for k in kept:
        vid = yt_id(k)
        if not vid or vid in idx: continue
        dst = os.path.join(OUT, slug, vid + '.txt')
        method, n = pull(vid, dst)
        idx[vid] = {'title': k.get('title'), 'channel': k.get('channel_or_publisher'), 'official': k.get('official'), 'priority': k.get('priority'), 'url': k.get('url'), 'method': method, 'cues': n, 'file': dst if method else None}
        got += 1 if method else 0
        json.dump(idx, open(idx_path, 'w'), indent=1); time.sleep(1.0)
    print(f'{slug}: {len(kept)} kept in scope, {sum(1 for v in idx.values() if v.get("method"))} transcripts on disk, {sum(1 for v in idx.values() if not v.get("method"))} without captions')
