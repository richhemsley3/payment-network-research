#!/usr/bin/env python3
"""Applies verification and refutation outcomes from ledger/verify/out/*.json to the ledgers.
Each output file: {"results": [{"id": "...", "result": "supports|qualified|unsupported|page-changed|not-fetched", "qualification": "", "fetch": "", "archive_url": "", "note": ""}]}
Refutation files: {"refutations": [{"id": "...", "refuted": true|false, "evidence_url": "", "evidence_quote": "", "reason": ""}]} (three per claim, majority rules)
A claim that is unsupported or page-changed with no archive, or refuted by two of three, moves to the ledger's "Claims this research could not verify" list."""
import json, os, glob, re, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
res, refs = {}, collections.defaultdict(list)
for f in glob.glob(os.path.join(ROOT, 'ledger', 'verify', 'out', '*.json')):
    try: d = json.load(open(f))
    except Exception as e: print('skip', f, e); continue
    for r in d.get('results', []): res[r['id']] = r
    for r in d.get('refutations', []): refs[r['id']].append(r)
moved = kept = qualified = archived = 0
for lf in glob.glob(os.path.join(ROOT, 'ledger', '*.md')):
    if lf.endswith('README.md'): continue
    lines = open(lf).read().split('\n'); out = []; dropped = []; in_sources = False
    for line in lines:
        if line.startswith('## '): in_sources = line.strip() == '## Sources'
        m = re.match(r'^\| (\w+-\d{3}) \|', line) if in_sources else None
        if not m: out.append(line); continue
        cid = m.group(1); cells = line[1:-1].split(' | '); r = res.get(cid); rf = refs.get(cid, [])
        if len(cells) < 11: out.append(line); continue
        refuted = sum(1 for x in rf if x.get('refuted')) >= 2 and len(rf) >= 3
        note = cells[10]
        if r and r.get('archive_url') and not cells[9].strip(): cells[9] = ' ' + r['archive_url'] + ' '; archived += 1
        if refuted:
            ev = next((x for x in rf if x.get('refuted')), {}); dropped.append(f"- {cid} · refuted by two of three readers · {ev.get('reason','')} · {ev.get('evidence_url','')}"); moved += 1; continue
        if r:
            if r['result'] == 'supports': note += ' · verified'; kept += 1
            elif r['result'] == 'qualified': note += ' · qualified: ' + (r.get('qualification') or ''); qualified += 1
            elif r['result'] in ('unsupported', 'page-changed') and not (r.get('archive_url') or cells[9].strip()): dropped.append(f"- {cid} · {r['result']} · {r.get('note','')}"); moved += 1; continue
            elif r['result'] in ('unsupported', 'page-changed'): note += f" · {r['result']}, archived copy kept"; kept += 1
            else: note += ' · not fetched'
        cells[10] = note.strip()
        out.append('|' + ' | '.join(c.strip() for c in cells).join([' ', ' ']) + '|' if False else '| ' + ' | '.join(c.strip() for c in cells) + ' |')
    if dropped:
        text = '\n'.join(out); head = '## Claims this research could not verify'
        text = text.rstrip('\n') + f"\n\n{head}\n\n" + '\n'.join(dropped) + '\n' if head not in text else text.replace(head + '\n', head + '\n' + '\n'.join(dropped) + '\n')
        open(lf, 'w').write(text)
    else: open(lf, 'w').write('\n'.join(out))
print(f'verified {kept}, qualified {qualified}, moved out {moved}, archive links added {archived}; {len(res)} results and {sum(len(v) for v in refs.values())} refutations read')
