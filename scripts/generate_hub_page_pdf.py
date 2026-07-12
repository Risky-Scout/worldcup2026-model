"""
Sports Prediction Tools Hub Page — Optimised Blueprint PDF
Generates: reports/Sports_Prediction_Tools_Hub_Page_Blueprint.pdf

Revenue-optimised version of the WizardOfOdds parent landing page blueprint.
Includes all original editorial content plus conversion architecture additions.
"""

import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle,
    PageBreak, KeepTogether, Preformatted
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../reports")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Colour Palette ─────────────────────────────────────────────────────────────
NAVY    = colors.HexColor("#0D1B2A")
GOLD    = colors.HexColor("#C9A84C")
GOLD_BG = colors.HexColor("#FFF8E7")
DKGRAY  = colors.HexColor("#2E3440")
MID     = colors.HexColor("#6C7A89")
LGRAY   = colors.HexColor("#F4F5F6")
WHITE   = colors.white
BLUE    = colors.HexColor("#1B4F99")
BLUE_BG = colors.HexColor("#EEF2FF")
GREEN   = colors.HexColor("#1A6B3C")
GREEN_BG= colors.HexColor("#E8F5E9")
RED     = colors.HexColor("#8B1A1A")
AMBER   = colors.HexColor("#E65C00")
CTA_BG  = colors.HexColor("#0D2B45")
NEW_BG  = colors.HexColor("#E8F4F0")
NEW_FG  = colors.HexColor("#0A5C44")

# ── Style Helpers ──────────────────────────────────────────────────────────────
def ps(name, **kw):
    base = dict(fontName="Helvetica", fontSize=10, textColor=DKGRAY,
                leading=14, spaceAfter=4, spaceBefore=2, alignment=TA_JUSTIFY)
    base.update(kw)
    return ParagraphStyle(name, **base)

COVER_TITLE  = ps("ct",  fontName="Helvetica-Bold", fontSize=22, textColor=WHITE,
                  alignment=TA_CENTER, leading=28)
COVER_SUB    = ps("cs",  fontName="Helvetica-Oblique", fontSize=13, textColor=GOLD,
                  alignment=TA_CENTER, leading=18)
COVER_DATE   = ps("cd",  fontSize=9.5, textColor=colors.HexColor("#A0AABF"),
                  alignment=TA_CENTER, leading=14)
H1           = ps("h1",  fontName="Helvetica-Bold", fontSize=17, textColor=NAVY,
                  leading=22, spaceBefore=14, spaceAfter=6, alignment=TA_LEFT)
H2           = ps("h2",  fontName="Helvetica-Bold", fontSize=13, textColor=BLUE,
                  leading=18, spaceBefore=12, spaceAfter=4, alignment=TA_LEFT)
H3           = ps("h3",  fontName="Helvetica-Bold", fontSize=11, textColor=NAVY,
                  leading=15, spaceBefore=10, spaceAfter=3, alignment=TA_LEFT)
H3_TOOL      = ps("h3t", fontName="Helvetica-Bold", fontSize=11, textColor=WHITE,
                  leading=15, spaceBefore=0, spaceAfter=0, alignment=TA_LEFT)
BODY         = ps("body", fontSize=9.5, leading=14, spaceAfter=4)
BODY_J       = ps("bodyj", fontSize=9.5, leading=14, spaceAfter=4, alignment=TA_JUSTIFY)
BULL         = ps("bull", fontSize=9.5, leading=13, leftIndent=14, spaceAfter=2)
NOTE         = ps("note", fontName="Helvetica-Oblique", fontSize=8.5, textColor=MID,
                  leading=12, spaceAfter=3, alignment=TA_LEFT)
CAP          = ps("cap",  fontName="Helvetica-Bold", fontSize=8, textColor=MID,
                  alignment=TA_CENTER, spaceAfter=2)
NEW_LABEL    = ps("newl", fontName="Helvetica-Bold", fontSize=8, textColor=NEW_FG,
                  leading=11, spaceAfter=0, alignment=TA_LEFT)
CTA_LINK     = ps("ctal", fontName="Helvetica-Bold", fontSize=9, textColor=GOLD,
                  leading=13, spaceAfter=2, alignment=TA_LEFT)
STEP_NUM     = ps("snum", fontName="Helvetica-Bold", fontSize=18, textColor=GOLD,
                  leading=22, spaceBefore=0, spaceAfter=0, alignment=TA_CENTER)
STEP_TITLE   = ps("stit", fontName="Helvetica-Bold", fontSize=10.5, textColor=NAVY,
                  leading=15, spaceBefore=0, spaceAfter=2, alignment=TA_LEFT)
FAQ_Q        = ps("faqq", fontName="Helvetica-Bold", fontSize=9.5, textColor=NAVY,
                  leading=14, spaceBefore=6, spaceAfter=1, alignment=TA_LEFT)
FAQ_A        = ps("faqa", fontSize=9.5, leading=13, spaceAfter=4,
                  leftIndent=12, alignment=TA_JUSTIFY)

# ── Reusable Flowables ─────────────────────────────────────────────────────────
def hr():
    return HRFlowable(width="100%", thickness=1.5, color=GOLD,
                      spaceAfter=8, spaceBefore=6)

def mini_hr():
    return HRFlowable(width="100%", thickness=0.5, color=MID,
                      spaceAfter=4, spaceBefore=4)

def section(title):
    return [hr(), Paragraph(title, H1)]

def h2(title):
    return [Paragraph(title, H2)]

def body(*paras):
    return [Paragraph(p, BODY_J) for p in paras]

def bullet(*items):
    return [Paragraph(f"• {i}", BULL) for i in items]

def note(text):
    return [Paragraph(f"<i>{text}</i>", NOTE)]

