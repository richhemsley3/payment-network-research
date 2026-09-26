#!/usr/bin/env python3
"""Renders Report 2 from parts/cards.json, the settled output of the insight rounds.

parts/cards.json:
  {"cards": [CARD, ...] in map order, "map": MAP, "tested": [{"was", "title", "decision", "now", "change"}], "keys": {card id: display key}}
CARD (from the round-two workflow): id, merged_from, title, kind, observed[{text, ids}], inference[{text, ids}],
  decision{question, options, evidence_favours, goals, owner}, position{discover, text, ids}, means[{surface, text, ids}],
  objection{text, ids}, resolution{text, ids}, limit, confidence
MAP: decisions[{id, question, recommendation, goals, owner, cards, confidence, would_change_it}], gaps[{title, why_major, cards, shore_up}],
  advantages[{title, why_credible, cards, press}], open_questions[{question, why_unknown, how_to_settle}], order[card ids]

Writes parts/decisions.html, parts/gaps.html, parts/insights.html, parts/open.html and parts/tested.html.
Every cited sentence renders as text followed by an {{rcite:...}} marker, which render.py turns into links to Report 1's register."""
import json, os, html, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(ROOT, 'parts', 'cards.json')))
S = {r['id'] for r in json.load(open(os.path.join(ROOT, 'sources.json')))}
KEYS = D['keys']
problems = []
def e(s): return html.escape(str(s or ''), quote=False)
def cite(ids, where):
    ids = [i for i in dict.fromkeys(ids or [])]
    proto = [i[6:] for i in ids if i.startswith('proto:')]
    ids = [i for i in ids if not i.startswith('proto:')]
    bad = [i for i in ids if i not in S]
    if bad: problems.append(f'{where}: ids not in the ledger: {", ".join(bad)}')
    ok = [i for i in ids if i in S]
    out = (' {{rcite:' + '+'.join(ok) + '}}') if ok else ''
    if proto: out += ' <span class="rs-cite">(prototype: ' + ', '.join(e(p) for p in proto) + ')</span>'
    return out
TOKEN = r'(?:proto:[^\s,()]+|[a-z]+-(?:w-|q)?[a-z0-9]+(?:-[a-z0-9]+)*)'
GROUP = re.compile(r'\((' + TOKEN + r'(?:,\s*' + TOKEN + r')*)\)')
def linkify(text, where):
    t = e(text)
    def rep(m):
        toks = [x.strip() for x in m.group(1).split(',')]
        if not all(x.startswith('proto:') or x in S for x in toks):
            unknown = [x for x in toks if not (x.startswith('proto:') or x in S)]
            if any(re.search(r'\d', x) for x in unknown): problems.append(f'{where}: unknown ids in text: {", ".join(unknown)}')
            return m.group(0)
        return cite(toks, where).strip()
    t = GROUP.sub(rep, t)
    for cid in sorted(KEYS, key=len, reverse=True):
        t = re.sub(r'\((?:the )?' + re.escape(cid) + r'(?: card)?\)', f'(<a class="gn-link" href="#n{KEYS[cid]}">insight {KEYS[cid]}</a>)', t)
        if '-' in cid: t = re.sub(r'(?<![\w/#-])' + re.escape(cid) + r'(?![\w-])', f'<a class="gn-link" href="#n{KEYS[cid]}">insight {KEYS[cid]}</a>', t)
        elif re.fullmatch(r'i\d{1,2}', cid): t = re.sub(r'(?<![\w/#-])' + cid + r'(?![\w-])', f'<a class="gn-link" href="#n{KEYS[cid]}">insight {KEYS[cid]}</a>', t)
    t = re.sub(r'\bd(\d{1,2})\b', lambda m: f'<a class="gn-link" href="#d{m.group(1)}">decision {m.group(1)}</a>', t)
    return t
def sent(item, where, need=True):
    t = linkify(item['text'], where).rstrip()
    if need and not [i for i in (item.get('ids') or []) if not i.startswith('proto:')]: problems.append(f'{where}: uncited sentence: {item["text"][:80]}')
    c = cite(item.get('ids'), where)
    if t.endswith('.') and c: return t[:-1] + c + '.'
    return t + c
def anchor(cid): return 'n' + KEYS[cid]
def card_link(cid): return f'<a class="gn-link" href="#{anchor(cid)}">{e(KEYS[cid])}</a>' if cid in KEYS else e(cid)
def goals(g):
    g = list(g or [])
    return (', '.join(g[:-1]) + ' and ' + g[-1]) if len(g) > 1 else (g[0] if g else '')
OWNER = {'experience': 'Owned by experience design.', 'business': 'Owned by the business. The experience can make it visible and easy.', 'both': 'Shared by the business and experience design.'}
STAND = {'ahead': 'Ahead', 'parity': 'At parity', 'behind': 'Behind', 'mixed': 'Mixed', 'unknown': 'Not known from public evidence'}

