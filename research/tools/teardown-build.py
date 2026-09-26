#!/usr/bin/env python3
"""Renders the lead report, the partner experience stage by stage, from the teardown data.

Inputs (paths passed as arguments, default the scratchpad teardown folder):
  clean/stage-<id>.json   one per stage: summary, by_partner, design_moves, unseen, evidence
  strategy.json           the cross-stage synthesis: thesis, patterns, discover_position, principles, moves, unseen
  keymap.json             evidence key -> ledger id
Writes parts/td-strategy.html, parts/td-stages.html and parts/td-counts.json.
Every cited sentence renders as text plus an {{rcite:...}} marker. Unknown ids fail the build."""
import json, os, re, sys, html, glob, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'ledger', 'teardown')
S = {r['id']: r for r in json.load(open(os.path.join(ROOT, 'sources.json')))}
KM = json.load(open(os.path.join(T, 'keymap.json')))
ORDER = ['1', '2', '3', '4', '5', '6a', '6b', '6c', '7']
NAMES = {'1': 'Evaluate', '2': 'Join and contract', '3': 'Onboard and certify', '4': 'Build and integrate', '5': 'Launch',
         '6a': 'Run: money', '6b': 'Run: disputes and fraud', '6c': 'Run: change, support and incidents', '7': 'Growing the relationship, and leaving it'}
NETS = {'visa': 'Visa', 'mastercard': 'Mastercard', 'amex': 'American Express', 'discover-family': 'Discover family', 'discover': 'Discover family'}
problems, cited = [], set()
def e(s): return html.escape(str(s or ''), quote=False)
def ids_of(ids, where):
    out = []
    for i in ids or []:
        k = i[4:] if i.startswith('new:') else i
        lid = KM.get(k) or (k if k in S else None)
        if not lid: problems.append(f'{where}: unknown id {i}'); continue
        out.append(lid)
    out = list(dict.fromkeys(out)); cited.update(out)
    return out
def sent(item, where):
    t = e(item['text']).rstrip()
    ids = ids_of(item.get('ids'), where)
    if not ids: problems.append(f'{where}: uncited: {item["text"][:70]}')
    c = (' {{rcite:' + '+'.join(ids) + '}}') if ids else ''
    return (t[:-1] + c + '.') if t.endswith('.') and c else t + c
def para(items, where): return ' '.join(sent(x, where) for x in items)
QT = ['Backing Our Partners', 'How We Partner', 'Explore our APIs', 'Explore Our APIs', 'Partner With Us', 'Partner with us']
def quote_titles(h):
    for q in QT: h = h.replace(q, f'<q>{q}</q>')
    return h
def net_name(n):
    n = n or ''
    if n.startswith('other:'): return n[6:].strip().capitalize() if n[6:].strip().islower() else n[6:].strip()
    return NETS.get(n, n)
def stage_link(s): return f'<a class="gn-link" href="#stage-{s}">{e(NAMES.get(str(s), s))}</a>'

stages = {s: json.load(open(os.path.join(T, 'clean', f'stage-{s}.json'))) for s in ORDER}
strat = json.load(open(os.path.join(T, 'strategy.json')))

# strategy
o = ['<div class="gn-prose rs-lead-block">' + ''.join(f'<p class="gn-prose">{sent(x, "thesis")}</p>' for x in strat['thesis']) + '</div>']
o.append('<h3 class="doc-s" id="patterns">How the incumbents\' partner experiences work</h3>')
for n, p in enumerate(strat['patterns'], 1):
    o.append(f'<section class="rs-insight"><div class="rs-insight-h"><span class="k">P{n}</span><b>{e(p["title"])}</b></div><div class="rs-insight-g">'
             f'<b>Observed</b><div>{para(p["text"], "pattern")}</div><b>Stages</b><div>{" · ".join(stage_link(s) for s in p.get("stages", []))}</div></div></section>')
o.append('<h3 class="doc-s" id="position">Where the Discover family stands</h3>')
o.append('<p class="gn-prose">' + para(strat['discover_position'], 'position') + '</p>')
o.append('<h3 class="doc-s" id="principles">Design principles for advantage</h3>')
for n, p in enumerate(strat['principles'], 1):
    o.append(f'<section class="rs-insight"><div class="rs-insight-h"><span class="k">{n}</span><b>{e(p["title"])}</b></div><div class="rs-insight-g">'
             f'<b>Why</b><div>{para(p["text"], "principle")}</div><b>Stages</b><div>{" · ".join(stage_link(s) for s in p.get("stages", []))}</div></div></section>')
