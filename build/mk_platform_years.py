# -*- coding: utf-8 -*-
# Добавляет в site/platform_data.json узлы Казахстана по годам — только в вариант «% ВВП» (bc_gdp).
# Источники векторов (54 листа, % ВВП, соцналог в ИПН, G112 = 0):
#   2024, 2025 — лист «GFS dynamics» файла Excels/Fiscal_GFS2026.xlsx (КГД по ключам КБК → GFS + соцвзносы и Нацфонд);
#   2000–2022 — лист «GFS dynamics 2000-2023» файла Excels/Fiscal_GFS2026.xlsx (МВФ GFS S13 как есть, G112 = 0, к G1111 прибавлен соцналог КБК 103101 по КГД, ВВП БНС);
#               листья, которых нет в дереве (гранты иностранных правительств G13FG/G13KFG), — из IMF_GFS CSV, S13.
#   2023 — существующий KAZ_ipn (МВФ 2023, соцналог по КГД → ИПН), переименовывается в KAZ_ipn_2023; 2026 — alt2026 как есть.
# Метод как у KAZ_2026: остальные 96 стран и их связи без изменений; у узла года рёбра ко всем странам с близостью >= порога
# варианта (самое сильное помечено как MST; если выше порога никого нет — одно самое сильное ребро); позиция — среднее соседей;
# кластер — голосование Louvain на 9 сидах (через базовые кластеры соседей по сообществу).
# Если в точке «среднее соседей» уже стоит другая страна (ближе CLEAR, напр. единственный сосед), узел сдвигается
# в ближайшую свободную точку вокруг неё (place); тот же сдвиг применяется к KAZ_ipn_2023 и KAZ_2026 во всех вариантах.
# Запуск из папки Fiscal: python site/build/mk_platform_years.py . 2000-2022 2024 2025
import sys, io, json, numpy as np, pandas as pd, networkx as nx, openpyxl
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
F = sys.argv[1]
YEARS = []
for a in sys.argv[2:] or ["2000-2022", "2024", "2025"]:
    lo, _, hi = a.partition("-"); YEARS += list(range(int(lo), int(hi or lo) + 1))
J = F + "/site/platform_data.json"; d = json.load(open(J, encoding="utf-8")); items = list(d["items"])

# ---- KAZ_ipn -> KAZ_ipn_2023 (идемпотентно; mk_platform_data.py создаёт KAZ_ipn) ----
OLD, NEW = "KAZ_ipn", "KAZ_ipn_2023"
if OLD in d["meta"]:
    d["meta"][NEW] = d["meta"].pop(OLD); d["cty"][NEW] = d["cty"].pop(OLD)
    d["meta"][NEW].update({"label": "Казахстан 2023 (соцналог → ИПН)", "note": "МВФ GFS 2023, соцналог по КГД перенесён в ИПН."})
    for var in d["variants"]:
        a = var.get("alt")
        if not a: continue
        for n in a["nodes"]:
            if n["id"] == OLD: n["id"] = NEW
        for l in a["links"]:
            if l["source"] == OLD: l["source"] = NEW
            if l["target"] == OLD: l["target"] = NEW


def header_cols(ws, row=2):
    return {str(ws.cell(row, c).value).strip(): openpyxl.utils.get_column_letter(c) for c in range(1, ws.max_column + 1) if ws.cell(row, c).value is not None}


# ---- источник 1: «GFS dynamics» (2024, 2025) ----
gv = openpyxl.load_workbook(F + "/Excels/Fiscal_GFS2026.xlsx", data_only=True)["GFS dynamics"]
gf = openpyxl.load_workbook(F + "/Excels/Fiscal_GFS2026.xlsx")["GFS dynamics"]
HG = header_cols(gf)
def gcell(a):
    v = gv[a].value
    if v is None and isinstance(gf[a].value, (int, float)): v = gf[a].value
    if v is None and isinstance(gf[a].value, str) and gf[a].value.startswith("="):
        raise SystemExit(f"GFS dynamics {a}: формула без сохранённого значения — откройте и сохраните файл в Excel")
    return v