# decisions
blocks = []
for n, d in enumerate(D['map']['decisions'], 1):
    did = f'd{n}'
    blocks.append(f'<section class="rs-insight rs-decision" id="{e(did)}"><div class="rs-insight-h"><span class="k">D{did[1:]}</span><b>{e(d["question"])}</b>'
                  f'<span class="gn-status is-quiet">{e(d["confidence"].capitalize())} confidence</span></div>\n<div class="rs-insight-g">'
                  f'<b>The evidence favours</b><div>{linkify(d["recommendation"], did)}</div>\n'
                  f'<b>Serves</b><div>{e(goals(d["goals"]).capitalize())}. {OWNER[d["owner"]]}</div>\n'
                  f'<b>Would change it</b><div>{linkify(d["would_change_it"], did)}</div>\n'
                  f'<b>Insights</b><div>{" · ".join(card_link(c) for c in d["cards"])}</div></div></section>')
open(os.path.join(ROOT, 'parts', 'decisions.html'), 'w').write('\n'.join(blocks) + '\n')

# gaps and advantages
g = ['<h3 class="doc-s" id="gaps-major">Major gaps to shore up</h3>', '<ol class="rv-l">']
for x in D['map']['gaps']:
    g.append(f'<li><b>{e(x["title"])}</b> {linkify(x["why_major"], "gap")} {linkify(x["shore_up"], "gap")} <span class="rs-refs">{" · ".join(card_link(c) for c in x["cards"])}</span></li>')
g += ['</ol>', '<h3 class="doc-s" id="advantages">Advantages to press</h3>', '<ol class="rv-l">']
for x in D['map']['advantages']:
    g.append(f'<li><b>{e(x["title"])}</b> {linkify(x["why_credible"], "advantage")} {linkify(x["press"], "advantage")} <span class="rs-refs">{" · ".join(card_link(c) for c in x["cards"])}</span></li>')
g.append('</ol>')
open(os.path.join(ROOT, 'parts', 'gaps.html'), 'w').write('\n'.join(g) + '\n')

# cards
out = []
for c in D['cards']:
    k = KEYS[c['id']]; w = c['id']
    obs = ' '.join(sent(s, w) for s in c['observed'])
    inf = ' '.join(sent(s, w, need=False) for s in c.get('inference', []))
    dec = c['decision']
    opts = ' '.join(f'{linkify(o, w).rstrip(".")}.' for o in dec['options'])
    pos = c['position']
    means = ' '.join(f'<b>{e(m["surface"])}.</b> {sent(m, w, need=False)}' for m in c['means'])
    chal = sent(c['objection'], w, need=False) + ' ' + sent(c['resolution'], w, need=False)
    first = [m for m in [c['id']] + list(c.get('merged_from', [])) if m[:1] == 'i' and m[1:].isdigit()]
    origin = (f'One of the first twelve ({", ".join(first)} in the first version), challenged in the pressure test and again in round two.' if first
              else 'Found by the search for missing insights, verified, and challenged again in round two.')
    block = [f'<section class="rs-insight" id="{anchor(c["id"])}"><div class="rs-insight-h"><span class="k">{e(k)}</span><b>{e(c["title"])}</b><span class="gn-status is-quiet">{e(c["confidence"].capitalize())} confidence</span></div>',
             '<div class="rs-insight-g">', f'<b>Observed</b><div>{obs}</div>']
    if inf: block.append(f'<b>The study infers</b><div>{inf}</div>')
    block += [f'<b>Decision</b><div><b>{e(dec["question"])}</b> {opts} {linkify(dec["evidence_favours"], w)} Serves {e(goals(dec["goals"]))}. {OWNER[dec["owner"]]}</div>',
              f'<b>Where Discover stands</b><div><b>{STAND[pos["discover"]]}.</b> {sent(pos, w, need=pos["discover"] != "unknown")}</div>',
              f'<b>What it means</b><div>{means}</div>',
              f'<b>Challenged</b><div>{chal}</div>',
              f'<b>Limit</b><div>{linkify(c["limit"], w)}</div>',
              f'<b>Origin</b><div>{e(origin)}</div>',
              '</div></section>']
    out.append('\n'.join(block))
open(os.path.join(ROOT, 'parts', 'insights.html'), 'w').write('\n\n'.join(out) + '\n')

# open questions
oq = ['<ol class="rv-l">'] + [f'<li><b>{e(q["question"])}</b> {linkify(q["why_unknown"], "open")} {linkify(q["how_to_settle"], "open")}</li>' for q in D['map']['open_questions']] + ['</ol>']
open(os.path.join(ROOT, 'parts', 'open.html'), 'w').write('\n'.join(oq) + '\n')

# what happened to the first twelve
rows = ''.join(f'<tr><td>{e(t["was"])}</td><td>{e(t["title"])}</td><td>{e(t["decision"])}</td><td>{card_link(t["now"]) if t.get("now") else "None"}</td><td>{e(t["change"])}</td></tr>' for t in D['tested'])
open(os.path.join(ROOT, 'parts', 'tested.html'), 'w').write(
    '<div class="gn-table-wrap"><table class="gn-table gn-table--dense"><thead><tr><th>Was</th><th>First version</th><th>Decision</th><th>Now</th><th>What changed</th></tr></thead>'
    f'<tbody>{rows}</tbody></table></div>\n')
print(f'{len(D["cards"])} cards, {len(D["map"]["decisions"])} decisions, {len(D["map"]["gaps"])} gaps, {len(D["map"]["advantages"])} advantages, {len(D["map"]["open_questions"])} open questions')
if problems:
    print('\n'.join(problems)); sys.exit(1)
