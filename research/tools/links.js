#!/usr/bin/env node
// links.js — every citation in the reports resolves to the ledger, every anchor exists, every image is within budget, every URL answers.
//   node tools/links.js [--no-http]
const fs = require('fs'), path = require('path'), https = require('https'), http = require('http');
const ROOT = path.resolve(__dirname, '..');
const NOHTTP = process.argv.includes('--no-http');
const sources = JSON.parse(fs.readFileSync(path.join(ROOT, 'sources.json'), 'utf8'));
const byId = Object.fromEntries(sources.map(s => [s.id, s]));
const norm = u => (u || '').replace(/&amp;/g, '&').replace(/[?&]t=\d+s?$/, '').replace(/&#x27;/g, "'").replace(/&quot;/g, '"').replace(/#.*$/, '').replace(/[?&](utm_[^&]*|ref=[^&]*)/g, '').replace(/\/$/, '').toLowerCase();
const pages = ['partner-experience.html', 'journey-map.html', 'competitive-networks.html', 'prototype-insights.html'].filter(f => fs.existsSync(path.join(ROOT, f)));
const problems = [], used = new Set(), urls = new Set();
const anchors = {};
for (const p of pages) {
  const html = fs.readFileSync(path.join(ROOT, p), 'utf8');
  const body = html.replace(/<h2 class="doc-s" id="register">[\s\S]*$/, '');
  anchors[p] = new Set([...html.matchAll(/\sid="([^"]+)"/g)].map(m => m[1]));
  for (const m of html.matchAll(/<a\b([^>]*)>/g)) {
    const attrs = m[1]; const src = (attrs.match(/data-src="([^"]+)"/) || [])[1]; const inBody = body.includes(m[0]); const href = (attrs.match(/href="([^"]+)"/) || [])[1];
    const also = ((attrs.match(/data-also="([^"]+)"/) || [])[1] || '').trim().split(/\s+/).filter(Boolean);
    for (const a of also) { if (inBody) used.add(a); const s2 = byId[a]; if (!s2) problems.push(`${p}: data-also ${a} not in ledger`); else if (href && s2.url && norm(href) !== norm(s2.url)) problems.push(`${p}: ${a} merged under a link to a different url`); }
    if (src) { if (inBody) used.add(src); const s = byId[src]; if (!s) problems.push(`${p}: data-src ${src} not in ledger`); else if (href && s.url && norm(href) !== norm(s.url)) problems.push(`${p}: ${src} href differs from ledger url\n   page   ${href}\n   ledger ${s.url}`); if (href && /^https?:/.test(href)) urls.add(href); }
    else if (href && /^https?:/.test(href) && !/localhost/.test(href)) problems.push(`${p}: external link without data-src: ${href.slice(0, 100)}`);
  }
  for (const m of html.matchAll(/<img\b[^>]*src="([^"]+)"[^>]*>/g)) {
    const f = path.join(ROOT, m[1]); if (!fs.existsSync(f)) { problems.push(`${p}: missing image ${m[1]}`); continue; }
    const kb = fs.statSync(f).size / 1024; if (kb > 120) problems.push(`${p}: image over 120 KB (${Math.round(kb)} KB): ${m[1]}`);
    if (!/\salt="/.test(m[0])) problems.push(`${p}: image without alt: ${m[1]}`);
  }
  for (const m of html.matchAll(/<figure\b[^>]*data-src="([^"]+)"/g)) { used.add(m[1]); if (!byId[m[1]]) problems.push(`${p}: figure data-src ${m[1]} not in ledger`); }
}
// report 2 anchors into report 1
if (pages.includes('prototype-insights.html')) {
  const html = fs.readFileSync(path.join(ROOT, 'prototype-insights.html'), 'utf8');
  for (const m of html.matchAll(/href="competitive-networks\.html#([^"]+)"/g)) if (!anchors['competitive-networks.html'].has(m[1])) problems.push(`prototype-insights.html: anchor #${m[1]} missing in competitive-networks.html`);
}
for (const p of pages) { const html = fs.readFileSync(path.join(ROOT, p), 'utf8'); for (const m of html.matchAll(/href="#([^"]+)"/g)) if (!anchors[p].has(m[1])) problems.push(`${p}: internal anchor #${m[1]} missing`); }
for (const p of pages) { const h = fs.readFileSync(path.join(ROOT, p), 'utf8'); for (const m of h.matchAll(/\[missing ([^\]]+)\]/g)) problems.push(`${path.basename(p)}: citation to ${m[1]} has no ledger row (moved to could-not-verify or removed)`); }
const unused = sources.filter(s => s.kind === 'source' && !used.has(s.id)).map(s => s.id);
console.log(`${pages.length} page(s), ${used.size} citations used, ${unused.length} ledger sources unused, ${urls.size} external urls`);
if (unused.length) fs.writeFileSync(path.join(ROOT, 'ledger', 'unused-ids.txt'), unused.join('\n'));
function head(u) { return new Promise(res => { try { const mod = u.startsWith('https') ? https : http; const req = mod.request(u, { method: 'HEAD', timeout: 15000, headers: { 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36' } }, r => { res(r.statusCode); r.resume(); }); req.on('error', () => res(0)); req.on('timeout', () => { req.destroy(); res(0); }); req.end(); } catch { res(0); } }); }
(async () => {
  if (!NOHTTP) {
    const list = [...urls]; let i = 0; const bad = [], hand = [];
    async function worker() { while (i < list.length) { const u = list[i++]; let code = await head(u); if (code < 200 || code >= 400) { code = await new Promise(res => { const mod = u.startsWith('https') ? https : http; try { const req = mod.get(u, { timeout: 20000, headers: { 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36', 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'accept-language': 'en-US,en;q=0.9' } }, r => { res(r.statusCode); r.resume(); }); req.on('error', () => res(0)); req.on('timeout', () => { req.destroy(); res(0); }); } catch { res(0); } }); } if (code >= 200 && code < 400) continue; if (code === 403 || code === 429 || code === 401) hand.push(`${code} ${u}`); else bad.push(`${code} ${u}`); } }
    await Promise.all(Array.from({ length: 8 }, worker));
    if (hand.length) console.log(`check by hand (${hand.length}):\n  ` + hand.join('\n  '));
    for (const b of bad) { const id = sources.find(s => norm(s.url) === norm(b.slice(b.indexOf(' ') + 1))); if (!(id && id.archive)) problems.push(`url failed and no archive: ${b}`); }
  }
  if (problems.length) { console.log(problems.join('\n')); console.log(`links: ${problems.length} problem(s)`); process.exit(1); }
  console.log('links: clean');
})();
