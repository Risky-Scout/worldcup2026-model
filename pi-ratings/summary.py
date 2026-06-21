"""
HTML summary report generator for Pi Ratings predictions.

Produces summary_YYYY-MM-DD.html — a self-contained HTML file (no external deps)
with one section per match:
  - Match header with teams, kickoff, Pi composite ratings, lambdas
  - Core probabilities table (1X2, BTTS, O/U, Asian HCP) at 4 decimal places
  - Top 10 scorelines table
  - Collapsible full market dump
  - Calculation trail (every formula with substituted values)

Usage:
    from summary import write_summary
    write_summary(predictions, calibration_state, output_dir)
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from predict_matches import PiMatchPrediction
    from calibrate import CalibrationState


_CSS = """
body { font-family: 'Segoe UI', Arial, sans-serif; background:#f4f6f8; color:#222; margin:0; padding:20px; }
h1 { color:#1a237e; border-bottom:3px solid #1a237e; padding-bottom:8px; }
h2 { color:#1565c0; margin-top:32px; border-left:4px solid #1565c0; padding-left:10px; }
.match-card { background:#fff; border-radius:8px; box-shadow:0 2px 6px rgba(0,0,0,.1);
              margin-bottom:28px; padding:20px; }
.match-header { display:flex; align-items:center; gap:20px; flex-wrap:wrap; }
.team-name { font-size:1.3em; font-weight:700; }
.vs { font-size:1em; color:#666; }
.meta { color:#555; font-size:0.88em; margin-top:6px; }
table { border-collapse:collapse; width:100%; margin:10px 0; }
th { background:#1565c0; color:#fff; padding:6px 10px; text-align:left; font-size:0.88em; }
td { padding:5px 10px; border-bottom:1px solid #e8ecf0; font-size:0.88em; }
tr:hover td { background:#f0f4ff; }
.prob-high { color:#1b5e20; font-weight:700; }
.prob-med  { color:#e65100; }
.prob-low  { color:#b71c1c; }
details summary { cursor:pointer; color:#1565c0; font-weight:600; margin:8px 0; }
details { background:#f8f9fc; border:1px solid #dde; border-radius:4px; padding:8px 12px; }
.audit-step { background:#fff8e1; border-left:3px solid #f9a825; padding:8px 12px;
              margin:6px 0; border-radius:0 4px 4px 0; font-family:monospace; font-size:0.85em; }
.footer { color:#888; font-size:0.82em; margin-top:40px; border-top:1px solid #ddd; padding-top:12px; }
.grid-sum-ok { color:#1b5e20; font-weight:600; }
"""


def _pct_class(p: float) -> str:
    if p >= 0.50:
        return "prob-high"
    if p >= 0.25:
        return "prob-med"
    return "prob-low"


def _fmt(p: float) -> str:
    return f"{p:.4f}"


def _market_row(label: str, value) -> str:
    if isinstance(value, float):
        css = _pct_class(value)
        return f'<tr><td>{label}</td><td class="{css}">{_fmt(value)}</td></tr>'
    return f"<tr><td>{label}</td><td>{value}</td></tr>"


def _render_match(pred: "PiMatchPrediction", idx: int) -> str:
    m = pred.markets
    at = pred  # shorthand

    # Core probability display lines
    core_rows = [
        ("Home Win",         m.get("home_win", 0.0)),
        ("Draw",             m.get("draw", 0.0)),
        ("Away Win",         m.get("away_win", 0.0)),
        ("BTTS Yes",         m.get("btts_yes", 0.0)),
        ("BTTS No",          m.get("btts_no", 0.0)),
        ("Over 1.5",         m.get("over_1_5", 0.0)),
        ("Under 1.5",        m.get("under_1_5", 0.0)),
        ("Over 2.5",         m.get("over_2_5", 0.0)),
        ("Under 2.5",        m.get("under_2_5", 0.0)),
        ("Over 3.5",         m.get("over_3_5", 0.0)),
        ("Under 3.5",        m.get("under_3_5", 0.0)),
        ("Double Chance 1X", m.get("double_chance_1x", 0.0)),
        ("Double Chance X2", m.get("double_chance_x2", 0.0)),
        ("DNB Home",         m.get("draw_no_bet_home", 0.0)),
        ("DNB Away",         m.get("draw_no_bet_away", 0.0)),
        ("Win to Nil Home",  m.get("win_to_nil_home", 0.0)),
        ("Win to Nil Away",  m.get("win_to_nil_away", 0.0)),
        ("Clean Sheet Home", m.get("clean_sheet_home", 0.0)),
        ("Clean Sheet Away", m.get("clean_sheet_away", 0.0)),
        ("xPts Home",        m.get("expected_points_home", 0.0)),
        ("xPts Away",        m.get("expected_points_away", 0.0)),
        ("Expected Home Goals", m.get("expected_home_goals", 0.0)),
        ("Expected Away Goals", m.get("expected_away_goals", 0.0)),
        ("AH Home -0.5",     m.get("asian_handicap_home_m0_5", 0.0)),
        ("AH Away -0.5",     m.get("asian_handicap_away_m0_5", 0.0)),
        ("AH Home +0.5",     m.get("asian_handicap_home_0_5", 0.0)),
        ("AH Away +0.5",     m.get("asian_handicap_away_0_5", 0.0)),
    ]

    core_table = "".join(_market_row(lbl, val) for lbl, val in core_rows)

    # Top 10 scorelines
    score_rows = "".join(
        f'<tr><td>{s["home_goals"]}-{s["away_goals"]}</td>'
        f'<td class="{_pct_class(s["probability"])}">{_fmt(s["probability"])}</td></tr>'
        for s in pred.top_scorelines[:10]
    )

    # Full market dump (collapsible) — work on a copy to avoid mutating pred.markets
    m_copy = dict(m)
    correct_score = m_copy.pop("correct_score_top_20", {})
    full_rows = ""
    for k, v in m_copy.items():
        if isinstance(v, float):
            full_rows += _market_row(k, v)
    if correct_score:
        full_rows += "<tr><td colspan='2'><strong>Correct Score Top 20</strong></td></tr>"
        for score_key, prob in correct_score.items():
            full_rows += _market_row(score_key, prob)

    # Audit trail
    audit = f"""
<div class="audit-step">
<strong>Step 1 — Pi Ratings</strong><br>
formula: composite = (home_rating + away_rating) / 2<br>
{at.home_team}: home_rating={at.home_pi_home:.4f}, away_rating={at.home_pi_away:.4f}
  → composite = ({at.home_pi_home:.4f} + {at.home_pi_away:.4f}) / 2 = <strong>{at.home_pi_composite:.4f}</strong>
  (from {at.home_n_matches} matches)<br>
{at.away_team}: home_rating={at.away_pi_home:.4f}, away_rating={at.away_pi_away:.4f}
  → composite = ({at.away_pi_home:.4f} + {at.away_pi_away:.4f}) / 2 = <strong>{at.away_pi_composite:.4f}</strong>
  (from {at.away_n_matches} matches)
</div>
<div class="audit-step">
<strong>Step 2 — Calibration Parameters</strong><br>
total_anchor = {at.total_anchor:.4f} ({at.total_source}, n={at.calibration_n_matches} 2026 matches)<br>
rho = {at.rho:.4f} ({at.rho_source}) — Dixon-Coles low-score correlation
</div>
<div class="audit-step">
<strong>Step 3 — Lambdas (Expected Goals per Team)</strong><br>
formula: margin = home_composite − away_composite<br>
formula: λ_H = max(0.30, total_anchor/2 + margin/2)<br>
formula: λ_A = max(0.30, total_anchor/2 − margin/2)<br>
margin = {at.home_pi_composite:.4f} − {at.away_pi_composite:.4f} = <strong>{at.margin:.4f}</strong><br>
λ_H = max(0.30, {at.total_anchor:.4f}/2 + {at.margin:.4f}/2) = <strong>{at.lambda_home:.4f}</strong><br>
λ_A = max(0.30, {at.total_anchor:.4f}/2 − {at.margin:.4f}/2) = <strong>{at.lambda_away:.4f}</strong>
</div>
<div class="audit-step">
<strong>Step 4 — Dixon-Coles PMF Grid (26×26)</strong><br>
formula: P(h,a) = τ(h,a,ρ) × Poisson(h; λ_H) × Poisson(a; λ_A), then normalise<br>
τ(0,0)=1−λ_H×λ_A×ρ, τ(1,0)=1+λ_A×ρ, τ(0,1)=1+λ_H×ρ, τ(1,1)=1−ρ, τ(h,a)=1 for h+a≥2<br>
With λ_H={at.lambda_home:.4f}, λ_A={at.lambda_away:.4f}, ρ={at.rho:.4f}:<br>
τ(0,0) = 1 − {at.lambda_home:.4f}×{at.lambda_away:.4f}×({at.rho:.4f})
       = <strong>{1 - at.lambda_home * at.lambda_away * at.rho:.4f}</strong><br>
Grid sum = <span class="grid-sum-ok">{at.pmf_grid_sum:.6f}</span>  (should be ≈1.000000)<br>
E[home goals] = {at.expected_home_goals:.4f},  E[away goals] = {at.expected_away_goals:.4f}
</div>
<div class="audit-step">
<strong>Step 5 — Market Derivations (cell summation)</strong><br>
home_win = Σ P(h,a) for h &gt; a = <strong>{m.get('home_win', 0.0):.4f}</strong><br>
draw     = Σ P(h,a) for h = a = <strong>{m.get('draw', 0.0):.4f}</strong><br>
away_win = Σ P(h,a) for h &lt; a = <strong>{m.get('away_win', 0.0):.4f}</strong><br>
over_2.5 = Σ P(h,a) for h+a &gt; 2.5 = <strong>{m.get('over_2_5', 0.0):.4f}</strong><br>
btts_yes = Σ P(h,a) for h≥1 AND a≥1 = <strong>{m.get('btts_yes', 0.0):.4f}</strong>
</div>
"""

    return f"""
<div class="match-card" id="match-{idx}">
  <div class="match-header">
    <span class="team-name">{at.home_team}</span>
    <span class="vs">vs</span>
    <span class="team-name">{at.away_team}</span>
  </div>
  <div class="meta">
    Stage: {at.stage} &nbsp;|&nbsp; Kickoff: {at.match_datetime} UTC
    &nbsp;|&nbsp; λ_H={at.lambda_home:.4f}, λ_A={at.lambda_away:.4f}
    &nbsp;|&nbsp; Pi: {at.home_team} {at.home_pi_composite:+.4f},
    {at.away_team} {at.away_pi_composite:+.4f}
  </div>

  <h3 style="margin-top:14px">Core Probabilities</h3>
  <table>
    <tr><th>Market</th><th>Probability (4 d.p.)</th></tr>
    {core_table}
  </table>

  <h3>Top 10 Scorelines</h3>
  <table>
    <tr><th>Score (H-A)</th><th>Probability</th></tr>
    {score_rows}
  </table>

  <details>
    <summary>Full Market Dump ({len(at.markets)} markets)</summary>
    <table>
      <tr><th>Market</th><th>Probability</th></tr>
      {full_rows}
    </table>
  </details>

  <details>
    <summary>Calculation Trail (every step, every number)</summary>
    {audit}
  </details>
</div>
"""


def write_summary(
    predictions: list,
    cal: "CalibrationState",
    out_dir: Path,
) -> Path:
    today = date.today().isoformat()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    match_sections = "".join(_render_match(p, i) for i, p in enumerate(predictions))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pi Ratings — World Cup 2026 Predictions {today}</title>
  <style>{_CSS}</style>
</head>
<body>
<h1>Pi Ratings — World Cup 2026 Match Predictions</h1>
<p><strong>Date:</strong> {today} &nbsp;|&nbsp;
   <strong>Generated:</strong> {now} &nbsp;|&nbsp;
   <strong>Matches:</strong> {len(predictions)}</p>
<p><strong>Calibration:</strong>
   total_anchor={cal.total_anchor:.4f} ({cal.total_source}),
   rho={cal.rho:.4f} ({cal.rho_source}),
   n={cal.n_matches_used} 2026 completed matches</p>
<p><em>All probabilities are pure-math Pi ratings → Dixon-Coles PMF.
   No external ML. Every formula shown in Calculation Trail.</em></p>

<h2>Scheduled Matches</h2>
{match_sections}

<div class="footer">
  Pi Ratings Standalone Engine — pi-ratings/ (worldcup2026-model) &nbsp;|&nbsp;
  Generated {now} &nbsp;|&nbsp;
  Model: PiRatings(alpha=0.15, beta=0.10) → DixonColesPMF(rho={cal.rho:.4f}) → MatchMarkets &nbsp;|&nbsp;
  Data: data/processed/v1/matches.parquet
</div>
</body>
</html>"""

    path = out_dir / f"summary_{today}.html"
    path.write_text(html, encoding="utf-8")
    return path
