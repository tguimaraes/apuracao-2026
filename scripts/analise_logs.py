"""Leitura detalhada dos logs de urna do 2º turno de 2026 numa amostra estratificada:
votos para presidente por faixa de 15 min, intervalos entre eleitores (fila/ociosidade) e eventos de biometria.
Uso: python analise_logs.py N SEED"""
import json, sys, io, random, re, time, urllib.request, datetime, collections, statistics
import py7zr, zipfile, gzip, lzma

BASE = "https://resultados.tse.jus.br/oficial/ele2026"; PLEITO = "3221"
UFS = ["ac","al","ap","am","ba","ce","df","es","go","ma","mt","ms","mg","pa","pb","pr","pe","pi","rj","rn","rs","ro","rr","sc","sp","se","to","zz"]
N = int(sys.argv[1]) if len(sys.argv) > 1 else 300; SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 2026
random.seed(SEED)

def get(url, binary=False, tries=3):
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (apuracao-2026 analise)"})
            with urllib.request.urlopen(req, timeout=60) as r: d = r.read()
            return d if binary else d.decode("utf-8", "replace")
        except Exception:
            if t == tries - 1: raise
            time.sleep(2)
def decompress(data):
    if data[:6] == b"7z\xbc\xaf\x27\x1c":
        with py7zr.SevenZipFile(io.BytesIO(data)) as z7: return "".join(b.read().decode("latin-1","replace") for b in z7.readall().values())
    if data[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(data)) as zf: return "".join(zf.read(n).decode("latin-1","replace") for n in zf.namelist())
    if data[:2] == b"\x1f\x8b": return gzip.decompress(data).decode("latin-1","replace")
    return lzma.decompress(data).decode("latin-1","replace")

universe = []
for uf in UFS:
    try: cs = json.loads(get(f"{BASE}/arquivo-urna/{PLEITO}/config/{uf}/{uf}-p00{PLEITO}-cs.json"))
    except Exception as e: print("sem cs", uf, e); continue
    for a in cs["abr"]:
        for m in a["mu"]:
            for z in m["zon"]:
                for s in z["sec"]: universe.append((uf, str(m["cd"]).zfill(5), str(z["cd"]).zfill(4), str(s["ns"]).zfill(4)))
total = len(universe)
sample = []
for uf in UFS:
    pool = [u for u in universe if u[0] == uf]
    if pool: sample += random.sample(pool, min(max(1, round(N * len(pool) / total)), len(pool)))
random.shuffle(sample); print("universo", total, "amostra", len(sample))

