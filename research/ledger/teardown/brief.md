# Brief for every teardown researcher

## The report you feed
Rich leads experience design for the Discover Global Network partner prototypes (Brightline story, Clearway product, developer site, agent portal) in /Users/richhemsley/Desktop/Claude/Global Network/. He wants to know how the competitors' partner experiences actually work, stage by stage, and how to approach design to create a competitive advantage. The report is organised by journey stage and covers every partner type: issuers (large banks, community banks, credit unions), acquirers and processors, payment facilitators and ISOs, ATM operators, fintechs and programme managers, developers, and merchants where they touch the network directly.

Networks to cover in depth: Visa, Mastercard, American Express, and the Discover family (Discover Global Network, PULSE, Diners Club). Use others (Interac, eftpos/AP+, STAR, NYCE, SHAZAM, UnionPay, JCB, Elo) only where they show a notably better or worse pattern.

## What "how the experience works" means
For your stage, per network and partner type: the steps in order, who does each, the named tools, portals and screens (Visa Online / Visa Access, Visa Resolve Online, Mastercard Connect, Mastercom, Technical Resource Center, American Express Knowledge Base, EASI, the PULSE client website, and so on), the documents and artefacts exchanged (forms, letters, bulletins, reports, files), what the partner sees and what they must do, how long the network says it takes where published, and where it breaks. Behind-login tools can often be seen through public user guides and manuals that banks, processors and credit unions republish, training and webinar videos, product documentation, API guides, release notes, job postings that describe the work, and court or regulator filings. Describe screens and flows concretely when a source shows them (menu names, fields, states, statuses).

## Existing evidence to mine first
Repo /Users/richhemsley/Desktop/Claude/payment-network-research/research:
- sources.json (every ledger row by id: claim, url, title, publisher, confidence, note) and ledger/<slug>.md.
- parts/profiles/<slug>.html and parts/portals/<slug>.html (network profiles and walk write-ups), ledger/walks/pane-notes.md (hand walk notes), ledger/raw/*/demo-moments.json (205 moments from Mastercard and American Express videos with timestamps).
- parts/cards.json (24 tested insights and 12 decisions).
- Partner operating profiles for seven audiences, not yet in the ledger: /private/tmp/claude-501/-Users-richhemsley-Desktop-Claude/a7b17a35-5948-40cb-a79f-825d4720b44b/scratchpad/ops-out.json (profiles[].roles, pains, needs, evidence rows with url and quote).
- Prior persona research: /Users/richhemsley/Desktop/Claude/Global Network/story/brightline-story/notes/research-persona-needs.md (orientation only).
Then research the public web to go deeper than any of these.

## Evidence rules
Every factual sentence cites a source: an existing ledger id, or a new evidence row with a key. A new row has: key, network (slug: amex visa mastercard dgn diners pulse star accel nyce shazam culiance jeanie affn jcb unionpay interac eftpos rupay cb girocard elo cross), claim, quote (verbatim, 25 words or fewer), url, title, publisher, published, label (Verified for primary documents, rules, official guides, filings, regulators, courts, or what you observed; Reported for press, analysts, forums, job postings, associations; Vendor for a company describing its own product or the pain it sells against), fetch (method and date). Open every URL you cite and confirm the quote. No assumptions: what partners feel or want needs a source, or it is labelled as inference. Say plainly where the public record is thin.

## Hard rules
Public sources only. Never sign in, create an account, submit a form or type into a site. Do not try to get past a bot check, CAPTCHA or paywall. Do not use the Browser pane or Chrome tools. Never read ~/Downloads or any file whose name contains dci-onboarding. No internal Discover or Capital One material. Captions and transcripts only from video, never download video files. Fetch with WebFetch or WebSearch, curl with a desktop Chrome user agent, node /Users/richhemsley/Desktop/Claude/payment-network-research/research/tools/text.js '<url>', or the Wayback Machine. Today is September 26, 2026.

## Rich's standing rules for the prototypes
The network's value beats process in the story. Estimated durations stay out of the product, though key service levels the network commits to may appear. No Visa or Mastercard metric or marketing line goes into a prototype, so their practice appears as patterns and benchmarks.

## Output
Write one JSON file to the path your task gives, with this shape:
{
 "stage": "...",
 "summary": [{"text": "...", "ids": ["ledger id or new:key"]}],
 "by_partner": [
   {"partner_type": "...",
    "networks": [{"network": "visa|mastercard|amex|discover-family|other:<name>",
                  "how_it_works": [{"text": "...", "ids": [...]}],
                  "tools_and_screens": [{"name": "...", "what_it_shows": "...", "ids": [...]}],
                  "friction": [{"text": "...", "ids": [...]}] }],
    "best_pattern": {"text": "...", "ids": [...]},
    "discover_today": {"text": "...", "ids": [...]} }],
 "design_moves": [{"title": "...", "partner_types": [...], "move": "...", "why_advantage": "...", "ids": [...], "evidence_strength": "strong|moderate|thin"}],
 "unseen": [{"what": "...", "why": "...", "how_to_see_it": "..."}],
 "evidence": [ new evidence rows ]
}
Prose: plain sentences under 30 words, no semicolons, no em or en dashes, no "not X, but Y", no rhetorical questions, no hype. British spellings as the reports use them (programme, centre). Return a short text summary when done: counts of rows, strongest findings, thinnest areas.
