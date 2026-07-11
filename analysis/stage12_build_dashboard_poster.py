"""Stage 12 -- full deliverable QA: rebuild dashboard + poster from scratch.

Why this exists (2026-07-10): the previous dashboard/poster (archived under
dashboard/_archive, poster/_archive) predated the entire scope restructuring (still
referenced the dropped district-vulnerability index, Moran's I/Gi* spatial clustering, and
regional fertility clustering) AND independently violated this project's own standing
technical spec: 1.2 MB each (hard ceiling is 60 KB), with embedded base64 raster images
(spec requires vanilla JS + inline SVG only, no external JS, no base64 images). Both
problems are fixed by rebuilding from scratch against the current, narrowed manuscript
scope (21 national indicators, no spatial/district content) using only inline SVG charts
generated here and vanilla JS for the sortable table -- no matplotlib PNG/base64 anywhere
in the shipped HTML.

2026-07-11 update: restyled to adopt the project's bespoke visual design language (gradient
masthead/header, accent-bar KPI cards, numbered section badges, dark-mode support, gold
takeaway callout) extracted from `_system/bespoke/bespoke_dash_tmpl.html` and
`bespoke_poster_tmpl.html`. Those templates embed the full ECharts JS library (~1 MB each) to
achieve that look, which conflicts with this project's own <60 KB / vanilla-JS-only ceiling --
so only the CSS/HTML design tokens were ported, not the ECharts dependency. Chart rendering
stays inline SVG (trend_svg, margin_svg); data-encoding colours stay the Okabe-Ito palette
already used in the manuscript figures. Only chrome (headers, cards, footers) uses the bespoke
ink/gold/gradient tokens.
"""
import pandas as pd
import numpy as np
import datetime
BUILD_DATE = datetime.date.today().isoformat()

ROOT = r"C:\Users\VGhanem\Documents\Claude\Projects\Public Health & Epidemiology Research Skills\23. Disease Burden Forecasting Ghana"

fc = pd.read_csv(ROOT + r"\outputs\data\national_forecasts_2030.csv")
panel = pd.read_csv(ROOT + r"\data\processed\national_panel.csv")
margin = pd.read_csv(ROOT + r"\outputs\data\aicc_margin_vs_uniform111.csv").sort_values("delta_aicc")

# ---------- Palette (Okabe-Ito colourblind-safe, matches manuscript figures) ----------
BLUE = "#0072b2"
GREEN = "#009e73"
PINK = "#cc79a7"
ORANGE = "#d55e00"
GREY = "#555555"
BG = "#ffffff"

# ---------- Bespoke chrome tokens (headers/cards/footers only -- never used for data encoding) ----------
INK = "#16222e"
MUTED = "#5b6b7b"
PRIMARY = "#1a5276"
PRIMARY2 = "#3a93cf"
GOLD = "#d4a017"

LABELS = {
    "life_expectancy_birth_yrs_who": "Life expectancy (WHO-GHO), yrs",
    "hale_birth_yrs": "Healthy life expectancy, yrs",
    "u5mr_who": "Under-five mortality, per 1,000",
    "ncd_premature_pct": "NCD premature mortality, %",
    "ncd_3070_probability_pct": "NCD 30-70 death probability, %",
    "total_ncd_deaths": "Total NCD deaths, n",
    "suicide_rate_crude_who": "Suicide rate, crude (WHO-GHO)",
    "suicide_rate_agestd_who": "Suicide rate, age-std. (WHO-GHO)",
    "tb_incidence_per100k": "Tuberculosis incidence, per 100,000",
    "hiv_new_infections_n": "HIV new infections, n",
    "hiv_new_infections_per1000": "HIV new infections, per 1,000",
    "malaria_incidence_per1000atrisk": "Malaria incidence, per 1,000 at risk",
    "oop_pct_che": "Out-of-pocket exp., % of CHE",
    "oop_percapita_usd": "Out-of-pocket exp. per capita, USD",
    "che_pct_gdp": "Current health exp., % GDP (WHO-GHO)",
    "che_percapita_usd": "Current health exp. per capita, USD",
    "life_expectancy_birth_yrs_wb": "Life expectancy (World Bank), yrs",
    "suicide_rate_wb": "Suicide rate (World Bank)",
    "che_pct_gdp_wb": "Current health exp., % GDP (World Bank)",
    "tfr_national_wb": "Total fertility rate (World Bank)",
    "pm25_exposure_wb": "PM2.5 exposure (World Bank)",
}
ROW_ORDER = list(LABELS.keys())

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ---------- SVG chart 1: national trend, 3 small multiples (U5MR, TB, Malaria) ----------
def trend_svg():
    series_defs = [
        ("u5mr_who", "Under-five mortality (per 1,000 live births)", BLUE, 0, 0),
        ("tb_incidence_per100k", "Tuberculosis incidence (per 100,000)", GREEN, 1, 0),
        ("malaria_incidence_per1000atrisk", "Malaria incidence (per 1,000 at risk)", PINK, 2, 0),
    ]
    W, H = 720, 230
    panel_w, gap = 220, 30
    svg_parts = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="Arial, sans-serif">']
    svg_parts.append(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
    for i, (col, title, color, cx, cy) in enumerate(series_defs):
        ox = 10 + i * (panel_w + gap)
        oy = 20
        pw, ph = panel_w, 150
        s = panel[["year", col]].dropna().sort_values("year")
        years = s["year"].values
        vals = s[col].values
        row = fc[fc["indicator"] == col].iloc[0]
        last_year = years[-1]
        last_val = vals[-1]
        fc2030 = row["arima_2030"]
        all_y = list(vals) + [fc2030]
        ymin, ymax = min(all_y) * 0.92, max(all_y) * 1.08
        xmin, xmax = years[0], 2030
        def px(x): return ox + (x - xmin) / (xmax - xmin) * pw
        def py(y): return oy + ph - (y - ymin) / (ymax - ymin) * ph
        pts = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in zip(years, vals))
        svg_parts.append(f'<text x="{ox}" y="{oy-6}" font-size="11" font-weight="bold" fill="#222">{esc(title)}</text>')
        svg_parts.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.6"/>')
        svg_parts.append(f'<line x1="{px(last_year):.1f}" y1="{py(last_val):.1f}" x2="{px(2030):.1f}" y2="{py(fc2030):.1f}" '
                          f'stroke="{color}" stroke-width="1.6" stroke-dasharray="4,3"/>')
        svg_parts.append(f'<circle cx="{px(2030):.1f}" cy="{py(fc2030):.1f}" r="3" fill="{color}"/>')
        svg_parts.append(f'<text x="{px(2030)-4:.1f}" y="{py(fc2030)-8:.1f}" font-size="10" text-anchor="end" fill="{color}">{fc2030:,.1f}</text>')
        svg_parts.append(f'<line x1="{ox}" y1="{oy+ph}" x2="{ox+pw}" y2="{oy+ph}" stroke="#ccc" stroke-width="1"/>')
        svg_parts.append(f'<text x="{ox}" y="{oy+ph+14}" font-size="9" fill="#666">{int(years[0])}</text>')
        svg_parts.append(f'<text x="{ox+pw}" y="{oy+ph+14}" font-size="9" text-anchor="end" fill="#666">2030</text>')
    svg_parts.append("</svg>")
    return "".join(svg_parts)

