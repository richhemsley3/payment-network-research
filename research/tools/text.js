#!/usr/bin/env node
// text.js — the rendered text of a page (innerText after scripts), for verifying quotes on script-rendered sites.
//   NODE_PATH=../story/brightline-story/node_modules node tools/text.js <url>
const { chromium } = require('playwright');
const url = process.argv[2];
(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 }, userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36', locale: 'en-US' });
  const page = await ctx.newPage();
  try { await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 40000 }); await page.waitForTimeout(3000); } catch (e) { }
  const t = await page.evaluate(() => document.body ? document.body.innerText : '');
  await browser.close(); process.stdout.write(t.slice(0, 400000));
})().catch(e => { console.error(e.message); process.exit(1); });
