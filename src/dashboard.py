from __future__ import annotations

import html
import json
import os
import sqlite3
from pathlib import Path
from typing import Any


def _rows(conn: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    previous_factory = conn.row_factory
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(query, params).fetchall()
    finally:
        conn.row_factory = previous_factory


def _relpath(path: Path, start: Path) -> str:
    return Path(os.path.relpath(path, start)).as_posix()


def _image_list(output_root: Path, dashboard_dir: Path, experiment_id: int, pattern: str) -> list[str]:
    experiment_dir = output_root / f"IOTA-{experiment_id:06d}"
    return [
        _relpath(path, dashboard_dir)
        for path in sorted(experiment_dir.glob(pattern))
    ]


def _load_dashboard_data(conn: sqlite3.Connection, output_root: Path, dashboard_dir: Path) -> dict[str, Any]:
    experiments = _rows(
        conn,
        """
        SELECT experiment_id, timestamp, objective, notes, config_hash, simulation_version
        FROM experiments
        ORDER BY experiment_id
        """,
    )
    summaries = _rows(
        conn,
        """
        SELECT experiment_id, metric_name, metric_value
        FROM summary_metrics
        ORDER BY experiment_id, metric_name
        """,
    )
    parameters = _rows(
        conn,
        """
        SELECT experiment_id, parameter_name, parameter_value
        FROM parameters
        WHERE parameter_name IN (
            'experiment.id',
            'simulation_version',
            'init.active_iotas',
            'init.initial_density',
            'init.total_iotas',
            'constants.amplitude_coupling',
            'run.ticks',
            'grid.size',
            'vectors.vector_count'
        )
        ORDER BY experiment_id, parameter_name
        """,
    )
    diffs = _rows(
        conn,
        """
        SELECT experiment_id, parameter_name, old_value, new_value
        FROM parameter_diffs
        ORDER BY experiment_id, parameter_name
        """,
    )
    metrics = _rows(
        conn,
        """
        SELECT
            experiment_id,
            tick,
            active_iotas,
            largest_coherence,
            coherence_count,
            coherence_ratio,
            entropy
        FROM metrics
        ORDER BY experiment_id, tick
        """,
    )
    artifacts = _rows(
        conn,
        """
        SELECT experiment_id, COUNT(*) AS artifact_count, COALESCE(SUM(bytes), 0) AS artifact_bytes
        FROM artifacts
        WHERE retained = 1
        GROUP BY experiment_id
        """,
    )

    summary_by_experiment: dict[int, dict[str, float]] = {}
    for row in summaries:
        summary_by_experiment.setdefault(row["experiment_id"], {})[row["metric_name"]] = row["metric_value"]

    params_by_experiment: dict[int, dict[str, str]] = {}
    for row in parameters:
        params_by_experiment.setdefault(row["experiment_id"], {})[row["parameter_name"]] = row["parameter_value"]

    diffs_by_experiment: dict[int, list[dict[str, str | None]]] = {}
    for row in diffs:
        diffs_by_experiment.setdefault(row["experiment_id"], []).append(
            {
                "parameter_name": row["parameter_name"],
                "old_value": row["old_value"],
                "new_value": row["new_value"],
            }
        )

    series_by_experiment: dict[int, list[dict[str, float]]] = {}
    for row in metrics:
        series_by_experiment.setdefault(row["experiment_id"], []).append(
            {
                "tick": row["tick"],
                "active_iotas": row["active_iotas"],
                "largest_coherence": row["largest_coherence"],
                "coherence_count": row["coherence_count"],
                "coherence_ratio": row["coherence_ratio"],
                "entropy": row["entropy"],
            }
        )

    artifacts_by_experiment = {
        row["experiment_id"]: {
            "count": row["artifact_count"],
            "bytes": row["artifact_bytes"],
        }
        for row in artifacts
    }

    experiment_data = []
    for row in experiments:
        experiment_id = row["experiment_id"]
        experiment_data.append(
            {
                "experiment_id": experiment_id,
                "label": f"IOTA-{experiment_id:06d}",
                "timestamp": row["timestamp"],
                "objective": row["objective"],
                "notes": row["notes"],
                "config_hash": row["config_hash"],
                "simulation_version": row["simulation_version"],
                "summary": summary_by_experiment.get(experiment_id, {}),
                "artifacts": artifacts_by_experiment.get(
                    experiment_id,
                    {"count": 0, "bytes": 0},
                ),
                "parameters": params_by_experiment.get(experiment_id, {}),
                "diffs": diffs_by_experiment.get(experiment_id, []),
                "series": series_by_experiment.get(experiment_id, []),
                "slices": _image_list(output_root, dashboard_dir, experiment_id, "slice_*.png"),
                "scatters": _image_list(output_root, dashboard_dir, experiment_id, "scatter_*.png"),
            }
        )

    comparison_images = [
        _relpath(path, dashboard_dir)
        for path in sorted((output_root / "experiments").glob("*.png"))
    ]
    return {
        "experiments": experiment_data,
        "comparison_images": comparison_images,
    }


def _html_shell(data: dict[str, Any]) -> str:
    payload = json.dumps(data, sort_keys=True)
    escaped_payload = html.escape(payload, quote=False)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="15">
  <title>Iota Lab Dashboard</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f7f4;
      --panel: #ffffff;
      --ink: #1f2421;
      --muted: #68706a;
      --line: #d9ddd7;
      --accent: #17745b;
      --accent-2: #7b5d1e;
      --plot-a: #17745b;
      --plot-b: #355f8a;
      --plot-c: #8a4f35;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font: 14px/1.45 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 18px 24px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
      position: sticky;
      top: 0;
      z-index: 10;
    }}
    h1, h2, h3 {{ margin: 0; letter-spacing: 0; }}
    h1 {{ font-size: 20px; }}
    h2 {{ font-size: 15px; margin-bottom: 12px; }}
    h3 {{ font-size: 13px; margin-bottom: 8px; color: var(--muted); }}
    main {{
      display: grid;
      grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
      gap: 16px;
      padding: 16px;
    }}
    aside, section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 6px;
    }}
    aside {{ overflow: hidden; }}
    .list {{ max-height: calc(100vh - 96px); overflow: auto; }}
    .experiment-button {{
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 4px 12px;
      width: 100%;
      padding: 12px 14px;
      border: 0;
      border-bottom: 1px solid var(--line);
      background: transparent;
      color: var(--ink);
      text-align: left;
      cursor: pointer;
      font: inherit;
    }}
    .experiment-button:hover, .experiment-button.active {{ background: #eef4ef; }}
    .experiment-button strong {{ font-size: 13px; }}
    .experiment-button span {{ color: var(--muted); font-size: 12px; }}
    .content {{ display: grid; gap: 16px; }}
    .panel {{ padding: 16px; }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(4, minmax(120px, 1fr));
      gap: 10px;
    }}
    .stat {{
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
      background: #fbfbf9;
    }}
    .stat span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 4px;
    }}
    .stat strong {{ font-size: 20px; }}
    .grid-2 {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }}
    .plot {{
      width: 100%;
      height: 260px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fbfbf9;
    }}
    svg {{ display: block; width: 100%; height: 100%; }}
    .axis {{ stroke: #8c938d; stroke-width: 1; }}
    .series-a {{ fill: none; stroke: var(--plot-a); stroke-width: 2; }}
    .series-b {{ fill: none; stroke: var(--plot-b); stroke-width: 2; }}
    .series-c {{ fill: none; stroke: var(--plot-c); stroke-width: 2; }}
    .muted {{ color: var(--muted); }}
    table {{ width: 100%; border-collapse: collapse; }}
    td, th {{
      padding: 7px 8px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }}
    th {{ color: var(--muted); font-weight: 600; font-size: 12px; }}
    code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 12px;
    }}
    .thumbs {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 10px;
    }}
    .thumb {{
      display: grid;
      gap: 6px;
      color: inherit;
      text-decoration: none;
    }}
    .thumb img {{
      width: 100%;
      aspect-ratio: 4 / 3;
      object-fit: contain;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fbfbf9;
    }}
    .comparison img {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fbfbf9;
    }}
    @media (max-width: 900px) {{
      main {{ grid-template-columns: 1fr; }}
      .stats {{ grid-template-columns: repeat(2, minmax(120px, 1fr)); }}
      .grid-2 {{ grid-template-columns: 1fr; }}
      .list {{ max-height: none; }}
    }}
  </style>
