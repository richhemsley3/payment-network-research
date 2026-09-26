#!/usr/bin/env python3
"""Writes parts/sentiment/<slug>.html for every network and parts/sentiment-section.html, from the quote rows in sources.json and the tiers the sweep reported."""
import json, os, collections, html, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = [r for r in json.load(open(os.path.join(ROOT, 'sources.json'))) if r['kind'] == 'quote']
tiers = {}
for f in glob.glob(os.path.join(ROOT, 'ledger', 'raw', '*', 'sentiment*.json')):
    tiers.update(json.load(open(f)).get('tiers', {}))
SLUGNAME = {'amex': 'American Express', 'visa': 'Visa', 'mastercard': 'Mastercard', 'dgn': 'Discover Global Network', 'diners': 'Diners Club', 'pulse': 'PULSE', 'star': 'STAR', 'accel': 'Accel', 'nyce': 'NYCE', 'shazam': 'SHAZAM', 'culiance': 'CULIANCE', 'jeanie': 'Jeanie', 'affn': 'AFFN', 'interlink': 'Interlink', 'plus': 'Plus', 'maestro': 'Maestro', 'cirrus': 'Cirrus', 'jcb': 'JCB', 'unionpay': 'UnionPay', 'interac': 'Interac', 'eftpos': 'eftpos', 'rupay': 'RuPay', 'cb': 'Cartes Bancaires', 'girocard': 'girocard', 'elo': 'Elo'}
def esc(x): return html.escape(str(x or ''), quote=True)
AUD = {'developer': 'developers', 'fintech': 'fintechs', 'acquirer': 'acquirers', 'processor': 'processors', 'merchant': 'merchants', 'atm_operator': 'ATM operators', 'issuer': 'issuers', 'program_manager': 'program managers', 'institutional': 'trade bodies and regulators'}
by = collections.defaultdict(list)
for r in S: by[r['network']].append(r)
def month(d):
    d = (d or '').split(' ')[0]
    import re
    m = re.match(r'(\d{4})-(\d{2})', d); names = ['January','February','March','April','May','June','July','August','September','October','November','December']
    return f"{names[int(m.group(2))-1]} {m.group(1)}" if m else (d or 'undated')
def quote(r):
    who = r['author'] if r['author'] else r['platform']
    return f'<blockquote class="rs-quote"><p>“{esc(r["excerpt"])}”</p><cite>{esc(who)} · {esc(r["platform"])} · {esc(month(r["date"]))} · {esc(AUD.get(r["audience"], r["audience"]))}, {esc(r["stance"])} · {{{{cite:{r["id"]}|source}}}}</cite></blockquote>'
def pick(rs, n):
    # balance: favourable first, then critical, then mixed and neutral, newest first within each
    order = {'favourable': 0, 'critical': 1, 'mixed': 2, 'neutral': 3}
    rs = sorted(rs, key=lambda r: (r['date'] or ''), reverse=True)
    out, seen = [], set()
    for st in ('favourable', 'critical', 'mixed', 'neutral'):
        for r in rs:
            if r['stance'] == st and r['id'] not in seen and len(r['excerpt']) >= 40 and len(r['excerpt'].split()) <= 25:
                out.append(r); seen.add(r['id']); break
    for r in rs:
        if len(out) >= n: break
        if r['id'] not in seen and len(r['excerpt']) >= 40 and len(r['excerpt'].split()) <= 25 and r['stance'] == 'critical': out.append(r); seen.add(r['id'])
    return out[:n]
def countline(slug, rs):
    c = collections.Counter(r['stance'] for r in rs)
    t = {k.split(':', 1)[1]: v for k, v in tiers.items() if k.split(':', 1)[0] == slug}
    ad = [AUD.get(a, a) for a, v in t.items() if v == 'Adequate']; th = [AUD.get(a, a) for a, v in t.items() if v == 'Thin']
    parts = [f"{len(rs)} partner {'item' if len(rs) == 1 else 'items'} read, {c['favourable']} favourable, {c['critical']} critical, {c['mixed'] + c['neutral']} neutral or mixed."]
    if ad: parts.append(f"Adequate evidence for {', '.join(ad)}.")
    if th: parts.append(f"Thin for {', '.join(th)}.")
    parts.append('Absent for every other partner audience.' if (ad or th) else 'Absent for every partner audience, so no reading is offered.')
    return ' '.join(parts)
