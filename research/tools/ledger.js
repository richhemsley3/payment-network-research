#!/usr/bin/env node
// ledger.js — reads ledger/*.md and writes sources.json. Markdown is the source of truth; never hand-edit the JSON.
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..'), L = path.join(ROOT, 'ledger');
const out = [];
const cells = line => line.slice(1, -1).split(/(?<!\\)\|/).map(c => c.replace(/\\\|/g, '|').trim());
for (const f of fs.readdirSync(L).filter(f => f.endsWith('.md') && f !== 'README.md')) {
  const slug = f.replace(/\.md$/, ''); let section = null;
  for (const line of fs.readFileSync(path.join(L, f), 'utf8').split('\n')) {
    if (line.startsWith('## ')) { section = line.slice(3).trim(); continue; }
    if (!line.startsWith('| ') || /^\|\s*-|^\| Id \|/.test(line)) continue;
    const c = cells(line);
    if (section === 'Sources' && c.length >= 11) out.push({ id: c[0], network: slug, kind: 'source', claim: c[1], dimension: c[2], title: c[3], publisher: c[4], url: c[5], published: c[6], accessed: c[7], confidence: c[8], archive: c[9] || null, note: c[10] || '' });
    else if (section === 'Screenshots' && c.length >= 7) out.push({ id: c[0], network: slug, kind: 'shot', step: c[1], url: c[2], captured: c[3], file: c[4], width: +c[5] || null, kb: +c[6] || null });
    else if (section === 'Demonstrations' && c.length >= 12) out.push({ id: c[0], network: slug, kind: 'video', title: c[1], channel: c[2], official: c[3] === 'yes', published: c[4], duration_s: +c[5] || null, url: c[6], accessed: c[7], shows: c[8], confidence: c[9], excerpts: c[10], frames: c[11] });
    else if (section === 'Sentiment' && c.length >= 10) out.push({ id: c[0], network: slug, kind: 'quote', platform: c[1], date: c[2], audience: c[3], stance: c[4], topic: c[5], author: c[6], excerpt: c[7], url: c[8], archive: c[9] || null });
  }
}
const ids = new Set(); const dup = out.filter(r => ids.has(r.id) ? true : (ids.add(r.id), false));
if (dup.length) { console.error('duplicate ids: ' + dup.map(d => d.id).join(', ')); process.exit(1); }
fs.writeFileSync(path.join(ROOT, 'sources.json'), JSON.stringify(out, null, 1));
const by = {}; for (const r of out) by[r.kind] = (by[r.kind] || 0) + 1;
console.log(`sources.json: ${out.length} rows`, by);
