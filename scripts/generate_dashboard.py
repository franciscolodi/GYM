#!/usr/bin/env python3
"""
Lee data/gym_sessions.csv y genera dist/index.html con un dashboard
de gráficos y reporte. Pensado para correr desde GitHub Actions
y publicarse en GitHub Pages.
"""
import csv
import json
import os
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT, "data", "gym_sessions.csv")
DIST_DIR = os.path.join(ROOT, "dist")
OUT_PATH = os.path.join(DIST_DIR, "index.html")


def load_sessions():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]
    rows.sort(key=lambda r: r["date"])
    return rows


TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Reporte de Gym</title>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.4/chart.umd.min.js" crossorigin="anonymous"></script>
<style>
  :root {{
    --bg: #f5f6f8; --card-bg: #ffffff; --text: #14161a; --text-muted: #6b7280;
    --accent: #ff5a36; --accent-2: #2563eb; --border: #e5e7eb;
    --green: #16a34a; --yellow: #eab308; --purple: #8b5cf6;
    box-sizing: border-box;
    padding-top: env(safe-area-inset-top, 0px);
    padding-bottom: env(safe-area-inset-bottom, 0px);
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --bg: #0f1115; --card-bg: #1a1d23; --text: #f3f4f6;
      --text-muted: #9ca3af; --border: #2a2d34;
    }}
  }}
  :root[data-theme="dark"] {{
    --bg: #0f1115; --card-bg: #1a1d23; --text: #f3f4f6;
    --text-muted: #9ca3af; --border: #2a2d34;
  }}
  html {{ scroll-padding-top: env(safe-area-inset-top, 0px); }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    -webkit-font-smoothing: antialiased;
  }}
  header {{ padding: 28px 20px 16px; max-width: 860px; margin: 0 auto; display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }}
  header h1 {{ font-size: 1.5rem; margin: 0 0 4px; letter-spacing: -0.02em; }}
  header p {{ margin: 0; color: var(--text-muted); font-size: 0.85rem; }}
  .theme-btn {{ background: var(--card-bg); border: 1px solid var(--border); color: var(--text); border-radius: 10px; padding: 8px 12px; cursor: pointer; font-size: 0.85rem; }}
  main {{ max-width: 860px; margin: 0 auto; padding: 0 16px 40px; }}
  .toolbar {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; background: var(--card-bg); border: 1px solid var(--border); border-radius: 14px; padding: 12px 14px; margin: 8px 0 18px; }}
  .toolbar label {{ font-size: 0.8rem; color: var(--text-muted); }}
  .toolbar select, .toolbar input {{ background: var(--bg); color: var(--text); border: 1px solid var(--border); border-radius: 8px; padding: 6px 8px; font-size: 0.85rem; }}
  .toolbar button {{ background: var(--accent-2); color: #fff; border: 0; border-radius: 8px; padding: 7px 12px; font-size: 0.85rem; cursor: pointer; }}
  .toolbar button.ghost {{ background: transparent; color: var(--text); border: 1px solid var(--border); }}
  .stats-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 16px 0 18px; }}
  @media (min-width: 480px) {{ .stats-grid {{ grid-template-columns: repeat(4, 1fr); }} }}
  .stat-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 14px; padding: 14px; }}
  .stat-card .value {{ font-size: 1.4rem; font-weight: 700; color: var(--accent); }}
  .stat-card .label {{ font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }}
  .card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 18px; margin-bottom: 18px; }}
  .card h2 {{ font-size: 1rem; margin: 0 0 12px; }}
  .chart-wrap {{ position: relative; width: 100%; height: 260px; }}
  .chart-wrap.tall {{ height: 320px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
  th, td {{ text-align: left; padding: 8px 6px; border-bottom: 1px solid var(--border); white-space: nowrap; }}
  th {{ color: var(--text-muted); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; }}
  .table-scroll {{ overflow-x: auto; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px; background: rgba(37,99,235,0.12); color: var(--accent-2); font-size: 0.7rem; font-weight: 600; }}
  .badge.ok {{ background: rgba(22,163,74,0.14); color: var(--green); }}
  .badge.warn {{ background: rgba(234,179,8,0.16); color: #a16207; }}
  .badge.bad {{ background: rgba(239,68,68,0.14); color: #dc2626; }}
  footer {{ text-align: center; color: var(--text-muted); font-size: 0.75rem; padding: 10px 0 20px; }}
  .insights {{ list-style: none; padding: 0; margin: 0; display: grid; gap: 8px; }}
  .insights li {{ background: var(--bg); border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; font-size: 0.85rem; }}
  .heatmap {{ display: grid; grid-auto-flow: column; grid-template-rows: repeat(7, 12px); gap: 3px; overflow-x: auto; padding-bottom: 6px; }}
  .heatmap .cell {{ width: 12px; height: 12px; border-radius: 3px; background: var(--border); }}
  .heatmap .cell.l1 {{ background: rgba(255,90,54,0.25); }}
  .heatmap .cell.l2 {{ background: rgba(255,90,54,0.45); }}
  .heatmap .cell.l3 {{ background: rgba(255,90,54,0.7); }}
  .heatmap .cell.l4 {{ background: rgba(255,90,54,1); }}
  .legend {{ display: flex; gap: 6px; align-items: center; font-size: 0.7rem; color: var(--text-muted); margin-top: 6px; }}
  .legend .cell {{ width: 12px; height: 12px; border-radius: 3px; }}
  .empty {{ color: var(--text-muted); font-size: 0.85rem; padding: 8px 0; }}
</style>
</head>
<body>
<header>
  <div>
    <h1>🏋️ Reporte de sesiones de gym</h1>
    <p>Actualizado automáticamente por GitHub Actions · última generación: {generated_at}</p>
  </div>
  <button class="theme-btn" id="themeBtn" type="button" aria-label="Cambiar tema">🌓 Tema</button>
</header>

<main>
  <div class="toolbar">
    <label for="monthSelect">Mes:</label>
    <select id="monthSelect"></select>
    <button class="ghost" id="allBtn" type="button">Todos</button>
    <span style="flex:1"></span>
    <button id="exportBtn" type="button">⬇ Exportar CSV</button>
  </div>

  <div class="stats-grid" id="statsGrid"></div>

  <div class="card">
    <h2>Duración por sesión (min)</h2>
    <div class="chart-wrap"><canvas id="durationChart" aria-label="Duración por sesión"></canvas></div>
  </div>

  <div class="card">
    <h2>Sesiones por día de la semana</h2>
    <div class="chart-wrap"><canvas id="weekdayChart" aria-label="Sesiones por día de la semana"></canvas></div>
  </div>

  <div class="card">
    <h2>Minutos por semana</h2>
    <div class="chart-wrap"><canvas id="weekChart" aria-label="Minutos por semana"></canvas></div>
  </div>

  <div class="card">
    <h2>Minutos por mes</h2>
    <div class="chart-wrap"><canvas id="monthChart" aria-label="Minutos por mes"></canvas></div>
  </div>

  <div class="card">
    <h2>Distribución de duraciones</h2>
    <div class="chart-wrap"><canvas id="histChart" aria-label="Distribución de duraciones"></canvas></div>
  </div>

  <div class="card">
    <h2>Hora de entrada por sesión</h2>
    <div class="chart-wrap"><canvas id="timeChart" aria-label="Hora de entrada"></canvas></div>
  </div>

  <div class="card">
    <h2>Hora de salida vs entrada</h2>
    <div class="chart-wrap"><canvas id="scatterChart" aria-label="Hora de salida vs entrada"></canvas></div>
  </div>

  <div class="card">
    <h2>Cumplimiento por estado</h2>
    <div class="chart-wrap"><canvas id="statusChart" aria-label="Cumplimiento por estado"></canvas></div>
  </div>

  <div class="card">
    <h2>Calendario de actividad</h2>
    <div class="heatmap" id="heatmap" aria-label="Heatmap de actividad"></div>
    <div class="legend">
      Menos
      <span class="cell" style="background: var(--border)"></span>
      <span class="cell l1"></span>
      <span class="cell l2"></span>
      <span class="cell l3"></span>
      <span class="cell l4"></span>
      Más
    </div>
  </div>

  <div class="card">
    <h2>Insights</h2>
    <ul class="insights" id="insights"></ul>
  </div>

  <div class="card">
    <h2>Récords</h2>
    <div class="table-scroll">
      <table id="recordsTable">
        <thead><tr><th>Métrica</th><th>Valor</th><th>Detalle</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <h2>Detalle de sesiones</h2>
    <div class="table-scroll">
      <table id="sessionsTable">
        <thead><tr><th>Fecha</th><th>Entrada</th><th>Salida</th><th>Min</th><th>Estado</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
    <div class="empty" id="emptyMsg" style="display:none">No hay sesiones para este filtro.</div>
  </div>
</main>

<footer>Generado desde data/gym_sessions.csv por un workflow de GitHub Actions.</footer>

<script>
const RAW_SESSIONS = {sessions_json};

// ---------- Utilidades ----------
const DOW = ['Domingo','Lunes','Martes','Miércoles','Jueves','Viernes','Sábado'];
const MONTHS_SHORT = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];

function parseDate(s) {{ const [y,m,d] = s.split('-').map(Number); return new Date(y, m-1, d); }}
function fmtMonth(ym) {{ const [y,m] = ym.split('-').map(Number); return `${{MONTHS_SHORT[m-1]}} ${{y}}`; }}
function timeToDecimal(t) {{ if (!t) return null; const parts = t.split(':'); const h = Number(parts[0]); const m = Number(parts[1]||0); if (isNaN(h)) return null; return h + m/60; }}
function toISOWeek(d) {{
  const t = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
  const day = t.getUTCDay() || 7;
  t.setUTCDate(t.getUTCDate() + 4 - day);
  const yearStart = new Date(Date.UTC(t.getUTCFullYear(),0,1));
  const week = Math.ceil(((t - yearStart)/86400000 + 1)/7);
  return `${{t.getUTCFullYear()}}-W${{String(week).padStart(2,'0')}}`;
}}
function statusBadge(s) {{
  const v = (s||'').toLowerCase();
  const cls = v.includes('complet') ? 'ok' : v.includes('parc') || v.includes('parcial') ? 'warn' : v.includes('skip') || v.includes('cancel') ? 'bad' : '';
  return `<span class="badge ${{cls}}">${{s||''}}</span>`;
}}

// Normaliza los datos una sola vez
const SESSIONS = RAW_SESSIONS.map(r => {{
  const date = r.date;
  const d = parseDate(date);
  const dur = parseFloat(r.duration_minutes) || 0;
  return {{
    ...r,
    _date: d,
    _ym: date.slice(0,7),
    _dow: d.getDay(),
    _week: toISOWeek(d),
    _dur: dur,
    _entry: timeToDecimal(r.entry_time),
    _exit: timeToDecimal(r.exit_time),
  }};
}});

// Lista de meses disponibles (descendente)
const months = Array.from(new Set(SESSIONS.map(s => s._ym))).sort().reverse();

// ---------- Estado ----------
let currentMonth = 'all';
let charts = {{}};

// ---------- Render ----------
function getFiltered() {{
  return currentMonth === 'all' ? SESSIONS : SESSIONS.filter(s => s._ym === currentMonth);
}}

function aggregate(list) {{
  const totalSessions = list.length;
  const totalMinutes = list.reduce((a,s) => a + s._dur, 0);
  const avg = totalSessions ? totalMinutes/totalSessions : 0;
  const longest = list.reduce((a,b) => !a || b._dur > a._dur ? b : a, null);
  const shortest = list.reduce((a,b) => !a || b._dur < a._dur ? b : a, null);
  const totalHours = totalMinutes/60;
  return {{ totalSessions, totalMinutes, avg, longest, shortest, totalHours }};
}}

function computeStreaks(list) {{
  // Racha de días consecutivos con sesión (usa fechas únicas ordenadas)
  const days = Array.from(new Set(list.map(s => s.date))).sort();
  let best = 0, bestRange = null, cur = 0, curStart = null, prev = null;
  for (const day of days) {{
    const d = parseDate(day);
    if (prev && (d - prev) === 86400000) {{ cur++; }}
    else {{ cur = 1; curStart = day; }}
    if (cur > best) {{ best = cur; bestRange = [curStart, day]; }}
    prev = d;
  }}
  // Racha actual: contar desde hoy hacia atrás
  let current = 0;
  if (days.length) {{
    const today = new Date(); today.setHours(0,0,0,0);
    let cursor = new Date(today);
    const set = new Set(days);
    const fmt = (d) => `${{d.getFullYear()}}-${{String(d.getMonth()+1).padStart(2,'0')}}-${{String(d.getDate()).padStart(2,'0')}}`;
    if (!set.has(fmt(cursor))) cursor.setDate(cursor.getDate()-1);
    while (set.has(fmt(cursor))) {{ current++; cursor.setDate(cursor.getDate()-1); }}
  }}
  return {{ best, bestRange, current }};
}}

function weekdayCounts(list) {{
  const arr = [0,0,0,0,0,0,0];
  list.forEach(s => arr[s._dow]++);
  // Reordena Lunes..Domingo para mostrar
  return {{ labels: ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'], data: [arr[1],arr[2],arr[3],arr[4],arr[5],arr[6],arr[0]] }};
}}

function weeklyMinutes(list) {{
  const map = new Map();
  list.forEach(s => map.set(s._week, (map.get(s._week)||0) + s._dur));
  const keys = Array.from(map.keys()).sort();
  return {{ labels: keys, data: keys.map(k => map.get(k)) }};
}}

function monthlyMinutes(list) {{
  const map = new Map();
  list.forEach(s => map.set(s._ym, (map.get(s._ym)||0) + s._dur));
  const keys = Array.from(map.keys()).sort();
  return {{ labels: keys.map(fmtMonth), data: keys.map(k => map.get(k)) }};
}}

function histogram(list) {{
  const bins = [
    {{ label: '<30', min: 0, max: 30 }},
    {{ label: '30-45', min: 30, max: 45 }},
    {{ label: '45-60', min: 45, max: 60 }},
    {{ label: '60-90', min: 60, max: 90 }},
    {{ label: '90+', min: 90, max: Infinity }},
  ];
  const counts = bins.map(b => list.filter(s => s._dur >= b.min && s._dur < b.max).length);
  return {{ labels: bins.map(b => b.label), data: counts }};
}}

function statusCounts(list) {{
  const map = new Map();
  list.forEach(s => map.set(s.status || '(sin estado)', (map.get(s.status||'(sin estado)')||0)+1));
  return {{ labels: Array.from(map.keys()), data: Array.from(map.values()) }};
}}

function heatmapData(list) {{
  if (!list.length) return null;
  const dates = list.map(s => s._date).sort((a,b) => a-b);
  const start = new Date(dates[0]); start.setDate(start.getDate() - start.getDay()); // domingo previo
  const end = new Date(dates[dates.length-1]);
  const days = new Map();
  list.forEach(s => {{ const k = s.date; days.set(k, (days.get(k)||0) + 1); }});
  const cells = [];
  let cursor = new Date(start);
  while (cursor <= end) {{
    const k = `${{cursor.getFullYear()}}-${{String(cursor.getMonth()+1).padStart(2,'0')}}-${{String(cursor.getDate()).padStart(2,'0')}}`;
    const c = days.get(k) || 0;
    const level = c === 0 ? 0 : c === 1 ? 1 : c === 2 ? 2 : c === 3 ? 3 : 4;
    cells.push({{ date: k, count: c, level }});
    cursor.setDate(cursor.getDate()+1);
  }}
  return cells;
}}

function buildInsights(list) {{
  if (!list.length) return ['Sin datos para el período seleccionado.'];
  const out = [];
  const wd = weekdayCounts(list);
  const maxIdx = wd.data.indexOf(Math.max(...wd.data));
  out.push(`Entrenás más los <strong>${{wd.labels[maxIdx]}}</strong> (${{wd.data[maxIdx]}} sesiones).`);

  const agg = aggregate(list);
  out.push(`Promedio por sesión: <strong>${{agg.avg.toFixed(0)}} min</strong> · total <strong>${{agg.totalHours.toFixed(1)}} h</strong>.`);

  const entries = list.map(s => s._entry).filter(v => v !== null);
  if (entries.length) {{
    const avgEntry = entries.reduce((a,b)=>a+b,0)/entries.length;
    const h = Math.floor(avgEntry); const m = Math.round((avgEntry-h)*60);
    out.push(`Hora promedio de entrada: <strong>${{String(h).padStart(2,'0')}}:${{String(m).padStart(2,'0')}}</strong>.`);
  }}

  const streaks = computeStreaks(list);
  if (streaks.best) out.push(`Racha máxima: <strong>${{streaks.best}} días</strong>${{streaks.bestRange ? ` (${{streaks.bestRange[0]}} → ${{streaks.bestRange[1]}})` : ''}}.`);

  // Comparación mensual (si hay al menos 2 meses distintos)
  const months = Array.from(new Set(list.map(s => s._ym))).sort();
  if (months.length >= 2) {{
    const last = months[months.length-1], prev = months[months.length-2];
    const minsOf = (m) => list.filter(s => s._ym === m).reduce((a,s) => a+s._dur, 0);
    const lm = minsOf(last), pm = minsOf(prev);
    if (pm > 0) {{
      const pct = ((lm - pm) / pm * 100).toFixed(0);
      const dir = lm >= pm ? 'subió' : 'bajó';
      out.push(`Respecto a <strong>${{fmtMonth(prev)}}</strong>, en <strong>${{fmtMonth(last)}}</strong> el volumen ${{dir}} un <strong>${{Math.abs(pct)}}%</strong>.`);
    }}
  }}
  return out;
}}

function buildRecords(list) {{
  const rows = [];
  const agg = aggregate(list);
  if (agg.longest) rows.push(['Sesión más larga', `${{agg.longest._dur.toFixed(0)}} min`, agg.longest.date]);
  if (agg.shortest) rows.push(['Sesión más corta', `${{agg.shortest._dur.toFixed(0)}} min`, agg.shortest.date]);

  const weekly = weeklyMinutes(list);
  if (weekly.data.length) {{
    const maxW = Math.max(...weekly.data);
    const idx = weekly.data.indexOf(maxW);
    rows.push(['Semana más intensa', `${{maxW.toFixed(0)}} min`, weekly.labels[idx]]);
  }}
  const monthly = monthlyMinutes(list);
  if (monthly.data.length) {{
    const maxM = Math.max(...monthly.data);
    const idx = monthly.data.indexOf(maxM);
    rows.push(['Mes más activo', `${{maxM.toFixed(0)}} min`, monthly.labels[idx]]);
  }}
  const streaks = computeStreaks(list);
  if (streaks.best) rows.push(['Racha máxima', `${{streaks.best}} días`, streaks.bestRange ? `${{streaks.bestRange[0]}} → ${{streaks.bestRange[1]}}` : '']);
  rows.push(['Racha actual', `${{streaks.current}} días`, '']);
  return rows;
}}

function renderStats(list) {{
  const agg = aggregate(list);
  const streaks = computeStreaks(list);
  const el = document.getElementById('statsGrid');
  el.innerHTML = `
    <div class="stat-card"><div class="value">${{agg.totalSessions}}</div><div class="label">Sesiones</div></div>
    <div class="stat-card"><div class="value">${{agg.totalHours.toFixed(1)}}h</div><div class="label">Tiempo total</div></div>
    <div class="stat-card"><div class="value">${{agg.avg.toFixed(0)}}m</div><div class="label">Promedio/sesión</div></div>
    <div class="stat-card"><div class="value">${{agg.longest ? agg.longest._dur.toFixed(0) : 0}}m</div><div class="label">Sesión más larga</div></div>
    <div class="stat-card"><div class="value">${{streaks.current}}</div><div class="label">Racha actual (días)</div></div>
    <div class="stat-card"><div class="value">${{streaks.best}}</div><div class="label">Racha máxima</div></div>
  `;
}}

function renderTable(list) {{
  const tbody = document.querySelector('#sessionsTable tbody');
  tbody.innerHTML = '';
  const empty = document.getElementById('emptyMsg');
  if (!list.length) {{ empty.style.display = 'block'; return; }}
  empty.style.display = 'none';
  list.forEach(r => {{
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${{r.date}}</td><td>${{(r.entry_time||'').slice(0,5)}}</td><td>${{(r.exit_time||'').slice(0,5)}}</td><td>${{r._dur.toFixed(0)}}</td><td>${{statusBadge(r.status)}}</td>`;
    tbody.appendChild(tr);
  }});
}}

function renderRecords(list) {{
  const tbody = document.querySelector('#recordsTable tbody');
  tbody.innerHTML = '';
  buildRecords(list).forEach(([k,v,d]) => {{
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${{k}}</td><td><strong>${{v}}</strong></td><td>${{d}}</td>`;
    tbody.appendChild(tr);
  }});
}}

function renderInsights(list) {{
  const ul = document.getElementById('insights');
  ul.innerHTML = buildInsights(list).map(t => `<li>${{t}}</li>`).join('');
}}

function renderHeatmap(list) {{
  const el = document.getElementById('heatmap');
  const cells = heatmapData(list);
  if (!cells) {{ el.innerHTML = '<div class="empty">Sin datos.</div>'; return; }}
  el.innerHTML = cells.map(c => `<div class="cell l${{c.level}}" title="${{c.date}}: ${{c.count}} sesión(es)"></div>`).join('');
}}

// ---------- Charts ----------
function destroyCharts() {{
  Object.values(charts).forEach(c => {{ try {{ c.destroy(); }} catch(e) {{}} }});
  charts = {{}};
}}

function themeColors() {{
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark' ||
    (!document.documentElement.getAttribute('data-theme') && window.matchMedia('(prefers-color-scheme: dark)').matches);
  return {{
    grid: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)',
    text: isDark ? '#9ca3af' : '#6b7280',
  }};
}}

function renderCharts(list) {{
  destroyCharts();
  const t = themeColors();
  Chart.defaults.color = t.text;
  Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";

  // Duración por sesión
  charts.duration = new Chart(document.getElementById('durationChart'), {{
    type: 'bar',
    data: {{
      labels: list.map(r => r.date.slice(5)),
      datasets: [{{ label: 'Minutos', data: list.map(r => r._dur), backgroundColor: '#ff5a36', borderRadius: 6, maxBarThickness: 36 }}]
    }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }},
      scales: {{ x: {{ grid: {{ display: false }} }}, y: {{ grid: {{ color: t.grid }}, beginAtZero: true }} }} }}
  }});

  // Día de la semana
  const wd = weekdayCounts(list);
  charts.weekday = new Chart(document.getElementById('weekdayChart'), {{
    type: 'bar',
    data: {{ labels: wd.labels, datasets: [{{ label: 'Sesiones', data: wd.data, backgroundColor: '#2563eb', borderRadius: 6, maxBarThickness: 48 }}] }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }},
      scales: {{ x: {{ grid: {{ display: false }} }}, y: {{ grid: {{ color: t.grid }}, beginAtZero: true, ticks: {{ precision: 0 }} }} }} }}
  }});

  // Minutos por semana
  const wk = weeklyMinutes(list);
  charts.week = new Chart(document.getElementById('weekChart'), {{
    type: 'line',
    data: {{ labels: wk.labels, datasets: [{{ label: 'Minutos', data: wk.data, borderColor: '#8b5cf6', backgroundColor: 'rgba(139,92,246,0.15)', tension: 0.3, fill: true, pointRadius: 4 }}] }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }},
      scales: {{ x: {{ grid: {{ display: false }} }}, y: {{ grid: {{ color: t.grid }}, beginAtZero: true }} }} }}
  }});

  // Minutos por mes
  const mo = monthlyMinutes(list);
  charts.month = new Chart(document.getElementById('monthChart'), {{
    type: 'bar',
    data: {{ labels: mo.labels, datasets: [{{ label: 'Minutos', data: mo.data, backgroundColor: '#16a34a', borderRadius: 6, maxBarThickness: 48 }}] }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }},
      scales: {{ x: {{ grid: {{ display: false }} }}, y: {{ grid: {{ color: t.grid }}, beginAtZero: true }} }} }}
  }});

  // Histograma
  const h = histogram(list);
  charts.hist = new Chart(document.getElementById('histChart'), {{
    type: 'bar',
    data: {{ labels: h.labels, datasets: [{{ label: 'Sesiones', data: h.data, backgroundColor: '#eab308', borderRadius: 6, maxBarThickness: 48 }}] }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }},
      scales: {{ x: {{ grid: {{ display: false }} }}, y: {{ grid: {{ color: t.grid }}, beginAtZero: true, ticks: {{ precision: 0 }} }} }} }}
  }});

  // Hora de entrada
  charts.time = new Chart(document.getElementById('timeChart'), {{
    type: 'line',
    data: {{ labels: list.map(r => r.date.slice(5)), datasets: [{{ label: 'Hora de entrada', data: list.map(r => r._entry), borderColor: '#2563eb', backgroundColor: 'rgba(37,99,235,0.15)', tension: 0.3, fill: true, pointRadius: 4, spanGaps: true }}] }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }},
      scales: {{ x: {{ grid: {{ display: false }} }}, y: {{ grid: {{ color: t.grid }}, min: 6, max: 23, ticks: {{ callback: v => `${{v}}:00` }} }} }} }}
  }});

  // Scatter entrada vs salida
  const pts = list.filter(s => s._entry !== null && s._exit !== null).map(s => ({{ x: s._entry, y: s._exit }}));
  charts.scatter = new Chart(document.getElementById('scatterChart'), {{
    type: 'scatter',
    data: {{ datasets: [{{ label: 'Entrada vs Salida', data: pts, backgroundColor: '#ff5a36', pointRadius: 5 }}] }},
    options: {{ responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ title: {{ display: true, text: 'Entrada' }}, min: 6, max: 23, grid: {{ color: t.grid }}, ticks: {{ callback: v => `${{v}}:00` }} }},
        y: {{ title: {{ display: true, text: 'Salida' }}, min: 6, max: 23, grid: {{ color: t.grid }}, ticks: {{ callback: v => `${{v}}:00` }} }}
      }} }}
  }});

  // Estado
  const st = statusCounts(list);
  charts.status = new Chart(document.getElementById('statusChart'), {{
    type: 'doughnut',
    data: {{ labels: st.labels, datasets: [{{ data: st.data, backgroundColor: ['#2563eb','#16a34a','#eab308','#ef4444','#8b5cf6','#ff5a36'] }}] }},
    options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: 'bottom' }} }} }}
  }});
}}

