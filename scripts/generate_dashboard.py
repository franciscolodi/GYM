#!/usr/bin/env python3
"""
Lee data/gym_sessions.csv y genera dist/index.html con un dashboard
de gráficos y reporte. Pensado para correr desde GitHub Actions
y publicarse en GitHub Pages.
"""
import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT, "data", "gym_sessions.csv")
DIST_DIR = os.path.join(ROOT, "dist")
OUT_PATH = os.path.join(DIST_DIR, "index.html")


def load_sessions():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]
    # Ordena por fecha ascendente por si el CSV no viene ordenado
    rows.sort(key=lambda r: r["date"])
    return rows


TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Reporte de Gym</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.4/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #f5f6f8;
    --card-bg: #ffffff;
    --text: #14161a;
    --text-muted: #6b7280;
    --accent: #ff5a36;
    --accent-2: #2563eb;
    --border: #e5e7eb;
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
  header {{ padding: 28px 20px 16px; max-width: 720px; margin: 0 auto; }}
  header h1 {{ font-size: 1.5rem; margin: 0 0 4px; letter-spacing: -0.02em; }}
  header p {{ margin: 0; color: var(--text-muted); font-size: 0.85rem; }}
  main {{ max-width: 720px; margin: 0 auto; padding: 0 16px 40px; }}
  .stats-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 16px 0 24px; }}
  @media (min-width: 480px) {{ .stats-grid {{ grid-template-columns: repeat(4, 1fr); }} }}
  .stat-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 14px; padding: 14px; }}
  .stat-card .value {{ font-size: 1.4rem; font-weight: 700; color: var(--accent); }}
  .stat-card .label {{ font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }}
  .card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 18px; margin-bottom: 18px; }}
  .card h2 {{ font-size: 1rem; margin: 0 0 12px; }}
  .chart-wrap {{ position: relative; width: 100%; height: 240px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
  th, td {{ text-align: left; padding: 8px 6px; border-bottom: 1px solid var(--border); white-space: nowrap; }}
  th {{ color: var(--text-muted); font-weight: 600; font-size: 0.75rem; text-transform: uppercase; }}
  .table-scroll {{ overflow-x: auto; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px; background: rgba(37,99,235,0.12); color: var(--accent-2); font-size: 0.7rem; font-weight: 600; }}
  footer {{ text-align: center; color: var(--text-muted); font-size: 0.75rem; padding: 10px 0 20px; }}
  .source-link {{ color: var(--accent-2); text-decoration: none; }}
</style>
</head>
<body>
<header>
  <h1>🏋️ Reporte de sesiones de gym</h1>
  <p>Actualizado automáticamente por GitHub Actions · última generación: {generated_at}</p>
</header>

<main>
  <div class="stats-grid" id="statsGrid"></div>

  <div class="card">
    <h2>Duración por sesión (min)</h2>
    <div class="chart-wrap"><canvas id="durationChart"></canvas></div>
  </div>

  <div class="card">
    <h2>Hora de entrada por sesión</h2>
    <div class="chart-wrap"><canvas id="timeChart"></canvas></div>
  </div>

  <div class="card">
    <h2>Detalle de sesiones</h2>
    <div class="table-scroll">
      <table id="sessionsTable">
        <thead><tr><th>Fecha</th><th>Entrada</th><th>Salida</th><th>Min</th><th>Estado</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>
</main>

<footer>Generado desde data/gym_sessions.csv por un workflow de GitHub Actions.</footer>

<script>
const sessions = {sessions_json};

const totalSessions = sessions.length;
const totalMinutes = sessions.reduce((s, r) => s + parseFloat(r.duration_minutes), 0);
const avgMinutes = totalSessions ? totalMinutes / totalSessions : 0;
const longest = sessions.length ? sessions.reduce((a, b) => parseFloat(a.duration_minutes) > parseFloat(b.duration_minutes) ? a : b) : null;
const totalHours = (totalMinutes / 60).toFixed(1);

document.getElementById('statsGrid').innerHTML = `
  <div class="stat-card"><div class="value">${{totalSessions}}</div><div class="label">Sesiones</div></div>
  <div class="stat-card"><div class="value">${{totalHours}}h</div><div class="label">Tiempo total</div></div>
  <div class="stat-card"><div class="value">${{avgMinutes.toFixed(0)}}m</div><div class="label">Promedio/sesión</div></div>
  <div class="stat-card"><div class="value">${{longest ? parseFloat(longest.duration_minutes).toFixed(0) : 0}}m</div><div class="label">Sesión más larga</div></div>
`;

const tbody = document.querySelector('#sessionsTable tbody');
sessions.forEach(r => {{
  const tr = document.createElement('tr');
  tr.innerHTML = `<td>${{r.date}}</td><td>${{(r.entry_time || '').slice(0,5)}}</td><td>${{(r.exit_time || '').slice(0,5)}}</td><td>${{parseFloat(r.duration_minutes).toFixed(0)}}</td><td><span class="badge">${{r.status}}</span></td>`;
  tbody.appendChild(tr);
}});

const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
const gridColor = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)';
const textColor = isDark ? '#9ca3af' : '#6b7280';
Chart.defaults.color = textColor;
Chart.defaults.font.family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";

new Chart(document.getElementById('durationChart'), {{
  type: 'bar',
  data: {{
    labels: sessions.map(r => r.date.slice(5)),
    datasets: [{{ label: 'Minutos', data: sessions.map(r => parseFloat(r.duration_minutes)), backgroundColor: '#ff5a36', borderRadius: 6, maxBarThickness: 36 }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{ x: {{ grid: {{ display: false }} }}, y: {{ grid: {{ color: gridColor }}, beginAtZero: true }} }}
  }}
}});

function timeToDecimal(t) {{
  if (!t) return 0;
  const [h, m] = t.split(':').map(Number);
  return h + m / 60;
}}

new Chart(document.getElementById('timeChart'), {{
  type: 'line',
  data: {{
    labels: sessions.map(r => r.date.slice(5)),
    datasets: [{{ label: 'Hora de entrada', data: sessions.map(r => timeToDecimal(r.entry_time)), borderColor: '#2563eb', backgroundColor: 'rgba(37,99,235,0.15)', tension: 0.3, fill: true, pointRadius: 4 }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{ legend: {{ display: false }} }},
    scales: {{ x: {{ grid: {{ display: false }} }}, y: {{ grid: {{ color: gridColor }}, min: 6, max: 23, ticks: {{ callback: v => `${{v}}:00` }} }} }}
  }}
}});
</script>
</body>
</html>
"""


def main():
    import datetime

    sessions = load_sessions()
    os.makedirs(DIST_DIR, exist_ok=True)
    html = TEMPLATE.format(
        sessions_json=json.dumps(sessions, ensure_ascii=False),
        generated_at=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    )
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard generado en {OUT_PATH} con {len(sessions)} sesiones.")


if __name__ == "__main__":
    main()
