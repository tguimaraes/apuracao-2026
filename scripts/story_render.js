const { chromium } = require('playwright');
const fs=require('fs');
(async()=>{ const caps=JSON.parse(fs.readFileSync('og/capitulos.json','utf8')); const tpl=fs.readFileSync('scripts/story_template.html','utf8');
 fs.mkdirSync('og/story',{recursive:true});
 const b=await chromium.launch(); const pg=await b.newPage({viewport:{width:1080,height:1920}});
 const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;');
 const shot=async(h,out)=>{ fs.writeFileSync('/tmp/story_tmp.html',h); await pg.goto('file:///tmp/story_tmp.html'); await pg.evaluate(()=>document.fonts.ready); await pg.waitForTimeout(200); await pg.screenshot({path:out}); };
 for (const c of caps){ await shot(tpl.replace('__NUM__',c.num).replace('__TITLE__',esc(c.title)).replace('__STAT__',esc(c.stat[0])).replace('__STATDESC__',esc(c.stat[1])), `og/story/${c.slug}.png`); }
 await shot(tpl.replace('__NUM__','índice').replace(' de 11','').replace('__TITLE__','Como Lula virou um jogo que estava perdendo').replace('__STAT__','4,4 mi').replace('__STATDESC__','de votos de vantagem, depois de sair 2,2 milhões atrás no 1º turno'), 'og/story/estudo.png');
 await b.close(); console.log('story ok'); })();