TS = re.compile(r"^(\d{2}/\d{2}/\d{4}) (\d{2}):(\d{2}):(\d{2})\t\S+\t\S+\t(\S+)\t(.*)$")
EV = {  # eventos exatos do componente VOTA
  "hab_bio": "Tipo de habilitação do eleitor [biométrica]",
  "hab_manual": "Tipo de habilitação do eleitor [manual]",
  "solic_manual": "Solicitação de dado pessoal do eleitor para habilitação manual",
  "tent_dedo": "Número de tentativas de reconhecimento do dedo",
  "timeout_dedo": "Timeout de reconhecimento do dedo",
  "id_cpf": "Identificador digitado pelo mesário foi: (CPF)",
  "id_titulo": "Identificador digitado pelo mesário foi: (Título de eleitor)",
  "justificativa": "Justificativa recebida",
  "corrigiu": "Eleitor corrigiu na tela de confirmação de candidato",
  "nao_encontrado": "Eleitor não encontrado para o identificador informado",
  "eleitores": "O voto do eleitor foi computado",
}
rows = []; tipos = collections.Counter()
for i, (uf, mun, zona, sec) in enumerate(sample):
    base = f"{BASE}/arquivo-urna/{PLEITO}/dados/{uf}/{mun}/{zona}/{sec}"
    row = {"uf": uf, "mun": mun, "zona": zona, "secao": sec, "erro": "", "bins": [0]*48, "votos": 0, "primeiro": "", "ultimo": "", "gaps_med": None, "gap_max_min": None,
           "ultima_hora": 0, "apos17": 0, "abertura": "", "encerramento": ""}
    for k in EV: row[k] = 0
    row["hab_tipos"] = {}; row["dur_med_s"] = None; row["dur_p90_s"] = None
    try:
        aux = json.loads(get(f"{base}/p00{PLEITO}-{uf}-m{mun}-z{zona}-s{sec}-aux.json"))
        h = aux["hashes"][0]; logname = next(a["nm"] for a in h["arq"] if a.get("tp") == "log")
        txt = decompress(get(f"{base}/{h['hash']}/{logname}", binary=True))
        times = []; durs = []; hab_t = None
        for line in txt.splitlines():
            m = TS.match(line)
            if not m or m.group(1) != "25/10/2026": continue
            hh, mm, ss, comp, msg = int(m.group(2)), int(m.group(3)), int(m.group(4)), m.group(5), m.group(6)
            secs = hh*3600 + mm*60 + ss
            if "Voto confirmado para [Presidente]" in msg:
                times.append(secs); row["bins"][min(47, secs // 1800)] += 1; row["votos"] += 1
                if secs > 17*3600: row["apos17"] += 1
                if 16*3600 <= secs < 17*3600: row["ultima_hora"] += 1
            else:
                m0 = msg.split("\t")[0]
                for k, pat in EV.items():
                    if m0.startswith(pat): row[k] += 1
                if m0.startswith("Tipo de habilitação do eleitor ["):
                    t_ = m0[len("Tipo de habilitação do eleitor ["):].rstrip("]"); row["hab_tipos"][t_] = row["hab_tipos"].get(t_, 0) + 1
                if m0.startswith("Eleitor foi habilitado"): hab_t = secs
                if m0.startswith("O voto do eleitor foi computado") and hab_t is not None: durs.append(secs - hab_t); hab_t = None
                if m0.startswith("Urna pronta para receber votos") and not row["abertura"]: row["abertura"] = f"{hh:02d}:{mm:02d}"
                if m0.startswith("Operador selecionou: Encerrar votação"): row["encerramento"] = f"{hh:02d}:{mm:02d}"
                if comp == "VOTA" and len(tipos) < 300: tipos[re.sub(r"\d+", "#", m0)[:90]] += 1
        if times:
            times.sort(); row["primeiro"] = f"{times[0]//3600:02d}:{times[0]%3600//60:02d}"; row["ultimo"] = f"{times[-1]//3600:02d}:{times[-1]%3600//60:02d}"
            gaps = [b - a for a, b in zip(times, times[1:])]
            if gaps: row["gaps_med"] = statistics.median(gaps); row["gap_max_min"] = round(max(gaps) / 60, 1)
        if durs: ds = sorted(durs); row["dur_med_s"] = ds[len(ds)//2]; row["dur_p90_s"] = ds[int(len(ds)*0.9)]
    except Exception as e:
        row["erro"] = f"{type(e).__name__}: {str(e)[:80]}"
    rows.append(row)
    if (i + 1) % 100 == 0: print("lidas", i + 1, flush=True)

json.dump({"gerado_em": datetime.datetime.now(datetime.timezone.utc).isoformat(), "pleito": PLEITO, "universo": total, "amostra": len(sample),
           "bins_min": 30, "secoes": rows, "tipos_msg": tipos.most_common(120)}, open("data/analise_logs.json", "w"), ensure_ascii=False)
ok = [r for r in rows if not r["erro"]]
print("ok", len(ok), "erros", len(rows) - len(ok), "votos", sum(r["votos"] for r in ok), "apos17", sum(r["apos17"] for r in ok))
agg = [sum(r["bins"][b] for r in ok) for b in range(48)]
print("votos por meia hora (0h..23h30):", agg)
print("eventos:", {k: sum(r[k] for r in ok) for k in EV})
ht = collections.Counter()
for r in ok: ht.update(r["hab_tipos"])
print("tipos de habilitação:", ht.most_common())