</head>
<body>
  <script id="dashboard-data" type="application/json">{escaped_payload}</script>
  <header>
    <div>
      <h1>Iota Lab Dashboard</h1>
      <div class="muted" id="run-count"></div>
    </div>
    <div class="muted">Auto-refreshes every 15 seconds</div>
  </header>
  <main>
    <aside>
      <div class="panel">
        <h2>Experiments</h2>
      </div>
      <div class="list" id="experiment-list"></div>
    </aside>
    <div class="content">
      <section class="panel" id="overview"></section>
      <section class="panel">
        <h2>Run Metrics</h2>
        <div class="grid-2">
          <div>
            <h3>Active Iotas</h3>
            <div class="plot" id="active-plot"></div>
          </div>
          <div>
            <h3>Largest Coherence</h3>
            <div class="plot" id="coherence-plot"></div>
          </div>
          <div>
            <h3>Coherence Ratio</h3>
            <div class="plot" id="ratio-plot"></div>
          </div>
          <div>
            <h3>Entropy</h3>
            <div class="plot" id="entropy-plot"></div>
          </div>
          <div>
            <h3>Coherence Count</h3>
            <div class="plot" id="count-plot"></div>
          </div>
        </div>
      </section>
      <section class="panel">
        <h2>Parameter Diff</h2>
        <div id="diff-table"></div>
      </section>
      <section class="panel">
        <h2>Snapshots</h2>
        <div class="thumbs" id="snapshots"></div>
      </section>
      <section class="panel comparison">
        <h2>Across Experiments</h2>
        <div class="grid-2" id="comparison-images"></div>
      </section>
    </div>
  </main>
  <script>
    const DATA = JSON.parse(document.getElementById('dashboard-data').textContent);
    let selectedIndex = Math.max(0, DATA.experiments.length - 1);

    function fmt(value, digits = 3) {{
      if (value === undefined || value === null || value === '') return 'n/a';
      const number = Number(value);
      if (!Number.isFinite(number)) return String(value);
      return Number.isInteger(number) ? String(number) : number.toFixed(digits);
    }}

    function fmtBytes(value) {{
      const bytes = Number(value || 0);
      if (bytes < 1024) return `${{bytes}} B`;
      if (bytes < 1024 * 1024) return `${{(bytes / 1024).toFixed(1)}} KB`;
      return `${{(bytes / (1024 * 1024)).toFixed(1)}} MB`;
    }}

    function decodeJson(value) {{
      try {{ return JSON.parse(value); }} catch (_) {{ return value ?? 'n/a'; }}
    }}

    function linePath(series, key, width, height, pad) {{
      if (!series.length) return '';
      const xs = series.map(row => Number(row.tick));
      const ys = series.map(row => Number(row[key]));
      const minX = Math.min(...xs);
      const maxX = Math.max(...xs);
      const minY = Math.min(0, ...ys);
      const maxY = Math.max(1, ...ys);
      const xScale = value => pad + ((value - minX) / Math.max(1, maxX - minX)) * (width - pad * 2);
      const yScale = value => height - pad - ((value - minY) / Math.max(1, maxY - minY)) * (height - pad * 2);
      return series.map((row, index) => `${{index ? 'L' : 'M'}} ${{xScale(Number(row.tick)).toFixed(2)}} ${{yScale(Number(row[key])).toFixed(2)}}`).join(' ');
    }}

    function renderPlot(targetId, experiment, key, className) {{
      const width = 640;
      const height = 260;
      const pad = 34;
      const path = linePath(experiment.series, key, width, height, pad);
      document.getElementById(targetId).innerHTML = `
        <svg viewBox="0 0 ${{width}} ${{height}}" role="img" aria-label="${{key}}">
          <line class="axis" x1="${{pad}}" y1="${{height - pad}}" x2="${{width - pad}}" y2="${{height - pad}}"></line>
          <line class="axis" x1="${{pad}}" y1="${{pad}}" x2="${{pad}}" y2="${{height - pad}}"></line>
          <path class="${{className}}" d="${{path}}"></path>
        </svg>
      `;
    }}

    function renderList() {{
      const list = document.getElementById('experiment-list');
      list.innerHTML = DATA.experiments.map((experiment, index) => {{
        const active = decodeJson(experiment.parameters['init.active_iotas']);
        const coupling = decodeJson(experiment.parameters['constants.amplitude_coupling']);
        const peak = experiment.summary.largest_coherence;
        return `
          <button class="experiment-button ${{index === selectedIndex ? 'active' : ''}}" data-index="${{index}}">
            <strong>${{experiment.label}}</strong>
            <span>active=${{active ?? 'n/a'}} · kA=${{coupling ?? 'n/a'}}</span>
            <span>${{experiment.objective || 'Unspecified'}}</span>
            <span>peak=${{fmt(peak, 0)}}</span>
          </button>
        `;
      }}).join('');
      list.querySelectorAll('button').forEach(button => {{
        button.addEventListener('click', () => {{
          selectedIndex = Number(button.dataset.index);
          render();
        }});
      }});
    }}

    function renderOverview(experiment) {{
      const summary = experiment.summary;
      const initialActive = summary.initial_active_iotas ?? decodeJson(experiment.parameters['init.active_iotas']);
      const totalIotas = summary.total_iotas ?? decodeJson(experiment.parameters['init.total_iotas']);
      const densityPercent = summary.initial_density_percent;
      const amplitudeCoupling = decodeJson(experiment.parameters['constants.amplitude_coupling']);
      document.getElementById('overview').innerHTML = `
        <h2>${{experiment.label}}</h2>
        <p class="muted">${{experiment.objective || 'Unspecified'}} · ${{experiment.timestamp}}</p>
        <div class="stats">
          <div class="stat"><span>Initial Active</span><strong>${{fmt(initialActive, 0)}}</strong></div>
          <div class="stat"><span>Total Iotas</span><strong>${{fmt(totalIotas, 0)}}</strong></div>
          <div class="stat"><span>Initial Density</span><strong>${{fmt(densityPercent, 6)}}%</strong></div>
          <div class="stat"><span>Peak Active</span><strong>${{fmt(summary.peak_active_iotas, 0)}}</strong></div>
          <div class="stat"><span>Final Active</span><strong>${{fmt(summary.final_active_iotas, 0)}}</strong></div>
          <div class="stat"><span>Largest Coherence</span><strong>${{fmt(summary.largest_coherence, 0)}}</strong></div>
          <div class="stat"><span>Final Coherence Ratio</span><strong>${{fmt(summary.final_coherence_ratio, 6)}}</strong></div>
          <div class="stat"><span>Amplitude Coupling</span><strong>${{fmt(amplitudeCoupling)}}</strong></div>
          <div class="stat"><span>Entropy</span><strong>${{fmt(summary.entropy)}}</strong></div>
          <div class="stat"><span>Artifacts</span><strong>${{experiment.artifacts.count}}</strong></div>
        </div>
        <table>
          <tr><th>Config Hash</th><td><code>${{experiment.config_hash}}</code></td></tr>
          <tr><th>Simulation Version</th><td><code>${{experiment.simulation_version}}</code></td></tr>
          <tr><th>Artifact Storage</th><td>${{fmtBytes(experiment.artifacts.bytes)}}</td></tr>
          <tr><th>Persistence</th><td>${{fmt(summary.persistence)}}</td></tr>
          <tr><th>Execution Time</th><td>${{fmt(summary.execution_time_seconds)}} seconds</td></tr>
        </table>
      `;
    }}

    function renderDiffs(experiment) {{
      const rows = experiment.diffs.length ? experiment.diffs : [
        {{ parameter_name: 'none', old_value: 'n/a', new_value: 'n/a' }}
      ];
      document.getElementById('diff-table').innerHTML = `
        <table>
          <thead><tr><th>Parameter</th><th>Old</th><th>New</th></tr></thead>
          <tbody>
            ${{rows.map(row => `
              <tr>
                <td><code>${{row.parameter_name}}</code></td>
                <td>${{decodeJson(row.old_value)}}</td>
                <td>${{decodeJson(row.new_value)}}</td>
              </tr>
            `).join('')}}
          </tbody>
        </table>
      `;
    }}

    function renderSnapshots(experiment) {{
      const images = [
        ...experiment.scatters.slice(-3).map(src => [src, '3D active-iota view']),
        ...experiment.slices.slice(-3).map(src => [src, 'Slice view'])
      ];
      document.getElementById('snapshots').innerHTML = images.length ? images.map(([src, label]) => `
        <a class="thumb" href="${{src}}">
          <img src="${{src}}" alt="${{label}}">
          <span>${{label}}</span>
        </a>
      `).join('') : '<p class="muted">No snapshots yet.</p>';
    }}

    function renderComparisonImages() {{
      document.getElementById('comparison-images').innerHTML = DATA.comparison_images.length ? DATA.comparison_images.map(src => `
        <a href="${{src}}"><img src="${{src}}" alt="Experiment comparison"></a>
      `).join('') : '<p class="muted">Comparison plots appear after experiments have run.</p>';
    }}

    function render() {{
      document.getElementById('run-count').textContent = `${{DATA.experiments.length}} experiment${{DATA.experiments.length === 1 ? '' : 's'}} recorded`;
      renderList();
      const experiment = DATA.experiments[selectedIndex];
      if (!experiment) {{
        document.getElementById('overview').innerHTML = '<h2>No experiments recorded</h2><p class="muted">Run the rig to populate the dashboard.</p>';
        return;
      }}
      renderOverview(experiment);
      renderPlot('active-plot', experiment, 'active_iotas', 'series-a');
      renderPlot('coherence-plot', experiment, 'largest_coherence', 'series-b');
      renderPlot('ratio-plot', experiment, 'coherence_ratio', 'series-b');
      renderPlot('entropy-plot', experiment, 'entropy', 'series-c');
      renderPlot('count-plot', experiment, 'coherence_count', 'series-b');
      renderDiffs(experiment);
      renderSnapshots(experiment);
      renderComparisonImages();
    }}

    render();
  </script>
</body>
</html>
"""


def save_dashboard(conn: sqlite3.Connection, output_root: Path) -> Path:
    dashboard_dir = output_root / "dashboard"
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    data = _load_dashboard_data(conn, output_root, dashboard_dir)
    dashboard_path = dashboard_dir / "index.html"
    dashboard_path.write_text(_html_shell(data), encoding="utf-8")
    return dashboard_path
