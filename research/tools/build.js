#!/usr/bin/env node
// build.js — one self-contained file per report in dist/: CSS and JS inlined, images as data URIs, Figtree in place of the licensed face.
//   REPORT1_URL=https://claude.ai/... node tools/build.js   (the url rewrites Report 2's links into Report 1)
const fs = require('fs'), path = require('path');
const ROOT = path.resolve(__dirname, '..'), DIST = path.join(ROOT, 'dist'); fs.mkdirSync(DIST, { recursive: true });
const LIMIT = 12 * 1024 * 1024;
for (const name of ['partner-experience.html', 'competitive-networks.html', 'prototype-insights.html']) {
  const src = path.join(ROOT, name); if (!fs.existsSync(src)) continue;
  let html = fs.readFileSync(src, 'utf8'); let css = '';
  html = html.replace(/<link rel="stylesheet" href="([^"]+)">\n?/g, (m, href) => { let s = fs.readFileSync(path.join(ROOT, href), 'utf8'); if (/typography\.css$/.test(href)) { s = s.replace(/@font-face\{[^}]*ProximaNova[^}]*\}\s*/g, '').replace(/'Proxima Nova'/g, "'Figtree'").replace(/Proxima Nova/g, 'Figtree'); } css += `\n/* ${href} */\n` + s.replace(/url\((['"]?)\.\.\/fonts\/[^)]*\)/g, 'url()'); return ''; });
  html = html.replace(/<script src="([^"]+)"><\/script>\n?/g, (m, s) => `<script>\n${fs.readFileSync(path.join(ROOT, s), 'utf8')}\n</script>\n`);
  html = html.replace('</head>', `<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Figtree:wght@400;600&display=swap">\n<style>${css}\n</style>\n</head>`);
  html = html.replace(/src="(assets\/[^"]+\.webp)"/g, (m, f) => `src="data:image/webp;base64,${fs.readFileSync(path.join(ROOT, f)).toString('base64')}"`);
  if (name !== 'competitive-networks.html' && process.env.REPORT1_URL) { html = html.replace(/href="competitive-networks\.html(#[^"]*)?"/g, (m, a) => `href="${process.env.REPORT1_URL}${a || ''}"`); if (process.env.REPORT2_URL) html = html.replace(/href="prototype-insights\.html(#[^"]*)?"/g, (m, a) => `href="${process.env.REPORT2_URL}${a || ''}"`); }
  html = html.replace(/<a\b(?![^>]*target=)([^>]*href="https?:[^"]*")/g, '<a target="_blank" rel="noopener"$1');
  const out = path.join(DIST, name); fs.writeFileSync(out, html);
  // Artifact variant: the publisher wraps the page in its own document shell, so the file starts with its title and styles and carries no shell tags.
  const TITLES = { 'partner-experience.html': 'Partner Experience Teardown', 'competitive-networks.html': 'Card Network Partner Study', 'prototype-insights.html': 'Partner Desk Research Insights' };
  let art = html.replace(/<!DOCTYPE html>\s*|<html[^>]*>\s*|<\/html>\s*|<head>\s*|<\/head>\s*|<\/body>\s*|<meta charset="utf-8">\s*|<meta name="viewport"[^>]*>\s*|<meta name="color-scheme"[^>]*>\s*/g, '');
  art = art.replace(/<body[^>]*>/, '<div class="gn-docs rs-page">');
  art = art.replace(/<title>[^<]*<\/title>\s*/, '');
  const styles = (art.match(/<link rel="stylesheet" href="https:\/\/fonts[^>]*>\s*<style>[\s\S]*?<\/style>\s*/) || [''])[0];
  art = art.replace(styles, '');
  art = `<title>${TITLES[name]}</title>\n` + styles + art.trimEnd() + '\n</div>\n';
  fs.writeFileSync(path.join(DIST, 'artifact-' + name), art);
  const mb = fs.statSync(out).size / 1024 / 1024; console.log(`${name}: ${mb.toFixed(2)} MB`);
  if (fs.statSync(out).size > LIMIT) { console.error(`${name} is over ${LIMIT / 1024 / 1024} MB`); process.exit(1); }
}
