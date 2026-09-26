#!/usr/bin/env node
// captions-browser.js — read a public YouTube video's captions the way its player does, inside a real page. Captions only, never the video.
//   NODE_PATH=../story/brightline-story/node_modules node tools/captions-browser.js <videoId> <out.txt>
const fs = require('fs'); const { chromium } = require('playwright');
const [vid, out] = process.argv.slice(2);
(async () => {
  const browser = await chromium.launch({ headless: true, args: ['--mute-audio', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ locale: 'en-US', userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36' });
  const page = await ctx.newPage(); let captured = null;
  page.on('response', async r => { try { if (/\/api\/timedtext/.test(r.url()) && !captured) { const b = await r.text(); if (b && b.length > 50) captured = b; } } catch {} });
  await page.goto(`https://www.youtube.com/watch?v=${vid}`, { waitUntil: 'domcontentloaded', timeout: 45000 });
  await page.waitForTimeout(2500);
  try { const b = page.locator('button:has-text("Reject all")').first(); if (await b.count()) { await b.click({ timeout: 3000 }); await page.waitForTimeout(1500); } } catch {}
  // switch captions on so the player requests them
  try { await page.evaluate(() => { const v = document.querySelector('video'); if (v) { v.muted = true; v.play().catch(() => {}); } }); } catch {}
  await page.waitForTimeout(2000);
  try { await page.keyboard.press('c'); } catch {}
  for (let i = 0; i < 20 && !captured; i++) await page.waitForTimeout(500);
  if (!captured) { // fall back to the transcript panel
    try { const more = page.locator('tp-yt-paper-button#expand, #expand').first(); if (await more.count()) await more.click({ timeout: 3000 }); } catch {}
    try { const btn = page.locator('button:has-text("Show transcript")').first(); if (await btn.count()) { await btn.click({ timeout: 5000 }); await page.waitForTimeout(3000); } } catch {}
    const segs = await page.evaluate(() => [...document.querySelectorAll('ytd-transcript-segment-renderer')].map(s => ((s.querySelector('.segment-timestamp') || {}).textContent || '').trim() + ' ' + ((s.querySelector('.segment-text') || {}).textContent || '').trim()));
    if (segs.length) { fs.writeFileSync(out, segs.map(s => '[' + s.replace(/^(\S+) /, '$1] ')).join('\n')); console.log(JSON.stringify({ vid, method: 'panel', cues: segs.length })); await browser.close(); return; }
  }
  if (captured && process.env.DEBUG) fs.writeFileSync(out + ".raw", captured);
  if (captured) {
    let lines = [];
    try { const j = JSON.parse(captured); lines = (j.events || []).filter(e => e.segs).map(e => { const s = Math.floor((e.tStartMs || 0) / 1000); return `[${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}] ` + e.segs.map(x => x.utf8).join('').replace(/\s+/g, ' ').trim(); }).filter(l => !/\]\s*$/.test(l)); }
    catch { lines = [...captured.matchAll(/<text start="([\d.]+)"[^>]*>([\s\S]*?)<\/text>/g)].map(m => { const s = Math.floor(+m[1]); return `[${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}] ` + m[2].replace(/<[^>]+>/g, '').replace(/&amp;#39;|&#39;/g, "'").replace(/&amp;/g, '&'); }); }
    fs.writeFileSync(out, lines.join('\n')); console.log(JSON.stringify({ vid, method: 'player', cues: lines.length }));
  } else console.log(JSON.stringify({ vid, method: null, cues: 0 }));
  await browser.close();
})().catch(e => { console.log(JSON.stringify({ vid, method: null, error: e.message.slice(0, 120) })); process.exit(0); });
