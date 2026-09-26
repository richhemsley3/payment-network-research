// QA: screenshots of a local report section by section at one width.
// Usage: node tools/qa-shots.js <url> <width> <outdir> <id>[,<id>...] [maxChunks]
// Each section runs from h2#id to the next h2.doc-s, split into 1500px chunks.
const { chromium } = require('playwright');
(async () => {
  const [url, width, out, ids, maxC] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: +width, height: 1000 }, deviceScaleFactor: 1 });
  await p.goto(url, { waitUntil: 'networkidle' });
  console.log('horizontal overflow px', await p.evaluate(() => document.documentElement.scrollWidth - innerWidth));
  const H = await p.evaluate(() => document.documentElement.scrollHeight);
  for (const id of ids.split(',')) {
    const r = await p.evaluate((id) => { const h = document.getElementById(id); if (!h) return null; const all = [...document.querySelectorAll('h2.doc-s, .doc-h')]; const i = all.indexOf(h); const top = h.getBoundingClientRect().top + scrollY; const nx = all[i + 1]; const end = nx ? nx.getBoundingClientRect().top + scrollY : document.documentElement.scrollHeight; return [top, end]; }, id);
    if (!r) { console.log('missing', id); continue; }
    let [top, end] = r; let n = 0;
    for (let y = top - 8; y < end && n < (+maxC || 3); y += 1500, n++) {
      const f = `${out}/qa-${width}-${id}-${n}.png`;
      await p.screenshot({ path: f, clip: { x: 0, y, width: +width, height: Math.min(1500, end - y, H - y) }, fullPage: true });
      console.log(f);
    }
    console.log(id, 'section height', Math.round(end - top));
  }
  await b.close();
})();
