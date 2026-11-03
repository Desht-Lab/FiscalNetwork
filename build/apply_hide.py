# -*- coding: utf-8 -*-
import sys, re; S, F = sys.argv[1], sys.argv[2]; p = F + "/site/Fiscal_network_97_platform.html"; t = open(p, encoding="utf-8").read()
if "const HIDE" in t: print("фильтр уже стоит"); sys.exit()
reps = [
 ("      const nodes = src.nodes.map((d) => { const m = DATA.meta[d.id];", "      const nodes = src.nodes.filter((d) => !HIDE.has(d.id)).map((d) => { const m = DATA.meta[d.id];"),
 ("      state.allLinks = src.links.map((l) =>", "      state.allLinks = src.links.filter((l) => !HIDE.has(l.source) && !HIDE.has(l.target)).map((l) =>"),
 ("      state.clusterMeta = v.clusters.map((c) => ({ id: c.id, name: c.name, color: c.color, count: c.n, g1: c.g1 }));", "      state.clusterMeta = v.clusters.map((c) => ({ id: c.id, name: c.name, color: c.color, count: nodes.filter((n) => n.cluster === c.id).length, g1: c.g1 }));"),
 ('    const KZ_IDS = { "": "KAZ", ipn: "KAZ_ipn", "2026": "KAZ_2026" };', '    const HIDE = new Set(["WSM", "KOS"]);   // Самоа и Косово не показываются ни в сети, ни на карте, ни в поиске\n    const KZ_IDS = { "": "KAZ", ipn: "KAZ_ipn", "2026": "KAZ_2026" };'),
 ("IMF GFS, S13, 54 листа, последний доступный год · 97 стран · ", "IMF GFS, S13, 54 листа, последний доступный год · 95 стран (без Самоа и Косово) · "),
 ("      state.clusterMeta.forEach((c) => {\n        const btn = document.createElement(\"button\");", "      state.clusterMeta.filter((c) => c.count > 0).forEach((c) => {\n        const btn = document.createElement(\"button\");"),
 ('document.getElementById("cluster-count").textContent = "· " + state.clusterMeta.length;', 'document.getElementById("cluster-count").textContent = "· " + state.clusterMeta.filter((c) => c.count > 0).length;'),
]
for a, b in reps:
    assert a in t, a[:60]; t = t.replace(a, b, 1)
open(p, "w", encoding="utf-8").write(t)
body = t[t.index("<body>"):]; body = re.sub(r"const DATA = \{.*?\};\n", "const DATA = __DATA__;\n", body, count=1, flags=re.S); open(S + "/platform_body.html", "w", encoding="utf-8").write(body); print("фильтр наложен")
