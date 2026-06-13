"""
Generate PDF articles for wizardofodds.com.
Run: python docs/articles/generate_pdfs.py
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from reportlab.lib.colors import HexColor
from pathlib import Path

OUT_DIR = Path(__file__).parent

# ── Color palette ──────────────────────────────────────────────────────────
GOLD   = HexColor("#b89a30")
DARK   = HexColor("#0a0e1a")
PANEL  = HexColor("#1a2030")
MUTED  = HexColor("#8892a8")
TEXT   = HexColor("#1a1a2e")
BLACK  = HexColor("#111111")
RULE   = HexColor("#d4af37")
BG     = HexColor("#f8f6f0")

# ── Styles ─────────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()

    styles = {}

    styles["site"] = ParagraphStyle("site",
        fontName="Helvetica-Bold", fontSize=9,
        textColor=GOLD, spaceAfter=2, alignment=TA_LEFT)

    styles["h1"] = ParagraphStyle("h1",
        fontName="Helvetica-Bold", fontSize=22,
        textColor=BLACK, spaceBefore=10, spaceAfter=6,
        leading=26)

    styles["h2"] = ParagraphStyle("h2",
        fontName="Helvetica-Bold", fontSize=14,
        textColor=BLACK, spaceBefore=18, spaceAfter=4,
        leading=18, borderPadding=(0,0,2,0))

    styles["h3"] = ParagraphStyle("h3",
        fontName="Helvetica-Bold", fontSize=11,
        textColor=HexColor("#2a3560"), spaceBefore=12, spaceAfter=3,
        leading=14)

    styles["body"] = ParagraphStyle("body",
        fontName="Helvetica", fontSize=10,
        textColor=BLACK, spaceBefore=0, spaceAfter=6,
        leading=15, alignment=TA_JUSTIFY)

    styles["body_small"] = ParagraphStyle("body_small",
        fontName="Helvetica", fontSize=9,
        textColor=HexColor("#333333"), spaceBefore=0, spaceAfter=4,
        leading=13, alignment=TA_JUSTIFY)

    styles["formula"] = ParagraphStyle("formula",
        fontName="Courier", fontSize=9,
        textColor=HexColor("#1a3060"), spaceBefore=4, spaceAfter=4,
        leading=13, leftIndent=24, backColor=HexColor("#eef2ff"),
        borderPadding=4)

    styles["callout"] = ParagraphStyle("callout",
        fontName="Helvetica-Oblique", fontSize=9.5,
        textColor=HexColor("#4a4a60"), spaceBefore=4, spaceAfter=4,
        leading=14, leftIndent=16, rightIndent=16,
        borderPadding=(6,6,6,6))

    styles["bullet"] = ParagraphStyle("bullet",
        fontName="Helvetica", fontSize=10,
        textColor=BLACK, spaceBefore=1, spaceAfter=1,
        leading=14, leftIndent=20, firstLineIndent=-12)

    styles["disclaimer"] = ParagraphStyle("disclaimer",
        fontName="Helvetica-Oblique", fontSize=8,
        textColor=MUTED, spaceBefore=4, spaceAfter=2,
        leading=11, alignment=TA_CENTER)

    styles["label"] = ParagraphStyle("label",
        fontName="Helvetica-Bold", fontSize=9,
        textColor=GOLD, spaceBefore=0, spaceAfter=1)

    return styles

def rule():
    return HRFlowable(width="100%", thickness=0.5, color=RULE,
                      spaceAfter=8, spaceBefore=4)

def thin_rule():
    return HRFlowable(width="100%", thickness=0.25, color=HexColor("#cccccc"),
                      spaceAfter=4, spaceBefore=4)

def sp(n=6):
    return Spacer(1, n)


# ═══════════════════════════════════════════════════════════════════════════
# ARTICLE 1
# ═══════════════════════════════════════════════════════════════════════════

def build_article1(styles):
    S = styles
    story = []

    # Header
    story.append(Paragraph("WIZARDOFODDS.COM", S["site"]))
    story.append(rule())
    story.append(Paragraph(
        "How the 2026 World Cup Prediction Model Works",
        S["h1"]))
    story.append(Paragraph(
        "A complete guide to the mathematical methods behind the joint score probability engine.",
        S["callout"]))
    story.append(rule())
    story.append(sp(4))

    # ── Introduction ──────────────────────────────────────────────────────
    story.append(Paragraph("Introduction", S["h2"]))
    story.append(Paragraph(
        "This model produces a <b>Probability Mass Function (PMF)</b> for the final score of "
        "every 2026 FIFA World Cup match. For each match the model computes P(Home goals = h, "
        "Away goals = a) for every possible regulation-time final score, where regulation time "
        "is defined as 90 minutes plus stoppage time. Extra time and penalty shootouts are "
        "explicitly excluded from all probabilities shown.",
        S["body"]))
    story.append(Paragraph(
        "Every other number derived from the model — match result probabilities (1X2), "
        "totals (over/under), both teams to score (BTTS), team totals, and correct score "
        "market prices — is computed by summing the appropriate cells of this single joint "
        "distribution. There is no separate model for each market type.",
        S["body"]))
    story.append(Paragraph(
        "The full grid, including an explicit tail-mass bucket for extreme scores, "
        "sums to exactly 1.0. This is enforced at every stage of the pipeline.",
        S["body"]))

    # ── Step 1: Team Ratings ───────────────────────────────────────────────
    story.append(Paragraph("Step 1: Rating Every Team — The Composite Prior", S["h2"]))
    story.append(Paragraph(
        "Each of the 48 World Cup teams is assigned an <b>attack lambda</b> (λ_att) and a "
        "<b>defense lambda</b> (λ_def). These represent expected goals scored and conceded "
        "against an average opponent at a neutral venue. The 2026 global World Cup average "
        "is 1.30 goals per team per match, calibrated from 2018 and 2022 data.",
        S["body"]))

    story.append(Paragraph("Four rating sources are blended in priority order:", S["body"]))
    data = [
        ["Priority", "Source", "Weight (market available)", "Weight (no market)"],
        ["1", "Market-implied (BDL bookmaker odds)", "70%", "—"],
        ["2", "Pi rating (penaltyblog)", "15%", "30%"],
        ["3", "Elo rating (penaltyblog)", "10%", "45%"],
        ["4", "Massey rating", "5%", "15%"],
        ["5", "Confederation baseline (floor)", "—", "10%"],
    ]
    t = Table(data, colWidths=[0.7*inch, 2.8*inch, 1.5*inch, 1.5*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), HexColor("#1a2030")),
        ("TEXTCOLOR",  (0,0), (-1,0), HexColor("#d4af37")),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 8.5),
        ("FONTNAME",   (0,1), (-1,-1), "Helvetica"),
        ("BACKGROUND", (0,2), (-1,2), HexColor("#f0f0f0")),
        ("BACKGROUND", (0,4), (-1,4), HexColor("#f0f0f0")),
        ("GRID",       (0,0), (-1,-1), 0.25, HexColor("#cccccc")),
        ("ROWBACKGROUND", (0,1), (-1,1), colors.white),
        ("ALIGN",      (2,0), (-1,-1), "CENTER"),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(sp(4))
    story.append(t)
    story.append(sp(8))

    story.append(Paragraph(
        "<b>Market-implied strength</b> is extracted from bookmaker odds for each team's "
        "three group-stage matches using a goal expectancy decomposition: the method "
        "reverse-engineers what attack and defense lambdas would produce the observed "
        "no-vig 1X2 market probabilities. Up to six bookmaker sources are used per match "
        "via the BallDontLie (BDL) API. Not all sources are available for every match.",
        S["body"]))
    story.append(Paragraph(
        "The Pi and Elo ratings are computed using the penaltyblog library. Pi ratings "
        "update continuously with each match result and respond faster to recent form. "
        "Elo ratings are more stable over longer periods.",
        S["body"]))
    story.append(Paragraph(
        "Confederation baselines are applied as a hard floor when rating data is absent. "
        "Historical World Cup averages by confederation: CONMEBOL 1.45, UEFA 1.35, "
        "CONCACAF 1.20, CAF 1.10, AFC 1.10, OFC 0.90 (attack lambda vs average opponent).",
        S["body"]))
    story.append(Paragraph(
        "<b>Host advantage:</b> The USA, Canada, and Mexico receive an adjustment of "
        "+0.10 to attack lambda and −0.10 to defense lambda as co-hosts. All other "
        "matches are treated as neutral venue; no home/away distinction is applied.",
        S["body"]))

    story.append(Paragraph(
        "Important limitation: the 2018 and 2022 World Cup data together cover 128 matches. "
        "This is a limited sample for calibrating team-level ratings, particularly for teams "
        "from smaller confederations with few World Cup appearances.",
        S["callout"]))

    # ── Step 2: Poisson PMF ───────────────────────────────────────────────
    story.append(Paragraph("Step 2: The Independent Poisson Model", S["h2"]))
    story.append(Paragraph(
        "Given the blended ratings for both teams, the model computes the match-specific "
        "expected goals for each side:",
        S["body"]))
    story.append(Paragraph(
        "λ_home = home_attack × away_defense × global_scale_factor\n"
        "λ_away = away_attack × home_defense × global_scale_factor",
        S["formula"]))
    story.append(Paragraph(
        "The number of goals each team scores is modeled as an independent "
        "<b>Poisson distribution</b>. The Poisson distribution describes the probability "
        "of a given count of events occurring in a fixed time interval when those events "
        "occur at a constant average rate and independently of one another. For goals in "
        "a football match this is an approximation — goals are not entirely independent "
        "(a goal changes the incentives for both teams) — but it is the standard model "
        "in the football forecasting literature and performs well on held-out data.",
        S["body"]))
    story.append(Paragraph(
        "The joint probability of a specific final score is:",
        S["body"]))
    story.append(Paragraph(
        "P(Home = h, Away = a) = [e^(−λ_home) × λ_home^h / h!] × [e^(−λ_away) × λ_away^a / a!]",
        S["formula"]))
    story.append(Paragraph(
        "This is computed for all integer pairs (h, a) from (0,0) up to the grid maximum "
        "(typically 8 or 9 goals per team). The remaining probability mass — for scores "
        "beyond the grid — is captured in an explicit tail-mass value shown alongside "
        "every prediction. The independence assumption is partially corrected in the "
        "market reconciliation step that follows.",
        S["body"]))

    # ── Step 3: Market Reconciliation ─────────────────────────────────────
    story.append(Paragraph("Step 3: Market Reconciliation", S["h2"]))
    story.append(Paragraph(
        "Market odds contain information that the pure Poisson model does not have access "
        "to: late team news, tactical changes, injury reports not yet public, and the "
        "aggregate view of professional traders. The reconciliation step incorporates "
        "this information.",
        S["body"]))
    story.append(Paragraph(
        "For each match, no-vig probabilities are extracted from all available bookmaker "
        "markets: match result (1X2), correct score lines, total goals over/under "
        "(0.5, 1.5, 2.5, 3.5), both teams to score, draw no bet, double chance, and "
        "team-level totals. The bookmaker margin is removed from all odds before use.",
        S["body"]))
    story.append(Paragraph(
        "A constrained optimization (SLSQP algorithm) then adjusts the initial Poisson "
        "PMF grid to satisfy these market constraints while minimizing divergence from "
        "the original distribution. The optimization operates on an 8×8 grid of joint "
        "probabilities subject to the constraint that all values remain non-negative "
        "and sum to 1.0.",
        S["body"]))
    story.append(Paragraph(
        "The result is the <b>market-reconciled PMF</b>: a distribution that respects "
        "both the model's fundamental strength estimates and the market's current pricing. "
        "When market odds are unavailable for a match (as may occur in the early "
        "tournament stages before lines are posted), the pure Poisson model is used directly.",
        S["body"]))

    # ── Step 4: Calibration ───────────────────────────────────────────────
    story.append(Paragraph("Step 4: Calibration", S["h2"]))
    story.append(Paragraph(
        "Calibration refers to the alignment between stated probabilities and observed "
        "frequencies. A calibrated model is one where outcomes it assigns 30% probability "
        "occur approximately 30% of the time over many predictions.",
        S["body"]))
    story.append(Paragraph(
        "The model uses <b>temperature scaling</b>: a single parameter T is fitted "
        "by minimizing exact-score log loss on out-of-sample predictions from the "
        "2018 and 2022 World Cups. The adjusted probability is:",
        S["body"]))
    story.append(Paragraph(
        "p_calibrated[h,a] ∝ p_raw[h,a] ^ (1/T)",
        S["formula"]))
    story.append(Paragraph(
        "T > 1 indicates the model is overconfident and flattens the distribution. "
        "T < 1 indicates underconfidence and sharpens it. T = 1 leaves the distribution "
        "unchanged.",
        S["body"]))
    story.append(Paragraph(
        "Calibration is evaluated using multiple metrics computed on out-of-sample "
        "predictions only (never on the training data):",
        S["body"]))
    metrics = [
        ("Exact-score log loss", "Primary metric. Measures how surprised the model was "
         "by actual final scores. Lower is better."),
        ("Ranked Probability Score (RPS)", "Standard metric for ordered categorical "
         "outcomes. Applied to the 1X2 market."),
        ("Brier score", "Mean squared error on binary market probabilities (BTTS, "
         "over/under)."),
        ("Expected Calibration Error (ECE)", "Direct measure of how often stated "
         "probabilities match observed frequencies across probability bins."),
        ("Ignorance score", "Log score for probabilistic forecasts."),
    ]
    for name, desc in metrics:
        story.append(Paragraph(
            f"<b>{name}:</b> {desc}", S["bullet"]))
    story.append(Paragraph(
        "Note: with only 128 matches across two tournaments available for calibration, "
        "these metrics carry meaningful uncertainty. The calibration temperature is "
        "a coarse correction, not a guarantee of statistical accuracy.",
        S["callout"]))

    # ── Step 5: Edge Screening ────────────────────────────────────────────
    story.append(Paragraph("Step 5: Edge Screening", S["h2"]))
    story.append(Paragraph(
        "Once a calibrated PMF is available, the model compares its implied probabilities "
        "against the market's no-vig probabilities for every available bet. The edge on "
        "any outcome is defined as:",
        S["body"]))
    story.append(Paragraph(
        "Edge = (Model probability − Market implied probability) / Market implied probability",
        S["formula"]))
    story.append(Paragraph(
        "A market is flagged as a potential value opportunity only when all three of the "
        "following conditions hold simultaneously:",
        S["body"]))
    conditions = [
        "Edge ≥ 4% (the minimum threshold is 0.04, hardcoded in the engine)",
        "The lower bound of the model's 90% confidence interval still exceeds the market "
        "implied probability. The CI is computed by perturbing λ by ±12% (a conservative "
        "assumed uncertainty on the lambda estimates) and taking the resulting range of "
        "PMF-derived probabilities.",
        "Market implied probability > 2% (outcomes with under 2% market-implied probability "
        "are excluded due to thin liquidity and high variance on the edge estimate)",
    ]
    for c in conditions:
        story.append(Paragraph(f"• {c}", S["bullet"]))
    story.append(sp(4))
    story.append(Paragraph(
        "Bets passing all three filters are displayed as value opportunities. The engine "
        "computes a <b>half-Kelly stake</b> for each:",
        S["body"]))
    story.append(Paragraph(
        "f* = edge / (decimal_odds − 1)    [Half-Kelly = f* / 2]\nCapped at 5% of bankroll",
        S["formula"]))
    story.append(Paragraph(
        "Half-Kelly is used rather than full Kelly because the 12% lambda uncertainty "
        "assumption is approximate. Overestimating the edge with full Kelly results in "
        "overbetting. The 5% cap is an additional hard limit regardless of computed edge.",
        S["body"]))

    # ── Pipeline ──────────────────────────────────────────────────────────
    story.append(Paragraph("The Daily Pipeline", S["h2"]))
    story.append(Paragraph(
        "An automated process runs at 4:30 AM UTC each day via a server-side timer. "
        "GitHub Actions runs as a fallback at 4:00 AM UTC and skips the pipeline if "
        "the server is confirmed healthy. The pipeline stages are:",
        S["body"]))
    stages = [
        ("Fetch", "Pull the latest match records, bookmaker odds (up to six sources), "
         "team statistics, expected goals, shot maps, match events, momentum data, and "
         "group standings from the BallDontLie API."),
        ("Build", "Rebuild versioned Parquet tables from raw API snapshots, catching "
         "schema changes."),
        ("Predict", "Run the composite prior, Poisson model, market reconciliation, "
         "calibration, and edge screening for every upcoming match."),
        ("Publish", "Write one JSON file per matchday containing the full PMF grid, "
         "all derived markets, the edge report, and calibration metadata."),
        ("Validate", "Verify internal consistency: PMF sums to 1.0 ± 1e-6, no "
         "probabilities outside [0,1], no missing required fields."),
        ("Deploy", "Upload prediction data and HTML pages to the production server "
         "via FTP."),
        ("Report", "Generate a matchday summary including group standings, advancement "
         "probabilities, and top value opportunities."),
    ]
    for name, desc in stages:
        story.append(Paragraph(f"<b>{name}:</b> {desc}", S["bullet"]))
    story.append(sp(4))
    story.append(Paragraph(
        "During match hours (approximately 14:00–04:00 UTC), a separate live process "
        "runs every minute to poll BallDontLie for live match states and update the "
        "in-play PMF. When the production server's WebSocket endpoint is active, "
        "updates are pushed directly to connected browsers.",
        S["body"]))

    # ── Limitations ───────────────────────────────────────────────────────
    story.append(Paragraph("Limitations and Scope", S["h2"]))
    lims = [
        "All probabilities represent regulation time only (90 minutes plus stoppage "
        "time). Extra time and penalty shootouts are not modeled.",
        "The Poisson independence assumption is an approximation. Teams adjust "
        "tactically after goals, creating correlation between home and away goal counts. "
        "Market reconciliation partially corrects for this but does not eliminate it.",
        "The calibration dataset covers 128 World Cup matches (2018 and 2022 combined). "
        "This is a small sample and calibration metrics carry meaningful uncertainty.",
        "The ±12% lambda uncertainty used for confidence intervals is a fixed assumption, "
        "not an empirically derived estimate for each match.",
        "Odds used for edge calculations are sourced at the time the daily prediction "
        "is generated. Odds move before kickoff. Always verify current odds before "
        "acting on any edge signal.",
        "Edge estimates are outputs of a probabilistic model. They are not guaranteed "
        "profit signals.",
    ]
    for l in lims:
        story.append(Paragraph(f"• {l}", S["bullet"]))

    story.append(sp(12))
    story.append(thin_rule())
    story.append(Paragraph(
        "All probabilities represent regulation time (90 minutes + stoppage time) only. "
        "Extra time and penalties are excluded. This article is for informational and "
        "educational purposes. Please gamble responsibly.",
        S["disclaimer"]))

    return story


# ═══════════════════════════════════════════════════════════════════════════
# ARTICLE 2
# ═══════════════════════════════════════════════════════════════════════════

def build_article2(styles):
    S = styles
    story = []

    story.append(Paragraph("WIZARDOFODDS.COM", S["site"]))
    story.append(rule())
    story.append(Paragraph(
        "A Guide to the WC 2026 Prediction Pages",
        S["h1"]))
    story.append(Paragraph(
        "What every number, chart, and indicator means — across all three pages.",
        S["callout"]))
    story.append(rule())
    story.append(sp(4))

    story.append(Paragraph(
        "There are three pages in the WC 2026 prediction section. Each draws from the "
        "same underlying joint score PMF engine. This guide explains every element "
        "visible on each page.",
        S["body"]))

    # ══════════════════════════════════════════════════════════
    # PAGE 1
    # ══════════════════════════════════════════════════════════
    story.append(Paragraph("Page 1 — Pre-Game Predictions", S["h2"]))
    story.append(Paragraph(
        "<b>URL:</b> sportsodds.wizardofodds.com/tools/odds-scanner/predictions/"
        "world cup/pre match.html",
        S["body_small"]))
    story.append(Paragraph(
        "This page lists every World Cup match scheduled for the current day, with the "
        "model's pre-game probability estimates and edge analysis. Data loads "
        "automatically and refreshes every five minutes from the latest prediction "
        "JSON. A red banner appears if the underlying data is more than four hours "
        "old, indicating a potential pipeline issue.",
        S["body"]))

    story.append(Paragraph("KPI Cards", S["h3"]))

    kpis = [
        ("Matches Today", "The number of World Cup matches with regulation kickoffs "
         "scheduled for today."),
        ("Value Bets", "The count of individual betting markets across all today's "
         "matches where the model's edge is at least 4% and the 90% confidence "
         "interval lower bound still exceeds the market's no-vig probability. This "
         "is a strict filter; the number is frequently zero or very small."),
        ("Best Edge", "The single largest edge found across all today's markets, "
         "expressed as a percentage. The sub-label identifies the specific market "
         "and match. A positive edge means the model assigns higher probability to "
         "the outcome than the market does. This does not guarantee a profitable bet."),
        ("Avg xG / Match", "The average of (λ_home + λ_away) across today's matches — "
         "the model's expected total goals per match. Derived from the composite prior "
         "after market reconciliation."),
    ]
    for name, desc in kpis:
        story.append(Paragraph(f"<b>{name}:</b> {desc}", S["bullet"]))
        story.append(sp(2))

    story.append(Paragraph("Bankroll Sizing Tool", S["h3"]))
    story.append(Paragraph(
        "Enter a bankroll amount and select a Kelly fraction. The table will then "
        "display a recommended dollar stake for every flagged value bet. Three "
        "fractions are available:",
        S["body"]))
    kelly = [
        ("Full Kelly", "The mathematically optimal fraction under the Kelly criterion. "
         "Produces large drawdowns in practice when model edge estimates contain error. "
         "Not recommended unless confidence in the edge estimate is high."),
        ("Half Kelly", "Bet size divided by two. Substantially reduces variance while "
         "retaining most of the theoretical edge. Used as the default in the "
         "engine's internal sizing calculations."),
        ("Quarter Kelly", "Conservative setting. Appropriate when acknowledging "
         "significant uncertainty in the model's probability estimates."),
    ]
    for name, desc in kelly:
        story.append(Paragraph(f"<b>{name}:</b> {desc}", S["bullet"]))
        story.append(sp(2))

    story.append(Paragraph("The Match Table", S["h3"]))
    story.append(Paragraph(
        "Each row represents one match. Columns from left to right:", S["body"]))

    cols = [
        ("Match", "Home team vs away team. All matches are treated as neutral venue "
         "except USA, Canada, and Mexico matches, which carry a small host-advantage "
         "adjustment (+0.10 attack lambda, −0.10 defense lambda)."),
        ("1X2 Probability Bars", "Three colored segments proportional to the regulation-time "
         "probabilities: Home Win (gold), Draw (gray), Away Win (blue). These are derived "
         "by summing the appropriate cells of the joint PMF: home win = sum of all cells "
         "where home goals > away goals; draw = main diagonal; away win = all cells where "
         "away goals > home goals."),
        ("O/U 2.5", "Probability that total regulation-time goals exceed 2.5 — i.e., that "
         "three or more goals are scored. Computed by summing all PMF cells where "
         "home_goals + away_goals ≥ 3."),
        ("BTTS", "Both Teams To Score — the probability that both teams score at least one "
         "regulation-time goal. Computed by summing all cells where home_goals ≥ 1 and "
         "away_goals ≥ 1."),
        ("Top Score", "The single most probable final score and its probability, directly "
         "read from the peak cell of the joint PMF grid."),
        ("xG (H–A)", "The model's expected goals for home and away separately (λ_home, "
         "λ_away). These are the Poisson mean parameters after market reconciliation."),
        ("Best Edge / Fair Odds", "The highest-edge market for this match that passes all "
         "three value filters (≥4% edge, CI check, ≥2% liquidity). Fair decimal odds = "
         "1 / model_probability. If no market passes the filters, this cell is blank."),
    ]
    for name, desc in cols:
        story.append(Paragraph(f"<b>{name}:</b> {desc}", S["bullet"]))
        story.append(sp(2))

    story.append(Paragraph("Expanded Row", S["h3"]))
    story.append(Paragraph(
        "Clicking a row reveals three sections:", S["body"]))

    exp = [
        ("Full Scoreline Distribution", "All scored probabilities from 0–0 through "
         "the grid maximum, ranked by probability. The top 15 are displayed with "
         "proportion bars. These values are read directly from the joint PMF grid "
         "with no further transformation."),
        ("All Markets", "Every market the model has priced: 1X2, Draw No Bet, Double "
         "Chance, Over/Under at 0.5 / 1.5 / 2.5 / 3.5 / 4.5, BTTS, and team-level "
         "totals (Home Over 0.5 / 1.5, Away Over 0.5 / 1.5). All computed from "
         "the same joint PMF."),
        ("Edge Report", "For each market: Model Probability, Market Implied (no-vig), "
         "and Edge%. Rows highlighted in gold pass all three value filters. The Kelly "
         "stake column reflects the bankroll and fraction selected above the table."),
    ]
    for name, desc in exp:
        story.append(Paragraph(f"<b>{name}:</b> {desc}", S["bullet"]))
        story.append(sp(2))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════
    # PAGE 2
    # ══════════════════════════════════════════════════════════
    story.append(Paragraph("Page 2 — PMF Distributions", S["h2"]))
    story.append(Paragraph(
        "<b>URL:</b> sportsodds.wizardofodds.com/tools/odds-scanner/predictions/"
        "world-cup/pre-match/Probability Distributions.html",
        S["body_small"]))
    story.append(Paragraph(
        "This page visualizes the complete probability distribution for every match. "
        "Select a match using the navigation chips at the top. All charts update "
        "immediately on selection and draw from the same joint PMF as Page 1.",
        S["body"]))

    story.append(Paragraph("Chart 1 — Joint Score PMF Heatmap", S["h3"]))
    story.append(Paragraph(
        "A color-coded grid where each cell (h, a) shows P(Home = h, Away = a). "
        "Home goals are on the vertical axis; away goals on the horizontal axis.",
        S["body"]))
    story.append(Paragraph(
        "Color scale: dark blue/black = near zero probability; warm orange/yellow = "
        "moderate (3–8%); bright green = the highest-probability cells (typically > 8%). "
        "The color mapping uses the square root of the probability relative to the "
        "maximum cell, which visually separates low-probability cells that would "
        "otherwise appear uniformly dark on a linear scale.",
        S["body"]))
    story.append(Paragraph(
        "Any market can be read directly from this grid. For example: over 2.5 is the "
        "sum of all cells in the top-right region where h + a ≥ 3; a clean sheet for "
        "the home team is the sum of the entire first column (a = 0).",
        S["body"]))
    story.append(Paragraph(
        "The <b>tail mass</b> shown below the heatmap is the probability captured in "
        "the explicit overflow bucket — scores beyond the grid boundary. The grid "
        "values plus the tail mass sum to exactly 100%.",
        S["body"]))

    story.append(Paragraph("Chart 2 — Marginal Goal Distributions", S["h3"]))
    story.append(Paragraph(
        "Two bar charts: one for the home team, one for the away team. Each bar "
        "represents P(team scores exactly k goals) for k = 0, 1, 2, ... The marginal "
        "for the home team is obtained by summing the joint PMF across all away goal "
        "counts for each value of home goals:",
        S["body"]))
    story.append(Paragraph(
        "P(Home = h) = Σ_a P(Home = h, Away = a)",
        S["formula"]))
    story.append(Paragraph(
        "The tallest bar for each team is typically at 1 goal for most World Cup group "
        "matches. A very tall P(0) bar indicates the model expects the team to be "
        "frequently shut out.",
        S["body"]))

    story.append(Paragraph("Chart 3 — Total Goals Distribution", S["h3"]))
    story.append(Paragraph(
        "A bar chart showing P(total regulation goals = k) for k = 0, 1, 2, ... "
        "Computed by summing all joint PMF cells along each diagonal (h + a = k). "
        "Common over/under lines (0.5, 1.5, 2.5, 3.5, 4.5) are shown as vertical "
        "dividers. The probability to the right of any divider is the Over probability "
        "for that line; to the left is the Under probability.",
        S["body"]))

    story.append(Paragraph("Chart 4 — Goal Difference Distribution", S["h3"]))
    story.append(Paragraph(
        "A bar chart centered on zero showing the probability of each possible "
        "goal difference (home goals minus away goals). Gold bars indicate home wins "
        "(positive difference), gray indicates a draw (zero), blue indicates away "
        "wins (negative difference). This chart makes it easy to see whether the "
        "model expects a close match or a one-sided one.",
        S["body"]))

    story.append(Paragraph("Chart 5 — Top 15 Most Likely Scorelines", S["h3"]))
    story.append(Paragraph(
        "A ranked bar chart of the 15 highest-probability individual final scores "
        "with exact percentages. These are the raw joint PMF values for the "
        "top 15 cells, sorted in descending order.",
        S["body"]))
    story.append(Paragraph(
        "For correct score betting: if the market is offering decimal odds of D on "
        "score S, the no-vig market-implied probability is approximately 1/D adjusted "
        "for margin. The edge on that score is (model_probability − 1/(D × margin)) "
        "/ (1/(D × margin)).",
        S["body"]))

    story.append(Paragraph("O/U Lines Table", S["h3"]))
    story.append(Paragraph(
        "A table listing Over and Under probabilities for every standard total line "
        "(0.5, 1.5, 2.5, 3.5, 4.5, 5.5). All computed by summing the appropriate "
        "region of the joint PMF.",
        S["body"]))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════
    # PAGE 3
    # ══════════════════════════════════════════════════════════
    story.append(Paragraph("Page 3 — Live In-Play PMF", S["h2"]))
    story.append(Paragraph(
        "<b>URL:</b> sportsodds.wizardofodds.com/tools/odds-scanner/predictions/"
        "world-cup/live/Probability Distributions.html",
        S["body_small"]))
    story.append(Paragraph(
        "This page activates when a World Cup match is in progress. When no matches "
        "are live it displays 'No live matches right now' along with the next "
        "scheduled kickoff. All probabilities remain regulation-time only.",
        S["body"]))

    story.append(Paragraph("How the Live Model Differs From Pre-Game", S["h3"]))
    story.append(Paragraph(
        "The pre-game model asks: what will the final score be from kickoff? "
        "The live model asks: given that the current score is H–A at minute t, "
        "what will the final score be at 90+ minutes?",
        S["body"]))
    story.append(Paragraph(
        "This is a conditional probability calculation. The live model only assigns "
        "probability to scores reachable from the current state. A match at 2–1 "
        "in the 70th minute cannot finish 1–0 or 0–0; those cells of the PMF grid "
        "are zero.",
        S["body"]))
    story.append(Paragraph(
        "The model computes expected remaining goals for each team using a "
        "<b>non-homogeneous hazard model</b> — meaning the goal rate varies by "
        "match minute. The temporal baseline is calibrated from the minute-by-minute "
        "goal distribution across the 2018 and 2022 World Cups (128 matches, "
        "approximately 330 goals):",
        S["body"]))
    hazard = [
        "Minutes 1–10: below-average rate (teams settling in)",
        "Minutes 25–45: rising rate as play opens up",
        "Minutes 45–50: elevated rate immediately following half-time kickoff",
        "Minutes 80–90+: above-average rate, particularly when a team is chasing "
        "the match",
    ]
    for h in hazard:
        story.append(Paragraph(f"• {h}", S["bullet"]))
    story.append(sp(4))
    story.append(Paragraph(
        "On top of the temporal baseline, <b>score-state multipliers</b> scale each "
        "team's goal rate based on the current score. These multipliers are calibrated "
        "from World Cup data and the football forecasting literature "
        "(Dixon & Robinson 1998):",
        S["body"]))

    mult_data = [
        ["Score state", "Effect on goal rates"],
        ["Draw at minute 60+", "Both teams ×1.10 (games open up in final 30 minutes)"],
        ["Home team losing by 1", "Home ×1.25, Away ×1.05 (counter-attack risk)"],
        ["Home team losing by 2+", "Home ×1.40, Away ×1.10"],
        ["Home team winning by 1", "Home ×0.90, Away ×1.10 (away team pushes)"],
        ["Home team winning by 2+", "Home ×0.80, Away ×1.15"],
    ]
    mt = Table(mult_data, colWidths=[2.5*inch, 4.0*inch])
    mt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), HexColor("#1a2030")),
        ("TEXTCOLOR",  (0,0), (-1,0), HexColor("#d4af37")),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTNAME",   (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE",   (0,0), (-1,-1), 8.5),
        ("BACKGROUND", (0,2), (-1,2), HexColor("#f0f0f0")),
        ("BACKGROUND", (0,4), (-1,4), HexColor("#f0f0f0")),
        ("GRID",       (0,0), (-1,-1), 0.25, HexColor("#cccccc")),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(sp(4))
    story.append(mt)
    story.append(sp(8))

    story.append(Paragraph(
        "When live expected goals (xG) data is available from BallDontLie, the model "
        "blends the live xG rate (60% weight) with the pre-game expected rate (40% "
        "weight) to produce a more responsive intensity estimate.",
        S["body"]))

    story.append(Paragraph("Connection Badge", S["h3"]))
    story.append(Paragraph(
        "A small indicator in the header shows the data delivery mode:", S["body"]))
    story.append(Paragraph(
        "<b>● WebSocket (green):</b> The browser has an active connection to the live "
        "prediction server. When BallDontLie sends a goal event or status change, "
        "the server recomputes the PMF and pushes it to connected browsers typically "
        "within 200 milliseconds. No page refresh is required.",
        S["bullet"]))
    story.append(Paragraph(
        "<b>○ Polling (yellow):</b> The real-time connection is unavailable. The page "
        "fetches updated data from a static JSON file every 60 seconds. Updates arrive "
        "with up to a one-minute delay. This is the fallback mode.",
        S["bullet"]))
    story.append(sp(4))

    story.append(Paragraph("Live KPI Cards", S["h3"]))
    live_kpis = [
        ("Matches Live", "Number of World Cup matches currently in progress per "
         "BallDontLie."),
        ("Next Kickoff", "Next match starting today, with kickoff time in Eastern time."),
        ("Goals Today", "Sum of goals scored across all live matches as of the "
         "last snapshot."),
        ("Data Age", "Time elapsed since the last live snapshot was generated. Under "
         "two minutes is normal during live matches. A value over ten minutes during "
         "a live match triggers the health warning banner."),
    ]
    for name, desc in live_kpis:
        story.append(Paragraph(f"<b>{name}:</b> {desc}", S["bullet"]))
        story.append(sp(2))

    story.append(Paragraph("Win Probability Bar", S["h3"]))
    story.append(Paragraph(
        "The same three-segment bar as on Page 1, but now conditional on the current "
        "live score and minute. These probabilities update with every new snapshot. "
        "They represent the probability of each regulation-time outcome given that "
        "the match is currently at score H–A at minute t.",
        S["body"]))
    story.append(Paragraph(
        "Directly below the bar, a <b>Pre-game → Live Shift</b> table shows, for each "
        "main market, the pre-game probability, the current live probability, and the "
        "arithmetic difference. A large shift on a market reflects how significantly "
        "the match state has altered the probability distribution.",
        S["body"]))

    story.append(Paragraph("Win Probability Sparkline", S["h3"]))
    story.append(Paragraph(
        "A small line chart showing the history of the home team's win probability "
        "from kickoff to the current minute. This history is stored locally in the "
        "browser session — it accumulates while the page is open and resets on reload. "
        "Sharp upward jumps correspond to home goals; sharp downward drops correspond "
        "to away goals.",
        S["body"]))

    story.append(Paragraph("Live Joint Score PMF Heatmap", S["h3"]))
    story.append(Paragraph(
        "The same heatmap as on Page 2, updated in real time. Two visual differences "
        "from the pre-game version:",
        S["body"]))
    story.append(Paragraph(
        "• The cell corresponding to the current live score is outlined in red.",
        S["bullet"]))
    story.append(Paragraph(
        "• All cells representing scores impossible from the current state (home goals "
        "below the current home score, or away goals below the current away score) "
        "carry zero probability and appear dark. The remaining probability is "
        "distributed only across reachable final scores.",
        S["bullet"]))
    story.append(sp(4))

    story.append(Paragraph("Next Goal Probabilities", S["h3"]))
    story.append(Paragraph(
        "Three values computed from the remaining expected goals λ_h_rem and λ_a_rem:",
        S["body"]))

    ng = [
        ("Home team scores next",
         "λ_h_rem / (λ_h_rem + λ_a_rem) — given that another goal is scored before "
         "the final whistle, the probability it goes to the home team."),
        ("Away team scores next",
         "λ_a_rem / (λ_h_rem + λ_a_rem) — same for the away team."),
        ("No more goals",
         "e^(−λ_h_rem) × e^(−λ_a_rem) — the joint probability that both Poisson "
         "processes produce zero additional goals, i.e., the current score is the "
         "final score."),
    ]
    for name, desc in ng:
        story.append(Paragraph(f"<b>{name}:</b> {desc}", S["bullet"]))
        story.append(sp(2))

    story.append(Paragraph("Top 10 Most Likely Final Scores (Live)", S["h3"]))
    story.append(Paragraph(
        "The same ranked list as on Page 2, but filtered to exclude scores that are "
        "no longer reachable. The current live score is marked with an arrow. "
        "As the match progresses and the remaining time shrinks, the top score's "
        "probability typically increases because fewer reachable outcomes remain.",
        S["body"]))

    story.append(Paragraph("Home and Away Marginal Charts", S["h3"]))
    story.append(Paragraph(
        "Bar charts showing P(team scores exactly k regulation-time goals) for each "
        "team, derived from the live PMF in the same way as on Page 2. Only values "
        "at or above the team's current score are non-zero.",
        S["body"]))

    # ── Limitations ───────────────────────────────────────────────────────
    story.append(Paragraph("Scope and Limitations — All Pages", S["h2"]))
    lims = [
        "All probabilities on all three pages represent regulation time (90 minutes "
        "plus stoppage time) only. Extra time and penalty shootouts are not included.",
        "The independence assumption in the Poisson model means the model does not "
        "directly account for the correlation introduced by tactical changes after "
        "goals. Market reconciliation partially corrects for this.",
        "Calibration is based on 128 World Cup matches from 2018 and 2022. "
        "Out-of-sample performance on the 2026 tournament specifically is unknown "
        "at this stage of the tournament.",
        "Edge estimates are outputs of a probabilistic model. They are not profit "
        "guarantees. Market odds move between the time predictions are generated and "
        "kickoff. Always verify current odds before acting.",
        "The WebSocket update speed is subject to network latency and server load. "
        "The stated target of under 200 milliseconds applies under normal conditions.",
    ]
    for l in lims:
        story.append(Paragraph(f"• {l}", S["bullet"]))

    story.append(sp(12))
    story.append(thin_rule())
    story.append(Paragraph(
        "All probabilities represent regulation time (90 minutes + stoppage time) only. "
        "Extra time and penalties are excluded. This guide is for informational and "
        "educational purposes. Please gamble responsibly.",
        S["disclaimer"]))

    return story


# ═══════════════════════════════════════════════════════════════════════════
# RENDER
# ═══════════════════════════════════════════════════════════════════════════

def render(story, output_path: Path, title: str):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=0.85*inch,
        rightMargin=0.85*inch,
        topMargin=0.9*inch,
        bottomMargin=0.8*inch,
        title=title,
        author="Wizard of Odds",
    )
    doc.build(story)
    print(f"✓ {output_path.name}  ({output_path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    styles = make_styles()
    render(build_article1(styles),
           OUT_DIR / "wc2026-how-the-model-works.pdf",
           "How the WC 2026 Prediction Model Works — Wizard of Odds")
    render(build_article2(styles),
           OUT_DIR / "wc2026-page-guide.pdf",
           "A Guide to the WC 2026 Prediction Pages — Wizard of Odds")
    print("Done.")
