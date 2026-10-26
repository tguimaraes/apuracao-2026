"""Gera uma página por capítulo (capitulos/<slug>.html) com Open Graph e a história, e os dados para as imagens de prévia."""
import re, json, html
s = open('estudo.html', encoding='utf-8').read()
BASE = "https://tguimaraes.github.io/apuracao-2026"
secs = re.findall(r'<section class="card" id="([a-z0-9]+)">(.*?)</section>', s, re.S)
SLUG = {'aritmetica':'de-onde-vieram-os-votos','geografia':'por-que-o-nordeste-decidiu','estados':'estado-por-estado','interior':'cidade-grande-e-pequena','perfil':'quem-votou-em-quem','2022':'foi-igual-a-2022','fatores':'o-que-explica-a-vitoria','prorrogacao':'a-prorrogacao-mudou-o-resultado','abstencao':'mais-gente-foi-votar','redes':'redes-e-ruas','urnas':'o-que-as-urnas-contam'}
STAT = {'aritmetica':('3 em cada 4','dos 14 milhões de votos que trocaram de mão foram para Lula'),'geografia':('13,7 milhões','de vantagem para Lula só no Nordeste'),'estados':('1 estado','trocou de lado entre os turnos: Minas Gerais'),
 'interior':('55% × 54%','a cidade de SP deu Lula; o estado de SP deu Flávio'),'perfil':('58%','de quem ganha até 2 salários mínimos votou em Lula'),'2022':('98%','das cidades deram menos votos a Lula que em 2022, e ele venceu assim mesmo'),
 'fatores':('6 fatores','em ordem de peso, do que mais importou ao que menos'),'prorrogacao':('35.521','votos depois das 17h, contra 4,43 milhões de margem'),'abstencao':('3 milhões','de pessoas a mais foram votar no 2º turno, a maior alta desde 1989'),
 'redes':('150 milhões','de views num vídeo do lado que perdeu'),'urnas':('10 segundos','é o tempo de um voto, segundo os registros de 3 mil urnas')}
caps = []
for sid, body in secs:
    if sid not in SLUG: continue
    num = re.search(r'<div class="eyebrow">(\d+)</div>', body).group(1)
    h2 = html.unescape(re.sub(r'<[^>]+>','', re.search(r'<h2>(.*?)</h2>', body, re.S).group(1))).strip()
    story = re.search(r'<div class="story">(.*?)</div>\s*<(?:svg|div)', body, re.S).group(1)
    paras = [html.unescape(re.sub(r'<[^>]+>','', p)).strip() for p in re.findall(r'<p>(.*?)</p>', story, re.S)]
    bullets = [html.unescape(re.sub(r'<[^>]+>','', p)).strip() for p in re.findall(r'<li>(.*?)</li>', story, re.S)]
    desc = paras[0][:200].rsplit(' ',1)[0] + ('…' if len(paras[0])>200 else '')
    slug = SLUG[sid]; stat = STAT[sid]
    caps.append({'id':sid,'num':num,'slug':slug,'title':h2,'desc':desc,'stat':stat,'paras':paras,'bullets':bullets})
    url = f"{BASE}/capitulos/{slug}.html"
    share_txt = f"Capítulo {num}: {h2}"
    page = f'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(h2)} · Como Lula venceu</title>