BIG = ['amex', 'visa', 'mastercard', 'dgn', 'diners', 'pulse']
os.makedirs(os.path.join(ROOT, 'parts', 'sentiment'), exist_ok=True)
allslugs = ['amex','visa','mastercard','dgn','diners','pulse','star','accel','nyce','shazam','culiance','jeanie','affn','interlink','plus','maestro','cirrus','jcb','unionpay','interac','eftpos','rupay','cb','girocard','elo']
for slug in allslugs:
    rs = by.get(slug, [])
    if slug in BIG:
        head = f'<h4 id="{slug}-sentiment">What partners say</h4>'
        body = ''.join(quote(r) for r in pick(rs, 4)) if rs else ''
        line = f'<p class="rs-count">{esc(countline(slug, rs))}</p>' if rs else '<p class="rs-count">No partner item was found in public forums, developer sites, trade press or regulator submissions in the window.</p>'
        open(os.path.join(ROOT, 'parts', 'sentiment', slug + '.html'), 'w').write(head + '\n' + body + '\n' + line + '\n')
    else:
        if rs:
            q = pick(rs, 1); body = quote(q[0]) if q else ''
            open(os.path.join(ROOT, 'parts', 'sentiment', slug + '.html'), 'w').write(body + f'<p class="rs-count">{esc(countline(slug, rs))}</p>\n')
        else:
            open(os.path.join(ROOT, 'parts', 'sentiment', slug + '.html'), 'w').write('<p class="rs-count">No partner sentiment found in public forums, developer sites, trade press or regulator submissions.</p>\n')
# the cross-network section
THEMES = [
 ('Authentication and signing', {'auth'}, 'Stack Overflow, GitHub issues, Hacker News'),
 ('Sandbox behaviour', {'sandbox'}, 'Stack Overflow, GitHub issues'),
 ('Documentation gaps', {'docs'}, 'Stack Overflow, GitHub issues, LinkedIn'),
 ('Fees and settlements', {'fees'}, 'Trade press, trade bodies, regulator submissions, forums'),
 ('Routing and network independence', {'routing'}, 'Trade press, regulator submissions, practitioner blogs'),
 ('Onboarding and access', {'onboarding', 'portal', 'support', 'certification'}, 'Merchant forums, Hacker News, GitHub issues'),
 ('Reliability', {'reliability'}, 'Stack Overflow, GitHub issues, processor help centres'),
 ('Rules and disputes', {'rules'}, 'Trade press, merchant forums, court objections'),
]
rows = []
for name, topics, where in THEMES:
    rs = [r for r in S if r['topic'] in topics]
    nets = sorted({r['network'] for r in rs})
    c = collections.Counter(r['stance'] for r in rs)
    rows.append(f"<tr><td>{esc(name)}</td><td>{esc(', '.join(sorted((SLUGNAME.get(n, n) for n in nets), key=str.lower)))}</td><td class=\"is-num\">{len(rs)}</td><td class=\"is-num\">{c['favourable']}</td><td class=\"is-num\">{c['critical']}</td><td class=\"is-num\">{c['mixed']+c['neutral']}</td><td>{esc(where)}</td></tr>")
cells = len(tiers); cc = collections.Counter(tiers.values())
tot = collections.Counter(r['stance'] for r in S)
sec = f'''<p class="gn-prose">The sweep ran the same query set for every network across developer Q&amp;A, code repositories, Hacker News, trade press, trade bodies and regulator submissions, from January 2023 to September 2026. It found {len(S)} partner items: {tot['favourable']} favourable, {tot['critical']} critical and {tot['mixed']+tot['neutral']} neutral or mixed. Two cautions shape the reading. Developer Q&amp;A exists to report problems, so it leans critical by design, and trade-body statements are advocacy. Each quote below is one voice, never a verdict on a network.</p>
<p class="gn-prose">The public record of partner opinion is thin. Of {cells} network and audience cells, {cc['Adequate']} reaches ten items from three sources, {cc['Thin']} hold three to nine, and {cc['Absent']} hold two or fewer. The only adequate cell is Mastercard's developers. Issuers, acquirers, ATM operators and program managers are almost silent in public for every network, which is itself the finding: the people who run these relationships do not discuss them where anyone can read.</p>
<div class="gn-table-wrap"><table class="gn-table gn-table--dense"><thead><tr><th>Theme</th><th>Networks named</th><th class="is-num">Items</th><th class="is-num">Favourable</th><th class="is-num">Critical</th><th class="is-num">Neutral or mixed</th><th>Where read</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>
'''
def theme_quotes(topics, ids):
    idx = {r['id']: r for r in S}
    return ''.join(quote(idx[i]) for i in ids if i in idx)
sec += '<h4>Integration</h4>\n<p class="gn-prose">Developer complaints cluster where the networks differ most from ordinary web APIs: request signing, mutual TLS, payload encryption and certificate handling. A recurring pattern is a call that works in the network’s own tester and fails from the developer’s code.</p>\n' + theme_quotes(None, ['visa-q16', 'mastercard-q17', 'mastercard-q33', 'amex-q03', 'mastercard-q12'])
sec += '<h4>Who pays, and who owns the second network</h4>\n<p class="gn-prose">Institutional voices argue about fees and about whether a second debit network is truly independent. Capital One’s ownership of PULSE and Discover is now part of that argument.</p>\n' + theme_quotes(None, ['pulse-q05', 'dgn-q02', 'mastercard-q18', 'mastercard-q07', 'star-q02', 'eftpos-q02', 'interac-q05', 'interac-q06'])
open(os.path.join(ROOT, 'parts', 'sentiment-section.html'), 'w').write(sec)
print('sentiment parts written;', len(S), 'items;', dict(cc))