def vec_sheet(y):
    col, gdp = HG[f"янв-дек {y}"], float(gcell(HG[f"% ВВП {y}"] + "1")); vec = pd.Series(0.0, index=items)
    for r in range(3, gf.max_row + 1):
        code = gf[f"{HG['Код GFS']}{r}"].value
        if code and str(code).endswith("_T") and code[:-2] in items:
            val = gcell(f"{col}{r}")
            if isinstance(val, (int, float)): vec[code[:-2]] = val / gdp * 100
    return vec, f"КГД {y} по ключам КБК → GFS, соцналог в ИПН."

# ---- источник 2: МВФ 2000–2022 ----
HIST = "GFS dynamics 2000-2023"            # лист в Excels/Fiscal_GFS2026.xlsx
hw = openpyxl.load_workbook(F + "/Excels/Fiscal_GFS2026.xlsx", data_only=True)[HIST]; HH = header_cols(hw)
# заголовки строки 2: год (числом или текстом) встречается дважды — первая колонка суммы, вторая доли ВВП (ВВП в строке 1);
# старый вариант заголовков «% ВВП <год>» тоже поддерживается
YCOL = {}
for c_ in range(1, hw.max_column + 1):
    h_ = str(hw.cell(2, c_).value).strip().replace("% ВВП ", "%")
    if h_.lstrip("%").isdigit():
        y_ = int(h_.lstrip("%")); L_ = openpyxl.utils.get_column_letter(c_)
        if h_.startswith("%") or y_ in YCOL: YCOL.setdefault(y_, [None, None])[1] = L_
        else: YCOL[y_] = [L_, None]
imf = None
def vec_imf(y):
    global imf
    if y not in YCOL or not all(YCOL[y]): return None, None
    col = YCOL[y][0]; gdp = hw[YCOL[y][1] + "1"].value
    vals = {hw[f"{HH['Код GFS']}{r}"].value: hw[f"{col}{r}"].value for r in range(3, hw.max_row + 1)}
    if not gdp or vals.get("G1_T") in (None, ""): return None, None
    vec = pd.Series(0.0, index=items)
    for i in items:
        v = vals.get(i + "_T")
        if v is None and i + "_T" not in vals:      # лист вне дерева — из CSV МВФ
            if imf is None:
                c = pd.read_csv(F + "/IMF_GFS/IMF.STA_GFS_SOO_XDC_allsectors.csv", low_memory=False)
                imf = c[(c.COUNTRY == "KAZ") & (c.SECTOR == "S13")].pivot_table(index="INDICATOR", columns="TIME_PERIOD", values="OBS_VALUE", aggfunc="sum") / 1e9
            v = imf.loc[i + "_T", y] if (i + "_T" in imf.index and y in imf.columns) else None
            v = None if v is None or pd.isna(v) else float(v)
        if isinstance(v, (int, float)): vec[i] = v / gdp * 100
    vec["G112"] = 0.0
    return vec, f"МВФ GFS {y}; G112 = 0, соцналог КБК 103101 (КГД) в ИПН."

CLEAR = 210   # мин. расстояние (в координатах раскладки) от узла КАЗ до любой другой страны с запасом под подпись; медиана до ближайшего соседа ~190
def place(x0, y0, others):
    P = np.array(others, dtype=float)
    def clear(x, y): return np.sqrt(((P - [x, y]) ** 2).sum(1)).min()
    if clear(x0, y0) >= CLEAR: return round(x0), round(y0)
    for r in np.arange(CLEAR, 4 * CLEAR + 1, CLEAR / 4):
        pts = [(x0 + r * np.cos(a), y0 + r * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 72, endpoint=False)]
        ok = [(clear(x, y), x, y) for x, y in pts if clear(x, y) >= CLEAR]
        if ok: _, x, y = max(ok); return round(x), round(y)
    return round(x0), round(y0)