o.append('<h3 class="doc-s" id="moves">The design moves, ranked</h3>')
o.append('<p class="gn-prose">Ranked by the advantage each would create for partners and for Discover, weighed against the strength of the evidence. Each links to the stage where the detail sits.</p>')
for m in sorted(strat['moves'], key=lambda m: m['rank']):
    o.append(f'<section class="rs-insight" id="move-{m["rank"]}"><div class="rs-insight-h"><span class="k">M{m["rank"]}</span><b>{e(m["title"])}</b>'
             f'<span class="gn-status is-quiet">{e(m["evidence_strength"].capitalize())} evidence</span></div><div class="rs-insight-g">'
             f'<b>The move</b><div>{e(m["what"])}</div><b>Why it wins</b><div>{para(m["why_advantage"], "move")}</div>'
             f'<b>For</b><div>{e(", ".join(m.get("partner_types", [])))}</div><b>Surfaces</b><div>{e(", ".join(m.get("surfaces", [])))}</div>'
             f'<b>Stage</b><div>{stage_link(m["stage"])}</div></div></section>')
open(os.path.join(ROOT, 'parts', 'td-strategy.html'), 'w').write(quote_titles('\n'.join(o)) + '\n')

# stages
o = []
for s in ORDER:
    d = stages[s]
    o.append(f'<h2 class="doc-s" id="stage-{s}">{e(NAMES[s])}</h2>')
    o.append('<p class="gn-prose">' + para(d['summary'], f'stage {s} summary') + '</p>')
    o.append(f'<h3 class="doc-s">Design moves at this stage</h3>')
    for n, m in enumerate(sorted(d['design_moves'], key=lambda m: ['strong', 'moderate', 'thin'].index(m.get('evidence_strength', 'thin'))), 1):
        ids = ids_of(m.get('ids'), f'stage {s} move')
        c = (' {{rcite:' + '+'.join(ids) + '}}') if ids else ''
        o.append(f'<section class="rs-insight"><div class="rs-insight-h"><span class="k">{s}.{n}</span><b>{e(m["title"])}</b><span class="gn-status is-quiet">{e(m.get("evidence_strength", "").capitalize())} evidence</span></div>'
                 f'<div class="rs-insight-g"><b>The move</b><div>{e(m["move"])}</div><b>Why it wins</b><div>{e(m["why_advantage"])}{c}</div>'
                 f'<b>For</b><div>{e(", ".join(m.get("partner_types", [])))}</div></div></section>')
    o.append(f'<h3 class="doc-s">How it works, by partner type</h3>')
    for bp in d['by_partner']:
        o.append(f'<h4 class="rs-pt">{e(bp["partner_type"])}</h4>')
        rows = []
        for nw in bp['networks']:
            w = f'stage {s} {bp["partner_type"][:20]} {nw["network"]}'
            how = ' '.join(sent(x, w) for x in nw.get('how_it_works', []))
            tools = ' '.join(f'<b>{e(t["name"])}.</b> ' + sent({'text': t.get('what_it_shows', ''), 'ids': t.get('ids')}, w) for t in nw.get('tools_and_screens', []))
            fr = ' '.join(sent(x, w) for x in nw.get('friction', []))
            rows.append(f'<tr><td>{e(net_name(nw["network"]))}</td><td>{how}</td><td>{tools or "None found in public"}</td><td>{fr or "None found in public"}</td></tr>')
        o.append('<div class="gn-table-wrap"><table class="gn-table gn-table--dense rs-teardown"><thead><tr><th>Network</th><th>How it works</th><th>Tools and screens</th><th>Friction</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>')
        extra = []
        if bp.get('best_pattern', {}).get('text'): extra.append(f'<b>Best pattern.</b> {sent(bp["best_pattern"], f"stage {s} best")}')
        if bp.get('discover_today', {}).get('text'): extra.append(f'<b>Discover today.</b> {sent(bp["discover_today"], f"stage {s} discover")}')
        if extra: o.append('<p class="gn-prose">' + ' '.join(extra) + '</p>')
    if d.get('unseen'):
        o.append('<h3 class="doc-s">What public sources could not show</h3><ol class="rv-l">' + ''.join(f'<li><b>{e(u["what"])}</b> {e(u["why"])} {e(u.get("how_to_see_it", ""))}</li>' for u in d['unseen']) + '</ol>')
open(os.path.join(ROOT, 'parts', 'td-stages.html'), 'w').write(quote_titles('\n'.join(o)) + '\n')

# cross-stage unseen
open(os.path.join(ROOT, 'parts', 'td-unseen.html'), 'w').write('<ol class="rv-l">' + ''.join(f'<li><b>{e(u["what"])}</b> {e(u["how_to_see_it"])}</li>' for u in strat['unseen']) + '</ol>\n')
pts = {bp['partner_type'] for d in stages.values() for bp in d['by_partner']}
counts = {'stages': len(ORDER), 'moves': len(strat['moves']), 'stage_moves': sum(len(d['design_moves']) for d in stages.values()),
          'cited': len(cited), 'verified_share': round(100 * sum(1 for i in cited if S[i].get('confidence') == 'Verified') / max(1, len(cited)))}
json.dump(counts, open(os.path.join(ROOT, 'parts', 'td-counts.json'), 'w'))
print(counts)
if problems:
    print(len(problems), 'problems'); print('\n'.join(problems[:30])); sys.exit(1)
