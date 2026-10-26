const { chromium } = require('playwright');
const fs=require('fs');
(async()=>{ const caps=JSON.parse(fs.readFileSync('og/capitulos.json','utf8')); const tpl=fs.readFileSync('scripts/og_template.html','utf8');
 const b=await chromium.launch(); const pg=await b.newPage({viewport:{width:1200,height:630}});
 const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;');
 for (const c of caps){ const h=tpl.replace('__NUM__',c.num).replace('__TITLE__',esc(c.title)).replace('__STAT__',esc(c.stat[0])).replace('__STATDESC__',esc(c.stat[1]));
   fs.writeFileSync('/tmp/og_tmp.html',h); await pg.goto('file:///tmp/og_tmp.html'); await pg.evaluate(()=>document.fonts.ready); await pg.waitForTimeout(200); await pg.screenshot({path:`og/${c.slug}.png`}); }
 // capa geral do estudo
 const h=tpl.replace('__NUM__','índice').replace(' de 11','').replace('__TITLE__','Como Lula virou um jogo que estava perdendo').replace('__STAT__','4,4 mi').replace('__STATDESC__','de votos de vantagem, depois de sair 2,2 milhões atrás no 1º turno');
 fs.writeFileSync('/tmp/og_tmp.html',h); await pg.goto('file:///tmp/og_tmp.html'); await pg.evaluate(()=>document.fonts.ready); await pg.waitForTimeout(200); await pg.screenshot({path:'og/estudo.png'});
 await b.close(); console.log('og ok'); })();