RS = 20261029; SEEDS = [RS] + list(range(8))
v = next(x for x in d["variants"] if x["key"] == "bc_gdp"); thr = v["thr"]
ids = [n["id"] for n in v["nodes"]]; node = {n["id"]: n for n in v["nodes"]}
X = pd.DataFrame({c: d["cty"][c]["gdp"] for c in ids}).T[items].astype(float).clip(lower=0)
base_cl = pd.Series({n["id"]: n["cl"] for n in v["nodes"]})
for y in YEARS:
    vec, note = vec_sheet(y) if f"янв-дек {y}" in HG else vec_imf(y)
    if vec is None:
        print(f"KAZ_{y}: нет данных — пропущен"); continue
    kid = f"KAZ_{y}"; vec["G112"] = 0.0
    k = vec.clip(lower=0).values
    sims = pd.Series({c: 2 * np.minimum(k, X.loc[c].values).sum() / (k.sum() + X.loc[c].values.sum()) for c in ids if c != "KAZ"}).sort_values(ascending=False)
    nb = sims[sims >= thr]; nb = nb if len(nb) else sims.head(1)
    top = sims.index[0]
    klinks = [{"source": kid, "target": c, "sim": round(float(s), 4), "mst": c == top, "below": bool(s < thr)} for c, s in nb.items()]
    links = [l for l in v["links"] if "KAZ" not in (l["source"], l["target"])] + klinks
    G = nx.Graph()
    for l in links: G.add_edge(l["source"], l["target"], sim=l["sim"])
    votes = []
    for sd in SEEDS:
        ck = next(c for c in nx.community.louvain_communities(G, weight="sim", seed=sd) if kid in c)
        votes.append(int(base_cl.reindex([c for c in ck if c != kid]).dropna().value_counts().idxmax()))
    vc = pd.Series(votes).value_counts(); cl = int(vc.idxmax()); vote_txt = ", ".join(f"кластер {a}: {b} из {len(votes)}" for a, b in vc.items())
    part = base_cl.drop("KAZ").to_dict(); part[kid] = cl
    mod = nx.community.modularity(G, [set(c for c, x in part.items() if x == k_) for k_ in sorted(set(part.values()))], weight="sim")
    others = [n for n in v["nodes"] if n["id"] != "KAZ"]
    kx, ky = place(np.mean([node[c]["x"] for c in nb.index]), np.mean([node[c]["y"] for c in nb.index]), [(n["x"], n["y"]) for n in others])
    nodes = others + [{"id": kid, "x": kx, "y": ky, "cl": cl, "strength": round(float(nb.sum()), 3), "deg": len(nb)}]
    st = dict(v["stats"]); st["рёбер"] = len(links); st["модулярность"] = round(mod, 3)
    v[f"alt{y}"] = {"nodes": nodes, "links": links, "stats": st, "kaz_cluster": cl, "kaz_votes": vote_txt,
                    "kaz_neighbours": [[c, round(float(s), 3)] for c, s in nb.items()],
                    "wlo": round(float(min(l["sim"] for l in links)), 4), "whi": round(float(max(l["sim"] for l in links)), 4)}
    m = dict(d["meta"]["KAZ"]); m.update({"label": f"Казахстан {y}", "year": y, "g1": round(float(vec.sum()), 2),
             "note": note + (" Соцвзносы G12 не заполнены." if vec["G1212"] == 0 and y >= 2024 else "")})
    d["meta"][kid] = m
    d["cty"][kid] = {"gdp": {i: round(float(vec[i]), 4) for i in items}}
    print(f"{kid}: доходы {vec.sum():.1f} % ВВП; кластер {cl} ({vote_txt}); соседи {[(c, round(s, 3)) for c, s in nb.items()]}")
# сдвиг KAZ_ipn_2023 / KAZ_2026, построенных другими скриптами, если они легли на чужой узел
for var in d["variants"]:
    for key in ("alt", "alt2026"):
        a = var.get(key)
        if not a: continue
        kn = next(n for n in a["nodes"] if n["id"].startswith("KAZ_"))
        kn["x"], kn["y"] = place(kn["x"], kn["y"], [(n["x"], n["y"]) for n in a["nodes"] if n is not kn])
json.dump(d, open(J, "w", encoding="utf-8"), ensure_ascii=False)
print("json записан")
