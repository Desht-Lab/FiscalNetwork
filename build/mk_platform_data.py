# -*- coding: utf-8 -*-
# Собирает данные платформы: 3 варианта сети (BC % ВВП p90, BC % G1 p90, cos % G1 p95) -> platform/platform_data.json
import sys, io, json, re, pandas as pd, numpy as np, networkx as nx
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
F, NETX, MONEY, RCAX = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
PL = F + "/site"
names = pd.read_excel(RCAX, "Статьи", header=2, index_col=0)["статья"]
SHORT = {"G1111": "ИПН", "G1112": "КПН", "G1113": "прочие налоги на доход", "G11411": "НДС", "G11412": "налоги с продаж", "G1142": "акцизы", "G1143": "фискальные монополии", "G1144": "налоги на услуги", "G11451": "транспортный налог", "G11452": "прочие налоги на использование", "G1146": "прочие налоги на товары", "G1151": "импортные пошлины", "G1152": "экспортные пошлины", "G1156": "прочие налоги на внешнюю торговлю", "G116": "прочие налоги", "G112": "налог на ФОТ", "G113IM": "налог на недвижимость", "G1211": "соцвзносы работников", "G1212": "соцвзносы работодателей", "G1213": "соцвзносы самозанятых", "G1411_NRES": "проценты от нерезидентов", "G1411_S1W": "проценты от резидентов", "G1412": "дивиденды", "G1413": "изъятия из квазикорпораций", "G1414I": "вменённые проценты", "G1415": "рента", "G1421": "продажи рыночных заведений", "G1422": "административные сборы", "G1423": "побочные продажи", "G1424": "вменённые продажи", "G143": "штрафы", "G1451": "текущие трансферты", "G1452": "капитальные трансферты", "G13FG": "гранты от правительств (тек.)", "G13KFG": "гранты от правительств (кап.)", "G13C_IO": "гранты МО (тек.)", "G13K_IO": "гранты МО (кап.)"}
def short(c): return SHORT.get(c, str(names.get(c, c))[:34])
P = pd.read_excel(NETX, "cosВВП % ВВП", header=2, index_col=0); items = [c for c in P.columns if str(c).startswith("G")]
PG = P[items].astype(float).fillna(0).clip(lower=0); G1 = PG.sum(axis=1); SH = PG.div(G1, axis=0) * 100
U = pd.read_excel(MONEY, "USD 2025", header=2, index_col=0).reindex(PG.index); GDP = U["ВВП, млн USD 2025"].astype(float)
Nm = pd.read_excel(NETX, "bcВВП Страны", header=2, index_col=0).reindex(PG.index); meta = Nm[["страна", "группа", "год"]]
VARIANTS = [
    ("bc_gdp", "Брей-Кёртис, % ВВП", "data_Fiscal_network_97_lastyear_bc_gdp90.txt", "bcВВП близость стран", 0.90, "2·Σmin/(Σa+Σb) по 54 листьям в % ВВП · порог p90", PG, "% ВВП"),
    ("bc_g1", "Брей-Кёртис, % доходов", "data_Fiscal_network_97_lastyear_bc_g190.txt", "bcG1 близость стран", 0.90, "2·Σmin/(Σa+Σb) по долям 54 листьев в доходах · порог p90", SH, "% доходов"),
    ("cos", "Косинус, % доходов", "data_Fiscal_network_97_lastyear_cosine95.txt", "cos близость стран", 0.95, "косинус векторов долей 54 листьев в доходах · порог p95", SH, "% доходов"),
]
WC = json.load(open(sys.argv[5], encoding="utf-8")); WC["KOS"] = WC["UNK"]
out = {"variants": [], "cty": {}, "items": {c: short(c) for c in items}, "meta": {}}
for c in PG.index:
    out["meta"][c] = {"label": str(meta.loc[c, "страна"]).strip(), "group": str(meta.loc[c, "группа"]), "year": int(meta.loc[c, "год"]), "g1": round(float(G1[c]), 2), "gdp": round(float(GDP[c]), 1), "ll": WC[c]["ll"], "n3": WC[c]["n3"]}
    out["cty"][c] = {"gdp": {k: round(float(PG.loc[c, k]), 3) for k in items}, "sh": {k: round(float(SH.loc[c, k]), 2) for k in items}}
