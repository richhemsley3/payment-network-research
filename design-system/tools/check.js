/* check.js: does the system obey its own foundations?
   node tools/check.js            → every page under docs/, components/, patterns/ and index.html
   node tools/check.js path.html  → one page
   Reports: text sizes off the ramp (13 15 22 28 40 64), weights other than 400/600, grounds and text colours
   off the palette, uppercase outside the eyebrow, more than five sizes on a screen, hex literals in a page,
   prose wider than the measure, Heritage more than twice in a block,
   paddings and gaps off the 4px grid (margins may be 2, for a second line under a title), radii outside 12/8/6/3/2/50%/999,
   box-shadows on elements that are not floating, more than two Heritage touches
   per demo, and any page error. Exit 1 on anything found.
   Needs playwright on NODE_PATH. */
const {chromium}=require('playwright'); const fs=require('fs'), path=require('path');
const ROOT=path.resolve(__dirname,'..');
const DEV=path.resolve(ROOT,'../developers'); const devPages=fs.existsSync(DEV)?['','docs/','api/'].flatMap(d=>fs.readdirSync(path.join(DEV,d)).filter(f=>f.endsWith('.html')).map(f=>'../developers/'+d+f)):[];
const list=process.argv.slice(2).length?process.argv.slice(2):['index.html'].concat(['docs','components','patterns','charts'].flatMap(d=>fs.readdirSync(path.join(ROOT,d)).filter(f=>f.endsWith('.html')).map(f=>d+'/'+f))).concat(devPages);
const RAMP=[13,15,22,28,40,64], RADII=['0px','2px','3px','6px','8px','12px','50%','999px'];
(async()=>{ const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1440,height:1000}}); let total=0;
 for(const f of list){ const errs=[]; p.removeAllListeners('pageerror'); p.on('pageerror',e=>errs.push('page error: '+String(e).split('\n')[0]));
  await p.goto('file://'+path.join(ROOT,f)); await p.waitForTimeout(250);
  const r=await p.evaluate(({RAMP,RADII})=>{
    const out={size:{},weight:{},grid:{},radius:{},shadow:[],accent:[],ground:{},ink:{},upper:[],sizes:[],hex:[],measure:[]};
    /* the palette the guide allows, as the browser reports it */
    const ALLOW_BG=new Set(['rgba(0, 0, 0, 0)','rgb(255, 255, 255)','rgb(242, 242, 249)','rgb(0, 2, 38)','rgb(229, 230, 249)','rgb(241, 241, 251)','rgb(230, 240, 227)','rgb(251, 239, 227)','rgb(249, 230, 227)','rgb(21, 23, 56)','rgb(230, 231, 237)','rgb(221, 221, 227)','rgb(204, 204, 211)','rgb(254, 98, 0)','rgb(232, 86, 0)','rgb(35, 7, 98)','rgb(49, 68, 183)','rgb(158, 170, 252)','rgb(63, 122, 51)','rgb(138, 106, 21)','rgb(192, 57, 43)','rgb(110, 124, 217)','rgb(178, 155, 36)','rgb(122, 79, 168)','rgb(145, 145, 153)','rgb(20, 22, 54)','rgb(127, 194, 107)','rgb(227, 185, 80)','rgb(240, 141, 126)']);
    const ALLOW_INK=new Set(['rgb(21, 23, 56)','rgb(82, 83, 98)','rgb(105, 106, 117)','rgb(145, 145, 153)','rgb(255, 255, 255)','rgb(49, 68, 183)','rgb(35, 7, 98)','rgb(63, 122, 51)','rgb(138, 106, 21)','rgb(192, 57, 43)','rgb(127, 194, 107)','rgb(227, 185, 80)','rgb(240, 141, 126)','rgb(158, 170, 252)','rgb(254, 98, 0)','rgb(204, 204, 211)','rgb(110, 124, 217)','rgb(178, 155, 36)','rgb(122, 79, 168)']);
    const scope = document.querySelector('.demo-b, .dd-b') ? '.demo-b *, .dd-b *' : '.dv-body *, .dv-top *, .doc *';
    const isDemo=el=>el.closest('.demo-b, .dd-b'); const inDont=el=>el.closest('.dd-b') && el.closest('.dd > div').querySelector('.dd-h.is-dont');
    const floats=el=>el.closest('.gn-float, .gn-panel, .gn-dialog, .gn-toast, .gn-menu-panel, .gn-popover, .gn-date, .gn-cmd, .gn-console, .gn-tip, .gn-answer');
    const px=v=>parseFloat(v)||0;
    const seenSizes=new Set();
    document.querySelectorAll(scope).forEach(el=>{
      if(inDont(el)) return; if(el.closest('svg')&&el.tagName!=='svg'&&!/text/i.test(el.tagName)) return; if(el.tagName==='OPTION'||el.tagName==='SELECT') return;
      const cs=getComputedStyle(el);
      if(el.childNodes.length && [...el.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())){
        const s=Math.round(px(cs.fontSize)); if(!RAMP.includes(s)&&!el.closest('.gn-avatar')) out.size[s]=(out.size[s]||[]).concat(el.className||el.tagName).slice(0,3); seenSizes.add(s);
        const w=cs.fontWeight; if(w!=='400'&&w!=='600') out.weight[w]=(out.weight[w]||[]).concat(el.className||el.tagName).slice(0,3);
        /* text colour from the palette only */
        if(!ALLOW_INK.has(cs.color)&&!/rgba\(255, 255, 255/.test(cs.color)&&!/rgba\(0, 2, 38/.test(cs.color)&&!el.closest('svg')) out.ink[cs.color]=(out.ink[cs.color]||[]).concat(el.className||el.tagName).slice(0,3);
        /* uppercase only on the eyebrow style and group labels */
        if(cs.textTransform==='uppercase'&&!el.closest('.gn-eyebrow, .gn-nav-group, .gn-doc-groups h3, .gn-tl-day h3, .gn-tree h6, .gn-cred-k, .gn-notifs .gn-eyebrow, .demo-l, .doc-rule h4, .dv-toc h6')) out.upper.push(el.className||el.tagName);
        /* measure: prose lines never longer than 62ch */
        if(/^(P|LI)$/.test(el.tagName)&&el.textContent.length>120&&el.getBoundingClientRect().width>px(cs.fontSize)*0.55*76&&!el.closest('.gn-code, pre')) out.measure.push(el.className||el.tagName);
      }
      /* grounds: white, one tone, ink, the tints, and nothing else */
      const bg=cs.backgroundColor; if(bg&&!ALLOW_BG.has(bg)&&!/rgba\(/.test(bg)&&!el.closest('svg, .swatches, .swatch, .gn-color-strip, .idx-pre, .tok .sw, .gn-chart-tip')&&el.tagName!=='INPUT'&&el.tagName!=='I') out.ground[bg]=(out.ground[bg]||[]).concat(el.className||el.tagName).slice(0,3);
      ['paddingTop','paddingRight','paddingBottom','paddingLeft','columnGap','rowGap','marginTop','marginBottom'].forEach(k=>{ const v=cs[k]; if(v&&v!=='normal'&&v!=='auto'){ const n=px(v); const step=/margin/.test(k)?2:4; if(n<0) return; if(Math.abs(n)>0.01&&Math.abs(n%step)>0.01&&!el.closest('.gn-chip, .gn-seg, .gn-stepper, .gn-tip, .dv-hist')) out.grid[k+':'+v]=(out.grid[k+':'+v]||[]).concat(el.className||el.tagName).slice(0,2) } });
      ['borderTopLeftRadius'].forEach(k=>{ const v=cs[k]; if(v&&!RADII.includes(v)&&el.tagName!=='INPUT'&&!el.closest('svg')) out.radius[v]=(out.radius[v]||[]).concat(el.className||el.tagName).slice(0,3) });
      if(cs.boxShadow&&cs.boxShadow!=='none'&&!floats(el)&&!/inset|0px 0px 0px/.test(cs.boxShadow)) out.shadow.push(el.className||el.tagName);
    });
    document.querySelectorAll('.demo-b, .dv-body').forEach((d,i)=>{ let n=0; d.querySelectorAll('*').forEach(el=>{ if(el.closest('svg')) return; const cs=getComputedStyle(el); if(cs.backgroundColor==='rgb(254, 98, 0)'||cs.color==='rgb(254, 98, 0)'&&el.children.length===0) n++ }); if(n>2) out.accent.push('block '+(i+1)+': '+n+' heritage touches, the rule is two') });
    /* five sizes per screen, six for a marketing page */
    if(!document.querySelector('.spec-r')&&seenSizes.size>(document.querySelector('.gn-band, .gn-hero')?6:5)) out.sizes.push([...seenSizes].sort((a,b)=>a-b).join(' '));
    /* hex literals written into a page instead of a token */
    document.querySelectorAll(scope).forEach(el=>{ const st=el.getAttribute('style')||''; if(/#[0-9a-f]{3,6}\b/i.test(st)&&!el.closest('.swatches, .idx-pre, .gn-color-strip, .dd-b, .tok')) out.hex.push((el.className||el.tagName)+' '+st.match(/#[0-9a-f]{3,6}/i)[0]) });
    return out;
  },{RAMP,RADII});
  const lines=[];
  Object.entries(r.size).forEach(([k,v])=>lines.push('size '+k+'px: '+v.join(', ')));
  Object.entries(r.weight).forEach(([k,v])=>lines.push('weight '+k+': '+v.join(', ')));
  Object.entries(r.grid).forEach(([k,v])=>lines.push('off grid '+k+': '+v.join(', ')));
  Object.entries(r.radius).forEach(([k,v])=>lines.push('radius '+k+': '+v.join(', ')));
  Object.entries(r.ground).forEach(([k,v])=>lines.push('ground off the palette '+k+': '+v.join(', ')));
  Object.entries(r.ink).forEach(([k,v])=>lines.push('text colour off the palette '+k+': '+v.join(', ')));
  if(r.upper.length) lines.push('uppercase outside the eyebrow: '+[...new Set(r.upper)].slice(0,4).join(', '));
  r.sizes.forEach(x=>lines.push('more than five sizes on the screen: '+x));
  if(r.hex.length) lines.push('hex literal in the page: '+[...new Set(r.hex)].slice(0,4).join(' · '));
  if(r.measure.length) lines.push('prose wider than the measure: '+[...new Set(r.measure)].slice(0,3).join(', '));
  if(r.shadow.length) lines.push('shadow on non-floating: '+[...new Set(r.shadow)].slice(0,4).join(', '));
  r.accent.forEach(a=>lines.push(a)); errs.forEach(e=>lines.push(e));
  if(lines.length){ total+=lines.length; console.log('\n'+f); lines.forEach(l=>console.log('  '+l)) }
 }
 console.log(total?'\ncheck: '+total+' findings across '+list.length+' pages':'check: clean, '+list.length+' pages obey the foundations'); await b.close(); process.exit(total?1:0) })();