// ---------- Filtros / eventos ----------
function renderAll() {{
  const list = getFiltered();
  renderStats(list);
  renderTable(list);
  renderRecords(list);
  renderInsights(list);
  renderHeatmap(list);
  renderCharts(list);
}}

function populateMonths() {{
  const sel = document.getElementById('monthSelect');
  sel.innerHTML = '';
  const optAll = document.createElement('option');
  optAll.value = 'all'; optAll.textContent = 'Todos los meses';
  sel.appendChild(optAll);
  months.forEach(ym => {{
    const o = document.createElement('option');
    o.value = ym; o.textContent = fmtMonth(ym);
    sel.appendChild(o);
  }});
  sel.value = currentMonth;
}}

document.getElementById('monthSelect').addEventListener('change', (e) => {{
  currentMonth = e.target.value;
  renderAll();
}});
document.getElementById('allBtn').addEventListener('click', () => {{
  currentMonth = 'all';
  document.getElementById('monthSelect').value = 'all';
  renderAll();
}});

document.getElementById('exportBtn').addEventListener('click', () => {{
  const list = getFiltered();
  const cols = ['date','entry_time','exit_time','duration_minutes','status'];
  const lines = [cols.join(',')];
  list.forEach(r => lines.push(cols.map(c => {{
    const v = String(r[c] ?? '');
    return v.includes(',') ? `"${{v.replace(/"/g,'""')}}"` : v;
  }}).join(',')));
  const blob = new Blob([lines.join('\\n')], {{ type: 'text/csv;charset=utf-8' }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `gym_${{currentMonth === 'all' ? 'all' : currentMonth}}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}});

// Tema manual
document.getElementById('themeBtn').addEventListener('click', () => {{
  const cur = document.documentElement.getAttribute('data-theme');
  const next = cur === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  renderCharts(getFiltered());
}});
(function initTheme() {{
  const saved = localStorage.getItem('theme');
  if (saved) document.documentElement.setAttribute('data-theme', saved);
}})();

// Re-render si cambia el tema del SO (solo si no hay override)
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {{
  if (!localStorage.getItem('theme')) renderCharts(getFiltered());
}});

// ---------- Init ----------
document.addEventListener('DOMContentLoaded', () => {{
  populateMonths();
  renderAll();
}});
</script>
</body>
</html>
"""


def main():
    sessions = load_sessions()
    os.makedirs(DIST_DIR, exist_ok=True)
    payload = json.dumps(sessions, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.format(
        sessions_json=payload,
        generated_at=datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M UTC"),
    )
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard generado en {OUT_PATH} con {len(sessions)} sesiones.")


if __name__ == "__main__":
    main()
