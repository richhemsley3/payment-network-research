# Payment network research

Competitive research on twenty-five card and ATM networks, read as a partner
would, for the Discover Global Network prototypes in the
payment-network-prototype repo. Everything is public, cited and dated. The
work, its rules and its loop are described in `research/README.md`.

## Layout

```
research/        the two reports, the evidence ledger and the tools
design-system/   the slice of the Global Network design system the reports load
package.json     Playwright, used by the walk, fetch, shot and check tools
```

`design-system/` is copied from payment-network-prototype at commit 7ebac82:
the tokens, `gn.css`, `shared/doc.css`, `shared/icons.js`, `gn-charts.js` and
the foundations checker `tools/check.js`. Change the system there and copy
the files across, never the other way. `design-system/fonts` is a local link
to the licensed Proxima Nova cuts. It is gitignored and never committed. The
published builds swap in Figtree.

## Setup

```
npm install
npm run build
npm run check
npm run dist
```

Python 3 runs the ledger and render scripts. Pillow and pypdf are only needed
for new screenshots and PDF reading.
