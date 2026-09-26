"""Short citation labels: a page name a reader recognises, with the publisher only where the page name alone is generic."""
import re
STOP = {'and','of','the','for','to','with','&','a','an','in','on','by','at','from','de','do','dos','da','des','du','la','le','et','und','der','die','das','-','–','—',':'}
PUB = [
    (r'^Board of Governors of the Federal Reserve System.*', 'Federal Reserve'),
    (r'^Federal Reserve.*', 'Federal Reserve'),
    (r'^U\.?S\.? Department of Justice.*', 'Justice Department'),
    (r'^U\.?S\.? Securities and Exchange Commission.*', 'SEC'),
    (r'^SEC EDGAR / (.*)', r'\1'),
    (r'^This research, observed in the browser$', 'Browser walk'),
    (r'^Office of the Comptroller of the Currency.*', 'OCC'),
    (r'^Payment Systems Regulator.*', 'Payment Systems Regulator'),
    (r'^Reserve Bank of Australia.*', 'Reserve Bank of Australia'),
    (r'^National Payments Corporation of India.*', 'NPCI'),
    (r'^American Express Travel Related Services.*', 'American Express'),
    (r'^Groupement des Cartes Bancaires.*', 'Cartes Bancaires'),
    (r'^U\.S\. SEC EDGAR.*', 'SEC'),
    (r'^Office of U\.S\. Senator .*?(\w+)$', r'Senator \1'),
    (r'^Court of Justice of the European Union.*', 'EU Court of Justice'),
    (r'^Supreme Court of the United States.*', 'US Supreme Court'),
    (r'^American Express Global Network( Services)?\b.*', 'American Express network'),
]
CUT = {'to','for','with','as','in','on','by','from','at','before','after','when','while','of'}
ALIAS = {'payment': ['psr'], 'american': ['amex'], 'visa': ['visa'], 'mastercard': ['mastercard']}
FILER = [(r'American Express.*', 'American Express'), (r'Discover Financial.*', 'Discover'), (r'Capital One.*', 'Capital One'), (r'Mastercard.*', 'Mastercard'), (r'Visa.*', 'Visa'), (r'Global Payments.*', 'Global Payments'), (r'Fiserv.*', 'Fiserv'), (r'Fidelity National.*|FIS\b.*', 'FIS')]
SUFFIX = r'(,? (Inc|Corp|Corporation|Incorporated|Company|Co|LLC|Ltd|Limited|plc|S\.A|S\.A\.S|GmbH|e\.V|AG|N\.A)\.?)+$'
def short_pub(p):
    p = (p or '').strip()
    for pat, rep in PUB:
        if re.match(pat, p): p = re.sub(pat, rep, p); break
    p = re.sub(r'\s*\([^)]*\)', '', p)
    p = re.split(r'\s+/\s+|,\s+', p)[0]
    p = re.sub(r'\s+via\s+.*$', '', p)
    p = re.sub(r'\s+(Investor Relations|Newsroom)$', '', p)
    p = re.sub(SUFFIX, '', p).strip(' ,')
    return p
def trim(words, n):
    w = list(words)
    for i, x in enumerate(w):
        if i >= 4 and x.lower() in CUT: w = w[:i]; break
    w = w[:n]
    while w and w[-1].lower().strip(',:') in STOP: w = w[:-1]
    return ' '.join(w).strip(' ,:')
def filer(t, pub):
    for pat, rep in FILER:
        if re.match(pat, t.strip()): return rep
    return pub
