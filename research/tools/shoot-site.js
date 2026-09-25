#!/usr/bin/env node
// shoot-site.js — one screenshot of a public page with consent banners declined or cleared, as WebP.
//   NODE_PATH=../story/brightline-story/node_modules node tools/shoot-site.js <url> <out.webp> [width height] [clipSelector]
const fs = require('fs'), path = require('path'), os = require('os'), { execFileSync } = require('child_process');
const { chromium } = require('playwright');
const [url, out, w = '1440', h = '1000', clipSel] = process.argv.slice(2);
if (!url || !out) { console.error('usage: shoot-site.js <url> <out.webp> [w h] [clipSelector]'); process.exit(2); }
const UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36';
async function clearBanners(page) {
  return await page.evaluate(() => {
    const t = s => (s || '').replace(/\s+/g, ' ').trim();
    const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const all = []; const walk = root => { root.querySelectorAll('*').forEach(el => { all.push(el); if (el.shadowRoot) walk(el.shadowRoot); }); }; walk(document);
    const btns = all.filter(el => /^(button|a)$/i.test(el.tagName) && vis(el));
    const pats = [/^reject all/i, /^alle ablehnen/i, /^tout refuser/i, /^rejeitar/i, /^decline/i, /^refuse/i, /only necessary/i, /necessary only/i, /essential only/i, /^reject/i, /do not (accept|consent)/i, /^no,? thanks/i];
    let note = null;
    for (const p of pats) { const b = btns.find(b => p.test(t(b.textContent))); if (b) { b.click(); note = 'declined: ' + t(b.textContent).slice(0, 30); break; } }
    // anything fixed or sticky that talks about cookies and covers real space goes, without consent
    const vw = innerWidth, vh = innerHeight;
    all.filter(el => vis(el)).forEach(el => { const cs = getComputedStyle(el); if ((cs.position === 'fixed' || cs.position === 'sticky') && /cookie|consent|privacy/i.test(el.textContent || '') && (el.textContent || '').length < 3000) { const r = el.getBoundingClientRect(); if (r.width * r.height > vw * vh * 0.04) { el.remove(); note = (note ? note + '; ' : '') + 'removed overlay'; } } });
    return note;
  });
}
(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: +w, height: +h }, userAgent: UA, locale: 'en-US', deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  try { await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 40000 }); } catch (e) { console.error('goto: ' + e.message.split('\n')[0]); }
  await page.waitForTimeout(2500); const n1 = await clearBanners(page); await page.waitForTimeout(800); const n2 = await clearBanners(page);
  const tmp = path.join(os.tmpdir(), 'shot-' + Date.now() + '.png');
  const el = clipSel ? await page.$(clipSel) : null;
  if (el) await el.screenshot({ path: tmp }); else await page.screenshot({ path: tmp });
  await browser.close();
  fs.mkdirSync(path.dirname(out), { recursive: true });
  execFileSync('python3', ['-c', `from PIL import Image; im=Image.open(${JSON.stringify(tmp)}).convert('RGB'); im.thumbnail((1400,4000)); im.save(${JSON.stringify(out)},'WEBP',quality=82)`]);
  fs.unlinkSync(tmp);
  console.log(JSON.stringify({ url: page.url ? url : url, out, kb: Math.round(fs.statSync(out).size / 1024), banner: n1 || n2 || null }));
})();