def new_tag(label="NEW ADDITION"):
    return Paragraph(f"▶ {label}", NEW_LABEL)

def cta_bar(links):
    """Render a row of CTA links inside a tinted box."""
    text = "   |   ".join(
        [f'<b><font color="#{GOLD.hexval()[2:]}">→ {lbl}</font></b>' for lbl in links]
    )
    t = Table([[Paragraph(text, CTA_LINK)]])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CTA_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    return [t, Spacer(1, 6)]

def tool_header(title, badge=None):
    """Dark navy header strip for a tool card."""
    badge_text = f'  <font color="#{GOLD.hexval()[2:]}">[{badge}]</font>' if badge else ""
    t = Table([[Paragraph(f"{title}{badge_text}", H3_TOOL)]])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return [t]

def sbook_cta_box(text):
    """Tinted green sportsbook CTA box."""
    t = Table([[Paragraph(text, ps("sb", fontName="Helvetica-Bold", fontSize=9.5,
                                   textColor=GREEN, leading=14, alignment=TA_CENTER))]])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GREEN_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("BOX", (0, 0), (-1, -1), 1, GREEN),
    ]))
    return [t, Spacer(1, 8)]


# ── Main Builder ───────────────────────────────────────────────────────────────
def build():
    path = os.path.join(OUTPUT_DIR, "Sports_Prediction_Tools_Hub_Page_Blueprint.pdf")
    doc = SimpleDocTemplate(
        path, pagesize=letter,
        leftMargin=0.85 * inch, rightMargin=0.85 * inch,
        topMargin=0.7 * inch, bottomMargin=0.7 * inch
    )
    story = []

    # ── COVER ──────────────────────────────────────────────────────────────────
    cover = Table([[
        Paragraph("SPORTS PREDICTION TOOLS", COVER_TITLE)
    ], [
        Paragraph("Hub Page — Revenue-Optimised Blueprint", COVER_SUB)
    ], [
        Paragraph(
            "WizardOfOdds  ·  Parent Landing Page  ·  July 2026  ·  "
            "All editorial content preserved · Conversion architecture added",
            COVER_DATE)
    ]])
    cover.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
    ]))
    story += [cover, Spacer(1, 12)]

    # SEO metadata box
    meta = Table([
        [Paragraph("<b>SEO Title:</b>", CAP),
         Paragraph("Sports Prediction Tools &amp; Betting Probability Models", BODY)],
        [Paragraph("<b>Meta Description:</b>", CAP),
         Paragraph("Explore the Wizard's sports prediction tools using probability models, "
                   "simulations, and market analysis to evaluate odds, player props &amp; "
                   "live betting markets.", BODY)],
        [Paragraph("<b>Schema Markup:</b>", CAP),
         Paragraph("FAQPage (11 questions) + HowTo (5 steps) — see Section 7 and Section 8",
                   BODY)],
    ], colWidths=[1.2 * inch, 5.55 * inch])
    meta.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LGRAY),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#C0C8D8")),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    story += [meta, Spacer(1, 6)]
    story += note("Legend: Shaded boxes marked ▶ NEW ADDITION are revenue/conversion additions. "
                  "All unshaded copy is the original boss-authored editorial content, unchanged.")
    story += [Spacer(1, 4)]

    # ── SECTION 1 · PAGE HEADLINE & INTRO ─────────────────────────────────────
    story += section("Sports Prediction Tools Powered by Probability Models")
    story += body(
        "Sports markets are constantly changing. A player's role can shift, a team's form "
        "can evolve, and live odds can move within seconds. Understanding those changes "
        "requires more than looking at past results or making a quick prediction.",
        "Wizard of Odds sports prediction tools are designed to analyse those moving pieces "
        "through probability models, simulations, and real-time market data. Instead of "
        "asking only what might happen, these tools look at the many possible outcomes, "
        "how likely each one is, and how those probabilities compare with sportsbook pricing.",
        "The result is a more complete picture of the market. Player props, team matchups, "
        "and live betting scenarios can all be examined through the same framework: "
        "analysing performance, measuring uncertainty, simulating outcomes, and comparing "
        "model expectations with available odds.",
        "This page brings together prediction models across football, basketball, tennis, "
        "and other sports, giving users a way to explore how data-driven forecasting works "
        "before and during games."
    )
    story += note("Internal links in live page: "
                  "wizardofodds.com/article/player-props-understanding-the-math-behind-the-lines/  "
                  "| wizardofodds.com/article/expected-value-in-player-prop-betting/  "
                  "| wizardofodds.com/article/variance-and-bankroll-management-for-player-props/")

    # ── SECTION 2 · TODAY'S TOP EDGES WIDGET [NEW] ────────────────────────────
    story += [Spacer(1, 8)]
    new_box_content = [
        [new_tag("NEW ADDITION — Revenue Element #1: Live Urgency Widget")],
    ]
    nb = Table(new_box_content, colWidths=[6.75 * inch])
    nb.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NEW_BG),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 1, NEW_FG),
    ]))
    story += [nb, Spacer(1, 4)]
    story += h2("Today's Top Model Edges")
    story += body(
        "Place this widget immediately after the opening paragraph — before the tools list. "
        "It intercepts users at the moment of highest intent and immediately demonstrates "
        "the value proposition: live proof of model output rather than several paragraphs of "
        "explanation."
    )
    edge_data = [
        [Paragraph("<b>Match / Market</b>", CAP),
         Paragraph("<b>Model Prob</b>", CAP),
         Paragraph("<b>Market Implied</b>", CAP),
         Paragraph("<b>Edge</b>", CAP),
         Paragraph("<b>Signal</b>", CAP)],
        ["[Team A vs Team B]  1X2", "58.4%", "52.1%", "+6.3pp",
         Paragraph("<b><font color='#1A6B3C'>BET</font></b>", CAP)],
        ["[Player]  Pts O 22.5",   "61.2%", "54.0%", "+7.2pp",
         Paragraph("<b><font color='#1A6B3C'>BET</font></b>", CAP)],
        ["[Team C vs D]  BTTS Yes","55.8%", "51.3%", "+4.5pp",
         Paragraph("<b><font color='#E65C00'>LEAN</font></b>", CAP)],
    ]
    et = Table(edge_data, colWidths=[2.4*inch, 1.0*inch, 1.2*inch, 0.8*inch, 1.0*inch])
    et.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#C0C8D8")),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [LGRAY, WHITE]),
        ("ALIGN",         (1, 0), (-1, -1), "CENTER"),
    ]))
    story += [et, Spacer(1, 4)]
    story += note("Implementation: JavaScript fetch() against wc-xray.json with "
                  "?t=Date.now() cache-bust. Falls back to 'Check back on match days' "
                  "when no live data. Each row links to the relevant tool page. "
                  "This widget is the single highest-converting element on the page.")
    story += cta_bar(["See full Market X-Ray analysis  →  wizardofodds.com/sports-odds/world-cup-market-xray/"])

    # ── SECTION 3 · SPORTSBOOK CTA BANNER [NEW] ───────────────────────────────
    story += [Spacer(1, 6)]
    nb2 = Table([[new_tag("NEW ADDITION — Revenue Element #2: Pre-Tool Sportsbook CTA")]],
                colWidths=[6.75 * inch])
    nb2.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NEW_BG),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 1, NEW_FG),
    ]))
    story += [nb2, Spacer(1, 4)]
    story += sbook_cta_box(
        "Before You Bet — Compare Lines at the Wizard's Recommended Sportsbooks\n"
        "The tools show you where the value is. The sportsbooks below are where you act on it.\n"
        "→ Compare Sportsbooks at WizardOfOdds   |   wizardofodds.com/online-sports-betting/"
    )
    story += note("Place this banner directly above the 'Explore Our Prediction Tools' section. "
                  "This intercepts users before they dive into tool descriptions and introduces "
                  "the affiliate funnel at the moment of highest general intent. "
                  "Replace /online-sports-betting/ with your affiliate-tracked URL.")

    # ── SECTION 4 · TOOL DESCRIPTIONS ─────────────────────────────────────────
    story += section("Explore Our Prediction Tools")
    story += body(
        "This suite of tools is built to analyse sports and betting markets through a "
        "consistent, probability-based modelling framework.",
        "Instead of treating each sport or market in isolation, the system applies "
        "structured statistical methods across players, teams, and live pricing to produce "
        "comparable, data-driven outputs. The goal is to connect performance modelling with "
        "market behaviour, so projections, edges, and outcomes are evaluated within the "
        "same analytical structure."
    )

    # ─── Market X-Ray ──────────────────────────────────────────────────────────
    story += [Spacer(1, 8)]
    story += tool_header("Market X-Ray", badge="+10.9% Rolling CLV · 25 Markets Evaluated")
    story += [Spacer(1, 4)]
    story += body(
        "Market X-Ray is a live market analysis tool that compares model-generated "
        "probabilities with real-time sportsbook odds across all available markets. It is "
        "designed to identify inefficiencies by measuring where pricing deviates from "
        "model-based expectations and translating those differences into structured signals.",
        "For each market, the system calculates probability estimates and compares them "
        "directly to live odds. From this comparison, it derives key metrics including edge "
        "(in percentage points), expected value (EV), and confidence grading.",
        "It also produces structured action indicators based on predefined model thresholds "
        "— BET, LEAN, or WAIT — to indicate whether a market meets defined value thresholds.",
        "During live events, the system updates approximately every 30 seconds, "
        "incorporating changes in odds and in-game developments to ensure projections remain "
        "current. This allows the model to reflect both pre-match structure and live market "
        "movement within the same framework.",
        "Performance is tracked using closing line value (CLV), which measures how "
        "model-based pricing compares to the final market line before an event begins. The "
        "system is currently running at +10.9% rolling CLV, meaning that across 25 evaluated "
        "markets, model probabilities have consistently been higher than the closing market "
        "implied.",
        "Rather than simply displaying odds, Market X-Ray evaluates market efficiency by "
        "benchmarking pricing against a predictive model. This allows it to distinguish "
        "between surface-level price movement and structurally mispriced markets.",
        "Consistent positive CLV is used as a long-term validation signal, indicating "
        "whether the model is systematically identifying value relative to the most "
        "efficient available market price."
    )
    story += note("Internal link: wizardofodds.com/article/expected-value-in-player-prop-betting/")
    story += cta_bar([
        "Launch Market X-Ray  →  wizardofodds.com/sports-odds/world-cup-market-xray/",
        "Compare Sportsbook Lines  →  wizardofodds.com/online-sports-betting/",
    ])

    # ─── WNBA ─────────────────────────────────────────────────────────────────
    story += [Spacer(1, 6)]
    story += tool_header("WNBA Player Props Predictive Model")
    story += [Spacer(1, 4)]
    story += body(
        "This model estimates how WNBA players are likely to perform in key statistical "
        "categories such as points, rebounds, and assists. It replaces intuition-based "
        "predictions with probability-driven projections built from historical data, usage "
        "profiles, and real-time context, helping assess whether sportsbook lines accurately "
        "reflect expected performance.",
        "The model begins with mean projections, which estimate a player's expected output "
        "based on factors such as minutes, usage rate, efficiency, pace, injuries, and "
        "rotation changes.",
        "This provides a central performance baseline, but because sportsbook prop lines are "
        "not built around simple averages, additional modelling is required to capture the "
        "full distribution of outcomes.",
        "To address this, the model uses simulation to generate thousands of possible game "
        "scenarios. This produces a probability curve for each stat line, estimating how "
        "often a player finishes over or under a given number.",
        "These probabilities are then compared directly to sportsbook odds to identify "
        "pricing inefficiencies and potential value.",
        "In practice, the model connects expected performance (mean projections), outcome "
        "variability (simulation), and market pricing (odds) into a single framework. The "
        "objective is not exact prediction of results, but identification of situations "
        "where model probabilities differ from implied market probabilities."
    )
    story += cta_bar([
        "Pre-Game Edge Board  →  wizardofodds.com/sports-odds/wnba-predictions/",
        "PMF Distributions  →  wizardofodds.com/sports-odds/wnba-distributions/",
        "Live Edges  →  wizardofodds.com/sports-odds/wnba-live-edges/",
        "Best WNBA Prop Books  →  wizardofodds.com/online-sports-betting/",
    ])

    # ─── NFL & College Football ────────────────────────────────────────────────
    story += [Spacer(1, 6)]
    story += tool_header("NFL & College Football Prediction System")
    story += [Spacer(1, 4)]
    story += body(
        "This system evaluates team strength across both the NFL and college football, "
        "including the FBS (Football Bowl Subdivision) and FCS (Football Championship "
        "Subdivision). It is designed to move beyond win–loss records by measuring "
        "underlying performance quality using structured statistical inputs.",
        "The model combines several key components: a team ranking system that evaluates "
        "overall strength independent of record, margin of victory to capture scoring "
        "dominance, and points-based efficiency metrics to assess offensive and defensive "
        "performance.",
        "It also applies cross-level adjustments to account for differences in competition "
        "strength between NFL, FBS, and FCS teams.",
        "Using these inputs, the model generates win probabilities, expected score ranges, "
        "and comparative strength ratings between teams.",
        "Over time, it also tracks performance trends, allowing it to identify teams that "
        "are improving, declining, overperforming, or underperforming relative to their "
        "record.",
        "Rather than relying on standings or simple outcomes, the system focuses on the "
        "underlying quality of performance that drives results. This allows for a more "
        "stable and consistent view of team strength across different levels of competition."
    )
    story += note("Internal links: wizardofodds.com/games/sports-betting/nfl  "
                  "| wizardofodds.com/games/sports-betting/college-football/")
    story += cta_bar([
        "NFL Rankings  →  wizardofodds.com/games/sports-betting/nfl/",
        "College Football  →  wizardofodds.com/games/sports-betting/college-football/",
        "Best NFL Books  →  wizardofodds.com/online-sports-betting/",
    ])

    # ─── Tennis ───────────────────────────────────────────────────────────────
    story += [Spacer(1, 6)]
    story += tool_header("Tennis Predictive Model")
    story += [Spacer(1, 4)]
    story += body(
        "This model forecasts outcomes in professional tennis using player-level performance "
        "data, both before matches and during live play. It is designed to capture not only "
        "who is likely to win, but how competitive a match is expected to be and how "
        "performance evolves across sets.",
        "Player strength is evaluated using multiple inputs, including recent form, "
        "head-to-head history, surface performance (hard court, clay, grass), and "
        "serve/return efficiency. These factors are combined to produce a baseline "
        "expectation of match performance under normal conditions.",
        "The model then incorporates variability through statistical simulation, generating "
        "a range of possible match outcomes. This allows it to estimate probabilities for "
        "match winners, total sets played, and margin of victory in sets.",
        "When live data is available, the model updates dynamically using in-match "
        "statistics and momentum indicators. This enables projections to adjust in real "
        "time as conditions change, rather than remaining fixed before the match begins.",
        "The system focuses on match structure as much as outcome to provide a consistent "
        "framework for understanding both expected results and how those results are likely "
        "to unfold."
    )
    story += cta_bar([
        "Best Tennis Betting Sites  →  wizardofodds.com/online-sports-betting/",
    ])

    # ── SECTION 5 · WORLD CUP ─────────────────────────────────────────────────
    story += [PageBreak()]
    story += section("World Cup Prediction Models")
    story += body(
        "The World Cup prediction suite includes several tools that are used to model "
        "football match outcomes in different ways. Together, they cover everything from "
        "pre-match score predictions to live updates during the game.",
        "Each tool looks at the match from a slightly different angle and at a different "
        "point in time. Some focus on predicting the full range of possible scorelines "
        "before kick-off, while others update probabilities as the match is being played.",
        "Even though they work at different levels, they all come from the same underlying "
        "probability model, which keeps all markets and outputs consistent with each other."
    )

    # ─── Full Outcome PMF ──────────────────────────────────────────────────────
    story += [Spacer(1, 8)]
    story += tool_header("Full Outcome PMF (Probability Mass Function)")
    story += [Spacer(1, 4)]
    story += body(
        "The Full Outcome PMF is the core probabilistic output of the prediction model. "
        "It represents the probability of every possible regulation-time scoreline, with "
        "each probability corresponding to the chance that the match finishes with a "
        "specific number of home and away goals after 90 minutes plus stoppage time. Extra "
        "time and penalty shootouts are not included.",
        "The Full Outcome PMF is a joint score probability mass function (Joint Score PMF), "
        "represented as a two-dimensional probability matrix in which each cell gives the "
        "probability of a specific regulation-time scoreline: P(Home Goals = h, Away Goals = a).",
    )
    pmf_data = [
        [Paragraph("<b>Home Goals</b>", CAP), Paragraph("<b>Away Goals</b>", CAP),
         Paragraph("<b>Probability (illustrative)</b>", CAP)],
        ["0", "0", "8%"], ["1", "0", "12%"], ["1", "1", "11%"],
        ["2", "1", "9%"], ["…", "…", "…"],
    ]
    pt = Table(pmf_data, colWidths=[1.5*inch, 1.5*inch, 3.75*inch])
    pt.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#C0C8D8")),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [LGRAY, WHITE]),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
    ]))
    story += [pt, Spacer(1, 6)]
    story += body(
        "Rather than modelling each betting market independently, all derived markets are "
        "calculated directly from this single probability distribution by summing the "
        "probabilities of the relevant scorelines. This ensures that every market is "
        "internally consistent and mathematically coherent.",
    )
    story += bullet(
        "<b>1X2 (Match Result):</b> Home Win = sum of scorelines where Home > Away; "
        "Draw = Home = Away; Away Win = Away > Home.",
        "<b>Totals (O/U):</b> Over 2.5 = sum where total goals ≥ 3; Under 2.5 = total ≤ 2.",
        "<b>BTTS Yes:</b> Sum of scorelines where both teams score ≥ 1 goal.",
        "<b>Clean Sheets:</b> Home CS = away scores 0; Away CS = home scores 0.",
    )
    story += cta_bar([
        "View PMF Distributions  →  wizardofodds.com/sports-odds/world-cup-2026-predictions/probability-model/",
        "Best World Cup Books  →  wizardofodds.com/online-sports-betting/",
    ])

    # ─── Today's World Cup Predictions ────────────────────────────────────────
    story += [Spacer(1, 6)]
    story += tool_header("Today's World Cup Predictions")
    story += [Spacer(1, 4)]
    story += body(
        "Today's World Cup Predictions displays every FIFA World Cup match for today that "
        "has been evaluated by the model. For each fixture, the model generates a complete "
        "Joint Score Probability Mass Function (PMF), assigning a probability to every "
        "possible regulation-time scoreline.",
        "All probabilities refer to the result after 90 minutes plus stoppage time only. "
        "Extra time and penalty shootouts are not included, making these predictions "
        "suitable for standard 90-minute betting markets.",
        "Each match row provides a summary of the model's predictions. Selecting (or "
        "expanding) a row reveals the complete set of derived probabilities, including: "
        "full scoreline distribution, 1X2, exact score, over/under goal totals, BTTS, "
        "clean sheets, and additional markets derived from the underlying Joint Score PMF.",
        "Because every market is derived from the same probability distribution, the "
        "predictions remain internally consistent, ensuring that all reported probabilities "
        "align with one another mathematically."
    )
    story += cta_bar([
        "Today's Predictions  →  wizardofodds.com/sports-odds/world-cup-2026-predictions/",
        "World Cup Odds &amp; Sportsbooks  →  wizardofodds.com/online-sports-betting/",
    ])

    # ─── Live PMF Engine ──────────────────────────────────────────────────────
    story += [Spacer(1, 6)]
    story += tool_header("Live PMF Engine")
    story += [Spacer(1, 4)]
    story += body(
        "A Live PMF Engine is a real-time, score-conditional probabilistic model that "
        "estimates a full probability mass function (PMF) over all possible regulation-time "
        "final scores given the current match state at time t (including score and time "
        "remaining). It is updated approximately every five minutes.",
        "In other words, at any moment during a match, the model computes "
        "P(final home = h, away = a) for every possible scoreline at the end of regulation "
        "time, producing a complete distribution of outcomes rather than a single prediction.",
        "The system is score-conditional, meaning its output depends on the exact game "
        "state at time t. Using a non-homogeneous hazard model, it allows scoring rates to "
        "vary over time — reflecting changes in pace, strategy, or game pressure.",
        "Betting markets such as moneylines, spreads, and totals are derived from this "
        "underlying probability distribution, which is recalculated as the PMF updates."
    )
    story += cta_bar([
        "Launch Live PMF Engine  →  wizardofodds.com/sports-odds/world-cup-2026-predictions/live/",
        "Live Betting Sportsbooks  →  wizardofodds.com/online-sports-betting/",
    ])

    # ─── Live Pitch ───────────────────────────────────────────────────────────
    story += [Spacer(1, 6)]
    story += tool_header("World Cup 2026 Live Pitch")
    story += [Spacer(1, 4)]
    story += body(
        "The WC 2026 Live Pitch tool is a real-time football prediction system that "
        "estimates the chances of each team winning a match as it progresses. It works by "
        "starting with pre-match team strength ratings based on historical performance and "
        "overall quality, then using a probability model to simulate possible match outcomes.",
        "As the match unfolds, the tool continuously updates its calculations based on "
        "events such as goals, red cards, and time remaining. Each event changes the "
        "probability of different outcomes because it affects how likely each team is to "
        "score or recover.",
        "Behind the scenes, the system repeatedly simulates the rest of the match many "
        "times using statistical methods — often goal-based models like Poisson distributions "
        "— and averages the results. This produces updated percentages for win, draw, and "
        "loss at any given moment.",
        "In simple terms, it is not a betting game but a dynamic calculator that constantly "
        "answers the question: 'If the match continued from this state, what are the most "
        "likely outcomes?'"
    )
    story += cta_bar([
        "Launch Live Pitch  →  wizardofodds.com/sports-odds/world-cup-2026-predictions/live-pitch/",
        "World Cup Live Betting  →  wizardofodds.com/online-sports-betting/",
    ])

    # ── SECTION 6 · HOW TO USE ─────────────────────────────────────────────────
    story += [PageBreak()]
    story += section("How to Use These Prediction Tools")
    story += body(
        "Each tool on the platform follows a consistent workflow, even though the exact "
        "outputs vary by sport or market. The key idea is to move from raw probability "
        "modelling to interpretation, and finally to comparison with sportsbook pricing."
    )
    story += note("Schema: Add HowTo JSON-LD to &lt;head&gt; — see Section 9 below.")

    steps = [
        ("#1", "Start with the Model Output",
         "The process begins with the model generating its core output: a probability-based "
         "projection. Depending on the tool, this might take the form of player performance "
         "distributions (such as points, rebounds, or assists), team-level win probabilities "
         "and expected score ranges, or full match outcome distributions. This initial output "
         "represents the model's 'fair value' view of the event before any market context "
         "is considered."),
        ("#2", "Understand the Probability, Not Just the Pick",
         "Once the probabilities are produced, the focus shifts away from simply asking who "
         "will win. Instead, the output is interpreted as a distribution of possible outcomes: "
         "how likely each outcome is, how performance is spread across different scenarios, "
         "and how much natural variability exists. Understanding this distribution is essential "
         "because it reflects uncertainty rather than a single predicted result."),
        ("#3", "Compare to Market Odds",
         "The next step is to compare model probabilities directly to sportsbook odds. This "
         "is where potential value is identified. When the model assigns a higher probability "
         "to an outcome than what is implied by the odds, it may indicate a positive expected "
         "value opportunity. Conversely, when the model probability is lower, the market may "
         "be overpriced relative to the model. This comparison is the core mechanism for "
         "evaluating efficiency in betting lines."),
        ("#4", "Use Simulation Outputs for Range Thinking",
         "Many tools include simulation outputs, which help shift thinking from single-point "
         "estimates to full outcome ranges. These simulations generate a wide distribution of "
         "possible results, showing not just averages but also how often different thresholds "
         "are reached. This makes it easier to understand variance and avoid overconfidence "
         "in any single projected number."),
        ("#5", "Use Live Tools for Real-Time Adjustments",
         "Live tools extend this framework into real-time environments. These systems "
         "continuously update based on the current game state — including score, time "
         "remaining, key events, and changes in betting markets. They are designed for "
         "in-play analysis, where probabilities evolve dynamically rather than remaining "
         "fixed before the event begins."),
    ]

    for num, title, desc in steps:
        row = Table([
            [Paragraph(num, STEP_NUM),
             [Paragraph(title, STEP_TITLE), Paragraph(desc, BODY_J)]]
        ], colWidths=[0.5 * inch, 6.25 * inch])
        row.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (1, 0), (1, -1), 8),
        ]))
        story += [row, Spacer(1, 4)]

    # ── SECTION 7 · WHY USE ────────────────────────────────────────────────────
    story += section("Why Use The Wizard's Prediction Tools?")
    story += body(
        "The Wizard's Prediction Tools are built around probability modelling instead of "
        "opinion-based analysis.",
        "Each tool breaks down sports events into measurable outcomes and assigns "
        "probabilities to them, so the focus stays on how likely something is rather than "
        "on trying to force a single prediction.",
        "The system uses the same underlying approach across different sports and markets. "
        "Player props, team matchups, and football scorelines are all expressed as "
        "probability distributions. That keeps everything on the same scale and makes it "
        "easier to compare different types of bets without switching logic or methods.",
        "A key part of the process is how the tools interact with sportsbook pricing. The "
        "models generate their own probabilities, and then those are compared directly to "
        "market odds. Differences between the two highlight where the market may be pricing "
        "an outcome higher or lower than the model expects. This is the main way potential "
        "value is identified.",
        "Simulation is used to show how results can vary in practice, not just what the "
        "average outcome looks like. Instead of focusing on a single number, the tools show "
        "a range of possible outcomes and how often they appear. That helps put volatility "
        "into context, especially in markets like player props or totals where results can "
        "swing quite a bit.",
        "Live tools extend this into in-play analysis. As games move forward, the models "
        "adjust based on score, time remaining, and key events. Odds shifts are also "
        "reflected in real time. This keeps the output aligned with what is happening in "
        "the match rather than staying fixed at pre-match assumptions.",
        "All in all, these tools help you look at sports through probabilities instead of "
        "opinions. They show how outcomes are priced by the model and how that compares to "
        "the sportsbook, so you can see where things line up and where they don't."
    )

    # ── SECTION 8 · RECOMMENDED SPORTSBOOKS [NEW] ─────────────────────────────
    story += [Spacer(1, 4)]
    nb3 = Table([[new_tag("NEW ADDITION — Revenue Element #3: Dedicated Sportsbook Section")]],
                colWidths=[6.75 * inch])
    nb3.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NEW_BG),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 1, NEW_FG),
    ]))
    story += [nb3, Spacer(1, 4)]
    story += h2("Recommended Sportsbooks")
    story += body(
        "The Wizard has evaluated hundreds of sportsbooks for odds quality, prop market "
        "depth, live betting availability, and payout reliability. The tools on this page "
        "are most useful when you have access to competitive lines — the sportsbooks below "
        "consistently rank highest on the metrics the model measures."
    )
    story += cta_bar([
        "See the Full Sportsbook Rankings at WizardOfOdds  →  wizardofodds.com/online-sports-betting/",
    ])
    story += note("Placement: This section goes directly before the FAQ. "
                  "Replace the CTA URL with your affiliate-tracked deep link for each "
                  "featured sportsbook — this is where revenue attribution lives. "
                  "Availability varies by region. Include a brief legal disclaimer.")

    # ── Play Responsibly ───────────────────────────────────────────────────────
    story += [Spacer(1, 4)]
    story += [Paragraph("<i>Play responsibly!</i>", NOTE)]
    story += [Spacer(1, 6)]

    # ── SECTION 9 · FAQ ────────────────────────────────────────────────────────
    story += section("FAQ")
    story += note("Add FAQPage JSON-LD schema for all 11 questions to the page &lt;head&gt;. "
                  "This unlocks Google FAQ rich results. See schema block below.")

    faqs = [
        ("1. What are these prediction tools?",
         "These are probability-based models that break down sports and betting markets into "
         "structured outcomes. Instead of focusing on opinions or single predictions, they "
         "show how likely different results are across players, teams, and matches."),
        ("2. Who are prediction tools meant for?",
         "They are mainly for users who already follow sports betting and want a more "
         "structured way to analyse it. This includes people comparing odds across sportsbooks, "
         "tracking value over time, or looking at player props, totals, and match markets in "
         "more detail."),
        ("3. Do prediction tools give guaranteed predictions?",
         "No. The tools don't produce guaranteed outcomes or fixed picks. They generate "
         "probability distributions, which show how likely different results are rather than "
         "predicting a single answer."),
        ("4. What is a probability distribution?",
         "It's a full range of possible outcomes with a probability attached to each one. "
         "Instead of saying 'this will happen,' it shows how often each outcome could happen "
         "across many scenarios."),
        ("5. Are live tools different from pre-match tools?",
         "Yes. Live tools update during the game based on score, time, and events. Pre-match "
         "tools stay fixed before kickoff, while live models adjust continuously as the match "
         "unfolds."),
        ("6. Do I need advanced betting knowledge to use prediction tools?",
         "No advanced background is required, but the tools are designed for users who are "
         "comfortable with betting markets and want a more structured, data-driven approach."),
        ("7. Are prediction tools financial advice?",
         "No. They are analytical tools for studying probabilities and market pricing. They "
         "don't guarantee results and should not be treated as financial advice."),
        ("8. Are these tools free to use?",
         "Yes. The prediction tools available on Wizard of Odds are designed to provide users "
         "with access to probability-based sports analysis, including pre-match forecasts, live "
         "updates, and market comparison tools. Availability may vary depending on the sport, "
         "event, and stage of development, as new models and features continue to be added."),
        # NEW FAQ questions
        ("9. Where can I bet on World Cup 2026 matches?  [NEW]",
         "The Wizard's sportsbook guide lists the top-rated books for World Cup betting, rated "
         "on odds quality, market depth, and reliability. "
         "→ wizardofodds.com/online-sports-betting/"),
        ("10. Which sportsbooks offer the best player prop markets?  [NEW]",
         "Prop market depth varies significantly between books. The Wizard's sportsbook "
         "comparison page ranks books specifically on prop availability and line quality. "
         "→ wizardofodds.com/online-sports-betting/"),
        ("11. How do I use these model outputs to identify value bets?  [NEW]",
         "Start with any tool's model probability for an outcome, then compare it to the "
         "implied probability from your sportsbook's odds. When the model's probability is "
         "meaningfully higher than the market-implied probability, that difference is the edge. "
         "The Market X-Ray tool does this comparison automatically across all available markets. "
         "→ wizardofodds.com/sports-odds/world-cup-market-xray/"),
    ]

    for i, (q, a) in enumerate(faqs):
        is_new = i >= 8
        q_style = ps(f"fq{i}", fontName="Helvetica-Bold", fontSize=9.5,
                     textColor=NEW_FG if is_new else NAVY,
                     leading=14, spaceBefore=6, spaceAfter=1, alignment=TA_LEFT)
        story += [Paragraph(q, q_style), Paragraph(a, FAQ_A)]

    story += [Spacer(1, 6)]
    story += note("Questions 9–11 are NEW additions. They serve both SEO (additional keyword "
                  "queries captured) and conversion (each answer contains an affiliate CTA). "
                  "Replace the CTA URLs with tracked affiliate links.")

    # ── SECTION 10 · SCHEMA MARKUP ────────────────────────────────────────────
    story += [PageBreak()]
    story += section("Schema Markup — Add to &lt;head&gt;")
    story += body(
        "Both blocks below should be included inside a single "
        "&lt;script type='application/ld+json'&gt; tag in the page &lt;head&gt;. "
        "This is a near-zero-effort change for a potentially significant SEO lift."
    )

    story += h2("HowTo Schema (How to Use — 5 Steps)")
    howto_code = (
        '{\n'
        '  "@context": "https://schema.org",\n'
        '  "@type": "HowTo",\n'
        '  "name": "How to Use the Wizard\'s Sports Prediction Tools",\n'
        '  "step": [\n'
        '    { "@type": "HowToStep", "name": "Start with the Model Output",\n'
        '      "text": "The process begins with the model generating its core output..." },\n'
        '    { "@type": "HowToStep", "name": "Understand the Probability, Not Just the Pick",\n'
        '      "text": "Interpret the output as a distribution of possible outcomes..." },\n'
        '    { "@type": "HowToStep", "name": "Compare to Market Odds",\n'
        '      "text": "Compare model probabilities directly to sportsbook odds..." },\n'
        '    { "@type": "HowToStep", "name": "Use Simulation Outputs for Range Thinking",\n'
        '      "text": "Use simulation outputs to shift from point estimates to ranges..." },\n'
        '    { "@type": "HowToStep", "name": "Use Live Tools for Real-Time Adjustments",\n'
        '      "text": "Live tools update continuously based on current game state..." }\n'
        '  ]\n'
        '}'
    )
    CODE_STYLE = ps("code", fontName="Courier", fontSize=7.5,
                    textColor=DKGRAY, leading=11, alignment=TA_LEFT)
    code_t = Table([[Preformatted(howto_code, CODE_STYLE)]],
                   colWidths=[6.75 * inch])
    code_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LGRAY),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 0.5, MID),
    ]))
    story += [code_t, Spacer(1, 10)]

    story += h2("FAQPage Schema (all 11 questions)")
    story += body(
        "Populate the mainEntity array with all 11 Q&A pairs from Section 9. "
        "Template for each entry:"
    )
    faq_code = (
        '{\n'
        '  "@context": "https://schema.org",\n'
        '  "@type": "FAQPage",\n'
        '  "mainEntity": [\n'
        '    {\n'
        '      "@type": "Question",\n'
        '      "name": "What are these prediction tools?",\n'
        '      "acceptedAnswer": {\n'
        '        "@type": "Answer",\n'
        '        "text": "These are probability-based models..."\n'
        '      }\n'
        '    },\n'
        '    // ... repeat for all 11 questions\n'
        '  ]\n'
        '}'
    )
    code_t2 = Table([[Preformatted(faq_code, CODE_STYLE)]],
                    colWidths=[6.75 * inch])
    code_t2.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LGRAY),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 0.5, MID),
    ]))
    story += [code_t2, Spacer(1, 10)]

    # ── SECTION 11 · MISSING SHELL PAGES ──────────────────────────────────────
    story += section("Missing WoO Shell Pages to Build")
    story += body(
        "The blueprint links to these tool URLs, but the corresponding WoO shell pages "
        "(following the deploy/pages/*.html pattern) do not yet exist in the repository. "
        "Each should be built as a WoO chrome wrapper with an iframe pointing to the "
        "sportsodds.wizardofodds.com tool URL — same pattern as wnba-predictions.html."
    )
    missing_data = [
        [Paragraph("<b>Tool</b>", CAP),
         Paragraph("<b>Target WoO URL</b>", CAP),
         Paragraph("<b>Priority</b>", CAP)],
        ["World Cup PMF Distributions",
         "/sports-odds/world-cup-2026-predictions/probability-model/",
         Paragraph("<b><font color='#8B1A1A'>HIGH</font></b>", CAP)],
        ["Today's WC Predictions",
         "/sports-odds/world-cup-2026-predictions/",
         Paragraph("<b><font color='#8B1A1A'>HIGH</font></b>", CAP)],
        ["Live PMF Engine",
         "/sports-odds/world-cup-2026-predictions/live/",
         Paragraph("<b><font color='#8B1A1A'>HIGH</font></b>", CAP)],
        ["Live Pitch",
         "/sports-odds/world-cup-2026-predictions/live-pitch/",
         Paragraph("<b><font color='#8B1A1A'>HIGH</font></b>", CAP)],
        ["NFL/College Football System",
         "Not yet linked to a live tool",
         Paragraph("<font color='#E65C00'>MEDIUM</font>", CAP)],
        ["Tennis Predictive Model",
         "Not yet linked to a live tool",
         Paragraph("<font color='#E65C00'>MEDIUM</font>", CAP)],
    ]
    mt = Table(missing_data, colWidths=[2.2*inch, 3.5*inch, 1.05*inch])
    mt.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#C0C8D8")),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [LGRAY, WHITE]),
        ("ALIGN",         (2, 0), (2, -1), "CENTER"),
    ]))
    story += [mt, Spacer(1, 6)]

    # ── SECTION 12 · IMPLEMENTATION NOTES ────────────────────────────────────
    story += section("Implementation Notes for the Developer")

    notes_data = [
        [Paragraph("<b>#</b>", CAP),
         Paragraph("<b>Item</b>", CAP),
         Paragraph("<b>Detail</b>", CAP)],
        ["1",
         Paragraph("<b>Live Edges Widget</b>", BODY),
         "JavaScript fetch() against wc-xray.json with ?t=Date.now() cache-bust. "
         "Graceful fallback to static message when no live data. "
         "Each row links to the relevant tool. Highest-converting element on the page."],
        ["2",
         Paragraph("<b>Affiliate URLs</b>", BODY),
         "All sportsbook CTAs currently point to /online-sports-betting/ as a placeholder. "
         "Replace with the affiliate-tracked deep link specific to each sport/sportsbook. "
         "Revenue attribution lives in those tracking parameters."],
        ["3",
         Paragraph("<b>FAQ + HowTo Schema</b>", BODY),
         "Drop both JSON-LD blocks (Section 10) into the page &lt;head&gt; inside a single "
         "&lt;script type='application/ld+json'&gt; tag. Near-zero effort for a potentially "
         "significant Google rich results lift."],
        ["4",
         Paragraph("<b>Page Architecture</b>", BODY),
         "This is a content page, NOT an iframe wrapper. Use the WoO shell template "
         "(deploy/pages/*.html) for the ~990-line nav + ~250-line footer, but replace "
         "the &lt;iframe&gt; block with the full editorial HTML from this document."],
        ["5",
         Paragraph("<b>Breadcrumb Depth</b>", BODY),
         "Set 3-level breadcrumbs: Home > Sports Prediction Tools > [Tool Name] "
         "on child tool pages. Builds semantic hierarchy for Google."],
    ]
    nt = Table(notes_data, colWidths=[0.3*inch, 1.5*inch, 4.95*inch])
    nt.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#C0C8D8")),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [LGRAY, WHITE]),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("ALIGN",         (0, 0), (0, -1), "CENTER"),
    ]))
    story += [nt, Spacer(1, 10)]

    # ── FOOTER ────────────────────────────────────────────────────────────────
    story += [hr()]
    story += [Paragraph(
        "Sports Prediction Tools Hub Page — Revenue-Optimised Blueprint  ·  July 2026  ·  "
        "WizardOfOdds  ·  Original editorial content unchanged; conversion architecture added.  ·  "
        "For internal use only. Not financial advice.",
        NOTE
    )]

    doc.build(story)
    print(f"  ✓  {path}")
    return path


if __name__ == "__main__":
    print("Generating Sports Prediction Tools Hub Page Blueprint PDF …")
    p = build()
    print(f"\nFile saved: {p}")
