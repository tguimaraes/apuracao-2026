"""Amostra estratificada de seções do 2º turno de 2026: conta votos confirmados depois das 17h (hora local da urna)
a partir dos logs públicos do TSE. Uso: python amostra_logs.py N SEED"""
import json, sys, io, random, re, time, csv, urllib.request, datetime, collections
import py7zr, zipfile, gzip, lzma

def decompress(data):
    """O arquivo .jez pode vir como 7z, zip, gzip ou texto puro."""
    if data[:6] == b"7z\xbc\xaf\x27\x1c":
        with py7zr.SevenZipFile(io.BytesIO(data)) as z7: return "".join(b.read().decode("latin-1","replace") for b in z7.readall().values())
    if data[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(data)) as zf: return "".join(zf.read(n).decode("latin-1","replace") for n in zf.namelist())
    if data[:2] == b"\x1f\x8b": return gzip.decompress(data).decode("latin-1","replace")
    if data[:6] == b"\xfd7zXZ\x00": return lzma.decompress(data).decode("latin-1","replace")
    try: return lzma.decompress(data).decode("latin-1","replace")
    except Exception: pass
    raise ValueError("formato desconhecido, magic=" + repr(data[:8]))

BASE = "https://resultados.tse.jus.br/oficial/ele2026"
PLEITO = "3221"
UFS = ["ac","al","ap","am","ba","ce","df","es","go","ma","mt","ms","mg","pa","pb","pr","pe","pi","rj","rn","rs","ro","rr","sc","sp","se","to","zz"]
N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
random.seed(SEED)

def get(url, binary=False, tries=3):
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (apuracao-2026 amostra)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                d = r.read()
            return d if binary else d.decode("utf-8", "replace")
        except Exception as e:
            if t == tries - 1: raise
            time.sleep(2)

# 1) universo: todas as seções, por UF
universe = []  # (uf, mun, zona, secao)
per_uf = {}
for uf in UFS:
    try:
        cs = json.loads(get(f"{BASE}/arquivo-urna/{PLEITO}/config/{uf}/{uf}-p00{PLEITO}-cs.json"))
    except Exception as e:
        print("sem cs para", uf, e); continue
    n = 0
    for a in cs["abr"]:
        for m in a["mu"]:
            for z in m["zon"]:
                for s in z["sec"]:
                    universe.append((uf, str(m["cd"]).zfill(5), str(z["cd"]).zfill(4), str(s["ns"]).zfill(4))); n += 1
    per_uf[uf] = n
total = len(universe)
print("seções no universo:", total, per_uf)

# 2) amostra estratificada proporcional por UF (mínimo 1 por UF)
sample = []
for uf in UFS:
    pool = [u for u in universe if u[0] == uf]
    if not pool: continue
    k = max(1, round(N * len(pool) / total))
    sample += random.sample(pool, min(k, len(pool)))
random.shuffle(sample)
print("amostra:", len(sample))

# 3) lê cada log
VOTE_RE = re.compile(r"voto.*(confirmad|computad)", re.I)
TS_RE = re.compile(r"^(\d{2}/\d{2}/\d{4}) (\d{2}:\d{2}:\d{2})")
rows = []; msg_types = collections.Counter(); examples = []
for i, (uf, mun, zona, sec) in enumerate(sample):
    base = f"{BASE}/arquivo-urna/{PLEITO}/dados/{uf}/{mun}/{zona}/{sec}"
    row = {"uf": uf, "mun": mun, "zona": zona, "secao": sec, "status": "", "votos_total": 0, "votos_pres_total": 0, "apos17_total": 0, "apos17_pres": 0, "ultimo_voto": "", "erro": ""}
    try:
        aux = json.loads(get(f"{base}/p00{PLEITO}-{uf}-m{mun}-z{zona}-s{sec}-aux.json"))
        h = aux["hashes"][0]; row["status"] = h.get("st", "")
        logname = next(a["nm"] for a in h["arq"] if a.get("tp") == "log")
        data = get(f"{base}/{h['hash']}/{logname}", binary=True)
        txt = decompress(data)
        last = ""
        for line in txt.splitlines():
            m = TS_RE.match(line)
            if not m: continue
            if "vot" in line.lower():
                msg = re.sub(r"^\S+ \S+\s+\S+\s+\S+\s+\S+\s*", "", line).strip()
                msg_types[msg[:80]] += 1
            if VOTE_RE.search(line):
                d, t = m.group(1), m.group(2)
                if d != "25/10/2026": continue
                is_pres = "presidente" in line.lower()
                row["votos_total"] += 1
                if is_pres: row["votos_pres_total"] += 1
                last = f"{d} {t}"
                if t > "17:00:00":
                    row["apos17_total"] += 1
                    if is_pres: row["apos17_pres"] += 1
                if len(examples) < 12 or (t > "17:00:00" and len(examples) < 40): examples.append(line[:120])
        row["ultimo_voto"] = last
    except Exception as e:
        row["erro"] = f"{type(e).__name__}: {str(e)[:80]}"
    rows.append(row)
    if (i + 1) % 20 == 0: print("lidas", i + 1, "de", len(sample), flush=True)

# 4) saída
with open("data/amostra_logs.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
ok = [r for r in rows if not r["erro"]]
tot_v = sum(r["votos_total"] for r in ok); tot_p = sum(r["votos_pres_total"] for r in ok)
late_v = sum(r["apos17_total"] for r in ok); late_p = sum(r["apos17_pres"] for r in ok)
# extrapolação: média por seção × universo, com erro padrão
import statistics
vals = [r["apos17_pres"] if tot_p else r["apos17_total"] for r in ok]
mean = statistics.mean(vals) if vals else 0
sd = statistics.pstdev(vals) if len(vals) > 1 else 0
se = sd / (len(vals) ** 0.5) if vals else 0
est = mean * total; lo = max(0, (mean - 1.96 * se) * total); hi = (mean + 1.96 * se) * total
summary = {"gerado_em": datetime.datetime.now(datetime.timezone.utc).isoformat(), "pleito": PLEITO, "universo_secoes": total, "amostra": len(sample), "lidas_ok": len(ok),
  "erros": len(rows) - len(ok), "votos_lidos": tot_v, "votos_presidente_lidos": tot_p, "apos17_lidos": late_v, "apos17_presidente_lidos": late_p,
  "secoes_com_voto_apos17": sum(1 for v in vals if v > 0), "media_por_secao": mean, "estimativa_nacional": round(est), "ic95": [round(lo), round(hi)],
  "ultimo_voto_mais_tarde": max((r["ultimo_voto"] for r in ok), default=""), "por_uf": {}}
for uf in UFS:
    rs = [r for r in ok if r["uf"] == uf]
    if rs: summary["por_uf"][uf] = {"secoes": len(rs), "apos17": sum(r["apos17_pres"] or r["apos17_total"] for r in rs), "votos": sum(r["votos_pres_total"] or r["votos_total"] for r in rs)}
summary["tipos_de_mensagem_com_vot"] = msg_types.most_common(25)
summary["exemplos"] = examples
json.dump(summary, open("data/amostra_logs.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in summary.items() if k not in ("por_uf",)}, ensure_ascii=False, indent=1))
