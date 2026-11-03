# -*- coding: utf-8 -*-
import sys, io, json; sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
F, S = sys.argv[1], sys.argv[2]
old = open(F + "/Fiscal_network_2023_viz.html", encoding="utf-8").read()
head = old[:old.index("</head>") + len("</head>\n")]
EXTRA_CSS = """    .viz-col { display: flex; flex-direction: column; gap: 8px; min-height: 0; min-width: 0; }
    .viz-col .viz-card { flex: 1 1 auto; min-height: 0; padding: 40px 48px; }
    .viz-col #viz { width: 100%; height: 100%; }
    .viz-col #viz svg { overflow: visible; }
    .viz-foot { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex: 0 0 auto; }
    .viz-foot .viz-hint, .viz-foot .viz-status { position: static; max-width: none; pointer-events: auto; }
    .viz-col #map { width: 100%; height: 100%; position: relative; }
    .viz-col #map svg { width: 100%; height: 100%; display: block; overflow: visible; }
    #map .land { fill: var(--node-muted); fill-opacity: .35; stroke: var(--border); stroke-width: .5px; }
    #map .map-label { font-family: "Space Grotesk", system-ui, sans-serif; font-weight: 600; paint-order: stroke; stroke-width: 2.4px; pointer-events: none; }
    .map-tip { position: fixed; z-index: 50; max-width: 360px; padding: 10px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--card); color: var(--fg); box-shadow: var(--shadow); font-size: 12px; pointer-events: none; }
    .map-tip b { display: block; font-size: 13.5px; margin-bottom: 3px; }
    .sidebar { overflow: auto; }
    .sidebar > .card.detail.flexy { flex: 0 0 auto; min-height: 0; }
    .sidebar > .card.detail.flexy .detail-body { max-height: 62vh; overflow: auto; }
    .sidebar-right > .card.flexy { flex: 0 0 auto; }
    .sidebar-right > .card.flexy .legend-list { max-height: 48vh; overflow: auto; }
    .stats-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px; margin: 10px 0 0; }
    .stats-grid .metric { padding: 6px 8px; } .stats-grid .metric-label { font-size: 9px; } .stats-grid .metric-value { font-size: 13px; }
    .stats-grid > .metric:last-child:nth-child(odd) { grid-column: auto; }
    @media (max-width: 1100px) { .viz-col .viz-card { min-height: 70vh; } .viz-foot { flex-wrap: wrap; } }
  </style>"""
head = head.replace("  </style>", EXTRA_CSS, 1)
D3PLUS = '<script src="https://cdn.jsdelivr.net/npm/d3plus@2"></script>'
head = head.replace(D3PLUS, D3PLUS + '\n  <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>\n  <script src="https://cdn.jsdelivr.net/npm/topojson-client@3.1.0/dist/topojson-client.min.js"></script>')
head = head.replace("<title>Сеть стран по доходам госсектора — Desht</title>", "<title>Сеть стран по доходам госсектора, 97 стран — Desht</title>")
body = open(S + "/platform_body.html", encoding="utf-8").read()
data = json.load(open(F + "/site/platform_data.json", encoding="utf-8"))
html = head + body.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
open(F + "/site/Fiscal_network_97_platform.html", "w", encoding="utf-8").write(html); print("записано", len(html) // 1024, "KB")
