# Research: card and ATM payment networks, read as a partner would

Competitive research on twenty-five card and ATM networks for the Discover
Global Network prototypes. Partners only: issuers, acquirers and processors,
merchants, ATM operators, fintechs and developers. Every claim is public,
cited and dated. Begun September 25, 2026.

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
4. Ledgers are written from raw and walks, then verified and refuted claim by claim.
5. `node tools/ledger.js` emits `sources.json`. `node tools/links.js` checks every citation, anchor, image and URL.
6. Reports are written from the ledgers. `node tools/copy-check.js` reads the copy.
7. `cd ../design-system && NODE_PATH=../story/brightline-story/node_modules node tools/check.js ../research/competitive-networks.html ../research/prototype-insights.html`
8. `node tools/build.js` writes `dist/`, then publish.

Preview: server `global-network` on port 8096, open `/research/competitive-networks.html`.

## Rules

- Public sources only. Nothing from a login, nothing internal, for any network including Discover.
- No accounts created, no credentials entered, no forms submitted, cookie banners declined.
- Captions only from video, never the file. Frames are few, small and attributed.
- Nothing from Visa or Mastercard goes into the prototypes. Report 2 carries patterns, not copy.
- No scores. Rungs, counts with denominators, and sentences that say when evidence is thin.
