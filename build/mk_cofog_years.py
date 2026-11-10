# -*- coding: utf-8 -*-
# Добавляет в site_cofog/Fiscal_COFOG_network_platform.html узлы Казахстана по годам (alt<год>) и ползунок года —
# по образцу site/build/mk_platform_years.py и ползунка в site/Fiscal_network_97_platform.html.
# Источник векторов: COFOG/Fiscal_COFOG_verification.xlsx, лист «Итог с поправками», 10 разделов GF01–GF10, млрд тг:
#   2010–2023 — колонка «МВФ»; 2024 — «Анкета»; 2025–2026 — «Оценка».
#   Если итог раздела в листе не посчитан (ошибка в сохранённом значении), раздел собирается как сумма статей
#   уровня 3 листа «Без поправок» + поправки листа «Поправки» (строки 6–12; перераспределение внутри здравоохранения
#   в сумме по разделу даёт ноль).
# ВВП: Excels/Fiscal_GFS2026.xlsx, лист «GFS dynamics 2000-2026», строка 1.
# 2023 год — базовый узел KAZ сети (МВФ 2023), отдельный alt не строится.
# Метод как в mk_platform_years.py: остальные страны и их связи без изменений; у узла года рёбра ко всем странам
# с близостью >= порога (если таких нет — одно самое сильное ребро); кластер — голосование Louvain на 9 сидах.
# Запуск из папки Fiscal (если xlsx открыт в Excel — передать копию):
#   python site_cofog/mk_cofog_years.py . [путь к Fiscal_COFOG_verification.xlsx] [путь к Fiscal_GFS2026.xlsx]
import sys, io, json, shutil, os, numpy as np, pandas as pd, networkx as nx, openpyxl
from openpyxl.utils import column_index_from_string as ci
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
F = sys.argv[1]
XV = sys.argv[2] if len(sys.argv) > 2 else F + "/COFOG/Fiscal_COFOG_verification.xlsx"
XG = sys.argv[3] if len(sys.argv) > 3 else F + "/Excels/Fiscal_GFS2026.xlsx"
HTML = F + "/site_cofog/Fiscal_COFOG_network_platform.html"; JSN = F + "/site_cofog/platform_data.json"
BASE_YEAR = 2023

# ---------- векторы Казахстана ----------
wv = openpyxl.load_workbook(XV, data_only=True)
it, bp, po = wv["Итог с поправками"], wv["Без поправок"], wv["Поправки"]
DIV = ["GF%02d" % i for i in range(1, 11)]
row = {it.cell(r, 1).value: r for r in range(6, it.max_row + 1)}
num = lambda v: v if isinstance(v, (int, float)) else None
def hdr_cols(ws):   # год -> [колонки] по строке 4 (год стоит над первой из двух колонок)
    out = {}
    for c in range(4, ws.max_column + 1):
        y = ws.cell(4, c).value
        if isinstance(y, int): out[y] = [c, c + 1]
    return out
ICOL, BCOL, PCOL = hdr_cols(it), hdr_cols(bp), hdr_cols(po)
def pick(ws, cols):   # колонка года, где заполнен хотя бы один раздел (МВФ, иначе анкета/оценка)
    for c in cols:
        if any(num(ws.cell(r, c).value) is not None for r in range(6, 30)) or isinstance(ws.cell(6, c).value, str): return c
    return cols[0]
def leafsum(ws, c, d):
    return sum(num(ws.cell(r, c).value) or 0 for r in range(7, ws.max_row + 1) if str(ws.cell(r, 1).value).startswith(d) and ws.cell(r, 3).value == 3)
def corr(c, d):
    return sum(num(po.cell(r, c).value) or 0 for r in range(6, 13) if str(po.cell(r, 1).value or "").startswith(d))
g = openpyxl.load_workbook(XG, data_only=True)["GFS dynamics 2000-2026"]
GDP = {g.cell(2, c).value: g.cell(1, c).value for c in range(1, g.max_column + 1) if isinstance(g.cell(2, c).value, int) and num(g.cell(1, c).value)}
KV = {}
for y, cols in sorted(ICOL.items()):
    c = pick(it, cols); src = str(it.cell(5, c).value)
    vals = {d: num(it.cell(row[d], c).value) for d in DIV}; how = ""
    if any(v is None for v in vals.values()):
        cb = pick(bp, BCOL[y]); cp = next(k for k in PCOL[y] if str(po.cell(5, k).value) == src) if y in PCOL else None
        vals = {d: leafsum(bp, cb, d) + (corr(cp, d) if cp else 0) for d in DIV}; how = " (сумма статей уровня 3)"
    if y not in GDP: print(f"{y}: нет ВВП — пропущен"); continue
    KV[y] = {"src": src, "how": how, "vec": {d: vals[d] / GDP[y] * 100 for d in DIV}}

