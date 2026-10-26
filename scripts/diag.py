"""Diagnóstico: descobre a estrutura dos arquivos de urna do 2º turno de 2026 no site do TSE."""
import json, sys, re, io, urllib.request

BASE = "https://resultados.tse.jus.br/oficial"
def get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (apuracao-2026 diag)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")

print("== ele-c.json")
elec = json.loads(get(f"{BASE}/comum/config/ele-c.json"))
print(json.dumps([pl for pl in elec.get("pl",[]) if pl.get("c")=="ele2026"], ensure_ascii=False)[:3000])
codes = set()
def walk(o):
    if isinstance(o, dict):
        if "cd" in o and ("nm" in o or "t" in o): codes.add(str(o["cd"]))
        for v in o.values(): walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
walk(elec)
print("\n== códigos encontrados:", sorted(codes))

print("\n== mun-e006258-cm.json (trecho SP)")
mun = json.loads(get(f"{BASE}/ele2026/6258/config/mun-e006258-cm.json"))
print("chaves mun:", list(mun.keys()), "abr[0] chaves:", list(mun["abr"][0].keys()), "cd:", mun["abr"][0]["cd"])
sp = next(a for a in mun["abr"] if str(a["cd"]).upper() == "SP")
print("mu[0]:", json.dumps(sp["mu"][0], ensure_ascii=False)[:700])
cap = next((m for m in sp["mu"] if str(m.get("cd")).zfill(5) == "71072"), sp["mu"][0])
print("municipio:", cap.get("cd"), cap.get("nm"), "chaves:", list(cap.keys()))
zs = cap.get("z") or cap.get("zonas") or []
print("zonas:", len(zs))
z = zs[0] if zs else {}
print("zona exemplo:", json.dumps(z, ensure_ascii=False)[:600])

# descobre o pleito do 2º turno pelo arquivo de configuração de seções (cs) do arquivo-urna
mun5 = str(cap["cd"]).zfill(5)
cs = None; pleito = None
for c in [str(x) for x in range(3221, 3232)] + ["3220"]:
    url = f"{BASE}/ele2026/arquivo-urna/{c}/config/sp/sp-p{c.zfill(6)}-cs.json"
    try:
        cs = json.loads(get(url)); pleito = c; print("cs OK pleito", c, url); break
    except Exception as e:
        print("x cs", c, type(e).__name__, str(e)[:50])
if not cs: print("sem cs"); sys.exit(0)
print("cs chaves:", list(cs.keys()))
print(json.dumps(cs, ensure_ascii=False)[:1500])
# acha uma seção de São Paulo capital
def find_secoes(o, path=()):
    if isinstance(o, dict):
        for k,v in o.items(): yield from find_secoes(v, path+(k,))
    elif isinstance(o, list):
        for v in o: yield from find_secoes(v, path)
abr = cs.get("abr", [])
mu = None
for a_ in abr:
    for m in a_.get("mu", []):
        if str(m.get("cd")).zfill(5) == mun5: mu = m
print("mu SP capital chaves:", list(mu.keys()) if mu else None)
z0 = mu["zon"][0] if mu and "zon" in mu else (mu["z"][0] if mu else None)
print("zona0:", json.dumps(z0, ensure_ascii=False)[:500])
zona = str(z0.get("cd")).zfill(4)
sec0 = z0.get("sec", z0.get("s"))[0]
secao = str(sec0.get("ns") or sec0.get("cd") or sec0).zfill(4)
print("testando aux:", mun5, zona, secao)
url = f"{BASE}/ele2026/arquivo-urna/{pleito}/dados/sp/{mun5}/{zona}/{secao}/p{pleito.zfill(6)}-sp-m{mun5}-z{zona}-s{secao}-aux.json"
j = json.loads(get(url)); print("aux:", json.dumps(j, ensure_ascii=False)[:800])
h = j["hashes"][0]; hs = h["hash"]; names = h.get("nmarquivos", [])
log = [n for n in names if n.endswith(".logjez")]
if log:
    lurl = url.rsplit("/",1)[0] + f"/{hs}/{log[0]}"
    data = get(lurl, binary=True); print("logjez bytes:", len(data), "magic:", data[:6])
    import py7zr
    with py7zr.SevenZipFile(io.BytesIO(data)) as z7:
        print("dentro do 7z:", z7.getnames())
        for name, bio in z7.readall().items():
            txt = bio.read().decode("latin-1", "replace"); lines = txt.splitlines(); print("linhas:", len(lines)); print("\n".join(lines[:12]))
            votos = [l for l in lines if "voto" in l.lower() and ("confirmado" in l.lower() or "computado" in l.lower())]
            print("linhas de voto:", len(votos)); print("\n".join(votos[:6])); print("..."); print("\n".join(votos[-6:]))
            fim = [l for l in lines if "encerr" in l.lower() or "fim" in l.lower()][:8]; print("encerramento:"); print("\n".join(fim))
