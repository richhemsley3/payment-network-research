#!/usr/bin/env node
// frame.js — one frame of a public YouTube video at a timestamp, captured from the player (nothing downloaded), as WebP ≤ 960 wide.
//   NODE_PATH=../story/brightline-story/node_modules node tools/frame.js <videoId> <seconds> <out.webp>
const fs = require('fs'), path = require('path'), os = require('os'), { execFileSync } = require('child_process');
const { chromium } = require('playwright');
const [vid, secs, out] = process.argv.slice(2);
if (!vid || !secs || !out) { console.error('usage: frame.js <videoId> <seconds> <out.webp>'); process.exit(2); }
(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--autoplay-policy=no-user-gesture-required', '--mute-audio'] });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, locale: 'en-US', userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36' });
  const page = await ctx.newPage();
  // the embed player with the timestamp: no ads in most cases, no comments, no recommendations
  await page.goto(`https://www.youtube.com/embed/${vid}?start=${secs}&autoplay=1&controls=0&mute=1&rel=0`, { waitUntil: 'domcontentloaded', timeout: 40000 });
  await page.waitForTimeout(1500);
  // consent pages, if any
  try { const b = page.locator('button:has-text("Reject all"), button:has-text("Accept all")').first(); if (await b.count()) await b.click({ timeout: 2000 }); } catch {}
  try { await page.locator('.ytp-large-play-button, button[aria-label="Play"]').first().click({ timeout: 3000 }); } catch {}
  let ready = false;
  for (let i = 0; i < 40 && !ready; i++) { await page.waitForTimeout(500); ready = await page.evaluate(s => { const v = document.querySelector('video'); if (!v) return false; if (Math.abs(v.currentTime - s) > 3 && v.readyState >= 2) { v.currentTime = s; } return v.readyState >= 2 && Math.abs(v.currentTime - s) <= 3; }, +secs); }
  await page.evaluate(() => { const v = document.querySelector('video'); if (v) v.pause(); });
  await page.waitForTimeout(400);
  const info = await page.evaluate(() => { const v = document.querySelector('video'); return v ? { t: v.currentTime, w: v.videoWidth, h: v.videoHeight, ready: v.readyState } : null; });
  const tmp = path.join(os.tmpdir(), 'frame-' + Date.now() + '.png');
  const v = await page.$('video'); if (v) await v.screenshot({ path: tmp }); else await page.screenshot({ path: tmp });
  await browser.close();
  fs.mkdirSync(path.dirname(out), { recursive: true });
  execFileSync('python3', ['-c', `from PIL import Image; im=Image.open(${JSON.stringify(tmp)}).convert('RGB'); im.thumbnail((960,960)); im.save(${JSON.stringify(out)},'WEBP',quality=80)`]);
  fs.unlinkSync(tmp);
  console.log(JSON.stringify({ vid, secs: +secs, out, kb: Math.round(fs.statSync(out).size / 1024), video: info }));
})().catch(e => { console.error(e.message); process.exit(1); });
