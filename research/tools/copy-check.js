#!/usr/bin/env node
// copy-check.js — reads the reports' text and flags the tells that copy-lint flags in the prototype, plus the report's own rules.
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..');
const pages = ['partner-experience.html', 'journey-map.html', 'competitive-networks.html', 'prototype-insights.html'].filter(f => fs.existsSync(path.join(ROOT, f)));
const out = [];
for (const p of pages) {
  let html = fs.readFileSync(path.join(ROOT, p), 'utf8');
  html = html.replace(/<(pre|code|script|style)\b[\s\S]*?<\/\1>/g, ' ').replace(/<q\b[^>]*>[\s\S]*?<\/q>/g, ' ').replace(/<a class="rs-src"[^>]*>[\s\S]*?<\/a>/g, ' ').replace(/<blockquote\b[^>]*>\s*<p>[\s\S]*?<\/p>/g, '<blockquote>').replace(/&#x27;|&#39;/g, "'").replace(/&quot;/g, '"').replace(/&amp;/g, '&');
  html = html.replace(/<h2 class="doc-s" id="register">[\s\S]*$/, ' ');
  const method = (html.match(/id="method"[\s\S]*?(?=<h2)/) || [''])[0];
  html = html.replace(/<td\b[^>]*>/g, '<td>TD:');
  const blocks = html.split(/<\/(?:p|li|td|th|figcaption|cite|h1|h2|h3|h4|b|span|div)>/).map(b => b.replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ').trim()).filter(t => t.length > 12);
  const methodText = method.replace(/<[^>]+>/g, ' ');
  const seen = new Set();
  for (const t of blocks) {
    if (seen.has(t)) continue; seen.add(t);
    const inMethod = methodText.includes(t.slice(0, 40));
    if (/;/.test(t) && !/&#?\w+;|https?:/.test(t)) out.push(`${p} semicolon: ${t.slice(0, 100)}`);
    if (/—|–/.test(t)) out.push(`${p} dash: ${t.slice(0, 100)}`);
    if (/\bnot\b[^.]{0,40}\bbut\b|, not (?:a|an|the|just|merely)\b|\brather than\b/i.test(t)) out.push(`${p} contrast cadence: ${t.slice(0, 100)}`);
    if (!inMethod && /\b(we|We|our|Our|us)\b/.test(t) && !/["“”']/.test(t)) out.push(`${p} first person outside Method: ${t.slice(0, 100)}`);
    if (/\b(key takeaways?|executive summary|in this (?:report|section)|as (?:mentioned|noted) (?:above|earlier)|it is worth noting|it's worth noting|leverag(?:e|ing)|seamless(?:ly)?|robust|cutting.edge|game.chang)/i.test(t)) out.push(`${p} tell phrase: ${t.slice(0, 100)}`);
    if (/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u.test(t)) out.push(`${p} emoji: ${t.slice(0, 80)}`);
    const cell = t.startsWith('TD:'); if (cell) { const t2 = t.slice(3); if (t2.length < 12) continue; }
    if (!cell && /^[A-Z][a-z-]+(?:, [a-z][a-z-]+)+(?:,? and [a-z][a-z-]+)?\.?$/.test(t) && !/\b(is|are|has|have|who|what|how|was|were)\b/.test(t)) out.push(`${p} noun list: ${t.slice(0, 100)}`);
    if (!cell && /(?:\b[A-Z][^.!?]{0,14}\. ){2,}[A-Z][^.!?]{0,14}\.$/.test(t)) out.push(`${p} staccato: ${t.slice(0, 100)}`);
    const words = t.split(' ').length; if (/^[A-Z]/.test(t) && /[.!?]$/.test(t) && !/\. /.test(t) && words > 42) out.push(`${p} long sentence ${words}w: ${t.slice(0, 100)}`);
  }
}
if (out.length) { console.log(out.join('\n')); console.log(`copy-check: ${out.length} flagged`); process.exit(1); }
console.log('copy-check: clean');