# ---- KAZ2: соцналог по КГД (1 321,3 млрд тг за 2023) перенесён в ИПН, G112 = 0 (в GFS G112 = 1 810 = соцналог + задвоенные налоги на собственность 489) ----
GDP_KZ_BN = 119251.0; SOCTAX_BN = 1321.3; SOC_PP = SOCTAX_BN / GDP_KZ_BN * 100
PG2 = PG.loc["KAZ"].copy(); PG2["G1111"] += SOC_PP; PG2["G112"] = 0.0; L2 = PG2.sum(); SH2 = PG2 / L2 * 100
print(f"KAZ2: ИПН {PG.loc['KAZ', 'G1111']:.2f} → {PG2['G1111']:.2f} % ВВП, G112 {PG.loc['KAZ', 'G112']:.2f} → 0, сумма листьев {G1['KAZ']:.2f} → {L2:.2f}")
KAZ2 = "KAZ_ipn"
out["allmed"] = {"gdp": {k: round(float(PG[k].median()), 3) for k in items}, "sh": {k: round(float(SH[k].median()), 2) for k in items}, "g1": round(float(G1.median()), 1)}
out["meta"][KAZ2] = {"label": "Казахстан (соцналог → ИПН)", "group": "Казахстан", "year": int(meta.loc["KAZ", "год"]), "g1": round(float(L2), 2), "gdp": round(float(GDP["KAZ"]), 1), "ll": [48, 68], "n3": "398", "note": f"Соцналог по КГД 2023 ({SOCTAX_BN:.0f} млрд тг = {SOC_PP:.2f} % ВВП) добавлен к ИПН G1111, строка G112 обнулена (в GFS она 1 810 млрд: соцналог 1 321 + задвоенные налоги на собственность 489)."}
out["cty"][KAZ2] = {"gdp": {k: round(float(PG2[k]), 3) for k in items}, "sh": {k: round(float(SH2[k]), 2) for k in items}}
RS = 20261029
for key, title, txt, sheet, q, desc, X, unit in VARIANTS:
    nodes_raw = json.load(open(PL + "/" + txt, encoding="utf-8"))
    comm = {n["id"]: int(re.search(r"сообщество: (\d+)", n["title"]).group(1)) for n in nodes_raw}
    colors = {}; pos = {}
    for n in nodes_raw: colors.setdefault(comm[n["id"]], n["color"]); pos[n["id"]] = (n["x"], n["y"])
    S = pd.read_excel(NETX, sheet, header=2, index_col=0).reindex(index=PG.index, columns=PG.index).astype(float)
    iu = np.triu_indices(len(S), 1); u = S.values[iu]; thr = float(np.quantile(u, q))
    G = nx.Graph(); G.add_nodes_from(S.index)
    for i, j in zip(*iu): G.add_edge(S.index[i], S.index[j], weight=1 - S.values[i, j], sim=float(S.values[i, j]))
    mst = nx.minimum_spanning_tree(G, weight="weight"); H = mst.copy()
    for i, j in zip(*iu):
        if S.values[i, j] >= thr: H.add_edge(S.index[i], S.index[j], weight=1 - S.values[i, j], sim=float(S.values[i, j]))
    cl = pd.Series(comm); parts = [set(cl[cl == k].index) for k in sorted(cl.unique())]
    mod = nx.community.modularity(H, parts, weight="sim")
    # сверка: Louvain с тем же seed на восстановленном графе даёт ли то же разбиение
    lv = sorted(nx.community.louvain_communities(H, weight="sim", seed=RS), key=lambda c: -len(c)); lvs = pd.Series({n: k + 1 for k, c in enumerate(lv) for n in c}).reindex(cl.index)
    from sklearn.metrics import adjusted_rand_score; ari = adjusted_rand_score(cl, lvs)
    strength = {n: sum(dd["sim"] for _, _, dd in H.edges(n, data=True)) for n in H.nodes()}
    links = [{"source": a, "target": b, "sim": round(dd["sim"], 4), "mst": bool(mst.has_edge(a, b)), "below": bool(dd["sim"] < thr)} for a, b, dd in H.edges(data=True)]
    clusters = []
    for k in sorted(cl.unique()):
        mem = cl[cl == k].index.tolist(); top = X.loc[mem].mean().sort_values(ascending=False).head(4)
        prof_gdp = {c: round(float(PG.loc[mem, c].median()), 3) for c in items}; prof_sh = {c: round(float(SH.loc[mem, c].median()), 2) for c in items}
        lead = ", ".join(f"{short(c)} {top[c]:.1f}" + ("%" if unit == "% ВВП" else "%") for c in top.index[:3])
        clusters.append({"id": int(k), "color": colors[k], "n": len(mem), "g1": round(float(G1[mem].median()), 1), "gdp_pc": None, "name": f"{short(top.index[0])} + {short(top.index[1])}", "desc": f"{len(mem)} стран, медиана доходов {G1[mem].median():.1f}% ВВП. Ведущие статьи ({unit}, среднее по сообществу): {lead}.", "prof": {"gdp": prof_gdp, "sh": prof_sh}, "members": mem})
    nodes = [{"id": n, "x": pos[n][0], "y": pos[n][1], "cl": comm[n], "strength": round(strength[n], 3), "deg": H.degree(n)} for n in S.index]
    # ---- альтернативная сеть: KAZ заменён на KAZ_ipn (соцналог -> ИПН, G112 = 0); порог тот же, пересчитаны MST и рёбра ----
    Xa = X.copy(); Xa.loc["KAZ"] = (PG2 if unit == "% ВВП" else SH2)
    if key.startswith("bc"): A_ = Xa.values[:, None, :]; B_ = Xa.values[None, :, :]; Sa = 2 * np.minimum(A_, B_).sum(2) / (A_.sum(2) + B_.sum(2))
    else: n_ = np.linalg.norm(Xa.values, axis=1); Sa = Xa.values @ Xa.values.T / np.outer(n_, n_)
    np.fill_diagonal(Sa, 0); Sa = pd.DataFrame(Sa, index=Xa.index, columns=Xa.index)
    Ga = nx.Graph(); Ga.add_nodes_from(Sa.index)
    for i, j in zip(*iu): Ga.add_edge(Sa.index[i], Sa.index[j], weight=1 - Sa.values[i, j], sim=float(Sa.values[i, j]))
    msta = nx.minimum_spanning_tree(Ga, weight="weight"); Ha = msta.copy()
    for i, j in zip(*iu):
        if Sa.values[i, j] >= thr: Ha.add_edge(Sa.index[i], Sa.index[j], weight=1 - Sa.values[i, j], sim=float(Sa.values[i, j]))
    votes = []
    for seed in [RS] + list(range(8)):
        cm = nx.community.louvain_communities(Ha, weight="sim", seed=seed); ck = [c for c in cm if "KAZ" in c][0]
        votes.append(int(cl.reindex([c for c in ck if c != "KAZ"]).value_counts().idxmax()))
    vc = pd.Series(votes).value_counts(); cl_alt = int(vc.idxmax()); vote_txt = ", ".join(f"кластер {k}: {v} из {len(votes)}" for k, v in vc.items())
    stra = {n: sum(dd["sim"] for _, _, dd in Ha.edges(n, data=True)) for n in Ha.nodes()}
    KI = "KAZ_ipn"; rn = lambda c: KI if c == "KAZ" else c
    links_alt = [{"source": rn(a), "target": rn(b), "sim": round(dd["sim"], 4), "mst": bool(msta.has_edge(a, b)), "below": bool(dd["sim"] < thr)} for a, b, dd in Ha.edges(data=True)]
    nbs = list(Ha.neighbors("KAZ")); kx = round(float(np.mean([pos[c][0] for c in nbs]))); ky = round(float(np.mean([pos[c][1] for c in nbs])))   # KAZ_ipn ставится в среднюю точку своих соседей по сети
    nodes_alt = [{"id": rn(n), "x": (kx if n == "KAZ" else pos[n][0]), "y": (ky if n == "KAZ" else pos[n][1]), "cl": (cl_alt if n == "KAZ" else comm[n]), "strength": round(stra[n], 3), "deg": Ha.degree(n)} for n in Sa.index]
    nbk = sorted(((c, round(float(Sa.loc["KAZ", c]), 3)) for c in Ha.neighbors("KAZ")), key=lambda x: -x[1])
    stats_alt = {"пар": int(len(u)), "медиана": round(float(np.median(Sa.values[iu])), 3), "порог": round(thr, 3), "макс": round(float(Sa.values[iu].max()), 3), "пар ≥ порога": int((Sa.values[iu] >= thr).sum()), "рёбер": Ha.number_of_edges(), "MST ниже порога": int(sum(1 for _, _, dd in msta.edges(data=True) if dd["sim"] < thr)), "сообществ": int(cl.nunique()), "модулярность": round(nx.community.modularity(Ha, [set(cl[cl == k].index) for k in sorted(cl.unique())], weight="sim"), 3)}
    alt = {"nodes": nodes_alt, "links": links_alt, "stats": stats_alt, "kaz_cluster": cl_alt, "kaz_votes": vote_txt, "kaz_neighbours": nbk, "wlo": round(float(min(l["sim"] for l in links_alt)), 4), "whi": round(float(max(l["sim"] for l in links_alt)), 4)}
    print(f"   KAZ_ipn [{key}]: соседи {nbk[:6]}; кластер {cl_alt} (у KAZ {comm['KAZ']}; голоса: {vote_txt}); рёбер {Ha.number_of_edges()} vs {H.number_of_edges()}")
    out["variants"].append({"key": key, "title": title, "desc": desc, "unit": unit, "thr": round(thr, 4), "q": q, "nodes": nodes, "links": links, "clusters": clusters, "alt": alt,
        "stats": {"пар": int(len(u)), "медиана": round(float(np.median(u)), 3), "порог": round(thr, 3), "макс": round(float(u.max()), 3), "пар ≥ порога": int((u >= thr).sum()), "рёбер": H.number_of_edges(), "MST ниже порога": int(sum(1 for _, _, dd in mst.edges(data=True) if dd["sim"] < thr)), "сообществ": int(cl.nunique()), "модулярность": round(mod, 3)},
        "wlo": round(float(min(l["sim"] for l in links)), 4), "whi": round(float(max(l["sim"] for l in links)), 4)})
    print(f"{key}: порог {thr:.3f}, рёбер {H.number_of_edges()}, сообществ {cl.nunique()}, модулярность {mod:.3f}, ARI(txt vs Louvain на восстановленном графе) {ari:.2f}, MST ниже порога {sum(1 for _, _, dd in mst.edges(data=True) if dd['sim'] < thr)}")
json.dump(out, open(PL + "/platform_data.json", "w", encoding="utf-8"), ensure_ascii=False)
print("json записан, размер", len(json.dumps(out, ensure_ascii=False)) // 1024, "KB")
