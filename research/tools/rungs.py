#!/usr/bin/env python3
"""Reads ledger/walks/*.json and assigns the descriptive rungs from the plan, plus the two counted facts.
Writes ledger/walks/rungs.json and prints a table. Rungs describe choices, they do not score."""
import json, os, glob, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, 'ledger', 'walks')
def rung_reading(S):
    s2, s3, s4 = S.get('S2') or {}, S.get('S3') or {}, S.get('S4') or {}
    readable = s2.get('readable', 0) or 0; walls = s2.get('walls', 0) or 0
    if s4.get('reference'): return 'reference, guides and samples readable' if (s4.get('sample_languages') or s4['reference'].get('code_blocks', 0) >= 3) else 'reference readable'
    if s3.get('links', 0) and s3.get('wall', 'none') == 'none': return 'catalogue only'
    if readable == 0 and walls > 0: return 'gateway only'
    return 'marketing pages only' if readable else 'gateway only'
def rung_sandbox(S):
    s5 = S.get('S5') or {}; w = s5.get('wall'); tr = s5.get('trail') or []
    if s5.get('try_it_console'): return 'try without an account'
    if w == 'account form': return 'self-service with free account'
    if w == 'login': return 'account required (sign-in wall)'
    if w == 'contact': return 'request by form'
    if w == 'invite': return 'invite only'
    if not s5.get('entry'): return 'no sandbox or sign-up path found'
    return 'path found, no wall reached'
def rung_cert(S):
    s6 = S.get('S6') or {}; return s6.get('rung', 'not described')
def rung_support(S):
    s7 = S.get('S7') or {}
    if not s7 or s7.get('note'): return 'no support route found'
    ch = []
    if s7.get('community'): ch.append('community')
    if s7.get('phones'): ch.append('phone')
    if s7.get('mailto'): ch.append('email')
    if s7.get('form'): ch.append('form')
    if s7.get('chat'): ch.append('chat')
    if s7.get('sla'): ch.append('response-time statement')
    return ', '.join(ch) if ch else 'contact page without listed channels'
def rung_change(S):
    s8 = S.get('S8') or {}
    if s8.get('status_page') and s8.get('changelog'): return 'status page plus changelog'
    if s8.get('changelog'): return 'release notes or changelog only'
    if s8.get('status_page'): return 'status page only'
    return 'none found'
def rung_search(S):
    s9 = S.get('S9') or {}
    if not s9.get('has_search'): return 'none'
    res = [r for r in s9.get('results', []) if r.get('top')]
    return f'site search, {len(res)} of 3 queries returned results' if res else 'search box present, no results captured'
def rung_audience(S):
    s1 = S.get('S1') or {}; words = s1.get('audience_words') or []
    labels = [l for l in (s1.get('nav_labels') or []) if re.search(r'issuer|acquirer|merchant|developer|partner|business|for |who we serve|fintech|atm', l, re.I)]
    if labels: return 'audience labels in navigation: ' + ', '.join(labels[:5])
    if words: return 'audience words on landing: ' + ', '.join(words[:6])
    return 'none'
rows = {}
for f in sorted(glob.glob(os.path.join(W, '*.json'))):
    if os.path.basename(f) == 'rungs.json': continue
    d = json.load(open(f)); S = d.get('stations', {}); key = os.path.basename(f)[:-5]
    s4, s5, s2, s12 = S.get('S4') or {}, S.get('S5') or {}, S.get('S2') or {}, S.get('S12') or {}
    rows[key] = { 'network': d.get('network'), 'seed': d.get('seed'), 'final': (S.get('S0') or {}).get('final_url'), 'date': d.get('date'), 'tier': d.get('tier'),
        'logged_out_reading': rung_reading(S), 'sandbox_access': rung_sandbox(S), 'certification_path': rung_cert(S), 'support_route': rung_support(S), 'change_and_health': rung_change(S), 'search': rung_search(S), 'audience_routing': rung_audience(S),
        'clicks_to_docs': s4.get('clicks_to_docs'), 'clicks_to_wall': s5.get('clicks_to_wall'), 'nav_items_readable': s2.get('readable'), 'nav_items_walled': s2.get('walls'), 'first_useful_thing': (s12.get('first') or {}).get('text'), 'first_useful_url': (s12.get('first') or {}).get('href'), 'first_useful_clicks': (s12.get('first') or {}).get('clicks'),
        'pages_visited': len(d.get('visited', [])), 'screenshots': len(d.get('screenshots', [])), 'errors': d.get('errors', []), 'cookie': (S.get('S0') or {}).get('cookie_banner') or (d.get('cookie_notes') or [{}])[0].get('banner') }
json.dump(rows, open(os.path.join(W, 'rungs.json'), 'w'), indent=1)
for k, r in rows.items(): print(f"{k:22s} | {r['logged_out_reading'][:38]:38s} | {r['sandbox_access'][:32]:32s} | {r['certification_path'][:22]:22s} | {r['change_and_health'][:26]:26s} | docs {r['clicks_to_docs']} wall {r['clicks_to_wall']}")
