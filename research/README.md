# Research: card and ATM payment networks, read as a partner would

Competitive research on twenty-five card and ATM networks for the Discover
Global Network prototypes, which live in the payment-network-prototype repo.
Partners only: issuers, acquirers and processors, merchants, ATM operators,
fintechs and developers. Every claim is public, cited and dated. Begun
September 25, 2026.

## What is here

```
competitive-networks.html   Report 1, the research
prototype-insights.html     Report 2, what it means for the prototypes
research.css / research.js  placement and the contents rail, tokens only
ledger/README.md            id scheme, columns, confidence labels
ledger/<slug>.md            one ledger per network, the source of truth
ledger/raw/<slug>/*.json    what each research agent returned, by dimension
ledger/walks/<slug>.json    walkthrough station records
sources.json                generated from ledger/*.md by tools/ledger.js
assets/<slug>/*.webp        screenshots and video frames
tools/                      walk, shoot, ledger, links, copy-check, build
dist/                       single-file builds for the Artifact, gitignored
```

## The loop

1. Desk research agents write `ledger/raw/<slug>/<dimension>.json`.
2. `tools/walk.js <slug> <url>` runs the station script and writes `ledger/walks/<slug>.json` and screenshots.
3. Demonstrations: discovery to `ledger/raw/<slug>/demos.json`, transcripts in the scratchpad, frames to `assets/<slug>/`.
4. `python3 tools/ledger-build.py` writes the ledgers from raw and walks and applies the verdicts in `ledger/verify/out/`. Ids come from `ledger/ids.json`, which only grows: an id is never reused.
5. `node tools/ledger.js` emits `sources.json`. `node tools/links.js` checks every citation, anchor, image and URL.
6. Reports are written from the ledgers. `node tools/copy-check.js` reads the copy.
7. `node ../design-system/tools/check.js ../research/competitive-networks.html ../research/prototype-insights.html`
8. `REPORT1_URL=<Report 1 link> node tools/build.js` writes `dist/`. Publish the `dist/artifact-*.html` files.

Preview: server `network-research` on port 8097, open `/research/competitive-networks.html`.

## Report 2: the insight rounds

Report 2 is rendered from `parts/cards.json`, the settled output of three multi-agent rounds run on September 25 and 26, 2026:

1. A pressure test of the first twelve insights through evidence, partner-value and contrarian lenses, with judges, a red team and a cross-set critic.
2. A search for missing insights across eight areas of partner value, with verification and a completeness critic.
3. A second round on all 25: a claim-by-claim audit, the experience decision each informs, Discover's competitive position, a decision map, a red team and a final edit.

New evidence from each round enters the ledger with `tools/insights-ingest.py <round> <rows.json> [accessed]`, is checked with `tools/verify-auto.py --ids <ids.json> --out auto-<round>.json`, and the residue goes to agents, whose verdicts land in `ledger/verify/out/agent-*.json`. `tools/cards-build.py` writes the decision blocks, gaps and advantages, cards, open questions and the record of the first twelve, and fails on any uncited observed sentence or unknown id. Citations in Report 2 are `{{rcite:id}}` markers that link into Report 1's register. A reference that starts with `proto:` points at a prototype file and renders as a plain pointer, never as evidence about a network.

## Published

Both reports are private Artifacts. They were first published from the Global
Network repo's path, so update them by passing the link as `url`.

- Report 1, Card Network Partner Study: https://claude.ai/artifact/PK46s4NK5N48ehy2mTgsL4
- Report 2, Partner Desk Research Insights: https://claude.ai/artifact/BxFGKe3NZSCHgs59L4WZG2

## Rules

- Public sources only. Nothing from a login, nothing internal, for any network including Discover.
- No accounts created, no credentials entered, no forms submitted, cookie banners declined.
- Captions only from video, never the file. Frames are few, small and attributed.
- Nothing from Visa or Mastercard goes into the prototypes. Report 2 carries patterns, not copy.
- No scores. Rungs, counts with denominators, and sentences that say when evidence is thin.
