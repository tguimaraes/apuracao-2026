# Roda no GitHub Actions (o contêiner do Claude não alcança o TSE). Baixa os resultados municipais
# dos dois turnos e grava um CSV compacto em data/tse/municipios.csv
import json, csv, urllib.request, concurrent.futures as cf, sys, time
BASE='https://resultados.tse.jus.br/oficial/ele2026/'
def get(url, tries=4):
    for i in range(tries):
        try:
            req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read().decode())
        except Exception as e:
            time.sleep(1.5*(i+1)); err=e
    print('falhou', url, err, file=sys.stderr); return None
cfg=get(BASE+'6258/config/mun-e006258-cm.json')
muns=[]
for ab in cfg['abr']:
    uf=ab['cd'].lower()
    for m in ab['mu']: muns.append((uf, m['cd'], m['nm'], m.get('c',''), m.get('z','')))
print('municipios', len(muns))
def cands(d):
    out={}
    for ag in d['carg'][0]['agr']:
        for p in ag['par']:
            for c in p['cand']: out[c['n']]=int(c['vap'])
    return out
def one(m):
    uf,cd,nm,cap,z=m; row=dict(uf=uf.upper(),cd=cd,nm=nm,capital=1 if str(cap)=='S' else 0)
    for ele,suf in ((6257,'1'),(6258,'2')):
        d=get(f'{BASE}{ele}/dados/{uf}/{uf}{cd}-c0001-e00{ele}-u.json')
        if not d: return None
        e,v=d['e'],d['v']; c=cands(d)
        row.update({f'te{suf}':int(e['te']),f'abs{suf}':int(e['a']),f'comp{suf}':int(e['c']),f'vb{suf}':int(v['vb']),f'vn{suf}':int(v['tvn']),f'lula{suf}':c.get('13',0),f'fl{suf}':c.get('22',0)})
    return row
rows=[]
with cf.ThreadPoolExecutor(16) as ex:
    for i,r in enumerate(ex.map(one, muns)):
        if r: rows.append(r)
        if i%500==0: print(i, file=sys.stderr)
rows.sort(key=lambda r:(r['uf'],r['nm']))
with open('data/tse/municipios.csv','w',newline='') as f:
    w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print('gravados', len(rows))