# ---------- данные страницы ----------
L = open(HTML, encoding="utf-8").read().split("\n")
iD = next(i for i, l in enumerate(L) if l.lstrip().startswith("const DATA = "))
d = json.loads(L[iD].strip()[len("const DATA = "):].rstrip(";")); items = list(d["items"])
assert items == DIV, items
for k in [k for k in d["meta"] if k.startswith("KAZ_")]: d["meta"].pop(k); d["cty"].pop(k, None)

CLEAR = 210
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
SRC_TXT = {"МВФ": "МВФ GFS COFOG", "Анкета": "анкета GFS Минфина", "Оценка": "оценка по отчётам Минфина"}
for v in d["variants"]:
    for k in [k for k in v if k.startswith("alt")]: v.pop(k)
    if v["key"] != "bc_gdp": continue
    thr = v["thr"]; ids = [n["id"] for n in v["nodes"]]; node = {n["id"]: n for n in v["nodes"]}
    X = pd.DataFrame({c: d["cty"][c]["gdp"] for c in ids}).T[items].astype(float).clip(lower=0)
    base_cl = pd.Series({n["id"]: n["cl"] for n in v["nodes"]})
    base_nb = {l["target"] if l["source"] == "KAZ" else l["source"] for l in v["links"] if "KAZ" in (l["source"], l["target"])}
    for y, kv in KV.items():
        if y == BASE_YEAR: continue
        kid = f"KAZ_{y}"; vec = pd.Series(kv["vec"])[items]; k = vec.clip(lower=0).values
        sims = pd.Series({c: 2 * np.minimum(k, X.loc[c].values).sum() / (k.sum() + X.loc[c].values.sum()) for c in ids if c != "KAZ"}).sort_values(ascending=False)
        nb = sims[sims >= thr]; nb = nb if len(nb) else sims.head(1); top = sims.index[0]
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
        if set(nb.index) == base_nb: kx, ky = node["KAZ"]["x"], node["KAZ"]["y"]     # тот же сосед, что у базового узла, — узел остаётся на месте
        else: kx, ky = place(np.mean([node[c]["x"] for c in nb.index]), np.mean([node[c]["y"] for c in nb.index]), [(n["x"], n["y"]) for n in others])
        nodes = others + [{"id": kid, "x": kx, "y": ky, "cl": cl, "strength": round(float(nb.sum()), 3), "deg": len(nb)}]
        st = dict(v["stats"]); st["рёбер"] = len(links); st["модулярность"] = round(mod, 3)
        v[f"alt{y}"] = {"nodes": nodes, "links": links, "stats": st, "kaz_cluster": cl, "kaz_votes": vote_txt,
                        "kaz_neighbours": [[c, round(float(s), 3)] for c, s in nb.items()],
                        "wlo": round(float(min(l["sim"] for l in links)), 4), "whi": round(float(max(l["sim"] for l in links)), 4)}
        m = dict(d["meta"]["KAZ"]); tot = float(vec.sum())
        m.update({"label": f"Казахстан {y}", "year": y, "g1": round(tot, 2),
                  "note": f"{SRC_TXT.get(kv['src'], kv['src'])} {y}, лист «Итог с поправками»{kv['how']}."})
        d["meta"][kid] = m
        d["cty"][kid] = {"gdp": {i: round(float(vec[i]), 3) for i in items}, "sh": {i: round(float(vec[i] / tot * 100), 2) for i in items}}
        print(f"{kid} [{kv['src']}{kv['how']}]: расходы {tot:.1f} % ВВП; кластер {cl} ({vote_txt}); соседи {[(c, round(s, 3)) for c, s in nb.items()]}")
ys = sorted(KV); Y0, Y1 = ys[0], ys[-1]
b = KV[BASE_YEAR]["vec"]; print("2023 лист − базовый узел, п.п. ВВП:", {i: round(b[i] - d["cty"]["KAZ"]["gdp"][i], 3) for i in items})

# ---------- правки кода страницы (идемпотентно) ----------
L[iD] = "    const DATA = " + json.dumps(d, ensure_ascii=False) + ";"
s = "\n".join(L)
def rep(old, new, must=True):
    global s
    if new in s: return   # уже применено
    if old not in s:
        if must: raise SystemExit("не найден фрагмент: " + old[:90])
        return
    s = s.replace(old, new)
