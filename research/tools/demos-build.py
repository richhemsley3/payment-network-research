#!/usr/bin/env python3
"""Writes parts/demos/<slug>.html from hand-picked moments (below) and the caption readings.
Each moment links to the video at its timestamp and cites the video's ledger row."""
import json, os, re, html
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(ROOT, 'sources.json')))
vid2row = {}
for r in S:
    if r['kind'] != 'video': continue
    m = re.search(r'(?:v=|youtu\.be/)([\w-]{11})', r.get('url') or '')
    if m: vid2row[m.group(1)] = r
    else: vid2row[r['url']] = r
def esc(x): return html.escape(str(x or ''), quote=True)
def secs(t): m, s = t.split(':'); return int(m) * 60 + int(s)
def row(vid, t, shows, who=None):
    r = vid2row.get(vid)
    if not r: return f'<tr><td colspan="4">[missing video {esc(vid)}]</td></tr>'
    url = f"https://www.youtube.com/watch?v={vid}&t={secs(t)}s" if t else r['url']
    who = who or f"{r.get('channel')}{'' if r.get('official') else ', third party'}"
    when = r.get('published') if r.get('published') not in (None, '', 'n.d.') else 'undated'
    return f'<tr><td class="is-num"><a class="rs-src" data-src="{esc(r["id"])}" href="{esc(url)}" title="{esc(r.get("title"))}">{esc(t or "listing")}</a></td><td>{esc(shows)}</td><td>{esc(who)}</td><td>{esc(when)}</td></tr>'
def table(rows): return '<div class="gn-table-wrap"><table class="gn-table gn-table--dense"><thead><tr><th class="is-num">Moment</th><th>What the video shows or says</th><th>Who showed it</th><th>Published</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>'
def listing(vids):
    out = []
    for vid, shows in vids:
        out.append(row(vid, None, shows))
    return out
