# Roda no GitHub Actions. Minas Gerais em detalhe: 1º turno municipal com todos os candidatos
# e a divisão do IBGE em mesorregiões/microrregiões, para cruzar com o 2º turno.
import json, csv, urllib.request, concurrent.futures as cf, sys, time, unicodedata
BASE='https://resultados.tse.jus.br/oficial/ele2026/'
def get(url, tries=4):
    for i in range(tries):
        try:
            req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read().decode())
        except Exception as e: time.sleep(1.5*(i+1)); err=e
    print('falhou', url, err, file=sys.stderr); return None
cfg=get(BASE+'6258/config/mun-e006258-cm.json')
muns=[(m['cd'],m['nm']) for ab in cfg['abr'] if ab['cd']=='MG' for m in ab['mu']]
print('MG municipios', len(muns))
def one(m):
    cd,nm=m; d=get(f'{BASE}6257/dados/mg/mg{cd}-c0001-e006257-u.json')
    if not d: return None
    row=dict(cd=cd,nm=nm)
    for ag in d['carg'][0]['agr']:
        for p in ag['par']:
            for c in p['cand']: row['c'+c['n']]=int(c['vap'])
    return row
rows=[]
with cf.ThreadPoolExecutor(16) as ex:
    for r in ex.map(one, muns):
        if r: rows.append(r)
keys=['cd','nm']+sorted({k for r in rows for k in r if k.startswith('c')})
with open('data/tse/mg_1turno_candidatos.csv','w',newline='') as f:
    w=csv.DictWriter(f, fieldnames=keys); w.writeheader(); [w.writerow({k:r.get(k,0) for k in keys}) for r in rows]
# IBGE
ibge=get('https://servicodados.ibge.gov.br/api/v1/localidades/estados/31/municipios?view=nivelado')
def norm(s): return ''.join(ch for ch in unicodedata.normalize('NFD',s.upper()) if unicodedata.category(ch)!='Mn').replace("'","")
mp={norm(m['municipio-nome']):m for m in ibge}
with open('data/tse/mg_ibge.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['cd_tse','nm','cd_ibge','mesorregiao','microrregiao'])
    falt=0
    for cd,nm in muns:
        m=mp.get(norm(nm))
        if not m: falt+=1; w.writerow([cd,nm,'','','']); continue
        w.writerow([cd,nm,m['municipio-id'],m['mesorregiao-nome'],m['microrregiao-nome']])
print('ibge sem par', falt)