<meta name="description" content="{html.escape(desc)}">
<meta property="og:type" content="article"><meta property="og:site_name" content="Como Lula venceu o 2º turno de 2026">
<meta property="og:title" content="{html.escape(h2)}"><meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{BASE}/og/{slug}.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{html.escape(h2)}"><meta name="twitter:description" content="{html.escape(desc)}"><meta name="twitter:image" content="{BASE}/og/{slug}.png">
<link rel="canonical" href="{url}">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap">
<style>
:root{{--bg:#F5F5F5;--card:#fff;--fg:#212121;--muted:#616161;--line:#E0E0E0;--info:#1565C0;--lula:#C62828;--flavio:#1565C0;color-scheme:light}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:17px/1.65 Roboto,system-ui,sans-serif;padding:0 max(16px,env(safe-area-inset-left)) 48px max(16px,env(safe-area-inset-right))}}
.bar{{background:#37474F;color:#fff;margin:0 -16px 20px;padding:14px 16px;font-size:.8rem;text-transform:uppercase;letter-spacing:.08em}}
.bar a{{color:#fff;text-decoration:none}}
.card{{max-width:760px;margin:0 auto;background:var(--card);border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.12),0 1px 2px rgba(0,0,0,.24);padding:28px}}
.eyebrow{{font-size:.72rem;text-transform:uppercase;letter-spacing:.09em;color:var(--muted);font-weight:500}}
h1{{font-size:1.6rem;line-height:1.25;margin:6px 0 14px;font-weight:500}}
.stat{{display:grid;grid-template-columns:auto 1fr;gap:16px;align-items:center;background:var(--bg);border-radius:8px;padding:14px 18px;margin:0 0 18px}}
.stat b{{font-size:2rem;color:var(--lula);white-space:nowrap}}.stat span{{color:var(--muted)}}
p{{max-width:68ch;font-size:1.08rem;line-height:1.7}}ul{{max-width:68ch;font-size:1.05rem}}li{{margin:8px 0}}
.btns{{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}}
.btn{{display:inline-block;padding:12px 18px;border-radius:24px;text-decoration:none;font-weight:500;font-size:.95rem;border:1px solid var(--line);color:var(--fg);background:#fff}}
.btn.p{{background:var(--info);color:#fff;border-color:var(--info)}}
.share{{margin-top:24px;border-top:1px solid var(--line);padding-top:16px}}
.share .l{{font-size:.8rem;color:var(--muted);margin-bottom:8px}}
.nav{{display:flex;justify-content:space-between;gap:12px;margin-top:22px;font-size:.9rem}}.nav a{{color:var(--info)}}
footer{{max-width:760px;margin:18px auto 0;font-size:.78rem;color:var(--muted);text-align:center}}
</style></head><body>
<div class="bar"><a href="../estudo.html">Como Lula venceu o 2º turno de 2026</a> · capítulo {num} de 11</div>
<main class="card">
  <div class="eyebrow">Capítulo {num}</div>
  <h1>{html.escape(h2)}</h1>
  <div class="stat"><b>{html.escape(stat[0])}</b><span>{html.escape(stat[1])}</span></div>
  {''.join(f'<p>{html.escape(p)}</p>' for p in paras)}
  {('<ul>' + ''.join(f'<li>{html.escape(b)}</li>' for b in bullets) + '</ul>') if bullets else ''}
  <div class="btns"><a class="btn p" href="../estudo.html#{sid}">Ver os gráficos e os números deste capítulo</a><a class="btn" href="../estudo.html">Ler o estudo completo</a><a class="btn" href="../">Painel da apuração</a></div>
  <div class="share"><div class="l">Compartilhar este capítulo</div>
    <div class="btns">
      <a class="btn" href="https://wa.me/?text={html.escape(share_txt + ' ' + url)}" target="_blank" rel="noopener">WhatsApp</a>
      <a class="btn" href="https://twitter.com/intent/tweet?text={html.escape(share_txt)}&url={url}" target="_blank" rel="noopener">X</a>
      <a class="btn" href="https://www.threads.net/intent/post?text={html.escape(share_txt + ' ' + url)}" target="_blank" rel="noopener">Threads</a>
      <a class="btn" href="https://www.linkedin.com/sharing/share-offsite/?url={url}" target="_blank" rel="noopener">LinkedIn</a>
      <button class="btn" type="button" id="copy">Copiar link</button>
    </div></div>
  <div class="nav"><span id="prev"></span><span id="next"></span></div>
</main>
<footer>Dados: TSE, Datafolha, FGV/CEPESP e logs públicos das urnas. Estudo independente, sem vínculo com candidatos, partidos ou com o TSE.</footer>
<script>
document.getElementById("copy").onclick=async function(){{try{{await navigator.clipboard.writeText("{url}");this.textContent="Link copiado";}}catch(e){{prompt("Copie o link:","{url}");}}setTimeout(()=>this.textContent="Copiar link",2500);}};
const C={json.dumps([[c['num'],c['slug'],c['title']] for c in caps], ensure_ascii=False)};
</script>
</body></html>'''
    open(f'capitulos/{slug}.html','w',encoding='utf-8').write(page)

# navegação anterior/próximo (segunda passada, agora com todos os capítulos)
allc = json.dumps([[c['num'],c['slug'],c['title']] for c in caps], ensure_ascii=False)
for i,c in enumerate(caps):
    f=f"capitulos/{c['slug']}.html"; t=open(f,encoding='utf-8').read()
    prev = f'<a href="{caps[i-1]["slug"]}.html">← {caps[i-1]["num"]}. {html.escape(caps[i-1]["title"])}</a>' if i>0 else ''
    nxt = f'<a href="{caps[i+1]["slug"]}.html">{caps[i+1]["num"]}. {html.escape(caps[i+1]["title"])} →</a>' if i<len(caps)-1 else ''
    t=t.replace('<span id="prev"></span>',f'<span id="prev">{prev}</span>').replace('<span id="next"></span>',f'<span id="next">{nxt}</span>')
    t=re.sub(r'const C=.*?;\n','',t)
    open(f,'w',encoding='utf-8').write(t)
json.dump(caps, open('og/capitulos.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(caps), "capítulos")
