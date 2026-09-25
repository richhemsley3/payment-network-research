# The evidence ledger

One markdown file per network is the source of truth. `tools/ledger.js` reads
them and writes `../sources.json`. Nothing is hand-edited in the JSON.

## Slugs

amex, visa, mastercard, dgn, diners, pulse, star, accel, nyce, shazam,
culiance, jeanie, affn, interlink, plus, maestro, cirrus, jcb, unionpay,
interac, eftpos, rupay, cb, girocard, elo, cross.

## Ids

Assigned once, never reused. `<slug>-<nnn>` sources, `<slug>-s<nn>`
screenshots, `<slug>-v<nn>` videos, `<slug>-f<nn>` frames, `<slug>-q<nn>`
sentiment items.

## Confidence

- **Verified**: read on a primary document actually fetched: the network's own
  rules, fee schedules, docs, filings, regulator documents, or observed in the
  browser with the date. An official channel showing its own product is
  Verified for what it shows, never for how it performs.
- **Reported**: trade press, analyst work with a stated method, practitioner
  writing, forum posts, third-party demonstrations. Sentiment is never better
  than Reported.
- **Vendor**: a network's or vendor's claim about itself with no outside check.
  Never a finding on its own.

## Dimensions

reach, services, surfaces, join, developer, pricing, rules, support, news,
sentiment, walk, demo.

## File shape

```
# <Network>

Owner <owner> · Kind <global card | US debit and ATM | domestic scheme> · Accessed <range> · Viewport 1440 by 1000 · Logged out unless the note says otherwise

## Sources
| Id | Claim | Dimension | Title | Publisher | URL | Published | Accessed | Confidence | Archive | Note |

## Screenshots
| Id | Step | URL | Captured | File | Width | KB |

## Demonstrations
| Id | Title | Channel | Official | Published | Duration | URL | Accessed | What it shows | Confidence | Excerpts | Frames |

## Sentiment
| Id | Platform | Date | Audience | Stance | Topic | Author as shown | Excerpt | URL | Archive |

## Not established
- ...
```

## Raw agent output

`raw/<slug>/<dimension>.json`, one file per research agent:

```
{ "network": "visa", "dimension": "developer", "accessed": "2026-09-25",
  "claims": [ { "claim": "...", "quote": "verbatim, 25 words or fewer", "url": "...", "title": "...",
                "publisher": "...", "published": "YYYY-MM-DD or n.d.", "label": "Verified|Reported|Vendor",
                "fetch": "webfetch|curl|search-snippet", "note": "" } ],
  "not_found": [ { "query": "...", "where": "...", "date": "..." } ],
  "contradictions": [ { "a": "...", "b": "...", "urls": ["...", "..."] } ],
  "gated_surfaces": [ { "name": "...", "url": "...", "named_at": "..." } ],
  "sources_read": [ { "url": "...", "title": "...", "ok": true, "wall": "none|login|contact|invite|bot|dead" } ] }
```
