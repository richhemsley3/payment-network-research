#!/usr/bin/env node
// fetch-browser.js — fetch a URL through the browser's own network stack (passes bot walls that block curl) and save the body.
//   NODE_PATH=../story/brightline-story/node_modules node tools/fetch-browser.js <url> <out>
const fs = require('fs'); const { chromium } = require('playwright');
const [url, out] = process.argv.slice(2);
(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36', locale: 'en-US' });
  // warm the origin so cookies and challenge tokens exist, then request the file
  try { const p = await ctx.newPage(); await p.goto(new URL(url).origin, { waitUntil: 'domcontentloaded', timeout: 30000 }).catch(() => {}); await p.waitForTimeout(1500); await p.close(); } catch {}
  const r = await ctx.request.get(url, { timeout: 90000, maxRedirects: 10 });
  const body = await r.body(); fs.writeFileSync(out, body);
  console.log(JSON.stringify({ status: r.status(), type: r.headers()['content-type'] || '', bytes: body.length }));
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
