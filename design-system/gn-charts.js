/* Global Network design system — the chart library.
   Dependency-free SVG, drawn from data, in the language: dotted grid, values on
   the left, a dated axis, the last point labelled, chart hues only past one
   series. Every chart takes a container and an options object and returns the
   svg. Load after gn.css.

   GNChart.line(el,{labels, series:[{name,values}], prev, fmt, min, max, area, step, points, label})
   GNChart.area(el,o)  GNChart.step(el,o)
   GNChart.bar(el,{labels, series, stacked, horizontal, fmt, highlight, label})
   GNChart.donut(el,{items:[{name,value}], fmt, center, centerLabel})
   GNChart.gauge(el,{value, min, max, fmt, bands:[{to,tone}], label})
   GNChart.radar(el,{axes:[…], series:[{name,values}], max})
   GNChart.waterfall(el,{steps:[{label,value,total}], fmt})
   GNChart.histogram(el,{bins:[…], start, width, unit, marker:{value,label}, tail})
   GNChart.scatter(el,{points:[{x,y,r,name,series}], xfmt, yfmt, series:[names]})
   GNChart.heatmap(el,{rows, cols, values:[[…]], fmt})
   GNChart.funnel(el,{steps:[{name,value}], fmt})
   GNChart.bullet(el,{value, target, max, fmt, label})
   GNChart.treemap(el,{items:[{name,value}], fmt})
   GNChart.box(el,{groups:[{name,min,q1,med,q3,max}], fmt})
   GNChart.dumbbell(el,{items:[{name,a,b}], names:[a,b], fmt, max})
   GNChart.spark(el,{values})
   GNChart.week(el,{values, today})
   GNChart.key(el,[{name,hue|tone}], {toggles:svg})   click an item to hide its series
   GNChart.ring(el,{value,max,size,fmt,tone})    GNChart.rings(el,{items:[{name,value,max}]})
   GNChart.lollipop(el,{items:[{name,value}],fmt,max})
   GNChart.activity(el,{values:[…], start, cols})   a calendar of days
   GNChart.delta(value, {fmt, good:'up'|'down'})   returns markup for a change
   Every mark carries data-tip; one floating tooltip serves all charts. Line and area charts add a hover line.
*/
window.GNChart=(function(){
  var NS='http://www.w3.org/2000/svg';
  var HUE=['var(--gn-interactive)','var(--gn-chart-2)','var(--gn-chart-3)','var(--gn-chart-4)','var(--gn-chart-5)'];
  var TONE={good:'var(--gn-good)',warn:'var(--gn-warn)',bad:'var(--gn-bad)',quiet:'var(--gn-outline)',track:'var(--gn-track)',ink:'var(--gn-interactive)'};
  function el(tag,a,txt){ var e=document.createElementNS(NS,tag); for(var k in a) if(a[k]!==undefined&&a[k]!==null) e.setAttribute(k,a[k]); if(txt!==undefined) e.textContent=txt; return e }
  function txt(x,y,s,cls,anchor){ return el('text',{x:x.toFixed(1),y:y.toFixed(1),'class':cls,'text-anchor':anchor||null},s) }
  function num(v,fmt){ if(fmt) return fmt(v); if(Math.abs(v)>=1e6) return (v/1e6).toFixed(1).replace(/\.0$/,'')+'M'; if(Math.abs(v)>=1e3) return (v/1e3).toFixed(1).replace(/\.0$/,'')+'k'; return Number.isInteger(v)?String(v):v.toFixed(1) }
  function wid(c,d){ if(typeof c==='string') c=document.querySelector(c); var w=c&&c.clientWidth; if(!w&&c&&c.parentNode) w=c.parentNode.clientWidth; return Math.max(240,Math.round(w||d||720)) }
  function mount(c,svg){ if(typeof c==='string') c=document.querySelector(c); if(!c) return svg; if(!c.classList.contains('gn-chart')) c.classList.add('gn-chart'); c.innerHTML=''; c.appendChild(svg); return svg }
  function svg(W,H,o){ var s=el('svg',{viewBox:'0 0 '+W+' '+H,role:'img','aria-label':o&&o.label||''}); return s }
  function nice(lo,hi){ if(hi===lo){ hi=lo+1 } var span=hi-lo, step=Math.pow(10,Math.floor(Math.log10(span))); var n=span/step; if(n<2) step/=5; else if(n<5) step/=2; return {lo:Math.floor(lo/step)*step, hi:Math.ceil(hi/step)*step, step:step} }
  function title(e,s){ var t=el('title'); t.textContent=s; e.appendChild(t); e.setAttribute('data-tip',s); return e }
  /* one floating tooltip for every chart on the page */
  var TIP; function tip(){ if(TIP) return TIP; TIP=document.createElement('div'); TIP.className='gn-chart-tip'; TIP.hidden=true; document.body.appendChild(TIP); return TIP }
  function showTip(html,x,y){ var t=tip(); t.innerHTML=html; t.hidden=false; var w=t.offsetWidth,h=t.offsetHeight; var lx=x+14, ly=y-h-10; if(lx+w>window.innerWidth-8) lx=x-w-14; if(ly<8) ly=y+14; t.style.left=(lx+window.scrollX)+'px'; t.style.top=(ly+window.scrollY)+'px' }
  function hideTip(){ if(TIP) TIP.hidden=true }
  document.addEventListener('mousemove',function(e){ var m=e.target.closest&&e.target.closest('[data-tip]'); if(m&&m.closest('.gn-chart')){ var s=m.getAttribute('data-tip'); showTip(s.replace(/ · /g,'<span class="sep"></span>'),e.clientX,e.clientY) } else if(TIP&&!TIP.hidden&&!(e.target.closest&&e.target.closest('.gn-chart-hover'))) hideTip() });
  function grp(s,i,name){ var g=el('g',{'data-series':i,'class':'series'}); if(name) g.setAttribute('data-name',name); s.appendChild(g); return g }
  /* a hover line for framed charts: nearest index, all series at once */
  function hoverLine(f,n,x,labels,series,fmt){
    var hl=el('line',{'class':'hl',x1:0,y1:f.T,x2:0,y2:f.H-f.B,style:'display:none'}); f.s.appendChild(hl);
    var pad=el('rect',{x:f.L,y:f.T,width:f.W-f.L-f.R,height:f.H-f.T-f.B,fill:'transparent','class':'gn-chart-hover'}); f.s.appendChild(pad);
    pad.addEventListener('mousemove',function(e){ var r=f.s.getBoundingClientRect(), px=(e.clientX-r.left)*(f.W/r.width); var i=Math.round((px-f.L)/((f.W-f.L-f.R)/(n-1||1))); i=Math.max(0,Math.min(n-1,i)); var xx=x(i); hl.setAttribute('x1',xx.toFixed(1)); hl.setAttribute('x2',xx.toFixed(1)); hl.style.display='';
      var html='<b>'+(labels[i]||'')+'</b>'+series.map(function(sr,si){ var v=sr.values[i]; return v===undefined?'':'<div><i style="background:'+(series.length>1?HUE[si%5]:HUE[0])+'"></i>'+(sr.name?sr.name+' ':'')+num(v,fmt)+'</div>' }).join(''); showTip(html,e.clientX,e.clientY) });
    pad.addEventListener('mouseleave',function(){ hl.style.display='none'; hideTip() });
  }

  /* a framed instrument: left values, bottom dates, dotted rules */
  function frame(o,W,H,lo,hi){
    var L=o.left||56, R=o.right||64, T=o.top||16, B=o.bottom||32;
    var s=svg(W,H,o), sc=nice(lo,hi); if(o.min!==undefined) sc.lo=o.min; if(o.max!==undefined) sc.hi=o.max;
    var y=function(v){ return T+(H-T-B)*(1-(v-sc.lo)/(sc.hi-sc.lo||1)) };
    [0,.5,1].forEach(function(f){ var v=sc.lo+(sc.hi-sc.lo)*f, yy=y(v); s.appendChild(el('line',{'class':'g',x1:L,y1:yy.toFixed(1),x2:W-R,y2:yy.toFixed(1)})); s.appendChild(txt(L-10,yy+4,num(v,o.fmt),'yl','end')) });
    return {s:s,L:L,R:R,T:T,B:B,W:W,H:H,y:y,lo:sc.lo,hi:sc.hi};
  }
  function axisLabels(f,labels){ var n=labels.length; if(!n) return; var idx=n>2?[0,Math.round((n-1)/2),n-1]:[0,n-1]; idx.forEach(function(i){ var x=f.L+(f.W-f.L-f.R)*(n>1?i/(n-1):0); f.s.appendChild(txt(x,f.H-8,labels[i],'xl',i===0?'start':i===n-1?'end':'middle')) }) }

  function line(c,o){
    o=o||{}; var W=o.w||wid(c,720), H=o.h||200, series=o.series||[{values:o.values||[]}], labels=o.labels||[];
    var all=[]; series.forEach(function(s){ all=all.concat(s.values) }); if(o.prev) all=all.concat(o.prev);
    var f=frame(o,W,H,Math.min.apply(null,all),Math.max.apply(null,all));
    var n=Math.max.apply(null,series.map(function(s){return s.values.length}));
    var x=function(i){ return f.L+(f.W-f.L-f.R)*(n>1?i/(n-1):0) };
    var path=function(vals){ var d=''; vals.forEach(function(v,i){ if(o.step&&i){ d+=' L'+x(i).toFixed(1)+','+f.y(vals[i-1]).toFixed(1) } d+=(i?' L':'M')+x(i).toFixed(1)+','+f.y(v).toFixed(1) }); return d };
    if(o.prev) f.s.appendChild(el('path',{'class':'l prev',d:path(o.prev)}));
    if(o.gradient){ var defs=el('defs'), gid='gng'+Math.random().toString(36).slice(2,7); var lg=el('linearGradient',{id:gid,x1:0,y1:0,x2:0,y2:1}); lg.appendChild(el('stop',{offset:'0%','stop-color':'var(--gn-interactive)','stop-opacity':.28})); lg.appendChild(el('stop',{offset:'100%','stop-color':'var(--gn-interactive)','stop-opacity':.02})); defs.appendChild(lg); f.s.appendChild(defs) }
    series.forEach(function(s,si){ var d=path(s.values), hue=series.length>1?HUE[si%5]:null, g=grp(f.s,si,s.name);
      if((o.area||o.area===undefined&&series.length===1&&o.area!==false)&&series.length===1){ g.appendChild(el('path',{'class':'a',d:d+' L'+x(s.values.length-1).toFixed(1)+','+(f.H-f.B)+' L'+f.L+','+(f.H-f.B)+' Z',style:o.gradient?'fill:url(#'+gid+');opacity:1':null})) }
      g.appendChild(el('path',{'class':'l',d:d,style:hue?'stroke:'+hue:null}));
      var last=s.values[s.values.length-1], lx=x(s.values.length-1), ly=f.y(last);
      g.appendChild(el('circle',{'class':'p',cx:lx.toFixed(1),cy:ly.toFixed(1),r:4,style:hue?'fill:'+hue:null}));
      if(o.endLabels!==false) g.appendChild(txt(lx+10,ly+4,num(last,o.fmt),'pl'));
      if(o.points){ s.values.forEach(function(v,i){ if(i===s.values.length-1) return; var p=el('circle',{'class':'p',cx:x(i).toFixed(1),cy:f.y(v).toFixed(1),r:3,style:'opacity:.5'+(hue?';fill:'+hue:'')}); title(p,(labels[i]||'')+' · '+num(v,o.fmt)); g.appendChild(p) }) }
    });
    axisLabels(f,labels);
    if(o.hover!==false) hoverLine(f,n,x,labels,series,o.fmt);
    return mount(c,f.s);
  }
  function area(c,o){ o=o||{}; if(o.stacked&&o.series&&o.series.length>1) return stackedArea(c,o); o.area=true; return line(c,o) }
  function stackedArea(c,o){
    var W=o.w||wid(c,720), H=o.h||200, labels=o.labels||[], series=o.series, n=series[0].values.length, tot=[]; for(var i=0;i<n;i++) tot.push(series.reduce(function(a,s){return a+(s.values[i]||0)},0));
    var f=frame({fmt:o.fmt,min:0,max:o.max,label:o.label},W,H,0,Math.max.apply(null,tot)); var x=function(i){ return f.L+(f.W-f.L-f.R)*(n>1?i/(n-1):0) };
    var base=[]; for(i=0;i<n;i++) base.push(0);
    series.forEach(function(s,si){ var top=s.values.map(function(v,i){ return base[i]+v }); var d='', back='';
      top.forEach(function(v,i){ d+=(i?' L':'M')+x(i).toFixed(1)+','+f.y(v).toFixed(1) }); for(i=n-1;i>=0;i--){ back+=' L'+x(i).toFixed(1)+','+f.y(base[i]).toFixed(1) }
      var g=grp(f.s,si,s.name); g.appendChild(el('path',{d:d+back+' Z',fill:HUE[si%5],'fill-opacity':.35})); g.appendChild(el('path',{'class':'l',d:d,style:'stroke:'+HUE[si%5]})); base=top });
    f.s.appendChild(txt(x(n-1)+10,f.y(tot[n-1])+4,num(tot[n-1],o.fmt),'pl'));
    axisLabels(f,labels); if(o.hover!==false) hoverLine(f,n,x,labels,series,o.fmt);
    return mount(c,f.s);
  }
  function ring(c,o){ o=o||{}; var size=o.size||64, sw=o.thick||(size>=64?8:6), r=size/2-sw/2, cx=size/2, cy=size/2, max=o.max||100, v=Math.max(0,Math.min(max,o.value||0)), s=el('svg',{'class':'gn-ring',viewBox:'0 0 '+size+' '+size,width:size,height:size,role:'img','aria-label':o.label||''});
    s.appendChild(el('circle',{cx:cx,cy:cy,r:r,fill:'none',stroke:'var(--gn-track)','stroke-width':sw}));
    var C=2*Math.PI*r; s.appendChild(title(el('circle',{cx:cx,cy:cy,r:r,fill:'none',stroke:o.tone?TONE[o.tone]:HUE[0],'stroke-width':sw,'stroke-dasharray':(C*v/max).toFixed(1)+' '+C.toFixed(1),transform:'rotate(-90 '+cx+' '+cy+')','stroke-linecap':'butt'}),(o.label?o.label+' · ':'')+num(v,o.fmt)+(o.max?' of '+num(max,o.fmt):'')));
    if(o.center!==false&&size>=48) s.appendChild(txt(cx,cy+4,o.center!==undefined?o.center:Math.round(100*v/max)+'%','rv','middle'));
    if(typeof c==='string') c=document.querySelector(c); if(c){ c.classList.add('gn-chart'); c.innerHTML=''; c.appendChild(s) } return s }
  function rings(c,o){ o=o||{}; var d=document.createElement('div'); d.className='gn-rings'; (o.items||[]).forEach(function(it){ var row=document.createElement('div'); row.className='gn-rings-r'; var holder=document.createElement('span'); ring(holder,{value:it.value,max:it.max||o.max||100,size:36,fmt:o.fmt,tone:it.tone,center:false}); row.appendChild(holder); var t=document.createElement('span'); t.innerHTML='<b>'+it.name+'</b><span>'+(it.sub||'')+'</span>'; row.appendChild(t); var v=document.createElement('span'); v.className='gn-num'; v.textContent=num(it.value,o.fmt)+(it.max||o.max?' of '+num(it.max||o.max||100,o.fmt):''); row.appendChild(v); d.appendChild(row) }); if(typeof c==='string') c=document.querySelector(c); if(c){ c.innerHTML=''; c.appendChild(d) } return d }
  function lollipop(c,o){ o=o||{}; var items=o.items||[], W=o.w||wid(c,720), rh=o.rowHeight||32, H=items.length*rh+8, s=svg(W,H,o), L=o.left||200, R=80, max=o.max||Math.max.apply(null,items.map(function(i){return i.value})), x=function(v){ return L+(W-L-R)*v/(max||1) };
    items.forEach(function(it,i){ var y=i*rh+rh/2+4; s.appendChild(txt(L-16,y+4,it.name,'xl','end')); s.appendChild(el('line',{x1:L,y1:y,x2:x(it.value).toFixed(1),y2:y,stroke:it.tone?TONE[it.tone]:HUE[0],'stroke-width':2})); s.appendChild(title(el('circle',{cx:x(it.value).toFixed(1),cy:y,r:6,fill:it.tone?TONE[it.tone]:HUE[0]}),it.name+' · '+num(it.value,o.fmt))); s.appendChild(txt(W-R+12,y+4,num(it.value,o.fmt),'wl')) });
    return mount(c,s) }
  function activity(c,o){ o=o||{}; var vals=o.values||[], cols=o.cols||Math.ceil(vals.length/7), cell=o.cell||14, gap=2, W=cols*(cell+gap)+40, H=7*(cell+gap)+20, s=svg(W,H,o), max=Math.max.apply(null,vals)||1, days=['M','','W','','F','',''];
    days.forEach(function(d,i){ if(d) s.appendChild(txt(4,i*(cell+gap)+cell-2+20,d,'xl')) });
    vals.forEach(function(v,i){ var col=Math.floor(i/7), row=i%7, a=v/max; var r=el('rect',{x:24+col*(cell+gap),y:20+row*(cell+gap),width:cell,height:cell,rx:2,fill:v?'var(--gn-interactive)':'var(--gn-gray-100)','fill-opacity':v?(0.2+a*0.8).toFixed(2):1}); title(r,(o.labels?o.labels[i]:'Day '+(i+1))+' · '+num(v,o.fmt)); s.appendChild(r) });
    if(o.months) o.months.forEach(function(m){ s.appendChild(txt(24+m[0]*(cell+gap),12,m[1],'xl')) });
    return mount(c,s) }
  function delta(v,o){ o=o||{}; var up=v>0, good=o.good==='down'?!up:up, tone=v===0?'quiet':good?'good':'bad'; return '<span class="gn-delta is-'+tone+'"><svg viewBox="0 0 12 12" aria-hidden="true">'+(v===0?'<path d="M2 6h8"/>':up?'<path d="M6 10V2M2.5 5.5L6 2l3.5 3.5"/>':'<path d="M6 2v8M2.5 6.5L6 10l3.5-3.5"/>')+'</svg>'+(o.fmt?o.fmt(Math.abs(v)):num(Math.abs(v)))+(o.suffix||'')+'</span>' }
  function step(c,o){ o=o||{}; o.step=true; o.area=false; return line(c,o) }

  function bar(c,o){
    o=o||{}; var labels=o.labels||[], series=o.series||[{values:o.values||[]}], n=labels.length||series[0].values.length;
    if(o.horizontal) return barH(c,o);
    var W=o.w||wid(c,720), H=o.h||200; var tot=[]; for(var i=0;i<n;i++){ tot.push(o.stacked?series.reduce(function(a,s){return a+(s.values[i]||0)},0):Math.max.apply(null,series.map(function(s){return s.values[i]||0}))) }
    var f=frame({fmt:o.fmt,min:o.min!==undefined?o.min:0,max:o.max,label:o.label,left:o.left,right:o.right||24},W,H,o.min!==undefined?o.min:0,Math.max.apply(null,tot));
    var slot=(f.W-f.L-f.R)/n, gap=Math.min(12,slot*.25), inner=slot-gap, k=series.length;
    for(var i=0;i<n;i++){ var x0=f.L+i*slot+gap/2, acc=0;
      series.forEach(function(s,si){ var v=s.values[i]||0, hue=k>1?HUE[si%5]:null; var g=f.s.querySelector('g[data-series="'+si+'"]')||grp(f.s,si,s.name);
        if(o.stacked){ var y1=f.y(acc+v), y0=f.y(acc); var r=el('rect',{'class':'b on',x:x0.toFixed(1),y:y1.toFixed(1),width:inner.toFixed(1),height:Math.max(0,y0-y1-1).toFixed(1),rx:2,style:hue?'fill:'+hue:null}); title(r,(labels[i]||'')+' · '+(s.name?s.name+' ':'')+num(v,o.fmt)); g.appendChild(r); acc+=v }
        else { var bw=inner/k, bx=x0+si*bw, yy=f.y(v); var on=o.highlight===undefined?true:o.highlight===i; var r2=el('rect',{'class':'b'+(on?' on':''),x:bx.toFixed(1),y:yy.toFixed(1),width:(bw-(k>1?2:0)).toFixed(1),height:Math.max(0,f.H-f.B-yy).toFixed(1),rx:2,style:hue&&on?'fill:'+hue:null}); title(r2,(labels[i]||'')+' · '+(s.name?s.name+' ':'')+num(v,o.fmt)); g.appendChild(r2) }
      });
      if(o.valueLabels&&!o.stacked){ f.s.appendChild(txt(x0+inner/2,f.y(tot[i])-6,num(tot[i],o.fmt),'pl','middle')) }
    }
    axisLabels(f,labels);
    return mount(c,f.s);
  }
  function barH(c,o){
    var items=o.items||o.labels.map(function(l,i){ return {name:l,value:o.series[0].values[i]} }); var W=o.w||wid(c,720), rh=o.rowHeight||32, H=items.length*rh+8;
    var s=svg(W,H,o), max=o.max||Math.max.apply(null,items.map(function(i){return i.value})), L=o.left||200, R=o.right||72;
    items.forEach(function(it,i){ var y=i*rh+8, w=(W-L-R)*(it.value/(max||1)); s.appendChild(txt(L-16,y+rh/2,it.name,'xl','end')); s.appendChild(el('rect',{'class':'b',x:L,y:y+rh/2-5,width:(W-L-R),height:10,rx:3})); var r=el('rect',{'class':'b on',x:L,y:y+rh/2-5,width:w.toFixed(1),height:10,rx:3,style:it.tone?'fill:'+TONE[it.tone]:null}); title(r,it.name+' · '+num(it.value,o.fmt)); s.appendChild(r); s.appendChild(txt(W-R+12,y+rh/2+4,num(it.value,o.fmt),'wl')) });
    return mount(c,s);
  }

  function donut(c,o){
    o=o||{}; var items=o.items||[], total=items.reduce(function(a,i){return a+i.value},0), W=o.w||wid(c,360), H=o.h||(o.half?140:200), cx=100, cy=o.half?H-24:H/2, r=72, sw=o.thick||24, s=svg(W,H,o), span=o.half?Math.PI:2*Math.PI;
    var a0=o.half?Math.PI:-Math.PI/2; items.forEach(function(it,i){ var a1=a0+span*(it.value/(total||1)); var large=a1-a0>Math.PI?1:0; var x0=cx+r*Math.cos(a0), y0=cy+r*Math.sin(a0), x1=cx+r*Math.cos(a1), y1=cy+r*Math.sin(a1);
      var p=el('path',{d:'M'+x0.toFixed(1)+','+y0.toFixed(1)+' A'+r+','+r+' 0 '+large+' 1 '+x1.toFixed(1)+','+y1.toFixed(1),fill:'none',stroke:it.tone?TONE[it.tone]:HUE[i%5],'stroke-width':sw,'class':'dn'}); title(p,it.name+' · '+num(it.value,o.fmt)+' · '+Math.round(100*it.value/(total||1))+'%'); grp(s,i,it.name).appendChild(p); a0=a1+0.02 });
    if(!o.half) s.appendChild(el('circle',{cx:cx,cy:cy,r:r-sw/2-1,fill:'var(--gn-bg-page)'}));
    s.appendChild(txt(cx,o.half?cy-6:cy+2,o.center!==undefined?o.center:num(total,o.fmt),'dc','middle')); if(o.centerLabel) s.appendChild(txt(cx,o.half?cy+14:cy+22,o.centerLabel,'xl','middle'));
    var room=Math.floor((W-8-218-44)/7); items.forEach(function(it,i){ var y=(o.half?cy-40:cy)-(items.length-1)*12+i*24; var nm=it.name.length>room?it.name.slice(0,Math.max(2,room-1))+'…':it.name; s.appendChild(el('rect',{x:200,y:y-6,width:10,height:10,rx:2,fill:it.tone?TONE[it.tone]:HUE[i%5]})); s.appendChild(title(txt(218,y+4,nm,'xl'),it.name+' · '+num(it.value,o.fmt))); s.appendChild(txt(W-8,y+4,Math.round(100*it.value/(total||1))+'%','wl','end')) });
    return mount(c,s);
  }
  function gauge(c,o){
    o=o||{}; var W=o.w||wid(c,240), H=o.h||140, cx=W/2, cy=H-20, r=88, sw=14, min=o.min||0, max=o.max||100, v=Math.max(min,Math.min(max,o.value||0)), s=svg(W,H,o);
    var arc=function(a,b,stroke,cls){ var x0=cx+r*Math.cos(a), y0=cy+r*Math.sin(a), x1=cx+r*Math.cos(b), y1=cy+r*Math.sin(b); return el('path',{d:'M'+x0.toFixed(1)+','+y0.toFixed(1)+' A'+r+','+r+' 0 '+(b-a>Math.PI?1:0)+' 1 '+x1.toFixed(1)+','+y1.toFixed(1),fill:'none',stroke:stroke,'stroke-width':sw,'stroke-linecap':'butt','class':cls||''}) };
    s.appendChild(arc(Math.PI,2*Math.PI,'var(--gn-track)'));
    var tone='ink'; (o.bands||[]).forEach(function(b){ if(v>=b.from&&(b.to===undefined||v<=b.to)) tone=b.tone });
    if(v>min) s.appendChild(title(arc(Math.PI,Math.PI+Math.PI*(v-min)/(max-min),TONE[tone]||HUE[0]),num(v,o.fmt)));
    s.appendChild(txt(cx,cy-8,num(v,o.fmt),'gv','middle')); if(o.label) s.appendChild(txt(cx,cy+12,o.label,'xl','middle'));
    s.appendChild(txt(cx-r,cy+14,num(min,o.fmt),'xl','middle')); s.appendChild(txt(cx+r,cy+14,num(max,o.fmt),'xl','middle'));
    return mount(c,s);
  }
  function radar(c,o){
    o=o||{}; var axes=o.axes||[], series=o.series||[], n=axes.length, W=o.w||wid(c,360), H=o.h||300, cx=W/2, cy=H/2, r=Math.min(W,H)/2-40, max=o.max||100, s=svg(W,H,o);
    var pt=function(i,v){ var a=-Math.PI/2+2*Math.PI*i/n; return [cx+r*(v/max)*Math.cos(a), cy+r*(v/max)*Math.sin(a)] };
    [.5,1].forEach(function(f){ var d=''; for(var i=0;i<n;i++){ var p=pt(i,max*f); d+=(i?' L':'M')+p[0].toFixed(1)+','+p[1].toFixed(1) } s.appendChild(el('path',{'class':'g',d:d+' Z',fill:'none'})) });
    for(var i=0;i<n;i++){ var p=pt(i,max), lp=pt(i,max*1.18); s.appendChild(el('line',{'class':'g',x1:cx,y1:cy,x2:p[0].toFixed(1),y2:p[1].toFixed(1)})); s.appendChild(txt(lp[0],lp[1]+4,axes[i],'xl','middle')) }
    series.forEach(function(sr,si){ var d=''; sr.values.forEach(function(v,i){ var p=pt(i,v); d+=(i?' L':'M')+p[0].toFixed(1)+','+p[1].toFixed(1) }); var hue=HUE[si%5]; s.appendChild(title(el('path',{d:d+' Z',fill:hue,'fill-opacity':.12,stroke:hue,'stroke-width':1.75}),sr.name||'')); sr.values.forEach(function(v,i){ var p=pt(i,v); s.appendChild(title(el('circle',{cx:p[0].toFixed(1),cy:p[1].toFixed(1),r:3,fill:hue}),axes[i]+' · '+num(v,o.fmt))) }) });
    return mount(c,s);
  }
  function waterfallH(c,o){
    var steps=o.steps||[], W=o.w||wid(c,720), rh=40, H=steps.length*rh+8, s=svg(W,H,o), L=o.left||180, R=110;
    var run=0, vals=[]; steps.forEach(function(st){ if(st.total){ run=st.value } else run+=st.value; vals.push(run) });
    var hi=Math.max.apply(null,vals.concat(steps.map(function(st){return st.total?st.value:0}))), lo=Math.min(0,Math.min.apply(null,vals)); var x=function(v){ return L+(W-L-R)*(v-lo)/(hi-lo||1) }; run=0;
    steps.forEach(function(st,i){ var y=i*rh+8, from=st.total?0:run, to=st.total?st.value:run+st.value; run=to;
      s.appendChild(txt(L-16,y+rh/2+4,st.label,'xl','end'));
      var r=el('rect',{'class':'w '+(st.total?'tot':st.value<0?'neg':''),x:Math.min(x(from),x(to)).toFixed(1),y:y+8,width:Math.max(2,Math.abs(x(from)-x(to))).toFixed(1),height:rh-16,rx:2}); title(r,st.label+' · '+num(st.value,o.fmt)); s.appendChild(r);
      s.appendChild(txt(W-R+12,y+rh/2+4,(st.total||st.value>=0?'':'−')+num(Math.abs(st.value),o.fmt),'wl'));
      if(i<steps.length-1) s.appendChild(el('line',{'class':'wc',x1:x(to).toFixed(1),y1:y+rh-8,x2:x(to).toFixed(1),y2:y+rh+8})) });
    return mount(c,s);
  }
  function waterfall(c,o){
    o=o||{}; if(o.horizontal) return waterfallH(c,o); var steps=o.steps||[], W=o.w||wid(c,720), H=o.h||220, s=svg(W,H,o), L=40, R=20, T=20, B=40;
    var run=0, vals=[]; steps.forEach(function(st){ if(st.total){ run=st.value } else run+=st.value; vals.push(run) });
    var hi=Math.max.apply(null,vals.concat(steps.map(function(st){return st.total?st.value:0}))), lo=Math.min(0,Math.min.apply(null,vals)); var y=function(v){ return T+(H-T-B)*(1-(v-lo)/(hi-lo||1)) };
    s.appendChild(el('line',{'class':'g',x1:L,y1:y(0).toFixed(1),x2:W-R,y2:y(0).toFixed(1)}));
    var slot=(W-L-R)/steps.length, bw=Math.min(120,slot*.7); run=0;
    steps.forEach(function(st,i){ var x=L+i*slot+(slot-bw)/2, from=st.total?0:run, to=st.total?st.value:run+st.value; run=to;
      var r=el('rect',{'class':'w '+(st.total?'tot':st.value<0?'neg':''),x:x.toFixed(1),y:Math.min(y(from),y(to)).toFixed(1),width:bw.toFixed(1),height:Math.max(2,Math.abs(y(from)-y(to))).toFixed(1),rx:2}); title(r,st.label+' · '+num(st.value,o.fmt)); s.appendChild(r);
      s.appendChild(txt(x+bw/2,Math.min(y(from),y(to))-6,(st.total||st.value>=0?'':'−')+num(Math.abs(st.value),o.fmt),'wl','middle')); s.appendChild(txt(x+bw/2,H-12,st.label,'xl','middle'));
      if(i<steps.length-1) s.appendChild(el('line',{'class':'wc',x1:(x+bw).toFixed(1),y1:y(to).toFixed(1),x2:(L+(i+1)*slot+(slot-bw)/2).toFixed(1),y2:y(to).toFixed(1)})) });
    return mount(c,s);
  }
  function histogram(c,o){
    o=o||{}; var bins=o.bins||[], W=o.w||wid(c,720), H=o.h||200, start=o.start||0, width=o.width||1, unit=o.unit||'';
    var f=frame({fmt:function(v){return num(v)},min:0,label:o.label,right:24},W,H,0,Math.max.apply(null,bins.concat(o.overlay||[]))); var slot=(f.W-f.L-f.R)/bins.length;
    bins.forEach(function(v,i){ var x=f.L+i*slot, tail=o.tail!==undefined&&(start+i*width)>=o.tail; var r=el('rect',{'class':'h'+(tail?' tail':''),x:(x+1).toFixed(1),y:f.y(v).toFixed(1),width:Math.max(1,slot-2).toFixed(1),height:Math.max(0,f.H-f.B-f.y(v)).toFixed(1),rx:2}); title(r,num(start+i*width)+' to '+num(start+(i+1)*width)+' '+unit+' · '+num(v)); f.s.appendChild(r) });
    if(o.curve){ var pts=bins.map(function(v,i){ return [f.L+i*slot+slot/2, f.y(v)] }); var d=''; pts.forEach(function(p,i){ if(!i){ d='M'+p[0].toFixed(1)+','+p[1].toFixed(1); return } var q=pts[i-1], cx1=(q[0]+p[0])/2; d+=' C'+cx1.toFixed(1)+','+q[1].toFixed(1)+' '+cx1.toFixed(1)+','+p[1].toFixed(1)+' '+p[0].toFixed(1)+','+p[1].toFixed(1) }); f.s.appendChild(el('path',{'class':'l',d:d,style:'stroke:var(--gn-text);stroke-width:1.5'})) }
    if(o.overlay){ var ov=o.overlay; ov.forEach(function(v,i){ var x=f.L+i*slot; f.s.appendChild(title(el('rect',{x:(x+1).toFixed(1),y:f.y(v).toFixed(1),width:Math.max(1,slot-2).toFixed(1),height:Math.max(0,f.H-f.B-f.y(v)).toFixed(1),rx:2,fill:HUE[1],'fill-opacity':.55}),(o.overlayName||'')+' · '+num(start+i*width)+' to '+num(start+(i+1)*width)+' '+unit+' · '+num(v))) }) }
    if(o.marker){ var mx=f.L+(f.W-f.L-f.R)*((o.marker.value-start)/(width*bins.length)); f.s.appendChild(el('line',{'class':'hm',x1:mx.toFixed(1),y1:f.T-6,x2:mx.toFixed(1),y2:f.H-f.B})); f.s.appendChild(txt(mx+8,f.T+4,o.marker.label||num(o.marker.value)+' '+unit,'pl')) }
    var end=start+width*bins.length; [start,start+(end-start)/2,end].forEach(function(v,i){ f.s.appendChild(txt(f.L+(f.W-f.L-f.R)*i/2,f.H-8,num(Math.round(v))+(i===2?' '+unit:''),'xl',i===0?'start':i===2?'end':'middle')) });
    return mount(c,f.s);
  }
  function scatter(c,o){
    o=o||{}; var pts=o.points||[], W=o.w||wid(c,720), H=o.h||260, xs=pts.map(function(p){return p.x}), ys=pts.map(function(p){return p.y});
    var f=frame({fmt:o.yfmt,min:o.ymin,max:o.ymax,label:o.label,right:24,bottom:40},W,H,Math.min.apply(null,ys),Math.max.apply(null,ys)); var xr=nice(Math.min.apply(null,xs),Math.max.apply(null,xs)); if(o.xmin!==undefined) xr.lo=o.xmin; if(o.xmax!==undefined) xr.hi=o.xmax;
    var x=function(v){ return f.L+(f.W-f.L-f.R)*(v-xr.lo)/(xr.hi-xr.lo||1) };
    pts.forEach(function(p){ var hue=p.series!==undefined?HUE[p.series%5]:HUE[0]; var cc=el('circle',{cx:x(p.x).toFixed(1),cy:f.y(p.y).toFixed(1),r:p.r||5,fill:hue,'fill-opacity':.7,stroke:'var(--gn-bg-page)','stroke-width':1}); title(cc,(p.name?p.name+' · ':'')+num(p.x,o.xfmt)+', '+num(p.y,o.yfmt)); f.s.appendChild(cc); if(p.label){ var right=x(p.x)>f.W*0.75; f.s.appendChild(txt(x(p.x)+(right?-1:1)*((p.r||5)+6),f.y(p.y)+4,p.name,'xl',right?'end':'start')) } });
    [xr.lo,(xr.lo+xr.hi)/2,xr.hi].forEach(function(v,i){ f.s.appendChild(txt(x(v),f.H-8,num(v,o.xfmt),'xl',i===0?'start':i===2?'end':'middle')) });
    if(o.xlabel) f.s.appendChild(txt(f.W-f.R,f.H-24,o.xlabel,'xl','end'));
    return mount(c,f.s);
  }
  function heatmap(c,o){
    o=o||{}; var rows=o.rows||[], cols=o.cols||[], vals=o.values||[], W=o.w||wid(c,720), L=o.left||96, T=24, cw=(W-L-8)/cols.length, ch=o.cell||24, H=T+rows.length*ch+8, s=svg(W,H,o);
    var flat=[].concat.apply([],vals), max=o.max||Math.max.apply(null,flat), min=o.min||0;
    cols.forEach(function(cn,j){ if(cols.length<=12||j%Math.ceil(cols.length/12)===0) s.appendChild(txt(L+j*cw+cw/2,14,cn,'xl','middle')) });
    rows.forEach(function(rn,i){ s.appendChild(txt(L-12,T+i*ch+ch/2+4,rn,'xl','end')); cols.forEach(function(cn,j){ var v=(vals[i]||[])[j]||0, a=(v-min)/(max-min||1); var r=el('rect',{x:(L+j*cw+1).toFixed(1),y:(T+i*ch+1).toFixed(1),width:(cw-2).toFixed(1),height:(ch-2).toFixed(1),rx:2,fill:'var(--gn-interactive)','fill-opacity':(0.06+a*.9).toFixed(2)}); title(r,rn+' · '+cn+' · '+num(v,o.fmt)); s.appendChild(r) }) });
    return mount(c,s);
  }
  function funnel(c,o){
    o=o||{}; var steps=o.steps||[], W=o.w||wid(c,720), rh=44, H=steps.length*rh+8, s=svg(W,H,o), max=steps[0]?steps[0].value:1, L=200, R=140;
    steps.forEach(function(st,i){ var y=i*rh+8, w=(W-L-R)*(st.value/(max||1)); s.appendChild(txt(L-16,y+rh/2+4,st.name,'xl','end')); s.appendChild(el('rect',{'class':'b',x:L,y:y+8,width:W-L-R,height:rh-16,rx:3})); var r=el('rect',{'class':'b on',x:L,y:y+8,width:w.toFixed(1),height:rh-16,rx:3,style:'fill-opacity:'+(1-i*0.12)}); title(r,st.name+' · '+num(st.value,o.fmt)); s.appendChild(r); s.appendChild(txt(W-R+12,y+rh/2+4,num(st.value,o.fmt)+(i?' · '+Math.round(100*st.value/(steps[i-1].value||1))+'%':''),'wl')) });
    return mount(c,s);
  }
  function bullet(c,o){
    o=o||{}; var W=o.w||wid(c,720), H=48, s=svg(W,H,o), L=o.left||160, R=80, max=o.max||100, x=function(v){ return L+(W-L-R)*v/max };
    s.appendChild(txt(L-16,28,o.label||'','xl','end'));
    (o.ranges||[]).forEach(function(r,i){ s.appendChild(el('rect',{x:x(i?o.ranges[i-1]:0).toFixed(1),y:14,width:(x(r)-x(i?o.ranges[i-1]:0)).toFixed(1),height:20,fill:'var(--gn-outline)','fill-opacity':(0.25+i*0.2).toFixed(2)})) });
    if(!o.ranges) s.appendChild(el('rect',{'class':'b',x:L,y:14,width:W-L-R,height:20,rx:2}));
    s.appendChild(title(el('rect',{'class':'b on',x:L,y:19,width:(x(o.value)-L).toFixed(1),height:10,rx:2}),num(o.value,o.fmt)));
    if(o.target!==undefined){ s.appendChild(title(el('line',{x1:x(o.target).toFixed(1),y1:10,x2:x(o.target).toFixed(1),y2:38,stroke:'var(--gn-text)','stroke-width':2}),'target '+num(o.target,o.fmt))) }
    s.appendChild(txt(W-R+12,28,num(o.value,o.fmt)+(o.target!==undefined?' of '+num(o.target,o.fmt):''),'wl'));
    return mount(c,s);
  }
  function treemap(c,o){
    o=o||{}; var items=(o.items||[]).slice().sort(function(a,b){return b.value-a.value}), W=o.w||wid(c,720), H=o.h||280, s=svg(W,H,o), total=items.reduce(function(a,i){return a+i.value},0);
    var x=0,y=0,w=W,h=H, i=0, labels=[]; /* slice and dice, alternating, good enough for a dozen items */
    while(i<items.length){ var rest=items.slice(i).reduce(function(a,it){return a+it.value},0); var it=items[i], f=it.value/(rest||1);
      var rw,rh,rx=x,ry=y; if(w>h){ rw=w*f; rh=h; x+=rw; w-=rw } else { rw=w; rh=h*f; y+=rh; h-=rh }
      var r=el('rect',{x:(rx+1).toFixed(1),y:(ry+1).toFixed(1),width:Math.max(0,rw-2).toFixed(1),height:Math.max(0,rh-2).toFixed(1),rx:3,fill:it.tone?TONE[it.tone]:HUE[i%5],'fill-opacity':(0.85-i*0.05).toFixed(2)}); title(r,it.name+' · '+num(it.value,o.fmt)+' · '+Math.round(100*it.value/(total||1))+'%'); s.appendChild(r);
      if(rw>72&&rh>32){ var chars=Math.floor((rw-20)/7.2), name=it.name.length>chars?it.name.slice(0,Math.max(1,chars-1))+'…':it.name; labels.push([rx+10,ry+20,name,rx+10,ry+36,num(it.value,o.fmt)]) }
      i++ }
    labels.forEach(function(l){ s.appendChild(txt(l[0],l[1],l[2],'tl')); s.appendChild(txt(l[3],l[4],l[5],'tv')) });
    return mount(c,s);
  }
  function box(c,o){
    o=o||{}; var groups=o.groups||[], W=o.w||wid(c,720), H=o.h||220, all=[]; groups.forEach(function(g){ all.push(g.min,g.max) });
    var f=frame({fmt:o.fmt,label:o.label,right:24,bottom:36},W,H,Math.min.apply(null,all),Math.max.apply(null,all)); var slot=(f.W-f.L-f.R)/groups.length, bw=Math.min(48,slot*.5);
    groups.forEach(function(g,i){ var cx=f.L+i*slot+slot/2; f.s.appendChild(el('line',{x1:cx,y1:f.y(g.max).toFixed(1),x2:cx,y2:f.y(g.min).toFixed(1),stroke:'var(--gn-outline)'})); [g.min,g.max].forEach(function(v){ f.s.appendChild(el('line',{x1:cx-8,y1:f.y(v).toFixed(1),x2:cx+8,y2:f.y(v).toFixed(1),stroke:'var(--gn-outline)'})) });
      var r=el('rect',{x:(cx-bw/2).toFixed(1),y:f.y(g.q3).toFixed(1),width:bw,height:Math.max(1,f.y(g.q1)-f.y(g.q3)).toFixed(1),rx:2,fill:'var(--gn-interactive)','fill-opacity':.18,stroke:'var(--gn-interactive)'}); title(r,g.name+' · median '+num(g.med,o.fmt)+' · '+num(g.q1,o.fmt)+' to '+num(g.q3,o.fmt)); f.s.appendChild(r);
      f.s.appendChild(el('line',{x1:(cx-bw/2).toFixed(1),y1:f.y(g.med).toFixed(1),x2:(cx+bw/2).toFixed(1),y2:f.y(g.med).toFixed(1),stroke:'var(--gn-interactive)','stroke-width':2}));
      f.s.appendChild(txt(cx,f.H-8,g.name,'xl','middle')) });
    return mount(c,f.s);
  }
  function dumbbell(c,o){
    o=o||{}; var items=o.items||[], W=o.w||wid(c,720), rh=36, H=items.length*rh+8, s=svg(W,H,o), L=o.left||200, R=100, max=o.max||Math.max.apply(null,items.map(function(i){return Math.max(i.a,i.b)})), min=o.min||0, x=function(v){ return L+(W-L-R)*(v-min)/((max-min)||1) };
    items.forEach(function(it,i){ var y=i*rh+rh/2+4; s.appendChild(txt(L-16,y+4,it.name,'xl','end')); s.appendChild(el('line',{x1:x(Math.min(it.a,it.b)).toFixed(1),y1:y,x2:x(Math.max(it.a,it.b)).toFixed(1),y2:y,stroke:'var(--gn-outline)','stroke-width':3}));
      s.appendChild(title(el('circle',{cx:x(it.a).toFixed(1),cy:y,r:6,fill:HUE[0]}),(o.names?o.names[0]+' ':'')+num(it.a,o.fmt))); s.appendChild(title(el('circle',{cx:x(it.b).toFixed(1),cy:y,r:6,fill:HUE[1]}),(o.names?o.names[1]+' ':'')+num(it.b,o.fmt)));
      s.appendChild(txt(W-R+12,y+4,num(it.a,o.fmt)+' · '+num(it.b,o.fmt),'wl')) });
    return mount(c,s);
  }
  function spark(c,o){ o=o||{}; var v=o.values||[], W=120,H=28, mx=Math.max.apply(null,v), mn=Math.min.apply(null,v), s=el('svg',{'class':'gn-spark',viewBox:'0 0 '+W+' '+H}); var d=v.map(function(y,i){ return (i?'L':'M')+(i*W/(v.length-1||1)).toFixed(1)+','+(H-2-(H-4)*((y-mn)/(mx-mn||1))).toFixed(1) }).join(' '); s.appendChild(el('path',{d:d})); if(typeof c==='string') c=document.querySelector(c); if(c){ c.innerHTML=''; c.appendChild(s) } return s }
  function week(c,o){ o=o||{}; var v=o.values||[], mx=Math.max.apply(null,v), d=document.createElement('span'); d.className='gn-week'; v.forEach(function(x,i){ var b=document.createElement('i'); b.style.setProperty('--h',Math.round(100*x/(mx||1))+'%'); if(i===(o.today!==undefined?o.today:v.length-1)) b.className='on'; b.title=(o.labels?o.labels[i]+' · ':'')+num(x,o.fmt); d.appendChild(b) }); if(typeof c==='string') c=document.querySelector(c); if(c){ c.innerHTML=''; c.appendChild(d) } return d }
  function key(c,items,o){ o=o||{}; if(typeof c==='string') c=document.querySelector(c); var d=document.createElement('div'); d.className='gn-chart-key'+(o.toggles?' is-toggles':''); items.forEach(function(it,i){ var sp=document.createElement('span'); if(o.toggles){ sp.setAttribute('data-series',it.series!==undefined?it.series:i); sp.addEventListener('click',function(){ var sv=typeof o.toggles==='string'?document.querySelector(o.toggles):o.toggles; sv=sv.tagName==='svg'?sv:sv.querySelector('svg'); var g=sv&&sv.querySelector('g[data-series="'+sp.getAttribute('data-series')+'"]'); if(g){ g.classList.toggle('is-off'); sp.classList.toggle('is-off') } }) } var sw=document.createElement('i'); sw.className=it.fill?'f1':''; sw.style.borderColor=it.tone?TONE[it.tone]:HUE[(it.hue!==undefined?it.hue:i)%5]; if(it.fill){ sw.style.background=it.tone?TONE[it.tone]:HUE[(it.hue!==undefined?it.hue:i)%5]; sw.style.borderColor='transparent' } if(it.dashed){ sw.className='prev' } sp.appendChild(sw); sp.appendChild(document.createTextNode(it.name)); d.appendChild(sp) }); if(c){ c.appendChild(d) } return d }
  return {line:line,area:area,stackedArea:stackedArea,step:step,bar:bar,ring:ring,rings:rings,lollipop:lollipop,activity:activity,delta:delta,waterfallH:waterfallH,barH:barH,donut:donut,gauge:gauge,radar:radar,waterfall:waterfall,histogram:histogram,scatter:scatter,heatmap:heatmap,funnel:funnel,bullet:bullet,treemap:treemap,box:box,dumbbell:dumbbell,spark:spark,week:week,key:key,HUE:HUE,TONE:TONE};
})();