ticks = "".join(f"<span>{y}</span>" for y in range(Y0, Y1 + 1, 4))
SL = ('        <div class="field-hint" style="margin-top:10px"><b>Казахстан: какой год в сети</b></div>\n'
      f'        <div class="field-hint" style="display:flex;align-items:center;gap:8px;margin-top:6px"><span><b>Год</b></span><b id="kaz-year-val" style="margin-left:auto;font-variant-numeric:tabular-nums">{BASE_YEAR}</b></div>'
      f'<input id="kaz-year" type="range" min="{Y0}" max="{Y1}" step="1" value="{BASE_YEAR}" list="kaz-year-ticks" style="width:100%;margin:4px 0 0;accent-color:var(--accent, #2563eb)"><datalist id="kaz-year-ticks"></datalist>'
      f'<div class="field-hint" style="display:flex;justify-content:space-between;font-size:10px;margin-top:-2px">{ticks}</div>\n'
      f'        <div class="field-hint" style="margin-top:4px">{Y0}–2023 — МВФ GFS COFOG, 2024 — анкета Минфина, 2025–2026 — оценка по отчётам Минфина (Fiscal_COFOG_verification.xlsx, лист «Итог с поправками»). Остальные страны — последний доступный год.</div>\n')
ANCH = '        <div class="field-hint">Карта: страны закрашены в границах цветом сообщества выбранного варианта; микространы без контура — точками. Связи показываются для закреплённой страны.</div>\n'
if 'id="kaz-year"' in s:   # ползунок уже есть — заменить блок целиком
    a = s.index('        <div class="field-hint" style="margin-top:10px"><b>Казахстан: какой год в сети</b></div>'); e = s.index(ANCH)
    s = s[:a] + SL + s[e:]
else:
    rep(ANCH, SL + ANCH)
rep('kazMode: "", allNodes', f'kazMode: "{BASE_YEAR}", allNodes')
rep('const kzId = (m) => (!m ? "KAZ" : m === "2023" ? "KAZ_ipn_2023" : "KAZ_" + m);', f'const kzId = (m) => (!m || m === "{BASE_YEAR}" ? "KAZ" : "KAZ_" + m);')
rep('const altKey = (m) => (!m ? "" : m === "2023" ? "alt" : "alt" + m);', f'const altKey = (m) => (!m || m === "{BASE_YEAR}" ? "" : "alt" + m);')
rep('const ALT = (v) => (state.kazMode && v[altKey(state.kazMode)]) || v;', 'const ALT = (v) => v[altKey(state.kazMode)] || v;')
KFN = (f'    const kazYears = (v) => {{ const ys = []; for (let y = {Y0}; y <= {Y1}; y++) if (y === {BASE_YEAR} || v[altKey(String(y))]) ys.push(y); return ys; }};\n'
       f'    const kazNearest = (v, y) => {{ const ys = kazYears(v); return ys.reduce((b, a) => (Math.abs(a - y) < Math.abs(b - y) ? a : b), ys[0]); }};\n'
       '    function syncKazRadios() { const v = DATA.variants[state.v]; const sel = document.getElementById("kaz-year"); const ys = kazYears(v);\n'
       '      document.getElementById("kaz-year-ticks").innerHTML = ys.map((y) => \'<option value="\' + y + \'"></option>\').join("");\n'
       f'      if (!ys.includes(+state.kazMode)) state.kazMode = "{BASE_YEAR}"; sel.value = state.kazMode; document.getElementById("kaz-year-val").textContent = state.kazMode; }}')
rep('    function syncKazRadios() {}', KFN)
rep('state.labelIds = active ? new Set(ids) : topByValue(30); state.labelIds.add(KZ());\n',
    'state.labelIds = active ? new Set(ids) : topByValue(30); state.labelIds.add(KZ());\n'
    '      if (!active) (state.adjacency.get(KZ()) || new Set()).forEach((id) => state.labelIds.add(id));   // подписи всех соседей Казахстана в сети выбранного года\n')
rep('(state.kazMode ? \'<div class="metric" style="grid-column:1/-1"><div class="metric-label">\' + KZ()', '(ALT(v).kaz_votes ? \'<div class="metric" style="grid-column:1/-1"><div class="metric-label">\' + KZ()')
LSN = '      document.getElementById("clear-all").addEventListener("click", resetAll);\n'
rep(LSN, '      const kazApply = () => { const sel = document.getElementById("kaz-year"); const y = String(kazNearest(DATA.variants[state.v], +sel.value)); sel.value = y; document.getElementById("kaz-year-val").textContent = y; if (y === state.kazMode) return; state.kazMode = y; const pinned = state.pinned; setVariant(state.v); if (pinned && isKZ(pinned)) pinCountry(KZ(), true); };\n'
    '      document.getElementById("kaz-year").addEventListener("input", kazApply);\n'
    '      document.getElementById("kaz-year").addEventListener("change", kazApply);\n' + LSN)
s = s.replace('"Доходы " + fmt1(n.g1)', '"Расходы " + fmt1(n.g1)')   # подсказки узлов: страница про расходы

bak = HTML.replace(".html", "_before_years.html.bak")
if not os.path.exists(bak): shutil.copy2(HTML, bak)
open(HTML, "w", encoding="utf-8", newline="\r\n").write(s)   # в исходном файле окончания строк CRLF
json.dump(d, open(JSN, "w", encoding="utf-8"), ensure_ascii=False)
print("html и json записаны; копия до правки:", os.path.basename(bak))
