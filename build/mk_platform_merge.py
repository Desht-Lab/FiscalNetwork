# -*- coding: utf-8 -*-
# Склеивает две страницы в одну платформу с переключателем «Доходы / Расходы»:
#   доходы  — site/Fiscal_network_97_platform.html (IMF GFS, 54 листа);
#   расходы — site_cofog/Fiscal_COFOG_network_platform.html (IMF GFS COFOG, 10 разделов; узлы Казахстана по годам
#             добавляет site/build/mk_cofog_years.py).
# Результат: site/Fiscal_platform.html. Код страницы один (от страницы доходов), данных два набора; раздел выбирается
# параметром адреса ?p=rev | ?p=exp, переключатель в шапке перезагружает страницу с другим параметром.
# Исходные страницы не меняются. Запуск из папки Fiscal: python site/build/mk_platform_merge.py .
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
F = sys.argv[1]
REV = F + "/site/Fiscal_network_97_platform.html"; EXP = F + "/site_cofog/Fiscal_COFOG_network_platform.html"; OUT = F + "/site/Fiscal_platform.html"

def split(path):
    L = open(path, encoding="utf-8").read().split("\n")
    i = next(i for i, l in enumerate(L) if l.lstrip().startswith("const DATA = "))
    return L, i, L[i].strip()[len("const DATA = "):].rstrip(";")
L, iD, rev = split(REV); _, _, exp = split(EXP)
json.loads(rev); json.loads(exp)

TXT = {
    "rev": {"title": "Сеть стран по доходам госсектора, 97 стран — Desht", "brand": "Сеть стран по доходам госсектора",
            "sub": "IMF GFS, S13, 54 листа, последний доступный год · 97 стран · ",
            "yearLabel": "<b>Год</b> (соцналог → ИПН)",
            "yearHint": "2023 = KAZ_ipn_2023 (МВФ GFS 2023). Кроме 2023 и 2026 — только в варианте «% ВВП».",
            "legendHint": "Louvain на графе варианта. Медиана доходов сектора госуправления, % ВВП. Клик — подсветить сообщество и открыть описание. Номера сообществ между вариантами не сопоставлены.",
            "itemsHead": "Статьи · % ВВП (в скобках % доходов)", "itemCol": "статья", "Cap": "Доходы", "low": "доходы"},
    "exp": {"title": "Сеть стран по расходам госсектора (COFOG), 72 страны — Desht", "brand": "Сеть стран по расходам госсектора: функции (COFOG)",
            "sub": "IMF GFS COFOG, S13, 10 разделов, последний доступный год · 72 страны · ",
            "yearLabel": "<b>Год</b>",
            "yearHint": "2010–2023 — МВФ GFS COFOG, 2024 — анкета Минфина, 2025–2026 — оценка по отчётам Минфина (Fiscal_COFOG_verification.xlsx, лист «Итог с поправками»). Остальные страны — последний доступный год.",
            "legendHint": "Louvain на графе варианта. Медиана расходов сектора госуправления, % ВВП. Клик — подсветить сообщество и открыть описание. Номера сообществ между вариантами не сопоставлены.",
            "itemsHead": "Разделы COFOG · % ВВП (в скобках % расходов)", "itemCol": "раздел", "Cap": "Расходы", "low": "расходы"},
}
L[iD] = ("    const PAGES = { rev: " + rev + ", exp: " + exp + " };\n"
         '    const PAGE = new URLSearchParams(location.search).get("p") === "exp" ? "exp" : "rev"; const EXP = PAGE === "exp";\n'
         "    const DATA = PAGES[PAGE];\n"
         "    const T = " + json.dumps(TXT, ensure_ascii=False) + "[PAGE];\n"
         '    document.title = T.title; document.querySelector(".brand-title").textContent = T.brand;\n'
         '    document.getElementById("kaz-year-label").innerHTML = T.yearLabel; document.getElementById("kaz-year-hint").textContent = T.yearHint; document.getElementById("legend-hint").textContent = T.legendHint;\n'
         '    document.getElementById("page-" + PAGE).classList.add("on");')
s = "\n".join(L)

def rep(old, new, n=1):
    global s
    c = s.count(old)
    if c != n: raise SystemExit(f"фрагмент найден {c} раз вместо {n}: {old[:100]}")
    s = s.replace(old, new)