# ---------- SVG chart 2: AICc margin, all 21 series, sorted, horizontal bars ----------
def margin_svg():
    W, H = 720, 460
    left_pad, right_pad, top_pad, bot_pad = 210, 40, 10, 25
    pw = W - left_pad - right_pad
    ph = H - top_pad - bot_pad
    n = len(margin)
    bar_h = ph / n * 0.7
    gap_h = ph / n
    maxv = margin["delta_aicc"].max()
    minv = min(0, margin["delta_aicc"].min())
    def px(v): return left_pad + (v - minv) / (maxv - minv) * pw
    svg = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="Arial, sans-serif">']
    svg.append(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
    thresh_x = px(2)
    svg.append(f'<line x1="{thresh_x:.1f}" y1="{top_pad}" x2="{thresh_x:.1f}" y2="{top_pad+ph}" stroke="#333" stroke-width="1" stroke-dasharray="3,2"/>')
    svg.append(f'<text x="{thresh_x+3:.1f}" y="{top_pad+10}" font-size="9" fill="#333">near-tie threshold (2)</text>')
    for i, (_, r) in enumerate(margin.iterrows()):
        y = top_pad + i * gap_h + (gap_h - bar_h) / 2
        color = BLUE if r["near_tie"] else ORANGE
        x0 = px(min(0, r["delta_aicc"]))
        w = abs(px(r["delta_aicc"]) - px(0))
        svg.append(f'<rect x="{x0:.1f}" y="{y:.1f}" width="{max(w,1):.1f}" height="{bar_h:.1f}" fill="{color}"/>')
        label = LABELS[r["indicator"]]
        svg.append(f'<text x="{left_pad-6}" y="{y+bar_h/2+3:.1f}" font-size="9" text-anchor="end" fill="#222">{esc(label)}</text>')
    svg.append(f'<text x="{left_pad}" y="{H-6}" font-size="10" fill="#444">AICc difference vs. uniform ARIMA(1,1,1)</text>')
    legend_y = top_pad + 8
    svg.append(f'<rect x="{W-right_pad-14}" y="{legend_y}" width="10" height="10" fill="{BLUE}"/>')
    svg.append(f'<text x="{W-right_pad-18}" y="{legend_y+9}" font-size="8" text-anchor="end" fill="#222">Near-tie</text>')
    svg.append(f'<rect x="{W-right_pad-14}" y="{legend_y+14}" width="10" height="10" fill="{ORANGE}"/>')
    svg.append(f'<text x="{W-right_pad-18}" y="{legend_y+23}" font-size="8" text-anchor="end" fill="#222">Decisive</text>')
    svg.append("</svg>")
    return "".join(svg)

TREND_SVG = trend_svg()
MARGIN_SVG = margin_svg()

# ---------- shared table HTML (Table 1 content) ----------
def table_rows_html():
    rows = []
    for ind in ROW_ORDER:
        d = fc[fc["indicator"] == ind].iloc[0]
        is_count = ind in ("total_ncd_deaths", "hiv_new_infections_n")
        conf = "Standard" if d["confidence"].strip().lower() == "standard" else "Low"
        def f(v):
            return f"{v:,.0f}" if is_count else f"{v:,.2f}"
        rows.append(
            f'<tr><td>{esc(LABELS[ind])}</td><td>{int(d["n_obs"])}</td><td>{int(d["last_year"])}</td>'
            f'<td>{esc(d["arima_order"])}</td><td>{f(d["last_value"])}</td><td>{f(d["arima_2030"])}</td>'
            f'<td>{f(d["arima_ci_low"])}–{f(d["arima_ci_high"])}</td><td>{f(d["ets_2030"])}</td>'
            f'<td><span class="tag {"std" if conf=="Standard" else "low"}">{conf}</span></td></tr>'
        )
    return "".join(rows)

TABLE_ROWS = table_rows_html()
print(f"TREND_SVG size: {len(TREND_SVG)/1024:.1f} KB | MARGIN_SVG size: {len(MARGIN_SVG)/1024:.1f} KB | TABLE_ROWS size: {len(TABLE_ROWS)/1024:.1f} KB")

n_standard = (fc["confidence"].str.strip().str.lower() == "standard").sum()
n_low = len(fc) - n_standard
low_rows = fc[fc["confidence"].str.strip().str.lower() != "standard"]
low_n_min, low_n_max = int(low_rows["n_obs"].min()), int(low_rows["n_obs"].max())
malaria_row = fc[fc["indicator"] == "malaria_incidence_per1000atrisk"].iloc[0]
u5mr_row = fc[fc["indicator"] == "u5mr_who"].iloc[0]
tb_row = fc[fc["indicator"] == "tb_incidence_per100k"].iloc[0]

sens = pd.read_csv(ROOT + r"\outputs\data\arima_order_sensitivity.csv")
n_matched_111 = (sens["matches_111"].astype(str).str.strip().str.lower() == "true").sum()
n_near_tie = (margin["near_tie"].astype(str).str.strip().str.lower() == "true").sum()

# Structural-break sensitivity (Table 5) -- read live, not hardcoded, so the dashboard/poster
# can never silently drift from the manuscript's own verified structural-break numbers.
sb = pd.read_csv(ROOT + r"\outputs\data\structural_break_sensitivity.csv")
sb_malaria = sb[sb["indicator"] == "malaria_incidence_per1000atrisk"].iloc[0]
sb_lifeexp_wb = sb[sb["indicator"] == "life_expectancy_birth_yrs_wb"].iloc[0]
n_covid_testable = (sb["covid_2020_testable"].astype(str).str.strip().str.lower() == "true").sum()
n_covid_decisive = (sb.loc[sb["covid_2020_testable"].astype(str).str.strip().str.lower() == "true", "covid_2020_delta_aicc"].astype(float) > 2).sum()
n_currency_testable = (sb["currency_2022_testable"].astype(str).str.strip().str.lower() == "true").sum()
n_currency_decisive = (sb.loc[sb["currency_2022_testable"].astype(str).str.strip().str.lower() == "true", "currency_2022_delta_aicc"].astype(float) > 2).sum()

# Pre-correction (raw-scale, uniform ARIMA(1,1,1)) malaria baseline -- recomputed live, not
# hardcoded, so this figure can never silently drift from the manuscript's own verified number.
import warnings
warnings.filterwarnings("ignore")
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
_mal = panel[["year", "malaria_incidence_per1000atrisk"]].dropna().sort_values("year")
_y = _mal["malaria_incidence_per1000atrisk"].values
_steps = 2030 - int(_mal["year"].max())
_arima_raw_111 = ARIMA(_y, order=(1, 1, 1)).fit().get_forecast(steps=_steps).predicted_mean[-1]
_ets_raw = ExponentialSmoothing(_y, trend="add", damped_trend=True).fit().forecast(_steps)[-1]
malaria_gap_before_pct = abs(_arima_raw_111 - _ets_raw) / _ets_raw * 100
malaria_gap_after_pct = abs(malaria_row["arima_2030"] - malaria_row["ets_2030"]) / malaria_row["ets_2030"] * 100

# ============================================================
# DASHBOARD
# ============================================================
DASHBOARD_HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ghana Burden Forecasting 2030 — Dashboard &amp; Source-Provenance Audit</title>
<style>
  :root {{
    --primary: {PRIMARY}; --primary2: {PRIMARY2}; --gold: {GOLD}; --ink: {INK};
    --bg: #f4f6f8; --card: #ffffff; --text: {INK}; --muted: {MUTED}; --border: #dde3e8;
  }}
  [data-theme="dark"] {{
    --bg: #0f1720; --card: #182430; --text: #e7edf3; --muted: #93a3b3; --border: #2a3949;
  }}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; transition: none !important; }} }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font-family: -apple-system, "Segoe UI", Arial, sans-serif; background:var(--bg); color:var(--text); transition: background .2s, color .2s; }}
  header.top {{
    background: linear-gradient(135deg, var(--primary), var(--primary2));
    color:#fff; padding:26px 28px; position:relative; overflow:hidden;
  }}
  header.top .brand {{
    position:absolute; top:20px; right:28px; background:rgba(255,255,255,0.16);
    border:1px solid rgba(255,255,255,0.4); border-radius:999px; padding:5px 14px;
    font-size:0.7rem; font-weight:700; letter-spacing:0.06em; text-transform:uppercase;
  }}
  header.top h1 {{ margin:0 160px 6px 0; font-size:1.35rem; line-height:1.3; max-width:900px; }}
  header.top p {{ margin:0; font-size:0.85rem; opacity:0.92; }}
  .toolbar {{
    max-width:1100px; margin:0 auto; padding:14px 20px 0; display:flex; gap:10px;
    align-items:center; flex-wrap:wrap; font-size:0.82rem;
  }}
  .toolbar input#search {{ padding:7px 12px; border:1px solid var(--border); border-radius:6px; font-size:0.82rem; width:220px; background:var(--card); color:var(--text); }}
  .toolbar button {{
    padding:7px 12px; border:1px solid var(--border); border-radius:6px; background:var(--card);
    color:var(--text); font-size:0.78rem; cursor:pointer; font-weight:600;
  }}
  .toolbar button:hover {{ border-color:var(--primary); color:var(--primary); }}
  .toolbar button:focus-visible, .toolbar input#search:focus-visible {{ outline:2px solid var(--primary2); outline-offset:1px; }}
  main {{ max-width:1100px; margin:0 auto; padding:18px 20px 20px; }}
  .kpi-row {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:14px; margin-bottom:20px; }}
  .kpi {{ background:var(--card); border:1px solid var(--border); border-left:4px solid var(--kc, var(--primary)); border-radius:8px; padding:14px 16px; }}
  .kpi .label {{ font-size:0.72rem; color:var(--muted); text-transform:uppercase; letter-spacing:0.03em; }}
  .kpi .value {{ font-size:1.5rem; font-weight:700; margin-top:4px; }}
  .kpi .delta {{ font-size:0.78rem; color:var(--muted); margin-top:2px; }}
  .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:20px; }}
  @media (max-width:800px) {{
    .grid {{ grid-template-columns:1fr; }}
    header.top h1 {{ margin-right:0; }}
    header.top .brand {{ position:static; display:inline-block; margin-top:10px; }}
  }}
  .card {{ background:var(--card); border:1px solid var(--border); border-radius:10px; padding:16px; }}
  .card h2 {{ margin:0 0 10px; font-size:1rem; color:var(--primary); }}
  [data-theme="dark"] .card h2 {{ color:var(--primary2); }}
  .card p.note {{ font-size:0.78rem; color:var(--muted); margin:8px 0 0; }}
  table {{ width:100%; border-collapse:collapse; font-size:0.82rem; }}
  th, td {{ padding:6px 8px; text-align:left; border-bottom:1px solid var(--border); }}
  th {{ cursor:pointer; user-select:none; background:var(--bg); position:sticky; top:0; white-space:nowrap; }}
  th:hover {{ color:var(--primary); }}
  td:nth-child(2), td:nth-child(3), td:nth-child(5), td:nth-child(6), td:nth-child(7), td:nth-child(8) {{ text-align:right; font-variant-numeric: tabular-nums; }}
  .tag {{ padding:2px 8px; border-radius:10px; font-size:0.72rem; font-weight:600; }}
  .tag.std {{ background:#e3f2ec; color:{GREEN}; }}
  .tag.low {{ background:#fdecec; color:#b3261e; }}
  .table-wrap {{ max-height:520px; overflow:auto; border:1px solid var(--border); border-radius:8px; }}
  footer {{ max-width:1100px; margin:0 auto; padding:16px 20px 40px; font-size:0.78rem; color:var(--muted); }}
  a {{ color:var(--primary); }}
  [data-theme="dark"] a {{ color:var(--primary2); }}
</style>
</head>
<body>
<header class="top">
  <span class="brand">Reproducible workflow · Ghana 2030</span>
  <h1>A Reproducible Workflow and Source-Provenance Audit for Forecasting Short National Health-Indicator Panels: A Worked Example from Ghana</h1>
  <p>25 indicators assembled, 21 forecastable · 6 documented data-integrity corrections · last rebuilt {BUILD_DATE}</p>
</header>
<div class="toolbar">
  <input id="search" type="text" placeholder="Filter indicator…" onkeyup="filterTable()" aria-label="Filter indicator">
  <button onclick="exportCSV()" aria-label="Export table as CSV">Export CSV</button>
  <button onclick="resetView()" aria-label="Reset filters and sorting">Reset</button>
  <button onclick="toggleTheme()" aria-label="Toggle dark mode">Toggle theme</button>
</div>
<main>
  <div class="kpi-row">
    <div class="kpi" style="--kc:{BLUE}"><div class="label">Documented corrections</div><div class="value">6</div><div class="delta">source-provenance pitfalls fixed (Table 1)</div></div>
    <div class="kpi" style="--kc:{GREEN}"><div class="label">Under-five mortality, 2030</div><div class="value">{u5mr_row['arima_2030']:.1f}</div><div class="delta">per 1,000 live births · SDG 3.2 target: 25</div></div>
    <div class="kpi" style="--kc:{PINK}"><div class="label">Order-selection near-ties</div><div class="value">{n_near_tie} / 21</div><div class="delta">uniform ARIMA(1,1,1) not decisively rejected</div></div>
    <div class="kpi" style="--kc:{ORANGE}"><div class="label">Structural breaks found</div><div class="value">malaria, WB life exp.</div><div class="delta">decisive: {n_covid_decisive} of {n_covid_testable} testable (COVID-2020), {n_currency_decisive} of {n_currency_testable} (currency-2022)</div></div>
    <div class="kpi" style="--kc:#7d3c98"><div class="label">Forecasting method</div><div class="value">ARIMA + ETS</div><div class="delta">LSTM did not outperform (walk-forward validated)</div></div>
  </div>

  <div class="card">
    <h2>Source-provenance audit: six silent data-integrity pitfalls (Table 1)</h2>
    <p class="note">The reusable contribution of this analysis is the workflow and these named pitfalls, not the Ghana-specific forecasts below. Each corrects a WHO GHO/World Bank export issue that produces output that looks correct and is not.</p>
    <table>
      <thead><tr><th>Source file / series</th><th>Pitfall</th><th>Correction applied</th></tr></thead>
      <tbody>
        <tr><td>All WHO GHO/GHE exports</td><td>Leading hashtag (HXL) metadata row breaks numeric coercion</td><td>Drop HXL row before numeric coercion</td></tr>
        <tr><td>Under-five mortality rate</td><td>Wealth-quintile stratification presents as year-level duplication</td><td>Retained national-total series; did not average across quintiles</td></tr>
        <tr><td>Air-pollution indicators (2 series)</td><td>Cause-of-death sub-category stratification presents as year-level duplication</td><td>Retained per-year maximum (all-causes total), not sum or average</td></tr>
        <tr><td>Crude suicide rate, 2021</td><td>Recurring WHO GHO export anomaly (36 rows vs. expected 3)</td><td>Retained only confidence-interval-bearing rows</td></tr>
        <tr><td>WHS compendium + consolidated GHO export</td><td>Near-total re-exports of the disease-specific source files</td><td>Used as internal consistency checks only, never merged as new observations</td></tr>
        <tr><td>Current health exp. (% GDP): WHO-GHO vs. World Bank</td><td>Two &quot;sources&quot; numerically identical to several decimal places</td><td>Flagged non-independent; excluded from cross-source validation claims</td></tr>
      </tbody>
    </table>
  </div>

  <div class="grid">
    <div class="card">
      <h2>National indicator trends and 2030 forecasts</h2>
      {TREND_SVG}
      <p class="note">Dashed segment: ARIMA point forecast to 2030. Full methodology in the manuscript (Figure 1).</p>
    </div>
    <div class="card">
      <h2>Order-selection sensitivity, all 21 series</h2>
      {MARGIN_SVG}
      <p class="note">AICc difference between each series' own selected order and a uniform ARIMA(1,1,1) refit. Only {n_matched_111} of 21 series matched the uniform order exactly; {n_near_tie} of 21 were statistical near-ties (manuscript Table 4).</p>
    </div>
  </div>

  <div class="card">
    <h2>Structural-break sensitivity</h2>
    <p class="note">Testing rather than assuming away the 2020 COVID-19 and 2022 Ghana currency-crisis breaks: a decisive currency-crisis break shifts the malaria 2030 forecast by a further {sb_malaria['currency_2022_pct_change_2030']:+.1f}% (larger than the order-selection effect above), and a decisive break at both candidate dates is found for the World Bank life-expectancy series -- a plausible partial explanation for its divergence from the WHO-GHO life-expectancy series, not a resolved causal account. Most series' break tests are underpowered on 2–5 post-break observations (manuscript Table 5).</p>
  </div>

  <div class="card">
    <h2>Full forecast table</h2>
    <div class="table-wrap">
    <table id="fctable">
      <thead><tr>
        <th onclick="sortTable(0)">Indicator</th>
        <th onclick="sortTable(1)">n</th>
        <th onclick="sortTable(2)">Last year</th>
        <th onclick="sortTable(3)">ARIMA order</th>
        <th onclick="sortTable(4)">Last value</th>
        <th onclick="sortTable(5)">ARIMA 2030</th>
        <th>95% CI</th>
        <th onclick="sortTable(7)">ETS 2030</th>
        <th onclick="sortTable(8)">Confidence</th>
      </tr></thead>
      <tbody>{TABLE_ROWS}</tbody>
    </table>
    </div>
  </div>
</main>
<footer>
  Source data: WHO Global Health Observatory / Global Health Estimates and World Bank World Development Indicators (public-domain, aggregate, de-identified).
  Methodology, full citations, and limitations: see manuscript. Repository:
  <a href="https://github.com/valentineghanem-bit/disease-burden-forecasting-ghana" target="_blank" rel="noopener">disease-burden-forecasting-ghana</a>.
</footer>
<script>
(function() {{
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {{
    document.documentElement.setAttribute('data-theme', 'dark');
  }}
}})();
function toggleTheme() {{
  const html = document.documentElement;
  html.setAttribute('data-theme', html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
}}
function filterTable() {{
  const q = document.getElementById('search').value.toLowerCase();
  document.querySelectorAll('#fctable tbody tr').forEach(function(row) {{
    row.style.display = row.cells[0].textContent.toLowerCase().includes(q) ? '' : 'none';
  }});
}}
let sortDir = {{}};
function sortTable(colIdx) {{
  const tbody = document.querySelector('#fctable tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  const dir = sortDir[colIdx] = !sortDir[colIdx];
  rows.sort(function(a, b) {{
    let x = a.cells[colIdx].textContent.trim();
    let y = b.cells[colIdx].textContent.trim();
    const xn = parseFloat(x.replace(/,/g, '')), yn = parseFloat(y.replace(/,/g, ''));
    if (!isNaN(xn) && !isNaN(yn)) {{ x = xn; y = yn; }}
    if (x < y) return dir ? -1 : 1;
    if (x > y) return dir ? 1 : -1;
    return 0;
  }});
  rows.forEach(function(r) {{ tbody.appendChild(r); }});
}}
const ORIGINAL_ROWS = document.querySelector('#fctable tbody').innerHTML;
function resetView() {{
  document.getElementById('search').value = '';
  document.querySelector('#fctable tbody').innerHTML = ORIGINAL_ROWS;
  sortDir = {{}};
}}
function exportCSV() {{
  const headerCells = Array.from(document.querySelectorAll('#fctable thead tr:last-child th'));
  const header = headerCells.map(function(th) {{ return '"' + th.textContent.trim().replace(/"/g, '""') + '"'; }});
  const rows = Array.from(document.querySelectorAll('#fctable tbody tr')).filter(function(r) {{ return r.style.display !== 'none'; }});
  const lines = [header.join(',')];
  rows.forEach(function(row) {{
    const cells = Array.from(row.cells).map(function(td) {{ return '"' + td.textContent.trim().replace(/"/g, '""') + '"'; }});
    lines.push(cells.join(','));
  }});
  const blob = new Blob([lines.join('\\n')], {{ type: 'text/csv' }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'ghana_forecast_2030_table.csv';
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  URL.revokeObjectURL(url);
}}
</script>
</body>
</html>
"""

with open(ROOT + r"\dashboard\Ghana_BurdenForecasting2030_Dashboard.html", "w", encoding="utf-8") as f:
    f.write(DASHBOARD_HTML)
print(f"Dashboard written: {len(DASHBOARD_HTML)/1024:.1f} KB")

# ============================================================
# POSTER (condensed table: top 8 rows by data-availability tier, representative spread)
# ============================================================
POSTER_ROW_ORDER = ["u5mr_who", "tb_incidence_per100k", "malaria_incidence_per1000atrisk",
    "hiv_new_infections_per1000", "life_expectancy_birth_yrs_who", "life_expectancy_birth_yrs_wb",
    "tfr_national_wb", "oop_pct_che"]

def poster_table_rows():
    rows = []
    for ind in POSTER_ROW_ORDER:
        d = fc[fc["indicator"] == ind].iloc[0]
        is_count = ind in ("total_ncd_deaths", "hiv_new_infections_n")
        conf = "Standard" if d["confidence"].strip().lower() == "standard" else "Low"
        def f(v):
            return f"{v:,.0f}" if is_count else f"{v:,.1f}"
        rows.append(f'<tr><td>{esc(LABELS[ind])}</td><td>{f(d["last_value"])}</td><td>{f(d["arima_2030"])}</td>'
                     f'<td>{f(d["ets_2030"])}</td><td><span class="tag {"std" if conf=="Standard" else "low"}">{conf}</span></td></tr>')
    return "".join(rows)

POSTER_TABLE_ROWS = poster_table_rows()

POSTER_HTML = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Ghana Burden Forecasting 2030 — Poster</title>
<style>
  :root {{
    --primary:{PRIMARY}; --primary2:{PRIMARY2}; --gold:{GOLD}; --ink:{INK}; --muted:{MUTED};
    --border:#dde1e6; --card:#f7f8fa;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family: Georgia, 'Times New Roman', serif; background:#fff; color:var(--ink); }}
  .poster {{ max-width:1400px; margin:0 auto; }}
  .masthead {{
    background: linear-gradient(135deg, var(--primary), var(--primary2));
    color:#fff; padding:26px 36px 22px;
  }}
  .masthead .kicker {{ font-family:Arial, sans-serif; font-size:0.75rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; opacity:0.85; margin-bottom:6px; }}
  .masthead h1 {{ margin:0; font-size:2rem; line-height:1.25; }}
  .masthead .authors {{ font-size:1.05rem; margin-top:10px; }}
  .masthead .affil {{ font-size:0.9rem; opacity:0.9; margin-top:2px; }}
  .masthead .badges {{ margin-top:12px; display:flex; gap:8px; flex-wrap:wrap; font-family:Arial, sans-serif; }}
  .masthead .badges span {{ background:rgba(255,255,255,0.16); border:1px solid rgba(255,255,255,0.4); border-radius:999px; padding:3px 11px; font-size:0.68rem; font-weight:600; }}
  .hook {{ background:var(--ink); color:#fff; font-family:Arial, sans-serif; font-size:1.05rem; font-weight:700; padding:12px 36px; line-height:1.4; }}
  .body-wrap {{ padding:22px 36px 0; }}
  .cols {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:26px; }}
  @media (max-width:1000px) {{ .cols {{ grid-template-columns:1fr; }} }}
  section {{ margin-bottom:18px; }}
  h2 {{ font-family: Arial, sans-serif; font-size:1.02rem; color:var(--primary); border-bottom:2px solid var(--border); padding-bottom:5px; margin:0 0 8px; display:flex; align-items:center; gap:8px; }}
  h2 .n {{
    display:inline-flex; align-items:center; justify-content:center; width:22px; height:22px;
    border-radius:50%; background:var(--primary); color:#fff; font-size:0.72rem; font-weight:700; flex:none;
  }}
  p {{ font-size:0.92rem; line-height:1.45; margin:0 0 10px; }}
  .kpi-strip {{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:16px; }}
  .kpi {{ font-family: Arial, sans-serif; background:var(--card); border:1px solid var(--border); border-bottom:3px solid var(--kc, var(--primary)); border-radius:8px; padding:10px 14px; flex:1; min-width:150px; }}
  .kpi .v {{ font-size:1.35rem; font-weight:700; color:var(--primary); }}
  .kpi .l {{ font-size:0.68rem; text-transform:uppercase; color:var(--muted); }}
  table {{ width:100%; border-collapse:collapse; font-family: Arial, sans-serif; font-size:0.78rem; }}
  th, td {{ padding:5px 6px; border-bottom:1px solid var(--border); text-align:left; }}
  td:nth-child(2), td:nth-child(3), td:nth-child(4) {{ text-align:right; font-variant-numeric: tabular-nums; }}
  th {{ background:var(--card); }}
  .tag {{ padding:1px 7px; border-radius:8px; font-size:0.68rem; font-weight:600; }}
  .tag.std {{ background:#e3f2ec; color:{GREEN}; }}
  .tag.low {{ background:#fdecec; color:#b3261e; }}
  .takeaway {{
    font-family: Arial, sans-serif; background:#fdf6e3; border:1px solid var(--gold); border-left:5px solid var(--gold);
    border-radius:6px; padding:14px 18px; margin:6px 36px 18px;
  }}
  .takeaway .lbl {{ font-size:0.68rem; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; color:var(--gold); margin-bottom:4px; }}
  .takeaway p {{ margin:0; font-size:0.92rem; }}
  footer {{
    font-family: Arial, sans-serif; font-size:0.75rem; color:#fff;
    background: linear-gradient(135deg, var(--ink), var(--primary));
    padding:16px 36px; display:flex; justify-content:space-between; align-items:center; gap:16px; flex-wrap:wrap;
  }}
  footer a {{ color:#bfe0f5; }}
  .figcap {{ font-family: Arial, sans-serif; font-size:0.72rem; color:var(--muted); margin-top:4px; }}
  .repo-box {{ font-family: Arial, sans-serif; text-align:center; border:1px solid rgba(255,255,255,0.4); border-radius:8px; padding:8px 14px; }}
  .repo-box .label {{ font-size:0.68rem; opacity:0.85; margin-bottom:2px; }}
  @page {{ size: A0 portrait; margin: 15mm; }}
  @media print {{
    body {{ background:#fff; }}
    .poster {{ max-width:none; }}
    section {{ break-inside: avoid; }}
    .cols {{ grid-template-columns:1fr 1fr 1fr !important; }}
    a {{ color:inherit; text-decoration:none; }}
  }}
</style>
</head>
<body>
<div class="poster">
  <div class="masthead">
    <div class="kicker">Reproducible workflow · Methods paper</div>
    <h1>A Reproducible Workflow and Source-Provenance Audit for Forecasting Short National Health-Indicator Panels: A Worked Example from Ghana</h1>
    <div class="authors">Valentine Golden Ghanem</div>
    <div class="affil">Ghana COCOBOD Cocoa Clinic, Accra, Ghana · ORCID 0009-0002-8332-0220</div>
    <div class="badges"><span>STROBE reporting</span><span>MIT-licensed code</span><span>Public-domain data</span><span>Open repository</span></div>
  </div>

  <div class="hook">Only 1 of 21 national indicators matched a uniform ARIMA(1,1,1) order — order selection is not a formality, and a decisive currency-crisis structural break moved the malaria forecast further than order selection did.</div>

  <div class="body-wrap">
  <div class="kpi-strip">
    <div class="kpi" style="--kc:{BLUE}"><div class="v">6</div><div class="l">Documented source-provenance corrections (Table 1)</div></div>
    <div class="kpi" style="--kc:{GREEN}"><div class="v">{u5mr_row['arima_2030']:.1f} / 1,000</div><div class="l">Under-5 mortality, 2030 (SDG target: 25)</div></div>
    <div class="kpi" style="--kc:{PINK}"><div class="v">{n_matched_111} of 21</div><div class="l">Series where uniform (1,1,1) matched exactly</div></div>
    <div class="kpi" style="--kc:{ORANGE}"><div class="v">{n_near_tie} of 21</div><div class="l">Order-selection near-ties (ΔAICc &lt; 2)</div></div>
    <div class="kpi" style="--kc:#7d3c98"><div class="v">malaria, WB life exp.</div><div class="l">Decisive structural breaks found (Table 5)</div></div>
  </div>

  <div class="cols">
    <div>
      <section>
        <h2><span class="n">1</span>Background</h2>
        <p>Public-domain WHO Global Health Observatory (GHO) and World Bank exports are the default empirical basis for national health-indicator forecasting, but these files carry undocumented structural pitfalls that silently corrupt an analysis if uncorrected, and forecasting choices — method, model order, fitting scale — are typically made ad hoc and per-indicator with no shared, reproducible protocol. Existing Ghana-specific forecasting work is disease- or indicator-specific, each selecting its own method and order independently without a protocol another analyst could reuse.</p>
      </section>
      <section>
        <h2><span class="n">2</span>Methods</h2>
        <p>A national indicator panel (21 forecastable series of 25 assembled, from 9 public-domain WHO/World Bank sources, individual series ranging 22–92 years) was built and audited for source-provenance pitfalls. LSTM neural networks were evaluated against classical methods (exponential smoothing, ARIMA) via multi-seed, multi-architecture walk-forward validation on two representative series; each series' ARIMA order was then selected by an AICc grid search rather than applied uniformly, and a structural-break sensitivity test was run for the 2020 COVID-19 and 2022 Ghana currency-crisis candidate breaks.</p>
      </section>
      <section>
        <h2><span class="n">3</span>Order-selection sensitivity</h2>
        {MARGIN_SVG.replace('width="720" height="460"', 'width="100%" height="380"').replace('viewBox="0 0 720 460"', 'viewBox="0 0 720 460" preserveAspectRatio="xMidYMid meet"')}
        <p class="figcap">AICc difference vs. a uniform ARIMA(1,1,1), all 21 series. Order mismatch was not concentrated among the shortest series — under-five mortality (n=92, the longest series) shows the largest correction.</p>
      </section>
    </div>

    <div>
      <section>
        <h2><span class="n">4</span>National forecast trends</h2>
        {TREND_SVG.replace('width="720" height="230"', 'width="100%" height="230"').replace('viewBox="0 0 720 230"', 'viewBox="0 0 720 230" preserveAspectRatio="xMidYMid meet"')}
        <p class="figcap">Historical trend (solid) and 2030 ARIMA point forecast (dashed) for three headline indicators.</p>
      </section>
      <section>
        <h2><span class="n">5</span>Key results</h2>
        <p><b>Under-five mortality</b> is projected to decline to {u5mr_row['arima_2030']:.1f} per 1,000 live births by 2030 (95% CI {u5mr_row['arima_ci_low']:.1f}–{u5mr_row['arima_ci_high']:.1f}), narrowly missing the SDG 3.2 target of 25.</p>
        <p><b>Malaria incidence</b>: an earlier uniform-order specification produced a {malaria_gap_before_pct:.0f}% ARIMA-vs-ETS disagreement ({_arima_raw_111:.1f} vs. {_ets_raw:.1f}, illustrative pre-correction figures, raw scale); refitting with the series' own AICc-selected order narrowed this to {malaria_gap_after_pct:.0f}% ({malaria_row['arima_2030']:.1f} vs. {malaria_row['ets_2030']:.1f}, final production forecast) — most of that narrower gap was a specification artefact, not a genuine model conflict. A decisive 2022 currency-crisis structural break shifts this series' forecast by a further {sb_malaria['currency_2022_pct_change_2030']:+.1f}%, a larger effect than the order-selection correction (Table 5).</p>
        <p><b>Classical methods beat LSTM</b> on both series tested in walk-forward validation (MAPE 0.18–0.29% for ETS/ARIMA vs. 2.3–14.1% for LSTM); LSTM was excluded from the forecasting roster.</p>
        <p><b>Life expectancy</b>: WHO-GHO projects a decline to 64.8 years by 2030 while the independently-sourced World Bank series projects a small increase to 67.6 years; a decisive structural break is found for the World Bank series at both 2020 and 2022, so this divergence is plausibly break-driven in part, not a settled two-source disagreement.</p>
      </section>
    </div>

    <div>
      <section>
        <h2><span class="n">6</span>Selected forecasts (full 21-series data underlying manuscript Figure 3)</h2>
        <table>
          <thead><tr><th>Indicator</th><th>Last value</th><th>ARIMA 2030</th><th>ETS 2030</th><th>Conf.</th></tr></thead>
          <tbody>{POSTER_TABLE_ROWS}</tbody>
        </table>
      </section>
      <section>
        <h2><span class="n">7</span>Limitations</h2>
        <p>Ecological analysis throughout; no individual-level data. LSTM-vs-classical validation tested on only 2 of 21 series. {n_low} of 21 series are low-confidence ({low_n_min}–{low_n_max} years). Structural-break tests were run for all testable series, but most had only 2–5 post-break observations — genuinely underpowered for reliably detecting a level shift, so decisive findings (malaria, World Bank life expectancy) should be read as suggestive, not confirmatory. Routine surveillance completeness in Ghana varies sharply by disease domain in facility-level audits, lowest for malaria (~25% in some years) -- bounding the malaria forecast's external validity most acutely. Findings are specific to Ghana.</p>
      </section>
      <section>
        <h2><span class="n">8</span>Conclusion</h2>
        <p>The contribution is a reusable, documented workflow and a named set of source-specific pitfalls, not novelty in order selection itself. Researchers reproducing national-indicator forecasts from these sources can adopt the workflow directly; the Ghana-specific forecasts illustrate it and are not offered as planning inputs.</p>
      </section>
    </div>
  </div>
  </div>

  <div class="takeaway">
    <div class="lbl">Takeaway for reproducers</div>
    <p>The reusable output here is the audit trail and the protocol, not the Ghana-specific numbers: six named WHO/World Bank export pitfalls, an AICc order-search step, and a structural-break check were each enough on their own to change a 2030 forecast by more than the reported margin of error — worth checking before any of these figures reach a policy table.</p>
  </div>

  <footer>
    <div>
    Data: WHO Global Health Observatory / Global Health Estimates; World Bank World Development Indicators (public-domain, aggregate, de-identified — no ethics approval required).
    No competing interests. No funding declared.
    </div>
    <div class="repo-box">
      <div class="label">Code &amp; data</div>
      <a href="https://github.com/valentineghanem-bit/disease-burden-forecasting-ghana">github.com/valentineghanem-bit/<br>disease-burden-forecasting-ghana</a>
    </div>
  </footer>
</div>
</body>
</html>
"""

with open(ROOT + r"\poster\Ghana_BurdenForecasting2030_Poster.html", "w", encoding="utf-8") as f:
    f.write(POSTER_HTML)
print(f"Poster written: {len(POSTER_HTML)/1024:.1f} KB")
