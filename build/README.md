# Сборка платформы Fiscal_network_97_platform.html

Python 3.10: C:/Users/Elina/AppData/Local/Programs/Python/Python310/python.exe. Запускать из папки Fiscal (пути в скриптах относительные к ней).

1. `mk_platform_data.py` — собирает `site/platform_data.json`.
   Аргументы: `<Fiscal> <Fiscal_network_97_lastyear.xlsx> <Fiscal_leaves_filled_2025USD.xlsx> <Fiscal_RCA_G1base_97_lastyear.xlsx> <wc_map.json>`
   (если файлы открыты в Excel — передавать копии). Вход: листы «cosВВП % ВВП», «bcВВП/bcG1/cos близость стран», «bcВВП Страны» сети; «USD 2025», «% G1» денежного файла; «Статьи» RCA; позиции узлов из `site/data_Fiscal_network_97_lastyear_*.txt`.
   Делает базовую сеть (3 варианта) и режим KAZ_ipn (alt). Режим KAZ_2026 (alt2026) этот скрипт НЕ делает — он добавлен другим сборщиком; при пересборке json этим скриптом alt2026 пропадёт.
2. `mk_platform_html.py` — склеивает html: шапка из `Fiscal_network_2023_viz.html` + `platform_body.html` (шаблон тела, синхронизирован с живой версией, включая KAZ_2026 и фильтр Самоа/Косово) + json.
   Аргументы: `<Fiscal> <папка с platform_body.html>`.
3. `apply_hide.py` — если html пересобрали без фильтра, накладывает его заново: скрывает WSM и KOS в сети, карте, поиске, легенде.
   Аргументы: `<папка build> <Fiscal>`.

4. `mk_platform_years.py` — узлы Казахстана по годам (alt<год>), только вариант «% ВВП» (bc_gdp); на странице — выпадающий список 2000–2026.
   2024–2025 — лист «GFS dynamics» (`Excels/Fiscal_GFS2026.xlsx`); 2000–2022 — `Excels/Fiscal_GFS_dynamics_2000_2023.xlsx` (МВФ S13, G112 → G1111);
   2023 — KAZ_ipn, скрипт переименовывает его в KAZ_ipn_2023; 2026 — alt2026 как есть. 2005–2009 у МВФ нет — пропускаются.
   Метод: остальные страны и связи без изменений, у узла года рёбра ко всем странам выше порога, кластер — Louvain на 9 сидах.
   Аргументы: `<Fiscal> 2000-2022 2024 2025`. Запускать после `mk_platform_data.py` (тот стирает alt-узлы), затем `mk_platform_html.py`.
   Колонки листов ищутся по заголовкам строки 2. Если в листе формулы без сохранённых значений — открыть и сохранить файл в Excel.
Пример (из папки Fiscal):
```
PY="C:/Users/Elina/AppData/Local/Programs/Python/Python310/python.exe"
"$PY" site/build/mk_platform_years.py . 2000-2022 2024 2025
"$PY" site/build/mk_platform_html.py . site/build
"$PY" site/build/apply_hide.py site/build .
```