P = {}
P['mastercard'] = ('''<h4 id="mastercard-video">Seen in demonstrations</h4>
<p class="gn-prose">Mastercard's own channels carry the most complete public record of any network. An official tutorial shows a developer signing up with an email and a password, filling a four-field project form and landing on a dashboard with sandbox credentials, with production left for another day. Two videos add what the desk research missed. The Mastercard Gateway's test merchant comes from the merchant's bank or payment service provider, and Click to Pay is switched on by that provider. Training modules show payment facilitators registered by their acquirer through Mastercard Connect, and issuers reporting questionable merchants to a mailbox.</p>''', [
    ('IeR9CwwrH9k', '0:52', 'Sign-up on Mastercard Developers, described as entering credentials and nothing more.'),
    ('IeR9CwwrH9k', '3:37', 'The create-project form: API chosen, project name, company, region, description.'),
    ('IeR9CwwrH9k', '4:20', 'The developer dashboard with sandbox access given at once.'),
    ('IeR9CwwrH9k', '4:59', 'Production is named and deferred to another video.'),
    ('c1xk7B9d4i8', '4:34', 'The Gateway Merchant Administration portal showing the captured test order.'),
    ('c1xk7B9d4i8', '13:34', 'Click to Pay is enabled by the merchant\u2019s payment service provider.'),
    ('xlT_Wp8JGLg', '2:37', 'Gateway test credentials and URL come from the merchant\u2019s bank or payment service provider.', 'scriptpapi, third party'),
    ('QZVkLBMl9D4', '5:47', 'An acquirer registers a payment facilitator with a signed request on Mastercard Connect, confirmed by email.'),
    ('dIEGhMeS8Ts', '9:18', 'Issuer analysts report a questionable merchant by email to a Mastercard mailbox.'),
    ('RtHIHF-INss', '1:08', 'Vendors register for Engage and receive training and product updates.'),
    ('L33At9gVBas', '0:19', 'Monthly Operations Bulletin highlights presented on Mastercard Academy.'),
])
P['amex'] = ('''<h4 id="amex-video">Seen in demonstrations</h4>
<p class="gn-prose">Public video of American Express's partner surfaces covers the merchant side only. Official tours of the Merchant website show settlements, submissions, disputes, custom reports, live chat and guided help, and one names a limit: payment searches cover 35 days at a time from the previous 16 months. The two dispute explainers differ by market. In the UK version Amex contacts the merchant. In the Canadian version the merchant hears from its merchant services provider. No public recording was found of the developer portal, the AMEX Enabled dashboard or the Knowledge Base.</p>''', [
    ('_fRxW33FJVg', '0:34', 'Settlements, one line each, expandable to submissions, adjustments and chargebacks.'),
    ('_fRxW33FJVg', '1:35', 'Payment search limited to 35 days at a time from the previous 16 months.'),
    ('7qrBvM2gCT4', '0:22', 'Daily dispute alerts and document upload on the Merchant website.'),
    ('7qrBvM2gCT4', '0:33', 'Live chat and WalkMe guided help inside the site.'),
    ('ZSh0kjmlKa4', '0:09', 'Amex works with the Card Member first, often without contacting the merchant.'),
    ('wfhSTOzpgTI', '0:23', 'In Canada the inquiry comes from the merchant services provider.'),
])
P['visa'] = ('''<h4 id="visa-video">Seen in demonstrations</h4>
<p class="gn-prose">Visa publishes a tutorial series for every step of the developer path, from creating a project to submitting a going-live request, and the Cybersource channel tours the Business Center that acceptance clients use. The captions could not be read: YouTube began refusing requests from this study's address partway through, so the rows below come from each video's public listing and are not a viewing. No public recording was found of Visa Access, Visa Resolve Online, the Fast Track application or the Visa Ready portal.</p>''', listing([
    ('crxdAEvZlfo', 'Listed as the Visa Developer Center dashboard: creating a project and its credentials.'),
    ('qMTJTnhfly8', 'Listed as the going-live request from inside a project.'),
    ('V5FQHtLOp1o', 'Listed as getting two-way SSL credentials: CSR upload, certificate download, a sandbox call.'),
    ('RZ7zlDA89xE', 'Listed as getting X-Pay Token credentials: API key and shared secret.'),
    ('Tz3_JFsrUHY', 'Listed as a tour of Visa Partner: programmes, Fast Track entry, Visa Ready listings.'),
    ('UDmAWGHPbWs', 'Listed as the Cybersource Business Center navigation and dashboard.'),
    ('GbMbHHefIBI', 'Listed as transaction search and actions in the Business Center.'),
]))
P['dgn'] = ('''<h4 id="dgn-video">Seen in demonstrations</h4>
<p class="gn-prose">No public recording of any Discover partner tool was found: not the Developer Center, the Partner Product Portal, EASI, the Release Compliance Tool, the Disputes Portal, eCentral or the Fraud and Risk Center. Discover has no partner-facing video channel. The one captioned video is an acceptance pitch to acquirer sales representatives, republished by a third party, which promises merchants one phone number for Discover, Visa and Mastercard inquiries.</p>''', [
    ('_6J-WF5KbFk', '2:43', 'Acquirer sales training: one point of contact, one phone number for three networks.', 'umdiscover, third party'),
])
P['diners'] = ('''<h4 id="diners-video">Seen in demonstrations</h4>
<p class="gn-prose">Diners Club International's channel has short explainers of the tools franchises and corporate clients use, including DCI GlobalNet, the portal franchises use to report financial data to the network. Captions were not available for any of them, so the rows come from the public listings.</p>''', listing([
    ('2BWvPE_EB7Y', 'Listed as DCI GlobalNet, the partner reporting portal for franchises.'),
    ('JNyuZvFf-9s', 'Listed as the Global Vision corporate-card reporting dashboard.'),
    ('zJVlbmczJrg', 'Listed as SalesConnect, the sales app for Diners Club and franchise staff.'),
    ('kZcz-VjXXR4', 'Listed as a franchise merchant portal sign-up, Diners Club del Ecuador.'),
]))
P['pulse'] = ('''<h4 id="pulse-video">Seen in demonstrations</h4>
<p class="gn-prose">PULSE's own channel holds the one public walkthrough of a gated PULSE tool, the Debit Dashboard for issuers, in its 2020 release. Captions were not available, so the row comes from the listing. No recording was found of DebitProtect, the client registration or dispute tooling.</p>''', listing([
    ('sZCzhgedZr0', 'Listed as a five-minute tour of the PULSE Debit Dashboard: transaction and revenue metrics, custom reports.'),
]))
os.makedirs(os.path.join(ROOT, 'parts', 'demos'), exist_ok=True)
for slug, (intro, rows) in P.items():
    body = rows if rows and isinstance(rows[0], str) and rows[0].startswith('<tr') else [row(*x) for x in rows]
    open(os.path.join(ROOT, 'parts', 'demos', slug + '.html'), 'w').write(intro + '\n' + table(body) + '\n')
    print(slug, len(body), 'rows', sum(1 for b in body if 'missing' in b), 'missing')
