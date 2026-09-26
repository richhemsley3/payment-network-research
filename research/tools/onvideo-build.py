import json,re
S=json.load(open('sources.json'))
v={}
for r in S:
    if r['kind']!='video': continue
    m=re.search(r'(?:v=|youtu\.be/)([\w-]{11})', r.get('url') or '')
    v[m.group(1) if m else r['url']]=r['id']
def c(*vids): return '{{cite:'+'+'.join(v[x] for x in vids)+'}}'
part=f'''<p class="gn-prose">The partner portals that matter most are behind logins, and public video is the only way to see some of them work. The search ran a fixed query set per network across YouTube, the networks' own channels and conference and webinar archives, and kept <!-- count:videos --> items out of more than 2,000 candidates, most of them cardholder material or advertising. Captions were read for 34 videos, 27 of them Mastercard's. YouTube stopped answering this study's caption requests partway through, so Visa, Diners Club and PULSE items are described from their public listings. A demonstration shows how a network presents a surface. It is not evidence of how the surface performs.</p>
<div class="gn-table-wrap"><table class="gn-table gn-table--dense"><thead><tr><th>Network</th><th class="is-num">Items kept</th><th class="is-num">Official</th><th class="is-num">Captions read</th><th>A gated surface shown in public</th></tr></thead><tbody>
<tr><td><a class="gn-link" href="#mastercard-video">Mastercard</a></td><td class="is-num">56</td><td class="is-num">40</td><td class="is-num">27</td><td>The developer dashboard after sign-up, the Gateway's Merchant Administration {c('IeR9CwwrH9k','c1xk7B9d4i8')}</td></tr>
<tr><td><a class="gn-link" href="#visa-video">Visa</a></td><td class="is-num">60</td><td class="is-num">47</td><td class="is-num">0</td><td>Developer Center projects and credentials, the Cybersource Business Center, from listings {c('crxdAEvZlfo','UDmAWGHPbWs')}</td></tr>
<tr><td><a class="gn-link" href="#amex-video">American Express</a></td><td class="is-num">30</td><td class="is-num">16</td><td class="is-num">6</td><td>The Merchant website and app. Nothing of the developer portal or Knowledge Base {c('_fRxW33FJVg')}</td></tr>
<tr><td><a class="gn-link" href="#dgn-video">Discover Global Network</a></td><td class="is-num">16</td><td class="is-num">4</td><td class="is-num">1</td><td>None</td></tr>
<tr><td><a class="gn-link" href="#pulse-video">PULSE</a></td><td class="is-num">15</td><td class="is-num">13</td><td class="is-num">0</td><td>The Debit Dashboard, 2020 release, from the listing {c('sZCzhgedZr0')}</td></tr>
<tr><td><a class="gn-link" href="#diners-video">Diners Club International</a></td><td class="is-num">9</td><td class="is-num">9</td><td class="is-num">0</td><td>DCI GlobalNet, the franchise reporting portal, from the listing {c('2BWvPE_EB7Y')}</td></tr>
<tr><td>RuPay and NPCI</td><td class="is-num">9</td><td class="is-num">9</td><td class="is-num">0</td><td>A partner-programme masterclass, slides only {c('ODHb3473bZE')}</td></tr>
<tr><td>eftpos and AP+</td><td class="is-num">8</td><td class="is-num">8</td><td class="is-num">0</td><td>None</td></tr>
<tr><td>Jeanie, through Worldpay</td><td class="is-num">3</td><td class="is-num">3</td><td class="is-num">0</td><td>Worldpay's disputes portal for acquiring clients, which is not the Jeanie participant surface {c('os45z7W40S4')}</td></tr>
<tr><td>STAR and Accel, through Fiserv</td><td class="is-num">3</td><td class="is-num">2</td><td class="is-num">0</td><td>Fiserv's developer studio, from the listing {c('LIsr0pun8mM')}</td></tr>
</tbody></table></div>
<p class="gn-prose">AFFN, Cartes Bancaires, CULIANCE, Elo, girocard, NYCE and SHAZAM each had one item or two, none showing a gated tool. JCB, UnionPay, Interac, Interlink, Plus, Maestro and Cirrus had none that met the criteria.</p>
<h4>What video shows that the pages do not</h4>
<p class="gn-prose">Mastercard's tutorial puts a number on self-service: a four-field project form and sandbox credentials on the next screen {c('IeR9CwwrH9k')}. The Gateway is the exception inside Mastercard. Its test merchant and its Click to Pay switch come from the merchant's bank or payment service provider, a route the developer site does not describe {c('c1xk7B9d4i8','xlT_Wp8JGLg')}. Payment facilitators are registered by their acquirer with a signed form on Mastercard Connect {c('QZVkLBMl9D4')}. American Express's Merchant website caps each payment search at 35 days from the previous 16 months {c('_fRxW33FJVg')}. One Finicity recording puts API integration for lenders at about four weeks and calls contracting and onboarding the longest part {c('-leMzb4ZWNI')}.</p>
<h4>What no public video shows</h4>
<p class="gn-prose">No recording was found of Visa Access, Mastercard Connect's own screens, the American Express Knowledge Base or AMEX Enabled dashboard, any Discover partner tool, the STAR, NYCE or SHAZAM participant portals, JCB Partner Online, the AP+ member portal or UnionPay's institution portal. For those surfaces the public pages and their login walls are the whole of the public record.</p>
'''
open('parts/on-video.html','w').write(part)
t=open('src/competitive-networks.html').read()
old='<h2 class="doc-s" id="on-video">Behind the wall, on video</h2><p class="gn-prose">Placeholder.</p>'
if old in t: t=t.replace(old,'<h2 class="doc-s" id="on-video">Behind the wall, on video</h2>\n<!-- include:parts/on-video.html -->'); open('src/competitive-networks.html','w').write(t)
print('on-video written')