def short_title(t, pub):
    """Returns (label, self_describing)."""
    t = (t or '').strip()
    m = re.search(r'\(result: ([^,)]+)', t)
    if m and t.lower().startswith('search'): return (trim(m.group(1).split(), 7), False)
    t = re.sub(r'https?://\S+', '', t)
    t = re.sub(r'\s*\([^)]*[\s\d][^)]*\)\s*$', '', t)
    t = re.sub(r'\s*\((OpenAPI specification|PDF|sales sheet|JSON|queryMainWeb JSON|e-book|home page)\)\s*$', '', t, flags=re.I)
    m = re.search(r'Form (10-K|10-Q|20-F|8-K|S-4)\b', t)
    if m:
        who = re.split(r'\s*,?\s*Form\s+', t)[0].strip(' ,') or re.split(r'Form (?:10-K|10-Q|20-F|8-K|S-4),?\s*', t)[-1]
        y = re.search(r'(20\d\d)', t[m.end():])
        return (f"{filer(who, pub)} {m.group(1)}{' ' + y.group(1) if y else ''}", True)
    m = re.search(r'(DEF 14A|Proxy Statement)', t)
    if m:
        y = re.search(r'(20\d\d)', t)
        return (f"{filer(t, pub)} proxy{' ' + y.group(1) if y else ''}", True)
    m = re.match(r'(FRB|OCC) Order No\. ([\d-]+)', t)
    if m: return (f"{'Federal Reserve' if m.group(1)=='FRB' else 'OCC'} order {m.group(2)}", True)
    if re.match(r'Complaint, United States v\. Visa', t): return ('Complaint, United States v. Visa', True)
    segs = [x.strip() for x in re.split(r'\s+[|–—·]\s+|\s+-\s+', t) if x.strip()]
    if not segs: return ('', False)
    seg = segs[0]
    if len(segs) > 1 and len(seg.split()) == 1 and segs[1].lower().startswith(seg.lower()): seg = segs[1]
    seg = re.sub(r'[®™]', '', seg)
    seg = re.sub(r'\s*\([^)]*\d[^)]*\)', '', seg)
    seg = re.split(r',\s+(?:Rules?|Sections?|Chapter|Table|Item|Part|Appendix)\b', seg)[0]
    seg = re.sub(r'^\d+\.\s+', '', seg)
    seg = re.sub(r',?\s+\d{1,2} \w+ 20\d\d$', '', seg)
    seg = re.sub(r',?\s+(January|February|March|April|May|June|July|August|September|October|November|December) 20\d\d$', '', seg)
    seg = re.sub(r'\s*\([^)]*[\s\d][^)]*\)\s*$', '', seg)
    if ': ' in seg:
        a, b = seg.split(': ', 1)
        if re.match(r'(Frequently Asked Questions|In Brief|Everything You Need to Know|Antitrust)$', a.strip()): seg = b
        elif len(a.split()) >= 2: seg = a
    w = seg.split()
    if ' and ' in seg:
        before = seg.split(' and ')[0].split()
        if len(before) >= 3 and len(w) > 6: w = before
    out = trim(w, 7)
    if out.count('(') > out.count(')'): out = out[:out.rindex('(')].strip(' ,')
    return (out, False)
def keyword(pub):
    words = [x for x in re.findall(r'[a-z0-9+]+', pub.lower()) if x not in STOP and x not in ('www','resources','com','eu','org','net','br','in','co','au','ca','the')]
    return words
def label(r):
    k = r.get('kind')
    if k == 'quote': return r.get('platform') or 'Forum'
    if k == 'video': return r.get('channel') or 'Video'
    pub = short_pub(r.get('publisher'))
    t, own = short_title(r.get('title'), pub)
    if '-w-' in r['id']:
        t = t or r.get('url', '')
        return f"{t}, walked" if r.get('dimension') == 'walk' else f"{t}, screenshot"
    if not t: return pub or r['id']
    if own: return t
    flat = re.sub(r'[^a-z0-9+]', '', t.lower())
    keys = keyword(pub)
    if keys and any(a in flat for a in [keys[0]] + ALIAS.get(keys[0], [])): return t
    return f"{pub}, {t}" if pub else t

def compact(r):
    """Table-cell label: the page name without the publisher, at most four words."""
    full = label(r)
    k = r.get('kind')
    if k in ('quote', 'video'): return full
    pub = short_pub(r.get('publisher'))
    t = full
    if pub and t.startswith(pub + ', '): t = t[len(pub) + 2:]
    elif ', ' in t and '-w-' not in r['id']:
        a, b = t.split(', ', 1)
        if len(a.split()) <= 4 and len(b.split()) >= 1: t = b
    w = t.split()
    if len(w) > 4:
        w = w[:4]
        while w and w[-1].lower().strip(',:') in STOP: w = w[:-1]
    return ' '.join(w).strip(' ,:')