# --- разметка ---
rep('<title>Сеть стран по доходам госсектора, 97 стран — Desht</title>', '<title>Сеть стран по доходам и расходам госсектора — Desht</title>')
rep('    .mode-switch { display: flex; gap: 6px; }', '    .mode-switch { display: flex; gap: 6px; }\n    #page-switch { margin-left: 16px; } #page-switch .pill-btn { text-decoration: none; }')
BR = ('          <div class="brand-sub" id="brand-sub">IMF GFS, S13, 54 листа, последний доступный год · 95 стран (без Самоа и Косово) · MST + рёбра выше порога · Louvain · Desht</div>\n'
      '        </div>\n      </div>\n')
rep(BR, BR.replace("IMF GFS, S13, 54 листа, последний доступный год · 95 стран (без Самоа и Косово) · MST + рёбра выше порога · Louvain · Desht", "") +
    '      <div class="mode-switch" id="page-switch" title="Раздел платформы"><a class="pill-btn" id="page-rev" href="?p=rev">Доходы</a><a class="pill-btn" id="page-exp" href="?p=exp">Расходы</a></div>\n')
rep('<span><b>Год</b> (соцналог → ИПН)</span>', '<span id="kaz-year-label"><b>Год</b></span>')
rep('<div class="field-hint" style="margin-top:4px">2023 = KAZ_ipn_2023 (МВФ GFS 2023). Кроме 2023 и 2026 — только в варианте «% ВВП».</div>', '<div class="field-hint" style="margin-top:4px" id="kaz-year-hint"></div>')
rep('<div class="field-hint">' + TXT["rev"]["legendHint"] + '</div>', '<div class="field-hint" id="legend-hint"></div>')
# --- код ---
rep('const HIDE = new Set(["WSM", "KOS"]);', 'const HIDE = new Set(EXP ? ["WSM"] : ["WSM", "KOS"]);   // в расходах Косово показывается: через него идёт мост MST к Узбекистану;')
rep('const kzId = (m) => (!m ? "KAZ" : m === "2023" ? "KAZ_ipn_2023" : "KAZ_" + m);', 'const kzId = (m) => (!m || (EXP && m === "2023") ? "KAZ" : m === "2023" ? "KAZ_ipn_2023" : "KAZ_" + m);   // в расходах 2023 — базовый узел KAZ')
rep('const altKey = (m) => (!m ? "" : m === "2023" ? "alt" : "alt" + m);', 'const altKey = (m) => (!m || (EXP && m === "2023") ? "" : m === "2023" ? "alt" : "alt" + m);')
rep('if (v[altKey(String(y))]) ys.push(y);', 'if ((EXP && y === 2023) || v[altKey(String(y))]) ys.push(y);')
rep('if (!v[altKey(state.kazMode)]) state.kazMode = "2023";', 'if (!ys.includes(+state.kazMode)) state.kazMode = "2023";')
rep("(state.kazMode ? '<div class=\"metric\" style=\"grid-column:1/-1\">", "(ALT(v) !== v ? '<div class=\"metric\" style=\"grid-column:1/-1\">")
rep('document.getElementById("brand-sub").textContent = "IMF GFS, S13, 54 листа, последний доступный год · 97 стран · " + v.title', 'document.getElementById("brand-sub").textContent = T.sub + v.title')
rep("'<div class=\"detail-sub\">Статьи · % ВВП (в скобках % доходов)</div>'", "'<div class=\"detail-sub\">' + T.itemsHead + '</div>'")
rep("<span class=\"emp-name\">статья</span>'", "<span class=\"emp-name\">' + T.itemCol + '</span>'")
rep('"Доходы " + fmt1(n.g1)', 'T.Cap + " " + fmt1(n.g1)', 2)
rep("<div class=\"metric-label\">Доходы, % ВВП</div>", "<div class=\"metric-label\">' + T.Cap + ', % ВВП</div>")
rep("' стран · доходы ' + fmt1(c.g1)", "' стран · ' + T.low + ' ' + fmt1(c.g1)")
rep("<span class=\"legend-meta\">доходы ' + fmt1(c.g1)", "<span class=\"legend-meta\">' + T.low + ' ' + fmt1(c.g1)")
rep("<span class=\"opt-sub\">доходы ' + fmt1(it.g1)", "<span class=\"opt-sub\">' + T.low + ' ' + fmt1(it.g1)")
rep('const lab = nodes.filter((n) => state.labelIds.has(n.id)).map(', 'const lab = (EXP ? [] : nodes.filter((n) => state.labelIds.has(n.id))).map(')

open(OUT, "w", encoding="utf-8", newline="\n").write(s)
print("записано:", OUT, f"{len(s.encode('utf-8')) / 1e6:.2f} МБ")
