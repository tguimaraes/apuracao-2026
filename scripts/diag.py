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
cap = next(m for m in sp["mu"] if m.get("c") == "S")
print("capital SP:", cap["cd"], cap["nm"], "zonas:", len(cap["z"]))
z = cap["z"][0]
print("zona exemplo:", json.dumps(z, ensure_ascii=False)[:600])

# tenta descobrir o código de arquivo-urna
zona = str(z["cd"]).zfill(4)
secao = str(z["s"][0]).zfill(4) if isinstance(z["s"][0], (str,int)) else str(z["s"][0]["cd"]).zfill(4)
mun5 = cap["cd"].zfill(5)
print("\n== testando aux.json em arquivo-urna para SP", mun5, zona, secao)
cands = [str(x) for x in range(3221, 3232)] + ["3220"] + [str(x) for x in range(3200, 3220)]
seen = set(); found = None
for c in cands:
    if c in seen: continue
    seen.add(c)
    url = f"{BASE}/ele2026/arquivo-urna/{c}/dados/sp/{mun5}/{zona}/{secao}/p{c.zfill(6)}-sp-m{mun5}-z{zona}-s{secao}-aux.json"
    try:
        j = json.loads(get(url)); print("OK", c, url); print(json.dumps(j, ensure_ascii=False)[:800]); found = (c, j, url); break
    except Exception as e:
        print("x", c, type(e).__name__, str(e)[:60])
if not found:
    print("Nenhum código funcionou; é preciso inspecionar o app do TSE."); sys.exit(0)
c, j, url = found
# baixa o logjez
h = j["hashes"][0]; hs = h["hash"]; names = h.get("nmarquivos", [])
print("arquivos:", names)
log = [n for n in names if n.endswith(".logjez")]
if log:
    lurl = url.rsplit("/",1)[0] + f"/{hs}/{log[0]}"
    data = get(lurl, binary=True); print("logjez bytes:", len(data), "magic:", data[:6])
    open("sample.logjez","wb").write(data)
    try:
        import py7zr
        with py7zr.SevenZipFile(io.BytesIO(data)) as z7:
            files = z7.getnames(); print("dentro do 7z:", files)
            for name, bio in z7.readall().items():
                txt = bio.read().decode("latin-1", "replace")
                lines = txt.splitlines(); print("linhas:", len(lines)); print("\n".join(lines[:15]))
                votos = [l for l in lines if "voto" in l.lower() and ("confirmado" in l.lower() or "computado" in l.lower())]
                print("linhas de voto:", len(votos)); print("\n".join(votos[:5])); print("..."); print("\n".join(votos[-5:]))
    except Exception as e:
        print("erro 7z:", e)
