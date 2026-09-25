#!/usr/bin/env node
// walk.js — runs the station script against one public property, logged out.
//   NODE_PATH=../story/brightline-story/node_modules node tools/walk.js <slug> <url> [A|B] [label]
// Writes ledger/walks/<slug>[-label].json and screenshots to assets/<slug>/ as WebP.
// No account is created, nothing is typed into a form except the site search, cookie banners are declined.
const path = require('path'), fs = require('fs'), os = require('os'), { execFileSync } = require('child_process');
const { chromium } = require('playwright');
const [slug, seed, tierArg, labelArg] = process.argv.slice(2);
if (!slug || !seed) { console.error('usage: walk.js <slug> <url> [A|B] [label]'); process.exit(2); }
const TIER = (tierArg || 'A').toUpperCase(), LABEL = labelArg ? '-' + labelArg : '';
const ROOT = path.resolve(__dirname, '..'), OUT = path.join(ROOT, 'ledger', 'walks', slug + LABEL + '.json');
const ASSETS = path.join(ROOT, 'assets', slug); fs.mkdirSync(ASSETS, { recursive: true }); fs.mkdirSync(path.dirname(OUT), { recursive: true });
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'walk-'));
const today = new Date().toISOString().slice(0, 10), stamp = today.replace(/-/g, '');
const UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36';
const rec = { network: slug, seed, tier: TIER, date: today, viewport: '1440x1000', logged_out: true, stations: {}, visited: [], screenshots: [], errors: [] };
const origin = u => { try { return new URL(u).origin; } catch { return ''; } };
const norm = s => (s || '').replace(/\s+/g, ' ').trim();
const same = (a, b) => origin(a) && origin(a) === origin(b);
let shotN = 0;
async function shot(page, station, note, clipSel) {
  try {
    shotN++; const base = `${slug}${LABEL}-${station.toLowerCase()}-${String(shotN).padStart(2, '0')}-${stamp}`;
    const png = path.join(TMP, base + '.png'), webp = path.join(ASSETS, base + '.webp');
    const el = clipSel ? await page.$(clipSel) : null;
    if (el) await el.screenshot({ path: png }); else await page.screenshot({ path: png, fullPage: false });
    execFileSync('python3', ['-c', `from PIL import Image; im=Image.open(${JSON.stringify(png)}).convert('RGB'); im.thumbnail((1400,4000)); im.save(${JSON.stringify(webp)},'WEBP',quality=82)`]);
    const kb = Math.round(fs.statSync(webp).size / 1024);
    rec.screenshots.push({ id: `${slug}${LABEL}-s${String(shotN).padStart(2, '0')}`, station, note, url: page.url(), captured: today, file: `assets/${slug}/${base}.webp`, kb });
    return `assets/${slug}/${base}.webp`;
  } catch (e) { rec.errors.push(`shot ${station}: ${e.message}`); return null; }
}
async function go(page, url, why) {
  const started = Date.now(); let status = null, finalUrl = url, ok = false;
  try { const r = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 35000 }); status = r ? r.status() : null; await page.waitForTimeout(1500); finalUrl = page.url(); ok = true; const banner = await declineCookies(page); if (banner) { rec.cookie_notes = rec.cookie_notes || []; if (rec.cookie_notes.length < 6) rec.cookie_notes.push({ url: finalUrl, banner }); } }
  catch (e) { rec.errors.push(`goto ${url}: ${e.message.split('\n')[0]}`); }
  rec.visited.push({ url, final: finalUrl, status, ms: Date.now() - started, why });
  return { ok, status, finalUrl };
}
async function declineCookies(page) {
  try { return await page.evaluate(() => {
    const t = s => (s || '').replace(/\s+/g, ' ').trim();
    const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const btns = [...document.querySelectorAll('button, a[role=button], a')].filter(vis);
    const pats = [/^reject all/i, /^decline/i, /^refuse/i, /only necessary/i, /necessary only/i, /essential only/i, /^reject/i, /do not (accept|consent)/i, /^no,? thanks/i];
    for (const p of pats) { const b = btns.find(b => p.test(t(b.textContent))); if (b) { b.click(); return 'declined: ' + t(b.textContent).slice(0, 40); } }
    const boxes = [...document.querySelectorAll('#onetrust-consent-sdk, #onetrust-banner-sdk, [id*="cookie" i], [class*="cookie-banner" i], [class*="cookieconsent" i], [class*="cookie-consent" i], [id*="consent" i], [class*="consent-banner" i], [aria-label*="cookie" i], [role=dialog]')].filter(vis).filter(el => /cookie|consent/i.test(el.textContent || '') && (el.textContent || '').length < 1500);
    if (boxes.length) { const closer = boxes.map(b => [...b.querySelectorAll('button, a')].find(x => /^(close|×|x|dismiss)$/i.test(t(x.textContent)) || /close/i.test(x.getAttribute('aria-label') || ''))).find(Boolean); if (closer) { closer.click(); return 'closed without consent'; } boxes.forEach(b => b.remove()); return 'accept-only banner, removed from view without consent'; }
    return null; }); } catch { return null; }
}
async function pageFacts(page) {
  return await page.evaluate(() => {
    const t = s => (s || '').replace(/\s+/g, ' ').trim();
    const vis = el => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el); return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
    const links = [...document.querySelectorAll('header a, nav a, [role=navigation] a')].filter(vis).map(a => ({ text: t(a.textContent).slice(0, 60), href: a.href })).filter(l => l.text).slice(0, 60);
    const ctas = [...document.querySelectorAll('a.btn, a.button, a[class*="btn"], a[class*="button"], button, a[role=button]')].filter(vis).map(b => ({ text: t(b.textContent).slice(0, 60), href: b.href || null })).filter(c => c.text).slice(0, 40);
    const signin = [...document.querySelectorAll('a, button')].filter(vis).filter(e => /^(sign ?in|log ?in|login|register|sign ?up|create account|my account)\b/i.test(t(e.textContent))).map(e => ({ text: t(e.textContent), href: e.href || null, top: Math.round(e.getBoundingClientRect().top) })).slice(0, 8);
    const menu = [...document.querySelectorAll('header a, nav a, [role=navigation] a')].map(a => ({ text: t(a.textContent).slice(0, 60), href: a.href })).filter(l => l.text && l.href && !/#$/.test(l.href) && !/^(javascript|mailto|tel):/.test(l.href)).filter((v, i, arr) => arr.findIndex(x => x.href === v.href) === i).slice(0, 80);
    const lm = { header: !!document.querySelector('header,[role=banner]'), nav: document.querySelectorAll('nav,[role=navigation]').length, main: !!document.querySelector('main,[role=main]'), footer: !!document.querySelector('footer,[role=contentinfo]'), search: !!document.querySelector('input[type=search], input[name*=search i], input[placeholder*=search i], [role=search]') };
    const hs = [...document.querySelectorAll('h1,h2,h3')].filter(vis).slice(0, 30).map(h => h.tagName.toLowerCase() + ': ' + t(h.textContent).slice(0, 80));
    const body = t(document.body ? document.body.innerText : '');
    const pw = !!document.querySelector('input[type=password]');
    const forms = [...document.querySelectorAll('form')].filter(vis).map(f => [...f.querySelectorAll('input,select,textarea')].filter(vis).map(i => i.name || i.id || i.placeholder || i.type).slice(0, 14));
    const audience = ['issuer', 'acquirer', 'merchant', 'developer', 'partner', 'processor', 'fintech', 'atm', 'bank', 'financial institution'].filter(w => new RegExp('\\b' + w + 's?\\b', 'i').test(body.slice(0, 6000)));
    const skip = [...document.querySelectorAll('a[href^="#"]')].some(a => /skip/i.test(a.textContent));
    return { menu_links: menu, title: document.title, lang: document.documentElement.lang || null, h1: t(document.querySelector('h1') ? document.querySelector('h1').textContent : ''), description: (document.querySelector('meta[name=description]') || {}).content || null, links, ctas, signin, landmarks: lm, headings: hs, words: body.split(' ').length, password_field: pw, forms, audience_words: audience, skip_link: skip, text: body.slice(0, 4000) };
  });
}
function classifyWall(f, status) {
  if (status && status >= 400) return status === 403 ? 'bot' : 'dead';
  if (f.password_field) return 'login';
  if (/request access|by invitation|invite/i.test(f.text) && f.words < 400) return 'invite';
  if (/contact us|contact sales|talk to/i.test(f.text) && f.words < 250) return 'contact';
  return 'none';
}
function findLinks(f, re, base) { return f.links.concat(f.menu_links || []).concat(f.ctas.filter(c => c.href).map(c => ({ text: c.text, href: c.href }))).filter(l => l.href && !/#$/.test(l.href) && re.test(l.text + ' ' + l.href) && same(l.href, base)).filter((v, i, a) => a.findIndex(x => x.href === v.href) === i); }
async function bodyLinks(page, re) {
  return await page.evaluate((src) => { const re = new RegExp(src, 'i'); const t = s => (s || '').replace(/\s+/g, ' ').trim(); return [...document.querySelectorAll('a[href]')].map(a => ({ text: t(a.textContent).slice(0, 70), href: a.href })).filter(l => l.text && re.test(l.text + ' ' + l.href)).slice(0, 40); }, re.source);
}
(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 }, userAgent: UA, locale: 'en-US' });
  const page = await ctx.newPage(); page.setDefaultTimeout(20000);
  const S = rec.stations;
  // S0 setup
  { const r = await go(page, seed, 'S0 seed'); const cookie = await declineCookies(page); const f = r.ok ? await pageFacts(page) : { text: '', words: 0, password_field: false };
    S.S0 = { final_url: r.finalUrl, status: r.status, redirected: origin(seed) !== origin(r.finalUrl) || seed.replace(/\/$/, '') !== r.finalUrl.replace(/\/$/, ''), cookie_banner: cookie, wall: classifyWall(f, r.status), lang: f.lang || null, geo_prompt: /choose your (country|region|location)|select (a|your) (country|region)/i.test(f.text) };
    if (!r.ok) { rec.errors.push('seed did not load'); } }
  const home = page.url(); let hf = null;
  // S1 landing
  try { hf = await pageFacts(page); const file = await shot(page, 'S1', 'landing');
    S.S1 = { title: hf.title, h1: hf.h1, description: hf.description, landmarks: hf.landmarks, nav_labels: hf.links.map(l => l.text).filter((v, i, a) => a.indexOf(v) === i).slice(0, 30), ctas: hf.ctas.slice(0, 15), signin: hf.signin, audience_words: hf.audience_words, headings: hf.headings.slice(0, 15), screenshot: file }; } catch (e) { rec.errors.push('S1 ' + e.message); hf = hf || { links: [], ctas: [], text: '', words: 0 }; }
  // S2 what is visible logged out: each primary nav item once
  try { const seen = new Set(), items = []; const cands = hf.links.concat(hf.menu_links || []).filter(l => same(l.href, home) && !/^(#|javascript)/.test(l.href) && !/#$/.test(l.href) && l.href.replace(/#.*$/, '') !== home.replace(/#.*$/, '')).filter(l => { const k = l.href.replace(/#.*$/, ''); if (seen.has(k)) return false; seen.add(k); return true; }).slice(0, 16);
    for (const l of cands) { const r = await go(page, l.href, 'S2 ' + l.text); if (!r.ok) { items.push({ nav: l.text, url: l.href, result: 'dead' }); continue; } const f = await pageFacts(page); const wall = classifyWall(f, r.status); items.push({ nav: l.text, url: r.finalUrl, status: r.status, result: wall === 'none' ? 'readable' : wall, words: f.words, title: f.title }); if (wall !== 'none' && rec.screenshots.filter(s => s.station === 'S2').length < 2) await shot(page, 'S2', 'wall: ' + l.text); }
    S.S2 = { items, walls: items.filter(i => i.result !== 'readable').length, readable: items.filter(i => i.result === 'readable').length }; } catch (e) { rec.errors.push('S2 ' + e.message); }
  // S3 catalogue
  try { const re = /product|solution|service|api|offer|what we do|capabilit/i; const cands = findLinks(hf, re, home).slice(0, 4); let best = null;
    for (const l of cands) { const r = await go(page, l.href, 'S3 ' + l.text); if (!r.ok) continue; const f = await pageFacts(page); const prods = await page.evaluate(() => { const t = s => (s || '').replace(/\s+/g, ' ').trim(); const m = document.querySelector('main') || document.body; return [...m.querySelectorAll('a[href]')].filter(a => { const r = a.getBoundingClientRect(); return r.width > 0 && t(a.textContent).length > 2; }).map(a => ({ text: t(a.textContent).slice(0, 70), href: a.href })).filter((v, i, arr) => arr.findIndex(x => x.href === v.href) === i).slice(0, 80); });
      const cand = { from: l.text, url: r.finalUrl, title: f.title, headings: f.headings.slice(0, 20), links: prods.length, sample: prods.slice(0, 30), wall: classifyWall(f, r.status) }; if (!best || prods.length > best.links) best = cand; }
    if (best) { await go(page, best.url, 'S3 best'); best.screenshot = await shot(page, 'S3', 'catalogue'); }
    S.S3 = best || { note: 'no catalogue link found in primary nav' }; } catch (e) { rec.errors.push('S3 ' + e.message); }
  if (TIER === 'A') {
    // S4 docs depth: breadth-first from landing for a page with code or endpoints
    try { const re = /\bdocs?\b|documentation|reference|api|spec|guide|developer/i; const q = findLinks(hf, re, home).slice(0, 5).map(l => ({ ...l, depth: 1 })); const seen = new Set(); let found = null, auth = null, openapi = null, langs = new Set(), testData = false, samplesUrl = null;
      while (q.length && !found) { const l = q.shift(); if (seen.has(l.href) || l.depth > 3) continue; seen.add(l.href); const r = await go(page, l.href, 'S4 ' + l.text); if (!r.ok) continue;
        const info = await page.evaluate(() => { const t = s => (s || '').replace(/\s+/g, ' ').trim(); const body = t(document.body.innerText); const code = document.querySelectorAll('pre, code').length; const ep = (body.match(/\b(GET|POST|PUT|DELETE|PATCH)\s+\/[\w\/{}\-]+/g) || []).length; const langs = [...document.querySelectorAll('[class*=lang], [data-lang], .tab, [role=tab]')].map(e => t(e.textContent)).filter(x => /^(curl|java|python|node|javascript|c#|\.net|go|ruby|php|kotlin|swift)/i.test(x)); const openapi = [...document.querySelectorAll('a[href]')].map(a => a.href).filter(h => /openapi|swagger|postman|\.yaml|\.json/i.test(h)).slice(0, 5); const auth = [...document.querySelectorAll('a[href]')].filter(a => /auth|oauth|credential|api key|two-way|mtls/i.test(t(a.textContent))).map(a => ({ text: t(a.textContent).slice(0, 60), href: a.href })).slice(0, 5); const test = /test card|test pan|sandbox data|test data|trigger value/i.test(body); const links = [...document.querySelectorAll('a[href]')].map(a => ({ text: t(a.textContent).slice(0, 60), href: a.href })).filter(x => x.text && /doc|reference|api|spec|guide|endpoint|sdk|sample|quick ?start|getting started/i.test(x.text + ' ' + x.href)).slice(0, 25); return { code, ep, langs, openapi, auth, test, links, title: document.title, pw: !!document.querySelector('input[type=password]') }; });
        info.langs.forEach(x => langs.add(x.toLowerCase())); if (info.openapi.length && !openapi) openapi = info.openapi; if (info.auth.length && !auth) auth = info.auth; if (info.test) testData = true;
        if (info.code >= 3 || info.ep >= 1) { found = { url: r.finalUrl, title: info.title, depth: l.depth, code_blocks: info.code, endpoints_seen: info.ep, login_wall: info.pw }; samplesUrl = r.finalUrl; break; }
        for (const nl of info.links) if (same(nl.href, home) && !seen.has(nl.href)) q.push({ ...nl, depth: l.depth + 1 }); if (q.length > 40) q.length = 40; }
      if (found) await shot(page, 'S4', 'reference page');
      S.S4 = { clicks_to_docs: found ? found.depth : null, reference: found, sample_languages: [...langs].slice(0, 12), openapi_or_postman: openapi, auth_docs: auth, public_test_data_mentioned: testData, pages_tried: seen.size }; } catch (e) { rec.errors.push('S4 ' + e.message); }
    // S5 sandbox or key path: follow get started to the first wall
    try { await go(page, home, 'S5 home'); const re = /get started|getting started|start building|sign up|register|create (an )?account|sandbox|request access|apply|join/i; let cands = findLinks(hf, re, home); if (!cands.length) cands = (await bodyLinks(page, re)).filter(l => same(l.href, home)); const trail = []; let wall = 'none', fields = null, console_ = false, url = null; const seen = new Set();
      let cur = cands[0]; for (let depth = 1; cur && depth <= 4; depth++) { if (seen.has(cur.href)) break; seen.add(cur.href); const r = await go(page, cur.href, 'S5 ' + cur.text); trail.push({ click: depth, text: cur.text, url: r.finalUrl, status: r.status }); if (!r.ok) { wall = 'dead'; break; } const f = await pageFacts(page); console_ = console_ || /try it|playground|api explorer|run request|send request/i.test(f.text); const w = classifyWall(f, r.status); if (w !== 'none' || f.forms.some(x => x.length >= 3)) { wall = w === 'none' ? 'account form' : w; fields = f.forms.find(x => x.length >= 3) || null; url = r.finalUrl; await shot(page, 'S5', 'first wall'); break; } const next = (await bodyLinks(page, re)).filter(l => same(l.href, home) && !seen.has(l.href))[0]; cur = next; }
      S.S5 = { entry: cands[0] || null, trail, clicks_to_wall: url ? trail.length : null, wall, fields_asked: fields, try_it_console: console_ }; } catch (e) { rec.errors.push('S5 ' + e.message); }
    // S6 certification and testing
    try { await go(page, home, 'S6 home'); const re = /certif|testing|go[- ]live|launch|accredit|compliance program|validation/i; let cands = findLinks(hf, re, home); if (!cands.length) cands = (await bodyLinks(page, re)).filter(l => same(l.href, home)); const pages = [];
      for (const l of cands.slice(0, 3)) { const r = await go(page, l.href, 'S6 ' + l.text); if (!r.ok) continue; const f = await pageFacts(page); const steps = (f.text.match(/\bstep \d|\b\d\.\s|phase \d/gi) || []).length; const tools = (f.text.match(/simulator|test suite|test tool|self[- ]certif|sandbox|validation tool|test kit/gi) || []).map(x => x.toLowerCase()).filter((v, i, a) => a.indexOf(v) === i); const timeline = (f.text.match(/\b\d+\s*(business )?(days|weeks|months)\b/gi) || []).slice(0, 5); pages.push({ from: l.text, url: r.finalUrl, title: f.title, words: f.words, steps_mentioned: steps, tools_named: tools, timelines: timeline, wall: classifyWall(f, r.status) }); if (pages.length === 1) await shot(page, 'S6', 'certification'); }
      S.S6 = { pages, rung: pages.length ? (pages.some(p => p.tools_named.length) ? 'steps and named tools' : (pages.some(p => p.steps_mentioned >= 3) ? 'steps' : 'prose')) : 'not described' }; } catch (e) { rec.errors.push('S6 ' + e.message); }
  }
  // S7 support
  try { await go(page, home, 'S7 home'); const re = /support|contact|help( center| centre)?\b|get in touch/i; let cands = findLinks(hf, re, home); if (!cands.length) cands = (await bodyLinks(page, re)).filter(l => same(l.href, home)); let best = null;
    for (const l of cands.slice(0, 3)) { const r = await go(page, l.href, 'S7 ' + l.text); if (!r.ok) continue; const f = await pageFacts(page); const info = await page.evaluate(() => { const t = s => (s || '').replace(/\s+/g, ' ').trim(); const body = t(document.body.innerText); return { phones: (body.match(/(\+?\d{1,2}[\s.-])?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}/g) || []).filter((v, i, a) => a.indexOf(v) === i).slice(0, 5), mailto: [...document.querySelectorAll('a[href^="mailto:"]')].map(a => a.href.slice(7)).slice(0, 5), form: !!document.querySelector('form textarea, form input[type=email]'), chat: /live chat|chat with/i.test(body), hours: (body.match(/\b\d{1,2}(:\d{2})?\s*(a\.?m\.?|p\.?m\.?)\b[^.]{0,60}/i) || [null])[0], community: [...document.querySelectorAll('a[href]')].filter(a => /community|forum|discussion/i.test(t(a.textContent))).map(a => a.href).slice(0, 3), sla: /service level|sla\b|response time|within \d+ (hours|business days)/i.test(body), languages: /english|español|français|中文|日本語|deutsch|português/i.test(body) }; });
      const cand = { from: l.text, url: r.finalUrl, title: f.title, ...info, wall: classifyWall(f, r.status) }; if (!best || (info.phones.length + info.mailto.length + (info.form ? 1 : 0)) > (best.phones.length + best.mailto.length + (best.form ? 1 : 0))) best = cand; }
    if (best) { await go(page, best.url, 'S7 best'); best.screenshot = await shot(page, 'S7', 'support'); }
    S.S7 = best || { note: 'no support or contact link found' }; } catch (e) { rec.errors.push('S7 ' + e.message); }
  if (TIER === 'A') {
    // S8 status and change
    try { await go(page, home, 'S8 home'); const re = /status|changelog|release notes|what'?s new|versioning|updates|announcements|bulletin/i; const cands = findLinks(hf, re, home).concat((await bodyLinks(page, re)).filter(l => same(l.href, home))).filter((v, i, a) => a.findIndex(x => x.href === v.href) === i).slice(0, 4); const pages = [];
      for (const l of cands) { const r = await go(page, l.href, 'S8 ' + l.text); if (!r.ok) continue; const f = await pageFacts(page); const dates = (f.text.match(/\b(20\d\d-\d\d-\d\d|(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? \d{1,2},? 20\d\d)\b/g) || []).slice(0, 5); pages.push({ from: l.text, url: r.finalUrl, title: f.title, dates_seen: dates, kind: /status/i.test(l.text + l.href) ? 'status' : 'change' }); }
      S.S8 = { pages, status_page: pages.some(p => p.kind === 'status'), changelog: pages.some(p => p.kind === 'change') }; } catch (e) { rec.errors.push('S8 ' + e.message); }
    // S9 search
    try { await go(page, home, 'S9 home'); const queries = ['authorization', 'test cards', 'certification']; const results = []; let hasSearch = false;
      for (const qy of queries) { try { await go(page, home, 'S9 reset'); let box = page.locator('input[type=search]:visible, input[name*=search i]:visible, input[placeholder*=search i]:visible, [role=search] input:visible, input[aria-label*=search i]:visible').first(); if (!(await box.count())) { const opener = page.locator('button[aria-label*=search i]:visible, a[aria-label*=search i]:visible, button:has-text("Search"):visible, a:has-text("Search"):visible').first(); if (await opener.count()) { await opener.click({ timeout: 3000 }); await page.waitForTimeout(800); box = page.locator('input[type=search]:visible, input[name*=search i]:visible, input[placeholder*=search i]:visible, [role=search] input:visible, input[aria-label*=search i]:visible, input[type=text]:visible').first(); } } if (!(await box.count())) { results.push({ query: qy, result: 'no search box' }); continue; } hasSearch = true; await box.fill(qy); await box.press('Enter'); await page.waitForTimeout(2500); const top = await page.evaluate(() => { const t = s => (s || '').replace(/\s+/g, ' ').trim(); const m = document.querySelector('main') || document.body; const items = [...m.querySelectorAll('a[href]')].filter(a => t(a.textContent).length > 12 && !/^(home|next|previous|\d+)$/i.test(t(a.textContent))); return { count_hint: (t(document.body.innerText).match(/(\d[\d,]*)\s+(results?|matches|items)/i) || [null, null])[1], top: items.slice(0, 5).map(a => t(a.textContent).slice(0, 80)) }; }); results.push({ query: qy, url: page.url(), ...top }); } catch (e) { results.push({ query: qy, result: 'error: ' + e.message.split('\n')[0] }); } }
      S.S9 = { has_search: hasSearch, results }; } catch (e) { rec.errors.push('S9 ' + e.message); }
    // S10 assistive quick check
    try { await go(page, home, 'S10 home'); const f = await pageFacts(page); const focus = []; for (let i = 0; i < 10; i++) { await page.keyboard.press('Tab'); focus.push(await page.evaluate(() => { const e = document.activeElement; if (!e || e === document.body) return 'body'; const t = (e.textContent || e.getAttribute('aria-label') || e.getAttribute('placeholder') || '').replace(/\s+/g, ' ').trim().slice(0, 40); return e.tagName.toLowerCase() + (t ? ': ' + t : ''); })); }
      const order = f.headings.map(h => h.split(':')[0]); const h1s = order.filter(x => x === 'h1').length; const skipsLevel = order.some((h, i) => i > 0 && +h[1] - +order[i - 1][1] > 1);
      S.S10 = { lang: f.lang, skip_link: f.skip_link, landmarks: f.landmarks, h1_count: h1s, heading_level_skips: skipsLevel, first_ten_tabs: focus, nav_reachable_by_keyboard: focus.some(x => /^a:|^button:/.test(x)) }; } catch (e) { rec.errors.push('S10 ' + e.message); }
    // S11 mobile landing
    try { const m = await ctx.newPage(); await m.setViewportSize({ width: 390, height: 844 }); await m.goto(home, { waitUntil: 'domcontentloaded', timeout: 35000 }); await m.waitForTimeout(1500); await declineCookies(m); const info = await m.evaluate(() => ({ overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth + 2, hamburger: !!document.querySelector('button[aria-label*=menu i], button[aria-expanded], [class*=hamburger], [class*=burger], button[class*=menu]'), nav_visible: [...document.querySelectorAll('nav a')].filter(a => { const r = a.getBoundingClientRect(); return r.width > 0 && r.height > 0; }).length })); const file = await shot(m, 'S11', 'mobile landing'); S.S11 = { ...info, screenshot: file }; await m.close(); } catch (e) { rec.errors.push('S11 ' + e.message); }
  }
  // S12 first useful thing: a concrete artefact within two clicks of the landing
  try { await go(page, home, 'S12 home'); const re = /\.pdf|interchange|bin (range|table)|specification|spec\b|fee schedule|rules|guide|reference|test cards|sdk|download/i; let l1 = (await bodyLinks(page, re)).slice(0, 12); const found = []; for (const l of l1) found.push({ clicks: 1, text: l.text, href: l.href });
    if (!found.length) { for (const nl of hf.links.filter(l => same(l.href, home)).slice(0, 6)) { const r = await go(page, nl.href, 'S12 ' + nl.text); if (!r.ok) continue; for (const l of (await bodyLinks(page, re)).slice(0, 5)) found.push({ clicks: 2, via: nl.text, text: l.text, href: l.href }); if (found.length) break; } }
    S.S12 = { candidates: found.slice(0, 10), first: found[0] || null }; } catch (e) { rec.errors.push('S12 ' + e.message); }
  await browser.close();
  rec.summary = { pages_visited: rec.visited.length, screenshots: rec.screenshots.length, errors: rec.errors.length, walls_in_nav: S.S2 ? S.S2.walls : null, clicks_to_docs: S.S4 ? S.S4.clicks_to_docs : null, clicks_to_wall: S.S5 ? S.S5.clicks_to_wall : null, sandbox_wall: S.S5 ? S.S5.wall : null };
  fs.writeFileSync(OUT, JSON.stringify(rec, null, 1)); console.log(JSON.stringify(rec.summary)); console.log('wrote ' + path.relative(ROOT, OUT));
})().catch(e => { rec.errors.push('fatal ' + e.message); fs.writeFileSync(OUT, JSON.stringify(rec, null, 1)); console.error(e); process.exit(1); });
