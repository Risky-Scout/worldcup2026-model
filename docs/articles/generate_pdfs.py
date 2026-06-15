"""
Generate PDF articles for wizardofodds.com.
Run: python3.10 docs/articles/generate_pdfs.py
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.colors import HexColor
from pathlib import Path

OUT_DIR = Path(__file__).parent

# ── Color palette ──────────────────────────────────────────────────────────────
GOLD        = HexColor("#d4af37")
DARK_BG     = HexColor("#0a0e1a")
ACCENT      = HexColor("#1a3a6b")
BODY_TEXT   = HexColor("#111111")
MUTED       = HexColor("#555555")
RULE_COLOR  = HexColor("#d4af37")
PAGE_BG     = HexColor("#f9f7f2")
LIGHT_GRAY  = HexColor("#f0f0f0")
MID_GRAY    = HexColor("#dddddd")
FORMULA_BG  = HexColor("#eef2ff")
FORMULA_FG  = HexColor("#1a2060")
CALLOUT_BG  = HexColor("#fdf8ed")
H3_COLOR    = HexColor("#1a3a6b")
TABLE_ALT   = HexColor("#f5f5f5")
DARK_PANEL  = HexColor("#1a2030")

PAGE_W, PAGE_H = letter
L_MARGIN = 0.85 * inch
R_MARGIN = 0.85 * inch
BODY_WIDTH = PAGE_W - L_MARGIN - R_MARGIN

# ── Styles ─────────────────────────────────────────────────────────────────────
def make_styles():
    styles = {}

    styles["site"] = ParagraphStyle("site",
        fontName="Helvetica-Bold", fontSize=8,
        textColor=GOLD, spaceAfter=2, spaceBefore=0, alignment=TA_LEFT)

    styles["h1"] = ParagraphStyle("h1",
        fontName="Helvetica-Bold", fontSize=23,
        textColor=BODY_TEXT, spaceBefore=10, spaceAfter=8,
        leading=28)

    styles["subtitle"] = ParagraphStyle("subtitle",
        fontName="Helvetica-Oblique", fontSize=11,
        textColor=MUTED, spaceBefore=0, spaceAfter=8,
        leading=15)

    styles["h2"] = ParagraphStyle("h2",
        fontName="Helvetica-Bold", fontSize=14,
        textColor=BODY_TEXT, spaceBefore=22, spaceAfter=4,
        leading=18)

    styles["h3"] = ParagraphStyle("h3",
        fontName="Helvetica-Bold", fontSize=11,
        textColor=H3_COLOR, spaceBefore=14, spaceAfter=3,
        leading=14)

    styles["h4"] = ParagraphStyle("h4",
        fontName="Helvetica-Bold", fontSize=10,
        textColor=ACCENT, spaceBefore=10, spaceAfter=2,
        leading=13)

    styles["body"] = ParagraphStyle("body",
        fontName="Helvetica", fontSize=10,
        textColor=BODY_TEXT, spaceBefore=0, spaceAfter=6,
        leading=15, alignment=TA_JUSTIFY)

    styles["body_tight"] = ParagraphStyle("body_tight",
        fontName="Helvetica", fontSize=10,
        textColor=BODY_TEXT, spaceBefore=0, spaceAfter=3,
        leading=14, alignment=TA_JUSTIFY)

    styles["body_small"] = ParagraphStyle("body_small",
        fontName="Helvetica", fontSize=9,
        textColor=MUTED, spaceBefore=0, spaceAfter=4,
        leading=13, alignment=TA_LEFT)

    styles["bullet"] = ParagraphStyle("bullet",
        fontName="Helvetica", fontSize=10,
        textColor=BODY_TEXT, spaceBefore=2, spaceAfter=3,
        leading=14, leftIndent=20, firstLineIndent=-12)

    styles["bullet_bold"] = ParagraphStyle("bullet_bold",
        fontName="Helvetica-Bold", fontSize=10,
        textColor=BODY_TEXT, spaceBefore=3, spaceAfter=1,
        leading=14, leftIndent=20, firstLineIndent=-12)

    styles["formula_line"] = ParagraphStyle("formula_line",
        fontName="Courier", fontSize=9,
        textColor=FORMULA_FG, spaceBefore=0, spaceAfter=0,
        leading=13, leftIndent=0)

    styles["formula_comment"] = ParagraphStyle("formula_comment",
        fontName="Courier-Oblique", fontSize=8.5,
        textColor=HexColor("#555599"), spaceBefore=0, spaceAfter=0,
        leading=12, leftIndent=0)

    styles["callout_inner"] = ParagraphStyle("callout_inner",
        fontName="Helvetica", fontSize=9.5,
        textColor=HexColor("#2a2a40"), spaceBefore=0, spaceAfter=0,
        leading=14)

    styles["callout_label"] = ParagraphStyle("callout_label",
        fontName="Helvetica-Bold", fontSize=8.5,
        textColor=GOLD, spaceBefore=0, spaceAfter=3,
        leading=11)

    styles["disclaimer"] = ParagraphStyle("disclaimer",
        fontName="Helvetica-Oblique", fontSize=7.5,
        textColor=MUTED, spaceBefore=2, spaceAfter=0,
        leading=10, alignment=TA_CENTER)

    styles["tbl_header"] = ParagraphStyle("tbl_header",
        fontName="Helvetica-Bold", fontSize=8.5,
        textColor=GOLD, spaceBefore=0, spaceAfter=0, leading=11)

    styles["tbl_cell"] = ParagraphStyle("tbl_cell",
        fontName="Helvetica", fontSize=8.5,
        textColor=BODY_TEXT, spaceBefore=0, spaceAfter=0, leading=12)

    styles["url"] = ParagraphStyle("url",
        fontName="Helvetica", fontSize=8.5,
        textColor=ACCENT, spaceBefore=2, spaceAfter=6, leading=12)

    styles["note"] = ParagraphStyle("note",
        fontName="Helvetica-Oblique", fontSize=9,
        textColor=HexColor("#444444"), spaceBefore=4, spaceAfter=4,
        leading=13, alignment=TA_JUSTIFY)

    styles["section_intro"] = ParagraphStyle("section_intro",
        fontName="Helvetica", fontSize=10.5,
        textColor=HexColor("#222222"), spaceBefore=0, spaceAfter=8,
        leading=16, alignment=TA_JUSTIFY)

    return styles


# ── Helper drawing primitives ──────────────────────────────────────────────────

def rule(color=RULE_COLOR, thickness=0.75):
    return HRFlowable(width="100%", thickness=thickness, color=color,
                      spaceAfter=8, spaceBefore=4)

def thin_rule(color=MID_GRAY):
    return HRFlowable(width="100%", thickness=0.35, color=color,
                      spaceAfter=4, spaceBefore=4)

def gold_thin_rule():
    return HRFlowable(width="100%", thickness=0.4, color=GOLD,
                      spaceAfter=6, spaceBefore=2)

def sp(n=6):
    return Spacer(1, n)


def formula_box(lines, styles, width=None):
    """Render a list of strings as a monospaced formula box with light blue bg."""
    w = width or (BODY_WIDTH - 0.4 * inch)
    rows = []
    for line in lines:
        if line.startswith("#"):
            rows.append([Paragraph(line, styles["formula_comment"])])
        else:
            rows.append([Paragraph(line, styles["formula_line"])])
    t = Table(rows, colWidths=[w])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), FORMULA_BG),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("TOPPADDING",    (0, 0), (0, 0),   9),
        ("BOTTOMPADDING", (-1, -1), (-1, -1), 9),
        ("TOPPADDING",    (0, 1), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -2), 2),
        ("BOX",           (0, 0), (-1, -1), 0.6, HexColor("#a8b8e8")),
    ]))
    return t


def callout_box(text, styles, label=None, width=None):
    """Gold left-border callout highlight box."""
    w = width or (BODY_WIDTH - 0.1 * inch)
    inner_cells = []
    if label:
        inner_cells.append([Paragraph(label, styles["callout_label"])])
    inner_cells.append([Paragraph(text, styles["callout_inner"])])
    inner_t = Table(inner_cells, colWidths=[w - 26])
    inner_t.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    outer = Table([[inner_t]], colWidths=[w])
    outer.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), CALLOUT_BG),
        ("LINEBEFORE",    (0, 0), (0, -1),  3.5, GOLD),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("BOX",           (0, 0), (-1, -1), 0.4, HexColor("#e8d88c")),
    ]))
    return outer


def section_rule(styles):
    return HRFlowable(width="100%", thickness=0.45, color=GOLD,
                      spaceAfter=7, spaceBefore=1)


def dark_header_block(title, subtitle, styles):
    """Dark navy block used for section headers with gold title."""
    cells = [[Paragraph(title, ParagraphStyle("dh",
                    fontName="Helvetica-Bold", fontSize=13,
                    textColor=GOLD, leading=16, spaceBefore=0, spaceAfter=2))]]
    if subtitle:
        cells.append([Paragraph(subtitle, ParagraphStyle("ds",
                    fontName="Helvetica-Oblique", fontSize=9,
                    textColor=HexColor("#99aacc"), leading=12, spaceBefore=0))])
    t = Table(cells, colWidths=[BODY_WIDTH])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), DARK_BG),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("TOPPADDING",    (0, 0), (0, 0),   10),
        ("BOTTOMPADDING", (-1, -1), (-1, -1), 10),
        ("TOPPADDING",    (0, 1), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -2), 2),
    ]))
    return t


def styled_table(data, col_widths, styles, alt_start=1, compact=False):
    """Dark-header, alternating-row styled table."""
    pad = 4 if compact else 5
    t = Table(data, colWidths=col_widths)
    ts_cmds = [
        ("BACKGROUND",    (0, 0),  (-1, 0),  DARK_BG),
        ("TEXTCOLOR",     (0, 0),  (-1, 0),  GOLD),
        ("FONTNAME",      (0, 0),  (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0),  (-1, -1), 8.5),
        ("FONTNAME",      (0, 1),  (-1, -1), "Helvetica"),
        ("TEXTCOLOR",     (0, 1),  (-1, -1), BODY_TEXT),
        ("GRID",          (0, 0),  (-1, -1), 0.25, MID_GRAY),
        ("VALIGN",        (0, 0),  (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0),  (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0),  (-1, -1), pad),
        ("LEFTPADDING",   (0, 0),  (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0),  (-1, -1), 8),
        ("WORDWRAP",      (0, 0),  (-1, -1), True),
    ]
    for i in range(alt_start, len(data), 2):
        ts_cmds.append(("BACKGROUND", (0, i), (-1, i), TABLE_ALT))
    t.setStyle(TableStyle(ts_cmds))
    return t


# ── Page header / footer ────────────────────────────────────────────────────────

def _make_page_decorator(article_title=""):
    def decorator(canvas, doc):
        canvas.saveState()
        w = PAGE_W
        # ── Warm off-white page background ──────────────────────────────
        canvas.setFillColor(PAGE_BG)
        canvas.rect(0, 0, w, PAGE_H, fill=1, stroke=0)
        # ── Header bar ──────────────────────────────────────────────────
        # Dark navy top bar
        canvas.setFillColor(DARK_BG)
        canvas.rect(0, PAGE_H - 0.70 * inch, w, 0.70 * inch, fill=1, stroke=0)
        # Gold accent line at bottom of header bar
        canvas.setFillColor(GOLD)
        canvas.rect(0, PAGE_H - 0.72 * inch, w, 0.02 * inch, fill=1, stroke=0)
        # Site name
        canvas.setFont("Helvetica-Bold", 9)
        canvas.setFillColor(GOLD)
        canvas.drawString(L_MARGIN, PAGE_H - 0.47 * inch, "WIZARDOFODDS.COM")
        # Article title
        if article_title:
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(HexColor("#8899bb"))
            canvas.drawRightString(w - R_MARGIN, PAGE_H - 0.47 * inch, article_title)
        # ── Footer ──────────────────────────────────────────────────────
        # Thin footer bar
        canvas.setFillColor(LIGHT_GRAY)
        canvas.rect(0, 0, w, 0.68 * inch, fill=1, stroke=0)
        canvas.setFillColor(GOLD)
        canvas.rect(0, 0.67 * inch, w, 0.012 * inch, fill=1, stroke=0)
        # Page number
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(MUTED)
        canvas.drawCentredString(w / 2, 0.44 * inch, f"— Page {doc.page} —")
        canvas.setFont("Helvetica-Oblique", 7)
        canvas.setFillColor(HexColor("#777777"))
        canvas.drawCentredString(
            w / 2, 0.28 * inch,
            "All probabilities represent regulation time only.  "
            "WizardOfOdds.com  |  Please gamble responsibly."
        )
        canvas.restoreState()
    return decorator


def render(story, output_path: Path, title: str, short_title: str = ""):
    deco = _make_page_decorator(short_title)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=L_MARGIN,
        rightMargin=R_MARGIN,
        topMargin=0.95 * inch,
        bottomMargin=0.80 * inch,
        title=title,
        author="Wizard of Odds",
        subject="World Cup 2026 Prediction Model",
        creator="WizardOfOdds.com",
    )
    doc.build(story, onFirstPage=deco, onLaterPages=deco)
    size_kb = output_path.stat().st_size // 1024
    print(f"  {output_path.name}  ({size_kb} KB)")


# ═══════════════════════════════════════════════════════════════════════════════
# ARTICLE 1 — How the Model Works
# ═══════════════════════════════════════════════════════════════════════════════

def build_article1(styles):
    S = styles
    story = []

    # ── Title block ────────────────────────────────────────────────────────────
    story += [
        Paragraph("WIZARDOFODDS.COM", S["site"]),
        rule(),
        Paragraph("How the 2026 World Cup Prediction Model Works", S["h1"]),
        Paragraph(
            "A complete, mathematically rigorous guide to the joint score probability engine "
            "powering every prediction on this site — from the composite team ratings through "
            "the Bivariate Poisson, market reconciliation, calibration, and edge screening.",
            S["subtitle"]),
        rule(),
        sp(8),
    ]

    # ── Introduction ───────────────────────────────────────────────────────────
    story += [
        KeepTogether([
            Paragraph("Introduction", S["h2"]),
            gold_thin_rule(),
            Paragraph(
                "Predicting football is an exercise in structured humility. A single match "
                "produces roughly two or three goals from a cascade of decisions, deflections, "
                "and individual moments that no model can fully capture. Even the best football "
                "models in the world — the ones running inside sharp sportsbooks and professional "
                "syndicates — are wrong more often than they are right about any individual game.",
                S["body"]),
            Paragraph(
                "What a good model <i>can</i> do is get the probabilities right over a large "
                "number of matches. Assign 30% to outcomes that happen 30% of the time. Be "
                "faster than the public at incorporating new information. Identify specific "
                "markets where the bookmaker's price doesn't reflect the available evidence. "
                "That is a narrower ambition than predicting winners — but it is the one that "
                "leads to long-run results.",
                S["body"]),
        ]),
        Paragraph(
            "This model produces a <b>full joint probability mass function (PMF) over every "
            "possible regulation-time final score</b> for every 2026 FIFA World Cup match. "
            "Every market you see on the site — Over/Under, Both Teams to Score (BTTS), 1X2 "
            "result, correct score — is derived mechanically from this single two-dimensional "
            "grid of probabilities. The architecture guarantees internal consistency: the "
            "numbers cannot contradict each other because they all flow from one source of "
            "truth. The model cannot simultaneously output 'Home Win = 45%' and a set of "
            "correct-score probabilities that sum to 52% across all home-win scorelines — "
            "an inconsistency that appears on sites blending data from separate models.",
            S["body"]),
        Paragraph(
            "The pipeline runs without human intervention 24 hours a day. Six competing "
            "parametric score models are trained daily on the combined historical and 2026 "
            "tournament data. The best-performing model feeds a composite rating system "
            "built from six independent data sources. The result is reconciled against live "
            "bookmaker prices, run through an automated calibration framework, and screened "
            "for edge opportunities. Every stage is described below.",
            S["body"]),
        sp(8),
    ]

    # ── What a Joint Score PMF Is ──────────────────────────────────────────────
    story += [
        KeepTogether([
            Paragraph("What a Joint Score PMF Actually Is", S["h2"]),
            gold_thin_rule(),
            Paragraph(
                "Before describing the engine, it helps to understand precisely what it produces. "
                "A PMF is a Probability Mass Function — a complete assignment of probability to "
                "every possible discrete outcome. For a football match, the <b>joint score PMF</b> "
                "is a two-dimensional grid. Each cell (h, a) holds P(Home = h, Away = a): the "
                "probability that the home team scores exactly h goals and the away team scores "
                "exactly a goals in regulation time.",
                S["body"]),
        ]),
        Paragraph(
            "The grid extends from (0, 0) through whatever maximum makes sense — typically "
            "8 or 9 goals per team — plus an explicit tail-mass bucket for extreme scores "
            "beyond the grid boundary. Every cell, including the tail, must sum to "
            "<b>exactly 1.0</b>. This is not approximate. It is a hard constraint enforced "
            "at every stage of the pipeline. Any rounding is immediately corrected by "
            "normalizing the grid.",
            S["body"]),
        Paragraph(
            "Here is why the grid architecture matters. Every betting market is simply a "
            "different question about this same distribution — a different way of summing "
            "certain cells. The PMF contains the answer to every possible question "
            "about regulation-time outcomes:",
            S["body"]),
        sp(4),
        styled_table([
            ["Market",                  "PMF Calculation",                          "Example (2-team match)"],
            ["Over 2.5 goals",          "Sum all cells where h + a >= 3",           "Cells (0,3),(1,2),(2,1),(3,0),(2,2),(3,1),..."],
            ["Under 2.5 goals",         "Sum all cells where h + a <= 2",           "Cells (0,0),(0,1),(0,2),(1,0),(1,1),(2,0)"],
            ["Both Teams to Score",     "All cells: h >= 1 AND a >= 1",             "Everything except row h=0 and column a=0"],
            ["Home Win",                "All cells where h > a",                    "Cells (1,0),(2,0),(2,1),(3,0),(3,1),(3,2),..."],
            ["Draw",                    "All cells where h = a (main diagonal)",    "Cells (0,0),(1,1),(2,2),(3,3),..."],
            ["Away Win",                "All cells where a > h",                    "Cells (0,1),(0,2),(1,2),(0,3),(1,3),(2,3),..."],
            ["Correct score 2-1",       "Single cell P(h=2, a=1)",                  "One number read directly from grid"],
            ["Home clean sheet",        "Sum entire column a=0",                    "P(0,0)+P(1,0)+P(2,0)+P(3,0)+..."],
        ], [1.55*inch, 2.05*inch, BODY_WIDTH-3.6*inch], S),
        sp(8),
        callout_box(
            "There is no separate model for each market type. The PMF is the entire model, "
            "and all markets are different questions about the same distribution. This "
            "guarantees internal consistency — a property that does not hold on sites "
            "that blend data from different sources or use different models for different markets.",
            S, label="The Internal Consistency Guarantee"),
        sp(10),
    ]

    # ── Step 1: Composite Prior ────────────────────────────────────────────────
    story += [
        Paragraph("Step 1: Rating Every Team — The Composite Prior", S["h2"]),
        gold_thin_rule(),
        Paragraph(
            "The first task is assigning each of the 48 teams an <b>attack lambda</b> "
            "(lambda_att) and a <b>defense lambda</b> (lambda_def). These represent "
            "expected goals scored and conceded against an average opponent at a neutral "
            "venue. The 2026 global World Cup baseline is <b>1.30 goals per team per "
            "match</b>, calibrated from the 128 matches played across the 2018 and 2022 "
            "World Cups.",
            S["body"]),
        Paragraph(
            "No single rating system is reliable enough to trust alone. Club data does not "
            "transfer cleanly to international football. FIFA rankings can lag months behind "
            "actual form. Bookmaker odds contain genuine signal but can be distorted by "
            "public betting flow on marquee matches. The solution is a <b>composite prior</b> "
            "blended from six independent data sources, each contributing information that "
            "no other source has access to.",
            S["body"]),
        sp(6),
        dark_header_block("The Six Rating Sources", "Weights shown are for matches with market odds available", S),
        sp(6),
        styled_table([
            ["Source",                   "Primary Data",                    "Approx. Weight", "Key Strength",              "Primary Weakness"],
            ["1. Market-Implied",        "Bookmaker 1X2 odds (up to 6)",    "30%",            "Late team news, sharp money","Requires available odds"],
            ["2. FIFA Ranking",          "March 2026 points snapshot",      "~12%",           "Long-run int'l performance", "Infrequent updates"],
            ["3. Qualifying Record",     "Attack/defense efficiency",       "~10%",           "Campaign-specific form",     "Small sample sizes"],
            ["4. Pi Rating",             "Goal-margin Elo (penaltyblog)",   "~18%",           "Fast form updates",          "Noisy on flukes"],
            ["5. Elo Rating",            "Win/loss/draw (penaltyblog)",     "~35%",           "Stability, long-run signal", "Ignores goal margins"],
            ["6. Confederation Baseline","Historical WC averages by region","~5%",            "Prevents extreme estimates", "No team-level info"],
        ], [1.3*inch, 1.5*inch, 0.85*inch, 1.45*inch, BODY_WIDTH-5.1*inch], S),
        sp(10),
    ]

    story += [
        KeepTogether([
            Paragraph("Source 1: Market-Implied Strength (30% weight)", S["h3"]),
            Paragraph(
                "When bookmaker odds are available for a match, they encode information that "
                "no rating system can access: late team news, undisclosed injuries, sharp money "
                "from professional bettors, and the aggregate view of every serious analyst "
                "who has looked at the match. Sharp books are very good at this. Ignoring "
                "available market information is leaving real signal on the table.",
                S["body"]),
            Paragraph(
                "The model extracts market-implied attack and defense lambdas by "
                "reverse-engineering what team strengths would produce the bookmaker's "
                "observed 1X2 probabilities. Before doing this, the bookmaker margin "
                "must be removed. Raw quoted odds always include a margin of roughly "
                "5–8% that inflates the implied probabilities. <b>SHIN normalization</b> "
                "is applied to all odds from all bookmakers to convert them to fair "
                "(no-margin) probabilities. Using raw odds as fair probabilities would "
                "consistently bias every market comparison — this step is not optional.",
                S["body"]),
        ]),
        Paragraph(
            "Up to 6 sportsbooks contribute to each match's market picture: FanDuel, "
            "DraftKings, BetMGM, BetRivers, Caesars, and Fanatics. Their no-vig "
            "probabilities are averaged to produce a consensus view that smooths out "
            "any single book's idiosyncratic positioning.",
            S["body"]),
        Paragraph(
            "The 30% weight is empirically determined by minimizing log-loss on "
            "completed WC2026 matches. This is the single largest weight in the "
            "composite, reflecting the genuine information content of well-supplied "
            "sharp markets.",
            S["body"]),
        sp(4),

        KeepTogether([
            Paragraph("Source 2: FIFA Ranking — March 2026 (~12% weight)", S["h3"]),
            Paragraph(
                "FIFA's official ranking points system, converted to an attack lambda "
                "via a calibrated sigmoid mapping. FIFA rankings capture long-run "
                "international performance across all competitions — friendlies, "
                "qualifiers, continental championships — and provide a useful signal "
                "particularly for teams with limited recent competitive data.",
                S["body"]),
            Paragraph(
                "Primary weakness: FIFA rankings update infrequently and can reflect "
                "results from years prior. A team that had a dismal October 2025 qualifying "
                "window would see that reflected in an immediate Elo update but potentially "
                "not in the FIFA ranking until the next official release. The model uses "
                "the March 2026 snapshot — the last official pre-tournament update.",
                S["body"]),
        ]),
        sp(4),

        KeepTogether([
            Paragraph("Source 3: Qualifying Record (~10% weight)", S["h3"]),
            Paragraph(
                "Each team's attack and defense efficiency during their qualifying campaign, "
                "Bayesian-shrunk toward their confederation's average. The shrinkage scales "
                "with the number of competitive matches played:",
                S["body"]),
        ]),
        formula_box([
            "Shrinkage weight  =  n / (n + 3)",
            "",
            "# where n = number of qualifying matches played",
            "# 3 = prior strength (equivalent to ~3 'ghost' matches at the confederation avg)",
            "",
            "A team with n=18 qualifying matches gets weight 18/21 = 0.857",
            "A team with n=6 qualifying matches gets weight  6/9  = 0.667",
        ], S),
        sp(6),
        Paragraph(
            "A nation that dominated its qualifying group is genuinely more dangerous "
            "than one that scraped through on goal difference, and this source captures "
            "that signal directly from the competitive record rather than relying on "
            "rating proxies.",
            S["body"]),
        sp(4),

        KeepTogether([
            Paragraph("Source 4: Pi Rating (~18% effective weight)", S["h3"]),
            Paragraph(
                "The Pi rating, computed using the penaltyblog library, is a goal-margin-sensitive "
                "variant of Elo. Unlike standard Elo which updates only on match result "
                "(win/draw/loss), Pi updates on the actual score. A team winning 4-0 earns a "
                "substantially larger rating boost than one winning 1-0. This makes Pi more "
                "responsive to genuine performance shifts and better suited for a model whose "
                "primary target is predicting scores rather than just results.",
                S["body"]),
        ]),
        sp(4),

        KeepTogether([
            Paragraph("Source 5: Elo Rating (~35% effective weight)", S["h3"]),
            Paragraph(
                "Classic international Elo, also from penaltyblog, based on win/loss/draw "
                "outcomes only. Elo is more stable over long periods than Pi precisely because "
                "it does not react to score margins — a team cannot inflate its Elo by running "
                "up the score against a weaker opponent. It serves as a stabilizing anchor that "
                "prevents the prior from swinging too sharply on an unusual scoreline, and it "
                "is the dominant signal for teams whose Pi and market data are sparse or "
                "potentially noisy.",
                S["body"]),
        ]),
        sp(4),

        KeepTogether([
            Paragraph("Source 6: Confederation Baseline (~5% as a soft floor)", S["h3"]),
            Paragraph(
                "Historical World Cup attack averages by confederation provide the final input. "
                "These figures represent what teams from each confederation have historically "
                "scored against World Cup-caliber opponents at a neutral venue:",
                S["body"]),
            sp(4),
            styled_table([
                ["Confederation", "Historical WC Attack Lambda", "Historical WC Defense Lambda", "Notes"],
                ["CONMEBOL",      "1.45",                        "1.10",                         "Brazil, Argentina historically strong"],
                ["UEFA",          "1.35",                        "1.20",                         "Most teams, relatively balanced"],
                ["CONCACAF",      "1.20",                        "1.35",                         "Mexico strongest; field varies widely"],
                ["CAF",           "1.10",                        "1.30",                         "Senegal, Morocco recent strong performers"],
                ["AFC",           "1.10",                        "1.35",                         "Japan, South Korea; improving rapidly"],
                ["OFC",           "0.90",                        "1.45",                         "Australia departed; small confederation"],
            ], [1.1*inch, 1.35*inch, 1.35*inch, BODY_WIDTH-3.8*inch], S),
            sp(6),
            Paragraph(
                "This acts as a soft floor — preventing any team from receiving a lambda "
                "estimate wildly inconsistent with what teams from their region have historically "
                "produced at World Cups. For well-rated teams with extensive data, this source "
                "contributes almost nothing to the composite. For data-sparse teams, it prevents "
                "impossible extreme estimates that would otherwise distort predictions.",
                S["body"]),
        ]),
        sp(8),
    ]

    story += [
        KeepTogether([
            Paragraph("Host Advantage and Altitude Adjustments", S["h3"]),
            Paragraph(
                "USA, Canada, and Mexico each receive a co-host adjustment of "
                "<b>+0.10 attack lambda</b> and <b>-0.10 defense lambda</b>, applied "
                "after the composite is blended. This reflects the measurable advantages "
                "of familiar geography, minimal travel, and genuine home crowd support — "
                "without overstating an effect that is smaller in a multi-host tournament "
                "than in a traditional single-host World Cup.",
                S["body"]),
            sp(4),
            styled_table([
                ["Venue",               "City",         "Elevation", "Lambda Multiplier", "Effect"],
                ["Estadio Azteca",      "Mexico City",   "2,230m",   "0.93x",             "~7% scoring reduction for both teams"],
                ["Estadio Akron",       "Guadalajara",   "1,560m",   "0.97x",             "~3% scoring reduction for both teams"],
                ["Estadio BBVA",        "Monterrey",     "530m",     "1.00x (none)",      "No meaningful altitude effect"],
                ["US venues (avg)",     "Various",       "~100m",    "1.00x (none)",      "Sea level or near-sea-level"],
                ["Canada venues",       "Various",       "~50m",     "1.00x (none)",      "No altitude adjustment"],
            ], [1.35*inch, 1.05*inch, 0.7*inch, 1.0*inch, BODY_WIDTH-4.1*inch], S),
            sp(4),
            Paragraph(
                "Both teams' lambdas are scaled equally at altitude venues — neither side "
                "has an acclimatization advantage when both are flying in from sea level.",
                S["note"]),
        ]),
        sp(8),
    ]

    story += [
        KeepTogether([
            Paragraph("Tournament Adjustment: Learning from 2026 Results", S["h3"]),
            Paragraph(
                "Once WC2026 matches complete, results feed directly back into each "
                "team's rating via Bayesian shrinkage. The mechanism ensures the model "
                "updates on genuine tournament evidence without overreacting to a "
                "single result:",
                S["body"]),
        ]),
        formula_box([
            "For a team with n completed WC2026 matches:",
            "",
            "Shrinkage weight  =  n / (n + 3)",
            "Tournament attack ratio  =  shrink(mean(actual_goals / prior_lambda), weight)",
            "                        =  weight * mean_ratio + (1 - weight) * 1.0",
            "",
            "# Capped at +/-30%: ratio is clipped to [0.70, 1.30]",
            "",
            "xG blend (active for all 22 adjusted teams):",
            "  blended_ratio  =  0.40 * actual_goals_ratio + 0.60 * xG_goals_ratio",
            "  (when BallDontLie shot data is available; reduces noise from small sample)",
        ], S),
        sp(6),
        callout_box(
            "As of June 2026: 22 teams have active tournament adjustments from "
            "11 completed WC2026 matches. The xG blend is active for all 22 teams. "
            "The shrinkage mechanism means a team that played 1 match gets weight "
            "1/(1+3) = 0.25 — only 25% of the raw adjustment survives; 75% stays "
            "anchored to the prior. A team with 3 matches gets 50/50.",
            S, label="Current Status — June 2026"),
        sp(8),
    ]

    story += [
        KeepTogether([
            Paragraph("Dynamic WC_AVG Scaling", S["h3"]),
            Paragraph(
                "This World Cup is playing fast. Historical average from 2018 and 2022: "
                "<b>1.30 goals per team per match</b>. Through 11 completed WC2026 "
                "matches, the observed rate is <b>1.455 goals per team per match</b>. "
                "This difference matters: a model calibrated to 1.30 will systematically "
                "underestimate scoring in a tournament that is producing 1.455.",
                S["body"]),
        ]),
        formula_box([
            "WC_AVG_scale  =  Observed_2026_rate / Historical_rate",
            "             =  1.455 / 1.300  =  1.119   (11.9% uplift)",
            "",
            "After composite prior is built:",
            "  lambda_final[team]  =  lambda_composite[team]  x  1.119",
            "",
            "# Applied to all 52 team lambdas (48 field + 4 spare)",
            "# Ensures global scoring expectations match the actual 2026 environment",
            "# Recalibrated daily as more matches complete",
        ], S),
        sp(6),
        Paragraph(
            "This is not a fudge factor — it is a principled correction. The composite "
            "prior tells us the relative strength of each team; the WC_AVG scale tells "
            "us what absolute level of scoring this specific tournament is producing. "
            "Both pieces of information are necessary for well-calibrated predictions.",
            S["body"]),
        sp(10),
    ]

    # ── Step 2: Bivariate Poisson ──────────────────────────────────────────────
    story += [
        Paragraph("Step 2: The Bivariate Poisson — Where the Model Gets Clever", S["h2"]),
        gold_thin_rule(),
        Paragraph(
            "With composite team ratings in hand, the model computes the joint score "
            "distribution. This is the technically most important step — and the one "
            "where this model goes beyond the standard football forecasting approach.",
            S["section_intro"]),
    ]

    story += [
        KeepTogether([
            Paragraph("The Standard Approach and Its Flaw", S["h3"]),
            Paragraph(
                "The textbook starting point for football forecasting is to model each "
                "team's goals as an independent Poisson random variable. The Poisson "
                "distribution has one parameter — its mean (lambda) — and gives the "
                "probability of exactly k events occurring in a fixed interval when "
                "events happen at a constant average rate. For goals in a 90-minute match, "
                "it is a reasonable approximation: goals are relatively rare and the "
                "time between goals is roughly exponentially distributed.",
                S["body"]),
        ]),
        Paragraph(
            "Given the estimated lambdas for home and away teams, the independent "
            "Poisson joint probability is:",
            S["body"]),
        formula_box([
            "P(H=h, A=a)  =  P(H=h)  x  P(A=a)",
            "",
            "           =  [e^(-lambda_h) x lambda_h^h / h!]",
            "              x [e^(-lambda_a) x lambda_a^a / a!]",
            "",
            "# This is the product of two independent Poisson PMFs.",
            "# Simple, fast, and well-understood. And subtly wrong.",
        ], S),
        sp(6),
        Paragraph(
            "The flaw is the independence assumption. <b>Goals are not independent.</b> "
            "When the first goal goes in at the 25th minute, everything changes. The "
            "losing team pushes forward, leaving more space behind. The winning team "
            "may sit deeper, inviting pressure. Tactical changes, substitutions, "
            "and psychological effects all reshape the match. The result: the correlation "
            "between home and away goals in football is small but <i>real and positive</i>. "
            "Both teams tend to score more in high-intensity, open matches. The independent "
            "Poisson misses this and systematically misprices draws relative to decisive "
            "results in certain match conditions.",
            S["body"]),
        sp(6),
    ]

    story += [
        KeepTogether([
            Paragraph("The Bivariate Poisson: Three Latent Processes", S["h3"]),
            Paragraph(
                "The Bivariate Poisson model (Karlis and Ntzoufras, 2003) handles this "
                "properly through an elegant mathematical construction. Instead of two "
                "independent processes, the model posits that the goals in a match arise "
                "from <b>three independent Poisson processes</b>:",
                S["body"]),
        ]),
        formula_box([
            "Z_1  ~  Poisson(lambda_1) :  home team's independent goal process",
            "Z_2  ~  Poisson(lambda_2) :  away team's independent goal process",
            "Z_3  ~  Poisson(lambda_3) :  shared latent 'match intensity' process",
            "                             (goals that arise from both teams' engagement",
            "                              in a high-energy, open match)",
            "",
            "Observed goals:",
            "  H  =  Z_1 + Z_3     (home total = own goals + shared intensity goals)",
            "  A  =  Z_2 + Z_3     (away total = own goals + shared intensity goals)",
        ], S),
        sp(6),
        Paragraph(
            "The intuition for Z_3: some matches have an unusually open, attacking "
            "character — both teams committing forward, creating chances, and scoring. "
            "Other matches are tight, defensive, and low-scoring regardless of the "
            "individual teams' quality. The shared intensity parameter lambda_3 captures "
            "this match-level factor that simultaneously lifts both teams' scoring rates.",
            S["body"]),
    ]

    story += [
        KeepTogether([
            Paragraph("The Joint Probability Formula", S["h3"]),
            Paragraph(
                "The joint probability of observing h home goals and a away goals under "
                "the Bivariate Poisson is derived by marginalizing over the possible values "
                "of the shared component Z_3 = k:",
                S["body"]),
        ]),
        formula_box([
            "P(H=h, A=a)  =  e^(-(lambda_1+lambda_2+lambda_3))",
            "                x SUM{k=0 to min(h,a)}",
            "                    [ lambda_1^(h-k) / (h-k)! ]",
            "                    x [ lambda_2^(a-k) / (a-k)! ]",
            "                    x [ lambda_3^k / k! ]",
            "",
            "# The sum runs from k=0 (no shared goals) to k=min(h,a) (maximum possible",
            "# shared contribution without exceeding observed totals for either team).",
            "",
            "Key property: when lambda_3 = 0",
            "  -> only the k=0 term survives",
            "  -> formula reduces exactly to independent Poisson",
            "  -> Bivariate Poisson IS independent Poisson when lambda_3 = 0",
        ], S),
        sp(6),
        Paragraph(
            "The covariance between home and away goals under this model is exactly "
            "lambda_3:",
            S["body"]),
        formula_box([
            "Cov(H, A)  =  lambda_3",
            "Corr(H, A) =  lambda_3 / sqrt((lambda_1+lambda_3) x (lambda_2+lambda_3))",
            "",
            "# Both are positive when lambda_3 > 0.",
            "# This is the theoretical formalization of 'open matches produce more",
            "# goals for both teams simultaneously.'",
        ], S),
        sp(6),
        callout_box(
            "Calibrated value from 11 completed WC2026 matches: lambda_3 = 0.170. "
            "Positive — this World Cup is showing exactly the mutual intensity correlation "
            "the model was built to capture. Cov(H, A) = 0.170. The independent "
            "Poisson assumption significantly understates this correlation.",
            S, label="Current Calibrated Value"),
        sp(8),
    ]

    story += [
        KeepTogether([
            Paragraph("The Six Parametric Competitors", S["h3"]),
            Paragraph(
                "The model does not simply run the Bivariate Poisson. It runs "
                "<b>six competing parametric models daily</b>, trained on the combined "
                "historical and 2026 data, and selects the winner by negative "
                "log-likelihood on held-out WC2026 match results. The competition "
                "ensures the model specializes to whatever structure the 2026 tournament "
                "is actually showing:",
                S["body"]),
        ]),
        sp(4),
        styled_table([
            ["#", "Model",                 "Core Mechanism",
             "Key Parameter",            "Current Status"],
            ["1", "Independent Poisson",   "Goals independent; joint prob = product",
             "lambda_h, lambda_a",        "Baseline"],
            ["2", "Dixon-Coles",           "Low-score correlation correction via rho",
             "rho (typically < 0)",      "Competing"],
            ["3", "Bivariate Poisson",     "Three-process shared intensity model",
             "lambda_3 = 0.170",         "LOG-LOSS CHAMPION"],
            ["4", "Weibull Copula",        "Weibull marginals linked by copula",
             "Shape/scale params",       "Competing"],
            ["5", "Negative Binomial",     "Overdispersion: variance > mean",
             "r (overdispersion)",       "Competing"],
            ["6", "Zero-Inflated Poisson", "Excess zero mass beyond Poisson",
             "pi (zero inflation)",      "Competing"],
        ], [0.22*inch, 1.3*inch, 1.75*inch, 1.2*inch, BODY_WIDTH-4.47*inch], S),
        sp(6),
        Paragraph(
            "All six compete on the same held-out WC2026 data in a walk-forward backtest "
            "— predicting each match from what was known before it was played. The model "
            "with the lowest negative log-likelihood wins and feeds all upstream "
            "calculations. The winner is reselected <b>daily</b> as more matches "
            "accumulate. Currently the Bivariate Poisson is dominant.",
            S["body"]),
        sp(10),
    ]

    # ── Step 3: Market Reconciliation ─────────────────────────────────────────
    story += [
        KeepTogether([
            Paragraph("Step 3: Market Reconciliation (SLSQP Optimization)", S["h2"]),
            gold_thin_rule(),
            Paragraph(
                "Even the Bivariate Poisson model with perfect team ratings cannot know "
                "about a starting goalkeeper injury announced 90 minutes before kickoff. "
                "Market reconciliation is the mechanism that incorporates this class of "
                "information — the kind of real-time intelligence that sharp bookmakers "
                "absorb instantly and that no parametric model can anticipate.",
                S["body"]),
        ]),
        Paragraph(
            "For each match, the model extracts fair market probabilities from all "
            "available bookmakers (after SHIN normalization) across every available "
            "market type: 1X2, Over/Under totals from 0.5 through 6.5 goals, Both "
            "Teams to Score, Draw No Bet, Double Chance, and correct score lines. "
            "Up to 6 bookmakers per market, averaged after SHIN normalization to "
            "remove each book's individual margin.",
            S["body"]),
        Paragraph(
            "A constrained optimization algorithm — <b>SLSQP (Sequential Least Squares "
            "Programming)</b> — then adjusts the parametric PMF grid to satisfy these "
            "market constraints while minimizing Kullback-Leibler divergence from the "
            "original parametric distribution:",
            S["body"]),
        formula_box([
            "Optimization problem:",
            "",
            "  minimize    KL(P_adjusted || P_parametric)",
            "              =  SUM{h,a} P_adj[h,a] * log(P_adj[h,a] / P_param[h,a])",
            "",
            "  subject to: P_adj[h,a] >= 0                    for all (h,a)",
            "              SUM{h,a} P_adj[h,a]  =  1.0",
            "              SUM{cells in market c} P_adj[h,a]  =  market_prob(c)",
            "              for each market c in available markets",
        ], S),
        sp(6),
        Paragraph(
            "KL divergence measures how far the adjusted distribution has moved from "
            "the starting point — minimizing it ensures the optimizer moves only as "
            "far from the parametric prior as the market evidence strictly requires. "
            "When SLSQP converges to a better solution than a simple weighted-average "
            "blend of the two distributions, SLSQP is used; otherwise the blend is used.",
            S["body"]),
        callout_box(
            "SLSQP performance: Only 1 non-convergence observed in 63 matches (98.4% "
            "convergence rate). When SLSQP does not converge, the weighted-average "
            "blend with 30% market weight is used as fallback. SLSQP dominates for "
            "virtually all matches where market and parametric probabilities differ materially.",
            S, label="Current Performance"),
        sp(10),
    ]

    # ── Step 4: Calibration ────────────────────────────────────────────────────
    story += [
        KeepTogether([
            Paragraph("Step 4: Calibration (Temperature Scaling)", S["h2"]),
            gold_thin_rule(),
            Paragraph(
                "A model is calibrated when its stated probabilities match observed "
                "frequencies. When it says 30%, outcomes should occur 30% of the time. "
                "Calibration is <i>distinct</i> from accuracy: an overconfident model can "
                "be directionally right (higher-probability outcomes happen more often "
                "than lower-probability ones) but numerically wrong (the stated "
                "probabilities are too extreme).",
                S["body"]),
        ]),
        Paragraph(
            "The model uses <b>temperature scaling</b>: a single scalar parameter T "
            "that adjusts the entire distribution uniformly. T is fitted by minimizing "
            "exact-score log loss on out-of-sample predictions from the 2018 and 2022 "
            "World Cups — never on training data.",
            S["body"]),
        formula_box([
            "For each cell (h, a) in the PMF grid:",
            "",
            "  p_calibrated[h,a]  proportional to  p_raw[h,a]^(1/T)",
            "",
            "  then renormalized: p_calibrated[h,a] /= SUM{h,a} p_raw[h,a]^(1/T)",
            "",
            "T > 1 : exponent (1/T) < 1 -> flattens distribution (corrects overconfidence)",
            "T < 1 : exponent (1/T) > 1 -> sharpens distribution (corrects underconfidence)",
            "T = 1 : identity transform -- no calibration change",
            "",
            "# Current calibrated value: T = 1.089",
            "# Interpretation: raw model is mildly overconfident.",
            "# The most likely scores get trimmed slightly; less likely scores get a boost.",
        ], S),
        sp(6),
        Paragraph("Five calibration metrics are evaluated on out-of-sample data only:", S["body"]),
        sp(4),
        styled_table([
            ["Metric",                         "Formula",                           "What It Measures"],
            ["Exact-score NLL",                 "-SUM log(p[actual score])",         "Primary: how surprised by actual scores"],
            ["Ranked Probability Score (RPS)",  "SUM (CDF_pred - CDF_actual)^2",    "1X2 market calibration"],
            ["Brier Score",                     "Mean (p_pred - outcome)^2",         "Binary market accuracy (BTTS, O/U)"],
            ["Expected Calibration Error (ECE)","Mean |freq - prob| per bin",        "Direct probability-frequency alignment"],
            ["Ignorance Score",                 "-SUM log2(p[outcome])",             "Information content of predictions"],
        ], [1.5*inch, 1.8*inch, BODY_WIDTH-3.3*inch], S),
        sp(6),
        callout_box(
            "Current T = 1.089. The correction is modest — the raw model is reasonably "
            "well-calibrated before adjustment. An honest caveat: 128 World Cup matches "
            "is a small calibration dataset. As the 2026 tournament adds completed "
            "matches, T will be re-estimated on a growing sample.",
            S, label="Current Calibration Temperature"),
        sp(10),
    ]

    # ── Step 5: Edge Screening ─────────────────────────────────────────────────
    story += [
        KeepTogether([
            Paragraph("Step 5: Edge Screening and Kelly Sizing", S["h2"]),
            gold_thin_rule(),
            Paragraph(
                "With a calibrated PMF for each match, the model compares its probability "
                "estimates against the bookmaker's no-vig prices for every available market. "
                "An edge exists when the model assigns higher probability than the market "
                "implies:",
                S["body"]),
        ]),
        formula_box([
            "Edge  =  (Model probability  -  Market implied probability)",
            "         /  Market implied probability",
            "",
            "# An edge of 0.08 means the model estimates the outcome is 8% MORE likely",
            "# than the market implies -- proportionally, not in absolute percentage points.",
            "",
            "# Example: Market implies 40%; model says 43.2%",
            "#   Edge = (0.432 - 0.400) / 0.400  =  0.08  =  8%",
        ], S),
        sp(6),
        Paragraph(
            "Raw edge alone is not enough to flag a market as a value opportunity. "
            "The model applies <b>three simultaneous filters</b> — all three must pass:",
            S["body"]),
        sp(4),
        styled_table([
            ["Filter",               "Condition",                "Purpose"],
            ["Edge threshold",       "Edge >= 4%",              "Minimum signal above estimation noise; "
                                                                 "markets below this likely reflect model "
                                                                 "uncertainty rather than genuine mispricing"],
            ["CI lower bound",       "Lower bound of 90% CI > market implied",
             "The CI is computed by perturbing lambda +/-12%. If even the pessimistic "
             "scenario (lambdas shifted against the edge) shows the model above market, "
             "the edge is robust"],
            ["Liquidity filter",     "Market implied > 2%",     "Very low-probability markets have thin "
                                                                 "liquidity and high variance on edge estimates; "
                                                                 "excluded to avoid false signals"],
        ], [0.9*inch, 1.7*inch, BODY_WIDTH-2.6*inch], S),
        sp(8),
        Paragraph("Kelly sizing for flagged markets:", S["body"]),
        formula_box([
            "Full Kelly fraction:  f*  =  Edge / (Decimal odds - 1)",
            "Half-Kelly:           f   =  f* / 2                       [default]",
            "Quarter-Kelly:        f   =  f* / 4                       [conservative]",
            "Hard cap:             f   =  min(f, 0.05)                 [5% of bankroll]",
            "",
            "# Half-Kelly is the default because +/-12% lambda uncertainty is a fixed",
            "# prior assumption. When true uncertainty exceeds 12%, Full Kelly overbets.",
            "# The 5% hard cap provides a backstop regardless of the computed fraction.",
        ], S),
        sp(10),
    ]

    # ── Step 6: CLV ────────────────────────────────────────────────────────────
    story += [
        KeepTogether([
            Paragraph("Step 6: Closing Line Value (CLV) — The Edge Litmus Test", S["h2"]),
            gold_thin_rule(),
            Paragraph(
                "Counting wins and losses is a poor way to evaluate a prediction model. "
                "A model that goes 60% on 1X2 bets might simply have been backing heavy "
                "favorites. A model that goes 48% might be consistently finding genuine "
                "value on underdogs and still be profitable. Wins and losses don't "
                "distinguish these cases.",
                S["body"]),
        ]),
        Paragraph(
            "<b>CLV is the industry-standard measure of whether a model has genuine edge.</b> "
            "The closing line is the bookmaker's final no-vig probability immediately "
            "before kickoff — the market's best collective estimate of the true probability, "
            "having absorbed every piece of publicly available information. It represents "
            "the aggregated opinion of every sharp bettor, quantitative model, and market "
            "maker who has looked at the match. It is the most informed number available.",
            S["body"]),
        Paragraph(
            "A model that consistently predicts <i>higher</i> probability than where the "
            "market ultimately closes is providing information the market was slow to price "
            "in. That positive CLV is evidence of genuine edge — not because the model was "
            "necessarily right about the specific outcome, but because it was ahead of the "
            "market's information flow.",
            S["body"]),
        Paragraph(
            "A model that consistently <i>loses</i> to the closing line — predicting lower "
            "probability than where the market closes — means the market was consistently "
            "smarter, and the model's apparent positive edges were illusions driven by "
            "stale or insufficient information.",
            S["body"]),
        callout_box(
            "15 markets tracked per match: the three 1X2 outcomes, BTTS Yes/No, "
            "Over/Under at 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, 6.5, and Under at "
            "1.5, 2.5, and 3.5. Closing odds are captured automatically at "
            "T-3 minutes before each kickoff by a dedicated pre-match pipeline "
            "watcher that sleeps until exactly 3 minutes before the scheduled "
            "kickoff, then fetches and normalizes closing lines across all 15 markets.",
            S, label="CLV Tracking Scope"),
        sp(10),
    ]

    # ── Key Definitions ────────────────────────────────────────────────────────
    story += [
        KeepTogether([
            Paragraph("Key Terms and Definitions", S["h2"]),
            gold_thin_rule(),
            Paragraph(
                "A complete reference for every term, symbol, and metric used "
                "throughout the model documentation and the prediction pages.",
                S["body"]),
            sp(6),
        ]),
        styled_table([
            ["Term / Symbol",            "Precise Definition"],
            ["lambda (general)",         "The rate parameter of a Poisson distribution. "
                                         "Equal to both the mean and variance of the distribution. "
                                         "In this model: the expected number of goals in 90 minutes."],
            ["lambda_att",               "A team's attack lambda — expected goals scored "
                                         "against an average opponent at a neutral venue."],
            ["lambda_def",               "A team's defense lambda — expected goals conceded "
                                         "against an average opponent at a neutral venue."],
            ["lambda_h",                 "Match-specific home team expected goals, after applying "
                                         "the composite prior, WC_AVG scale, and opponent adjustment."],
            ["lambda_a",                 "Match-specific away team expected goals (same calculation)."],
            ["lambda_1, lambda_2",       "Bivariate Poisson components: home and away independent "
                                         "goal processes after separating out the shared component."],
            ["lambda_3",                 "Bivariate Poisson shared intensity parameter. "
                                         "Cov(H,A) = lambda_3. Currently 0.170 for WC2026."],
            ["PMF",                      "Probability Mass Function. The full grid of P(h,a) values "
                                         "for all integer score combinations. Sums to exactly 1.0."],
            ["Joint PMF",                "The two-dimensional PMF grid: P(H=h, A=a) for all (h,a). "
                                         "The core output of the model."],
            ["Marginal PMF",             "The one-dimensional distribution for a single team's goals, "
                                         "derived by summing the joint PMF across the other team's axis."],
            ["Temperature T",            "Calibration parameter. p_cal ∝ p_raw^(1/T), then renormalized. "
                                         "T=1.089 currently. T>1 flattens (corrects overconfidence)."],
            ["No-vig probability",       "Bookmaker odds with the bookmaker margin removed. "
                                         "Computed via SHIN normalization."],
            ["SHIN normalization",       "A method to remove bookmaker margin from quoted odds that "
                                         "assumes the margin is applied multiplicatively. Standard in "
                                         "the professional sports betting literature."],
            ["KL divergence",            "Kullback-Leibler divergence. Measures how much one probability "
                                         "distribution differs from another. Minimized in SLSQP reconciliation."],
            ["SLSQP",                    "Sequential Least Squares Programming. A constrained nonlinear "
                                         "optimization algorithm used for market reconciliation."],
            ["Edge",                     "(Model prob - Market prob) / Market prob. Positive = model "
                                         "assigns higher probability than market implies."],
            ["CLV",                      "Closing Line Value. Model probability minus closing (pre-kickoff) "
                                         "no-vig market probability. Positive = model was ahead of market."],
            ["Kelly fraction f*",        "Edge / (Decimal odds - 1). The bet size fraction that "
                                         "maximizes long-run bankroll growth rate."],
            ["NLL",                      "Negative Log-Likelihood. -SUM log(p[actual outcome]). "
                                         "The primary metric for selecting among the six model competitors."],
            ["RPS",                      "Ranked Probability Score. SUM (CDF_predicted - CDF_actual)^2. "
                                         "Standard calibration metric for ordered categorical outcomes."],
            ["Brier Score",              "Mean squared error on binary probability forecasts. "
                                         "Range [0,1]. Lower is better."],
            ["ECE",                      "Expected Calibration Error. Mean |observed frequency - stated probability| "
                                         "across probability bins. Directly measures calibration alignment."],
            ["WC_AVG scale",             "Dynamic multiplier applied to all team lambdas to match "
                                         "observed 2026 tournament scoring rate. Currently 1.119."],
            ["Bayesian shrinkage",       "Pulling an estimate toward a prior value by a factor n/(n+k). "
                                         "Prevents overreaction to small sample sizes."],
            ["Dixon-Coles rho",          "Correlation correction parameter for low-scoring outcomes "
                                         "(0-0, 1-0, 0-1, 1-1). Negative rho boosts these scorelines."],
        ], [1.5*inch, BODY_WIDTH-1.5*inch], S),
        sp(10),
    ]

    # ── Worked Example ────────────────────────────────────────────────────────
    story += [
        KeepTogether([
            Paragraph("Worked Example: How P(2-1) Gets Calculated", S["h2"]),
            gold_thin_rule(),
            Paragraph(
                "To make the pipeline concrete, here is a step-by-step example of how "
                "the model computes the probability of a specific final score — say, "
                "a 2-1 home win — for a hypothetical WC2026 match.",
                S["body"]),
        ]),
        Paragraph(
            "<b>Starting inputs (after composite prior and WC_AVG scaling):</b>",
            S["h4"]),
        formula_box([
            "Home team: lambda_att = 1.52,  lambda_def = 1.10",
            "Away team: lambda_att = 1.20,  lambda_def = 1.25",
            "",
            "Match lambda parameters (after reconciliation):",
            "  lambda_h = home_att x away_def x WC_scale  =  1.52 x 1.25 x 1.119  =  2.127",
            "  lambda_a = away_att x home_def x WC_scale  =  1.20 x 1.10 x 1.119  =  1.477",
            "",
            "Bivariate Poisson parameters after calibration:",
            "  lambda_1 = 1.957  (home independent component)",
            "  lambda_2 = 1.307  (away independent component)",
            "  lambda_3 = 0.170  (shared intensity component)",
        ], S),
        sp(6),
        Paragraph(
            "<b>Calculating P(H=2, A=1) using the Bivariate Poisson formula:</b>",
            S["h4"]),
        formula_box([
            "P(H=2, A=1) = e^(-(lambda_1+lambda_2+lambda_3))",
            "              x SUM{k=0 to min(2,1)=1}",
            "                  [lambda_1^(2-k)/(2-k)!] x [lambda_2^(1-k)/(1-k)!] x [lambda_3^k/k!]",
            "",
            "Constant:   e^(-(1.957+1.307+0.170)) = e^(-3.434) = 0.03240",
            "",
            "k=0 term:   [1.957^2/2!] x [1.307^1/1!] x [0.170^0/0!]",
            "          = [3.830/2] x [1.307] x [1]",
            "          = 1.915 x 1.307 x 1.000  =  2.502",
            "",
            "k=1 term:   [1.957^1/1!] x [1.307^0/0!] x [0.170^1/1!]",
            "          = [1.957] x [1] x [0.170]",
            "          = 1.957 x 1.000 x 0.170  =  0.333",
            "",
            "Sum:        2.502 + 0.333 = 2.835",
            "",
            "P(H=2, A=1) = 0.03240 x 2.835  =  0.0919  =  9.19%",
            "",
            "# Fair American odds for correct score 2-1: +988  (= 1/0.0919 - 1, expressed as +odds)",
        ], S),
        sp(6),
        Paragraph(
            "After temperature calibration (T = 1.089), the cell is adjusted:",
            S["body"]),
        formula_box([
            "p_calibrated  proportional to  0.0919^(1/1.089)  =  0.0919^0.9183  =  0.0938",
            "              (then renormalized across all cells to sum to 1.0)",
            "",
            "# The calibrated probability for 2-1 is approximately 0.0938 = 9.38%",
            "# Fair odds after calibration: approximately +966",
        ], S),
        sp(6),
        Paragraph(
            "This single cell of 9.38% feeds into the Edge Report for the correct score "
            "2-1 market. If a bookmaker is offering +1100 American odds on this scoreline, "
            "the no-vig implied probability is roughly 1/12 = 8.33%. The edge would be "
            "(9.38% - 8.33%) / 8.33% = 12.6% — a significant value signal that would "
            "easily pass all three filters and appear in the edge report.",
            S["body"]),
        sp(10),
    ]

    # ── Automated Pipeline ─────────────────────────────────────────────────────
    story += [
        KeepTogether([
            Paragraph("The Automated Pipeline: A Living System", S["h2"]),
            gold_thin_rule(),
            Paragraph(
                "Every stage described above runs without human intervention, around the "
                "clock. The pipeline is not a tool that runs when someone presses a button "
                "— it is a continuously running system that treats each completed World Cup "
                "match as a new data point to incorporate.",
                S["body"]),
        ]),
        sp(6),
        styled_table([
            ["Pipeline Cycle",      "Frequency",                "Scope"],
            ["Full Retraining",     "Daily, 8:00 AM UTC",
             "Fetch all API data. Retrain all 6 parametric models on combined historical "
             "+ 2026 data. Rebuild composite prior with updated tournament adjustments. "
             "Regenerate predictions for all upcoming fixtures. Log calibration metrics. "
             "Deploy updated prediction JSONs to production."],
            ["Odds Refresh",        "Hourly",
             "Capture latest odds movements from bookmakers. Update CLV tracking records. "
             "Re-run predictions if newly completed matches have appeared since the "
             "daily retraining run."],
            ["Live Snapshots",      "Every 2 min (9 AM-3 AM ET)",
             "Fetch current score, match clock, and live xG data. Compute conditional "
             "PMF given current state. Apply score-state multipliers. Upload live "
             "JSON to server. Self-chains when match detected in progress."],
            ["Closing Odds",        "T-3 min before each kickoff",
             "Dedicated watcher checks schedule every 15 min. When match within "
             "15 min, sleeps to T-3. Fetches final closing lines across all 15 markets. "
             "Applies SHIN normalization. Records CLV data. Bootstraps live snapshot "
             "chain to ensure live page is active from the opening whistle."],
        ], [1.1*inch, 1.4*inch, BODY_WIDTH-2.5*inch], S),
        sp(10),
    ]

    # ── Model Architecture Summary ─────────────────────────────────────────────
    story += [
        KeepTogether([
            Paragraph("Full Model Architecture: Data Flow Summary", S["h2"]),
            gold_thin_rule(),
            Paragraph(
                "The complete data flow, from raw inputs to the final edge report, "
                "is summarized below. Every stage is fully automated.",
                S["body"]),
            sp(6),
        ]),
        styled_table([
            ["Stage",               "Input",                "Output",               "Key Method"],
            ["1. Data Fetch",       "BallDontLie API, bookmaker feeds",
             "Raw odds, match results, xG, shot data",
             "API polling + schema validation"],
            ["2. Composite Prior",  "FIFA, Elo, Pi, qualifying, bookmaker odds",
             "lambda_att, lambda_def per team",
             "Weighted blend of 6 sources"],
            ["3. Host/Altitude",    "lambda_att, lambda_def + venue metadata",
             "Adjusted lambdas",
             "+/-0.10 host adj; 0.93x / 0.97x altitude"],
            ["4. Tournament Adj.",  "WC2026 completed match results + xG",
             "Per-team adjustment factors",
             "Bayesian shrinkage n/(n+3)"],
            ["5. WC_AVG Scale",     "Observed 2026 scoring rate",
             "All team lambdas x 1.119",
             "Dynamic scale to match tournament pace"],
            ["6. Model Competition","Team lambdas + historical data",
             "Winner PMF (Bivariate Poisson currently)",
             "Walk-forward NLL comparison of 6 models"],
            ["7. Market Reconciliation","Parametric PMF + bookmaker market odds",
             "Market-adjusted PMF",
             "SLSQP minimize KL divergence"],
            ["8. Calibration",      "Market PMF + T = 1.089",
             "Calibrated PMF (the final grid)",
             "Temperature scaling p ∝ p^(1/T)"],
            ["9. Edge Screening",   "Calibrated PMF + market prices",
             "Value bet flags + Kelly stakes",
             "3-filter screen: edge, CI, liquidity"],
            ["10. CLV Tracking",    "Model probs + closing line at T-3",
             "CLV records per market",
             "15 markets tracked per match"],
        ], [0.9*inch, 1.3*inch, 1.4*inch, BODY_WIDTH-3.6*inch], S),
        sp(10),
    ]

    # ── Limitations ────────────────────────────────────────────────────────────
    story += [
        Paragraph("Honest Limitations", S["h2"]),
        gold_thin_rule(),
        Paragraph(
            "No model of football should be presented without an honest accounting "
            "of what it cannot do. The following limitations are real and material.",
            S["body"]),
        sp(6),
        Paragraph(
            "<b>Regulation time only.</b> All probabilities represent 90 minutes plus "
            "stoppage time. Extra time and penalty shootouts are not modeled. For knockout "
            "matches that go to extra time, the regulation-time distribution is not the "
            "complete picture of match outcomes.",
            S["bullet"]),
        sp(2),
        Paragraph(
            "<b>lambda_3 = 0.170 is an average, not a per-match value.</b> The Bivariate "
            "Poisson substantially improves on the independence assumption, but the shared "
            "intensity parameter is fitted across all completed matches combined. A match "
            "in the 85th minute with a team pressing for an equalizer has dramatically "
            "different dynamics than a settled 2-0 game at minute 60. The live model's "
            "score-state multipliers handle this in real time, but the pre-game "
            "prior is still an approximation of the true match-level correlation.",
            S["bullet"]),
        sp(2),
        Paragraph(
            "<b>11 completed WC2026 matches is a small sample.</b> lambda_3, the "
            "calibration temperature T, and the WC_AVG scaling factor are all estimated "
            "from 11 data points as of June 2026. These carry meaningful statistical "
            "uncertainty. All three will stabilize as the tournament progresses to 48 "
            "and then 64 total matches.",
            S["bullet"]),
        sp(2),
        Paragraph(
            "<b>Lambda uncertainty is a fixed prior, not a per-match estimate.</b> "
            "The +/-12% used to compute confidence intervals is a conservative global "
            "assumption. For teams with extensive, recent competitive data — Brazil, "
            "France, Germany — 12% likely overstates the true uncertainty. For teams "
            "from data-sparse qualifying regions, 12% may understate it. A fully "
            "Bayesian treatment would require per-team posterior distributions that "
            "the current architecture does not implement.",
            S["bullet"]),
        sp(2),
        Paragraph(
            "<b>Odds move between prediction and kickoff.</b> Edge estimates are "
            "calculated when the pipeline runs. By the time you see them, the market "
            "may have moved. A +6% edge computed at 8:00 AM UTC may have narrowed or "
            "disappeared by kickoff at 3:00 PM. Always verify current odds at your "
            "book before acting on any edge signal from this site.",
            S["bullet"]),
        sp(2),
        Paragraph(
            "<b>Positive expected value does not guarantee positive returns in any "
            "finite sample.</b> Even a well-calibrated model with genuine edge will "
            "experience losing streaks. The Kelly sizing and CI filter are designed "
            "to manage variance over time, not eliminate it from any individual result. "
            "Football remains genuinely hard to predict. A good model makes you more "
            "informed, not omniscient.",
            S["bullet"]),
        sp(14),
        thin_rule(),
        sp(4),
        Paragraph(
            "All probabilities represent regulation time (90 minutes + stoppage time) only. "
            "Extra time and penalties are excluded. This article is for informational and "
            "educational purposes only. Please gamble responsibly.",
            S["disclaimer"]),
    ]

    return story


# ═══════════════════════════════════════════════════════════════════════════════
# ARTICLE 2 — Page Guide
# ═══════════════════════════════════════════════════════════════════════════════

def build_article2(styles):
    S = styles
    story = []

    # ── Title block ────────────────────────────────────────────────────────────
    story += [
        Paragraph("WIZARDOFODDS.COM", S["site"]),
        rule(),
        Paragraph("A Guide to the WC 2026 Prediction Pages", S["h1"]),
        Paragraph(
            "What every number, chart, and indicator means across all three pages — "
            "and how to make the most of each one.",
            S["subtitle"]),
        rule(),
        sp(8),
    ]

    # ── Foundation ─────────────────────────────────────────────────────────────
    story += [
        KeepTogether([
            Paragraph("The Foundation: One PMF, All Markets", S["h2"]),
            gold_thin_rule(),
            Paragraph(
                "Most football prediction tools give you a win probability and call it "
                "a day. This one gives you the <b>entire joint probability distribution "
                "over every possible scoreline</b> — the probability the match ends 0-0, "
                "that it ends 2-1, that it ends 4-3 — and derives every betting market "
                "mechanically from that single distribution.",
                S["body"]),
            Paragraph(
                "That architecture is not a cosmetic difference. It means every number on "
                "every page is internally consistent by construction. The Over 2.5 "
                "probability and the 1X2 probabilities cannot contradict each other "
                "the way they frequently do on aggregator sites that blend data from "
                "different sources. When you see an edge on this site, you are looking "
                "at a discrepancy between a coherent probability system and the "
                "bookmaker's price — not an artifact of mismatched models.",
                S["body"]),
        ]),
        Paragraph(
            "Every page draws from the same underlying joint score PMF grid. Each cell "
            "(h, a) holds P(Home = h, Away = a): the probability the home team scores "
            "exactly h goals and the away team scores exactly a goals in regulation time. "
            "The grid sums to exactly 1.0. All markets are arithmetic operations on "
            "this grid:",
            S["body"]),
        sp(4),
        styled_table([
            ["Market",                    "Formula",                         "Interpretation"],
            ["Over 2.5 goals",            "SUM all cells where h+a >= 3",    "Upper-right region of the PMF grid"],
            ["Under 2.5 goals",           "SUM all cells where h+a <= 2",    "Lower-left region of the PMF grid"],
            ["Both Teams to Score",       "SUM cells where h>=1 AND a>=1",   "Everything except row 0 and column 0"],
            ["Home Win",                  "SUM cells where h > a",           "Below the main diagonal of the grid"],
            ["Draw",                      "SUM cells where h = a",           "The main diagonal (0-0, 1-1, 2-2, ...)"],
            ["Correct Score 2-1",         "P(h=2, a=1)",                     "Single cell — read directly"],
            ["P(Home scores exactly h)",  "SUM over all a of P(h,a)",        "Row marginal — collapse across all a"],
        ], [1.45*inch, 1.85*inch, BODY_WIDTH-3.3*inch], S),
        sp(8),
    ]

    # ═══════════════════════════════════════════════════════
    # PAGE 1
    # ═══════════════════════════════════════════════════════
    story += [
        Paragraph("Page 1 — Pre-Game Predictions", S["h2"]),
        gold_thin_rule(),
        Paragraph(
            "sportsodds.wizardofodds.com/tools/odds-scanner/predictions/world%20cup/pre%20match.html",
            S["url"]),
        Paragraph(
            "The command center for today's matches. Every World Cup match scheduled "
            "for today appears in the main table with the model's probability estimates, "
            "expected goals, and edge analysis against live bookmaker prices. The data "
            "refreshes automatically and a red banner appears if the underlying prediction "
            "file is more than four hours old — a signal the automated pipeline may have "
            "encountered an issue.",
            S["body"]),
        sp(6),
    ]

    story += [
        KeepTogether([
            Paragraph("The KPI Cards", S["h3"]),
            Paragraph(
                "Four summary numbers compress the entire day's modeling output into "
                "a single glance.",
                S["body"]),
            sp(4),
            styled_table([
                ["Card",             "What It Shows",                       "How to Read It"],
                ["Matches Today",    "Regulation kickoffs scheduled today", "Simple count. 0 = off-day or rest day."],
                ["Value Bets",       "Markets passing all three edge filters simultaneously",
                 "Edge >= 4% AND 90% CI lower bound > market implied AND market implied > 2%. "
                 "Frequently zero — that is correct behavior in a well-priced market."],
                ["Best Edge",        "Single largest edge % across today's markets",
                 "Specific match and market labeled below the number. Does NOT guarantee "
                 "the bet will win. Confirm current odds before acting."],
                ["Avg xG / Match",   "Average (lambda_home + lambda_away) today",
                 "The model's expected total goals per match. 2.6 = higher-scoring slate. "
                 "2.2 = defensive slate. Useful context before drilling into individual matches."],
            ], [0.9*inch, 1.55*inch, BODY_WIDTH-2.45*inch], S),
        ]),
        sp(10),
    ]

    story += [
        KeepTogether([
            Paragraph("The Bankroll Sizing Tool", S["h3"]),
            Paragraph(
                "Enter a bankroll amount and select a Kelly fraction. For every market "
                "passing all three edge filters, the tool computes a recommended dollar "
                "stake using the Kelly criterion: the fraction of your bankroll that "
                "maximizes the long-run growth rate of the bankroll given this edge.",
                S["body"]),
            sp(4),
            styled_table([
                ["Fraction",       "Stake Formula",              "Recommended When"],
                ["Full Kelly",     "f* = Edge / (Decimal - 1)",
                 "Only when highly confident in edge accuracy. Produces large drawdowns "
                 "in practice when edge estimates contain error."],
                ["Half Kelly",     "f*/2  [default]",
                 "Standard recommendation in sports modeling literature when parameter "
                 "uncertainty is non-negligible. Retains most compounding advantage with "
                 "substantially lower variance."],
                ["Quarter Kelly",  "f*/4  [conservative]",
                 "Early in tournament when calibration sample is small, or when "
                 "spreading capital across several simultaneous positions."],
            ], [0.8*inch, 1.5*inch, BODY_WIDTH-2.3*inch], S),
            sp(4),
            Paragraph(
                "All three fractions are hard-capped at <b>5% of your entered bankroll</b> "
                "regardless of what the formula computes. This prevents extreme positions "
                "when the model identifies an unusually large apparent edge.",
                S["body"]),
        ]),
        sp(8),
    ]

    story += [
        KeepTogether([
            Paragraph("The Match Table", S["h3"]),
            Paragraph(
                "Each row represents one match. The columns, working left to right:",
                S["body"]),
        ]),
        sp(4),
        styled_table([
            ["Column",          "Description"],
            ["Match",           "Home vs. away. Neutral venue for all except USA/Canada/Mexico "
                                "who receive +0.10 attack / -0.10 defense as co-hosts."],
            ["1X2 Bars",        "Three-segment bar: Home Win (gold), Draw (gray), Away Win (blue). "
                                "Probabilities sum to 100%. Derived by summing appropriate cells of "
                                "the joint PMF grid. Fair American odds shown have no bookmaker margin."],
            ["O/U 2.5",         "P(total regulation goals >= 3). Sum of all cells where h+a >= 3. "
                                "Above 55% = model leans higher-scoring. Below 45% = tight match."],
            ["BTTS",            "P(both teams score >= 1). Sum of all cells except first row and "
                                "first column. A 35% BTTS means good chance one team gets shut out."],
            ["Top Score",       "The single most probable scoreline (peak cell of the PMF) with its "
                                "probability. Usually 1-0 or 1-1 carrying 12-18% in group stage."],
            ["xG (H-A)",        "lambda_home and lambda_away after market reconciliation. 1.8-0.7 = "
                                "clear favorite-underdog. 1.2-1.1 = near coin flip."],
            ["Best Edge",       "Highest-edge market passing all three filters. Empty when none "
                                "qualifies. Fair American odds shown are model no-margin prices."],
        ], [0.8*inch, BODY_WIDTH-0.8*inch], S),
        sp(8),
    ]

    story += [
        KeepTogether([
            Paragraph("The Expanded Row", S["h3"]),
            Paragraph(
                "Clicking any match row expands it to reveal three additional panels "
                "with the full detail behind the summary numbers.",
                S["body"]),
        ]),
        sp(4),
        styled_table([
            ["Panel",                        "Contents"],
            ["Full Scoreline Distribution",
             "All non-trivial scorelines ranked from most to least likely, with probability "
             "bars. These are raw joint PMF cell values. For correct-score betting: if a "
             "book offers American odds on score S, convert to no-vig fair probability "
             "and compare to the model's cell value for that score."],
            ["All Markets",
             "Every market the engine has priced from the joint PMF: 1X2, BTTS, "
             "Over/Under at every standard line from 0.5 through 6.5 goals, Draw No Bet, "
             "Double Chance, Win to Nil (home/away), Asian Handicap -0.5, and team-level "
             "totals. Every number here flows from the same underlying distribution."],
            ["Edge Report",
             "For each market: model probability, no-vig market implied probability "
             "(averaged across up to 6 bookmakers after SHIN normalization), edge %, "
             "fair American odds, and current market American odds. Gold-highlighted "
             "rows have passed all three value filters. The Kelly Stake column reflects "
             "your entered bankroll and selected fraction."],
        ], [1.6*inch, BODY_WIDTH-1.6*inch], S),
        sp(6),
        callout_box(
            "How to use Page 1: Start with the KPI cards to calibrate expectations. "
            "Scan the table for matches with a non-zero Best Edge. Expand any such match, "
            "read the full Edge Report carefully, and verify the current odds at your "
            "preferred book before placing anything. Odds change between prediction "
            "generation (8 AM UTC daily) and kickoff.",
            S, label="Usage Guide"),
        sp(10),
    ]

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # PAGE 2
    # ═══════════════════════════════════════════════════════
    story += [
        Paragraph("Page 2 — Probability Distributions", S["h2"]),
        gold_thin_rule(),
        Paragraph(
            "sportsodds.wizardofodds.com/tools/odds-scanner/predictions/world-cup/pre-match/"
            "Probability%20Distributions.html",
            S["url"]),
        Paragraph(
            "Where Page 1 compresses model output into a single row per match, this "
            "page opens it completely. Select a match using the navigation chips at the "
            "top and every chart updates immediately to show the full probability landscape. "
            "Not just the most likely result — the entire distribution from every angle.",
            S["body"]),
        sp(6),
    ]

    story += [
        KeepTogether([
            Paragraph("Chart 1 — Joint Score PMF Heatmap", S["h3"]),
            Paragraph(
                "The heatmap is the model in its purest form. Every cell (h, a) shows "
                "P(Home = h, Away = a). Home goals increase upward on the vertical axis; "
                "away goals increase rightward on the horizontal axis.",
                S["body"]),
            Paragraph(
                "The color scale uses the <b>square root</b> of each cell's probability "
                "relative to the maximum cell value. This is deliberate. Without the "
                "square root, cells above ~8% would appear bright and everything else "
                "would look uniformly dark — the distribution is so heavily concentrated "
                "in the low-scoring top-left region that a linear scale is visually "
                "useless. The square root transformation separates moderate-probability "
                "cells (3–5%) from near-zero ones, making the full grid readable.",
                S["body"]),
        ]),
        Paragraph(
            "Every betting market is readable directly from this heatmap. Some examples:",
            S["body"]),
        sp(4),
        styled_table([
            ["What You Want to Know",       "Where to Look on the Heatmap"],
            ["Over 2.5 goals probability",  "Sum of all cells in the upper-right region where h+a >= 3"],
            ["BTTS probability",            "Everything except the first row (h=0) and first column (a=0)"],
            ["Home clean sheet",            "First column only (a=0): all cells where away scores 0"],
            ["Away clean sheet",            "First row only (h=0): all cells where home scores 0"],
            ["Correct score 2-1",           "Single cell at row h=2, column a=1 — read the number"],
            ["Draw probability",            "Diagonal cells: (0,0), (1,1), (2,2), (3,3), ..."],
            ["Home win by exactly 2",       "Sum of cells where h-a = 2: (2,0),(3,1),(4,2),etc."],
        ], [2.0*inch, BODY_WIDTH-2.0*inch], S),
        sp(6),
        Paragraph(
            "The <b>tail mass</b> shown below the heatmap is the probability assigned "
            "to scores beyond the grid boundary (more than ~8-9 goals per team). In "
            "practice vanishingly small but nonzero — it must exist so the grid sums "
            "to exactly 100%.",
            S["body"]),
        sp(8),
    ]

    story += [
        KeepTogether([
            Paragraph("Chart 2 — Marginal Goal Distributions", S["h3"]),
            Paragraph(
                "Two bar charts side by side: the probability the home team scores "
                "exactly k goals (left), and the same for the away team (right). "
                "These marginals are derived by collapsing the joint PMF along each axis:",
                S["body"]),
        ]),
        formula_box([
            "Marginal distributions:",
            "",
            "  P(Home = h)  =  SUM over all a  of  P(Home=h, Away=a)  [collapse columns]",
            "  P(Away = a)  =  SUM over all h  of  P(Home=h, Away=a)  [collapse rows]",
            "",
            "# Each marginal bar chart shows P(team scores exactly k goals) for k = 0,1,2,...",
            "# The bars must sum to 1.0 for each team independently.",
        ], S),
        sp(6),
        Paragraph(
            "A tall bar at k = 0 indicates this team is frequently shut out — the model "
            "assigns high probability to them failing to score at all. A relatively flat "
            "distribution across k = 1 and k = 2 reflects a strong attacking rate. "
            "In most World Cup group-stage matches, the tallest bar sits at k = 1 for "
            "both teams.",
            S["body"]),
        sp(8),
    ]

    story += [
        KeepTogether([
            Paragraph("Chart 3 — Total Goals Distribution", S["h3"]),
            Paragraph(
                "A bar chart showing the probability of each possible total goal count "
                "from 0 through 8+. Computed by summing all cells along each anti-diagonal "
                "of the joint PMF:",
                S["body"]),
        ]),
        formula_box([
            "P(Total = k)  =  SUM over all (h,a) where h+a=k  of  P(h,a)",
            "",
            "# k=0: only cell (0,0)",
            "# k=1: cells (1,0) and (0,1)",
            "# k=2: cells (2,0),(1,1),(0,2)",
            "# k=3: cells (3,0),(2,1),(1,2),(0,3)  ... and so on",
        ], S),
        sp(6),
        Paragraph(
            "Standard over/under lines (0.5, 1.5, 2.5, 3.5, 4.5, 5.5) appear as vertical "
            "dividers on the chart. The probability to the right of any divider is the "
            "Over probability for that line; to the left is the Under. This chart makes "
            "the model's entire total-goals market visible at once — you can see Over 2.5 "
            "and Over 3.5 and Over 4.5 simultaneously without navigating to a table.",
            S["body"]),
        sp(8),
    ]

    story += [
        KeepTogether([
            Paragraph("Chart 4 — Goal Difference Distribution", S["h3"]),
            Paragraph(
                "Centered on zero, this bar chart shows P(goal difference = d) for "
                "every possible value d = home goals - away goals. Gold bars indicate "
                "home wins (d > 0), gray indicates draws (d = 0), blue indicates away "
                "wins (d < 0).",
                S["body"]),
            Paragraph(
                "A heavily gold-skewed distribution means the model sees the home team "
                "as a clear favorite. A roughly symmetric distribution means the match "
                "is genuinely even. The height of the gray bar relative to the gold and "
                "blue bars shows how likely a draw is given these two specific teams. "
                "High-scoring expected matches tend to have shorter gray bars — when "
                "both teams are expected to score frequently, exact ties become less "
                "probable.",
                S["body"]),
        ]),
        sp(8),
    ]

    story += [
        KeepTogether([
            Paragraph("Chart 5 — Top 20 Most Likely Scorelines", S["h3"]),
            Paragraph(
                "A ranked bar chart of the 20 most probable individual final scores "
                "with exact percentages and fair American odds shown next to each bar. "
                "The fair odds have no bookmaker margin — they represent what a perfectly "
                "calibrated market would offer for each specific score.",
                S["body"]),
            Paragraph(
                "As a general reference: the top cell in most group-stage matches "
                "carries 12–20% probability. Any score above 6% is in the top tier "
                "of the distribution. Values below 1% are common correct-score offerings "
                "that carry long odds.",
                S["body"]),
            Paragraph(
                "For correct-score betting: if your sportsbook is offering American odds "
                "on scoreline S, first convert to a no-vig fair probability (divide 1 "
                "by the decimal equivalent after removing the bookmaker margin), then "
                "compare to the model's percentage for that cell. A book offering +550 "
                "on a score the model gives 12% probability implies a fair price of "
                "+733 — a meaningful gap worth investigating.",
                S["body"]),
        ]),
        sp(8),
    ]

    story += [
        KeepTogether([
            Paragraph("O/U Lines Table", S["h3"]),
            Paragraph(
                "A clean table listing Over and Under probabilities for every standard "
                "total line from 0.5 through 6.5. All values are computed directly from "
                "the joint PMF — no additional modeling involved. Useful for quickly "
                "comparing the model's view across all lines without doing arithmetic "
                "from the chart.",
                S["body"]),
        ]),
        sp(6),
        callout_box(
            "How to use Page 2: After finding an interesting match on Page 1, come "
            "here for the full picture. The heatmap shows where probability is concentrated. "
            "The goal difference chart shows how result probabilities break down. "
            "The top scorelines chart helps evaluate correct-score prices at your book. "
            "The total goals chart shows all O/U markets simultaneously.",
            S, label="Usage Guide"),
        sp(10),
    ]

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    # PAGE 3
    # ═══════════════════════════════════════════════════════
    story += [
        Paragraph("Page 3 — Live In-Play PMF", S["h2"]),
        gold_thin_rule(),
        Paragraph(
            "sportsodds.wizardofodds.com/tools/odds-scanner/predictions/world-cup/live/"
            "Probability%20Distributions.html",
            S["url"]),
        Paragraph(
            "This page activates when a World Cup match is in progress. When no match "
            "is live, it displays the next scheduled kickoff. All probabilities are "
            "regulation time only — 90 minutes plus stoppage time. Extra time and "
            "penalty shootouts are not in scope.",
            S["body"]),
        sp(6),
    ]

    story += [
        KeepTogether([
            Paragraph("How the Live Model Differs from Pre-Game", S["h3"]),
            Paragraph(
                "The pre-game model asks: <i>what will the final score be from kickoff?</i> "
                "The live model asks something fundamentally different: "
                "<b>given that the current score is H-A at minute t, what will "
                "the final score be at the 90th minute?</b>",
                S["body"]),
        ]),
        Paragraph(
            "That distinction is fundamental. Once a match is in progress, some final "
            "scores have become impossible. If the match is 2-1 in the 70th minute, "
            "the final score cannot be 1-0, 0-0, 2-0, or any score where home is below "
            "2 or away is below 1. Those grid cells are locked at zero probability. "
            "The remaining probability — 100% minus whatever was locked in those "
            "impossible cells — redistributes entirely across the reachable outcomes.",
            S["body"]),
        Paragraph(
            "This is conditional probability in action. It is what separates a proper "
            "live model from a pre-game model that simply gets refreshed on a 60-second "
            "timer. The live model's grid is a fundamentally different distribution — "
            "a conditional PMF rather than a prior PMF — and the two should never "
            "be confused.",
            S["body"]),
        Paragraph(
            "The live model also changes how it estimates remaining goal rates. Rather "
            "than assuming a constant rate across 90 minutes, it uses a "
            "<b>non-homogeneous hazard model</b>: the goal-scoring rate varies by "
            "match minute, calibrated from the minute-by-minute goal distribution "
            "across 128 World Cup matches from 2018 and 2022.",
            S["body"]),
        sp(4),
        styled_table([
            ["Match Phase",             "Minutes",    "Goal Rate Pattern",    "Explanation"],
            ["Early game",              "1-10",       "Below average",        "Teams settling in; low pressing intensity"],
            ["First half build-up",     "25-40",      "Rising",               "Matches open up as confidence builds"],
            ["Half-time transition",    "45-50",      "Elevated",             "Both teams fresh; first 5 min of 2nd half active"],
            ["Closing phase",           "75-90+",     "Above average",        "Teams chasing, committing forward; tired legs"],
        ], [1.3*inch, 0.75*inch, 1.1*inch, BODY_WIDTH-3.15*inch], S),
        sp(8),
    ]

    story += [
        KeepTogether([
            Paragraph("Score-State Multipliers", S["h3"]),
            Paragraph(
                "On top of the temporal baseline, score-state multipliers adjust each "
                "team's goal rate based on the current scoreline. A home team losing "
                "by one goal in the 70th minute will push forward, increasing both "
                "its own attack rate and the away team's counter-attacking opportunity. "
                "These multipliers are calibrated from World Cup data and the academic "
                "football forecasting literature (Dixon and Robinson, 1998):",
                S["body"]),
        ]),
        sp(4),
        styled_table([
            ["Score State",                       "Home Rate",  "Away Rate",  "Primary Effect"],
            ["Tied at minute 60 or later",        "x1.10",      "x1.10",
             "Both teams press for a winner; match becomes more open"],
            ["Home team losing by exactly 1",     "x1.25",      "x1.05",
             "Home pushes forward; away positions for the counter-attack"],
            ["Home team losing by 2 or more",     "x1.40",      "x1.10",
             "Home commits to attack; significant spaces available"],
            ["Home team winning by exactly 1",    "x0.90",      "x1.10",
             "Home defends lead; away increases forward pressure"],
            ["Home team winning by 2 or more",    "x0.80",      "x1.15",
             "Home manages the game; away committed to reducing deficit"],
        ], [1.95*inch, 0.7*inch, 0.7*inch, BODY_WIDTH-3.35*inch], S),
        sp(6),
        Paragraph(
            "When live expected goals (xG) data is available from BallDontLie, the "
            "model blends the live xG-derived rate (60% weight) with the pre-game "
            "prior (40% weight). This blend activates at minute 15 — before that, "
            "live xG from only a handful of shots is too noisy to be useful. By "
            "minute 70, the live model is genuinely tracking the actual shot volumes "
            "and quality observed in the match, not just the pre-game forecast.",
            S["body"]),
        formula_box([
            "From minute 15 onward:",
            "",
            "  lambda_effective  =  0.60 * lambda_xg_live  +  0.40 * lambda_pre_game",
            "",
            "# lambda_xg_live = xG-based rate derived from actual shots in current match",
            "# lambda_pre_game = original pre-game expected rate from composite prior",
            "# Blend allows the model to track actual match intensity in real time",
        ], S),
        sp(8),
    ]

    story += [
        KeepTogether([
            Paragraph("Connection Badge", S["h3"]),
            Paragraph(
                "A small indicator shows how the page is receiving live data:",
                S["body"]),
            sp(4),
            styled_table([
                ["Badge",               "Color",   "Meaning"],
                ["WebSocket Active",    "Green",
                 "Browser has an active push connection to the live prediction server. "
                 "When a goal or status change is reported, the server recomputes the "
                 "full conditional PMF and pushes it to all connected browsers within "
                 "approximately 200 milliseconds. No manual refresh needed."],
                ["Polling Active",      "Yellow",
                 "Push connection unavailable. The page fetches updated data from a "
                 "static JSON file every 60 seconds. Updates arrive with up to a "
                 "one-minute delay. This is the automatic fallback mode — no user "
                 "action required."],
            ], [1.1*inch, 0.6*inch, BODY_WIDTH-1.7*inch], S),
        ]),
        sp(8),
    ]

    story += [
        KeepTogether([
            Paragraph("Live KPI Cards", S["h3"]),
            sp(4),
            styled_table([
                ["Card",           "What It Shows",                      "Normal Value"],
                ["Matches Live",   "World Cup matches currently in progress", "0-4 during match window"],
                ["Next Kickoff",   "Next scheduled match with Eastern Time",  "Used when no live match"],
                ["Goals Today",    "Total goals across live/recent matches",   "Accumulates through the day"],
                ["Data Age",       "Time since last live snapshot",           "Under 2 min = normal; "
                                                                               "Over 10 min triggers warning"],
            ], [0.9*inch, 2.0*inch, BODY_WIDTH-2.9*inch], S),
        ]),
        sp(8),
    ]

    story += [
        KeepTogether([
            Paragraph("Win Probability Bar", S["h3"]),
            Paragraph(
                "The same three-segment bar as on Page 1 — Home Win (gold), Draw (gray), "
                "Away Win (blue) — but now <b>conditional on the current score and minute</b>. "
                "These are conditional probabilities: P(outcome | current_score = H-A, "
                "minute = t). They update with every new live snapshot.",
                S["body"]),
        ]),
        Paragraph(
            "Watch this bar during a live match and you see the model's view of the "
            "contest shifting in real time. A home goal pushes the gold segment rightward "
            "immediately. A late away equalizer can collapse the home win probability "
            "from 80% to 30% in a single update.",
            S["body"]),
        sp(6),

        KeepTogether([
            Paragraph("Pre-Game to Live Shift Table", S["h3"]),
            Paragraph(
                "Directly below the win probability bar, for each main market: the "
                "pre-game probability, the current live conditional probability, and "
                "the arithmetic difference between them. A large positive shift on "
                "Home Win combined with large negative shifts on Draw and Away Win "
                "tells you the home team has taken control of a match that was expected "
                "to be closer. This table is one of the most informative features on "
                "the live page — it quantifies exactly how the match is deviating from "
                "the pre-game expectation.",
                S["body"]),
        ]),
        sp(6),

        KeepTogether([
            Paragraph("Win Probability Sparkline", S["h3"]),
            Paragraph(
                "A compact line chart showing the home team's win probability from kickoff "
                "to the current minute. This history accumulates in your browser session "
                "and resets on page reload — it is stored client-side, not on the server. "
                "Sharp upward jumps correspond to home goals; sharp downward drops "
                "correspond to away goals. The sparkline makes visible what the current "
                "snapshot cannot: whether the home team earned their current probability "
                "gradually through sustained pressure, or in a single dramatic moment, "
                "and how volatile the match has been.",
                S["body"]),
        ]),
        sp(8),
    ]

    story += [
        KeepTogether([
            Paragraph("Live Joint Score PMF Heatmap", S["h3"]),
            Paragraph(
                "The same heatmap structure as on Page 2, updated with every live "
                "snapshot and annotated with two visual cues that distinguish it "
                "from the pre-game version:",
                S["body"]),
            sp(4),
            styled_table([
                ["Visual Cue",              "Description"],
                ["Red cell outline",        "The cell corresponding to the current live score is "
                                            "outlined in red. This is the 'current state' marker — "
                                            "the match is here now and can only move to cells "
                                            "reachable from this point."],
                ["Dark unreachable cells",  "All cells where home goals < current home score OR "
                                            "away goals < current away score are forced to zero "
                                            "and appear dark. These outcomes are no longer possible."],
            ], [1.35*inch, BODY_WIDTH-1.35*inch], S),
        ]),
        sp(6),
        Paragraph(
            "As the match progresses, the dark region grows and the probability "
            "concentrates into fewer and fewer bright cells. In stoppage time of a "
            "1-0 match, the heatmap may assign 85–90% probability to the single "
            "1-0 cell, with small amounts on 1-1 (away equalizes), 2-0 "
            "(home extends), and a handful of other reachable outcomes.",
            S["body"]),
        sp(8),
    ]

    story += [
        KeepTogether([
            Paragraph("Next Goal Probabilities", S["h3"]),
            Paragraph(
                "Three values derived from the remaining expected goals "
                "lambda_h_rem and lambda_a_rem:",
                S["body"]),
        ]),
        formula_box([
            "Home scores next:",
            "  lambda_h_rem / (lambda_h_rem + lambda_a_rem)",
            "  = P(next goal is a home goal | at least one more goal scored)",
            "",
            "Away scores next:",
            "  lambda_a_rem / (lambda_h_rem + lambda_a_rem)",
            "  = P(next goal is an away goal | at least one more goal scored)",
            "",
            "No more goals:",
            "  e^(-lambda_h_rem) x e^(-lambda_a_rem)",
            "  = P(both remaining Poisson processes produce exactly 0 goals)",
            "  = P(current score IS the final score)",
            "",
            "# As the match enters stoppage time with shrinking remaining lambdas,",
            "# 'No more goals' typically climbs above 80-90%.",
        ], S),
        sp(6),
        Paragraph(
            "<b>Home/Away scores next:</b> These are conditional probabilities given "
            "that a goal will be scored — they sum to 1.0 between them and ignore the "
            "possibility of no more goals. Use them to evaluate next-scorer and "
            "first-to-score live markets.",
            S["body"]),
        Paragraph(
            "<b>No more goals:</b> The joint Poisson probability that both remaining "
            "goal processes produce zero goals. This is the probability the match "
            "ends at the current score. Compare against your book's live Under "
            "line for the current total.",
            S["body"]),
        sp(8),
    ]

    story += [
        KeepTogether([
            Paragraph("Top 10 Most Likely Final Scores (Live)", S["h3"]),
            Paragraph(
                "The same ranked scoreline list as on Page 2, restricted to reachable "
                "outcomes only. The current live score is marked with an arrow. "
                "As the match approaches the final whistle, the probability on the "
                "leading score climbs rapidly — in an 88th-minute 1-0 match, the 1-0 "
                "cell may carry 8 or 9 times the probability it held before kickoff.",
                S["body"]),
            Paragraph(
                "This list tells you not just what is most likely but how much more "
                "likely it is than the alternatives. A top entry with 85% probability "
                "means the match is essentially decided. A top entry with 45% means "
                "there are still meaningful alternatives in play.",
                S["body"]),
        ]),
        sp(6),
        callout_box(
            "How to use Page 3: Most valuable during fast-moving matches where the "
            "pre-game expectation is being rapidly revised — a 2-0 scoreline in the "
            "30th minute reshapes the entire distribution. Also useful for evaluating "
            "live betting markets: compare the 'No more goals' probability against your "
            "book's live Under line; compare Next Goal fractions against live next-scorer "
            "pricing. The model's conditional probabilities update every 90 seconds "
            "during match windows.",
            S, label="Usage Guide"),
        sp(10),
    ]

    # ── Frequently Asked Questions ─────────────────────────────────────────────
    story += [
        KeepTogether([
            Paragraph("Common Questions About the Prediction Pages", S["h2"]),
            gold_thin_rule(),
            Paragraph(
                "Answers to the most common questions about interpreting the numbers "
                "and using the prediction pages effectively.",
                S["body"]),
        ]),
        sp(6),

        KeepTogether([
            Paragraph("Why does the model sometimes show 0 value bets?", S["h3"]),
            Paragraph(
                "Because the World Cup market is one of the best-covered betting markets "
                "in the world. Professional syndicates, sharp books, and quantitative "
                "models all focus heavily on these matches. The result is that the market "
                "is frequently very efficiently priced. A day with zero value bets is not "
                "a failure of the model — it is the model correctly recognizing that the "
                "bookmakers' prices are fair today.",
                S["body"]),
            Paragraph(
                "Value bets are more likely to appear when: a match involves a team "
                "with significant recent-form information that the model has incorporated "
                "but the public has not fully priced; when a specific market (like a "
                "correct score) is listed at odds that imply a probability lower than "
                "the model's grid value; or when the model's lambda estimates differ "
                "materially from what a simple 1X2 back-calculation would suggest.",
                S["body"]),
        ]),
        sp(4),

        KeepTogether([
            Paragraph("Why is the model probability for Over 2.5 different from the bookmaker's implied probability?", S["h3"]),
            Paragraph(
                "Several reasons. First, the model's pre-game parametric estimate "
                "(the Bivariate Poisson) and the market's price may reflect different "
                "information sets. The market may know about a key player injury that "
                "the model's lambda estimates haven't fully absorbed. Second, even after "
                "market reconciliation, the optimizer minimizes KL divergence — it moves "
                "the distribution toward the market but doesn't simply copy it.",
                S["body"]),
            Paragraph(
                "Third, different bookmakers offer different Over 2.5 lines. The model "
                "averages across all available books after SHIN normalization; if you are "
                "comparing to a specific book's price, their margin and market position "
                "may differ from the consensus.",
                S["body"]),
        ]),
        sp(4),

        KeepTogether([
            Paragraph("What does 'fair odds' mean on the site? Is that what I should expect to be offered?", S["h3"]),
            Paragraph(
                "Fair odds on this site are the model's no-margin American odds for each "
                "outcome — the odds a perfectly calibrated, zero-margin market would offer. "
                "In practice, every bookmaker adds a margin of 5–8% (sometimes more on "
                "exotic markets like correct scores). So the market odds available to you "
                "will typically be worse than the fair odds shown here.",
                S["body"]),
            Paragraph(
                "The fair odds are useful for comparison: if a book is offering odds "
                "significantly better than the fair odds shown, the model sees a value "
                "opportunity. If the book's odds are significantly worse than the fair "
                "odds, the book has a large margin on that market.",
                S["body"]),
        ]),
        sp(4),

        KeepTogether([
            Paragraph("The live model's probabilities changed before a goal happened — why?", S["h3"]),
            Paragraph(
                "The live model's conditional PMF updates based on two inputs: the "
                "current score and minute (which change the temporal hazard rate and "
                "score-state multipliers), and the live xG data (which reflects actual "
                "shot accumulation in the match). Even without a goal, the distribution "
                "shifts as time passes because the remaining expected goals shrink — "
                "a 0-0 at the 70th minute carries very different probabilities than "
                "the same 0-0 at the 25th minute.",
                S["body"]),
            Paragraph(
                "The xG blend (60% live xG rate, 40% pre-game prior, active from "
                "minute 15) also updates continuously. If one team is dominating "
                "possession and generating high xG without scoring, the live model "
                "will reflect that elevated attacking pressure even before a goal "
                "goes in.",
                S["body"]),
        ]),
        sp(4),

        KeepTogether([
            Paragraph("How should I interpret the Edge Report when Best Edge is shown but the match is hours away?", S["h3"]),
            Paragraph(
                "Treat it as a starting point, not a final signal. The edge report is "
                "generated at 8:00 AM UTC each day. The odds used for comparison are "
                "the best available at that time. By the time a match kicks off — "
                "potentially 8 or 10 hours later — the market may have moved. The "
                "best practice is to check the current odds at your book and recompute "
                "the edge manually using the model probabilities shown in the All Markets "
                "panel. The model probabilities themselves do not change significantly "
                "unless a major injury or lineup change is announced and the hourly "
                "update incorporates it.",
                S["body"]),
        ]),
        sp(8),
    ]

    # ── Understanding the Live PMF in Detail ──────────────────────────────────
    story += [
        KeepTogether([
            Paragraph("The Live PMF in Real Scenarios", S["h2"]),
            gold_thin_rule(),
            Paragraph(
                "A walk-through of how the Live In-Play PMF changes across three "
                "representative match scenarios. All probabilities are illustrative "
                "but representative of actual model output.",
                S["body"]),
        ]),
        sp(4),

        Paragraph("Scenario A: Match is 0-0 at the 60th minute", S["h4"]),
        Paragraph(
            "The pre-game model might have given Home Win 45%, Draw 28%, Away Win 27%. "
            "At 0-0 in minute 60, the conditional PMF updates:",
            S["body"]),
        formula_box([
            "Remaining expected goals: lambda_h_rem ≈ 0.65, lambda_a_rem ≈ 0.50",
            "  (roughly 30 minutes remain; hazard rate increases as both teams push)",
            "  Score-state multiplier at 0-0 after min 60: both teams x1.10",
            "  lambda_h_rem_adjusted ≈ 0.72,  lambda_a_rem_adjusted ≈ 0.55",
            "",
            "Likely updated probabilities (illustrative):",
            "  Home Win: ~39%  (lower than pre-game; less time for decisive goals)",
            "  Draw:     ~38%  (higher; 0-0 at 60 min makes draw much more likely)",
            "  Away Win: ~23%  (lower for same reasons as Home Win)",
            "  No more goals: e^(-0.72) x e^(-0.55) ≈ 0.487 x 0.577 ≈ 28%",
        ], S),
        sp(4),

        Paragraph("Scenario B: Match is 2-0 at the 30th minute", S["h4"]),
        Paragraph(
            "A dramatic early lead completely reshapes the distribution. The 2-0 home "
            "lead at minute 30 means scores of (0,0), (0,1), (1,0), (1,1), (2,1), "
            "(0,2) and many others are now impossible — the away team hasn't scored "
            "and the home team has 2. The remaining expected goals cover a full 60 minutes.",
            S["body"]),
        formula_box([
            "Remaining expected goals: lambda_h_rem ≈ 1.10, lambda_a_rem ≈ 0.85",
            "  Score-state multiplier: home winning by 2 -> home x0.80, away x1.15",
            "  lambda_h_rem_adj ≈ 0.88,  lambda_a_rem_adj ≈ 0.98",
            "",
            "Reachable final scores from (2,0): (2,0),(2,1),(2,2),(3,0),(3,1),(3,2),(4,0)...",
            "",
            "Likely updated probabilities (illustrative):",
            "  Home Win: ~82%  (strong favorite; large lead with 60 min remaining)",
            "  Draw:      ~9%  (away needs 2 goals to tie)",
            "  Away Win:  ~9%  (away needs 3 goals)",
            "  No more goals: e^(-0.88) x e^(-0.98) ≈ 0.415 x 0.375 ≈ 15.6%",
            "  Most likely final score: 2-0 (~30%), then 2-1 (~26%), then 3-0 (~14%)",
        ], S),
        sp(4),

        Paragraph("Scenario C: Match is 1-1 at the 85th minute", S["h4"]),
        Paragraph(
            "The classic late-game tension. Most scores are now impossible; "
            "only scores reachable from 1-1 remain. The dark region of the heatmap "
            "covers most of the grid, leaving only a bright cluster near (1,1), "
            "(2,1), (1,2), and (2,2).",
            S["body"]),
        formula_box([
            "Remaining expected goals: lambda_h_rem ≈ 0.14, lambda_a_rem ≈ 0.14",
            "  Hazard rate is elevated in stoppage time, but only ~5-7 minutes remain",
            "  Score-state at 1-1 after min 60: both teams x1.10 -> ≈ 0.15 each",
            "",
            "No more goals: e^(-0.15) x e^(-0.15) = 0.861 x 0.861 ≈ 74%",
            "",
            "Likely updated probabilities (illustrative):",
            "  Home Win: ~11%  (home needs to score; ~14% lambda, 5 min)",
            "  Draw:     ~74%  (most likely — no more goals)",
            "  Away Win: ~15%  (away slightly more likely to score in this scenario)",
            "",
            "Top 10 live scores: 1-1 (~74%), 2-1 (~8%), 1-2 (~12%), 2-2 (~1%), ...",
        ], S),
        sp(8),
    ]

    # ── Quick Reference ────────────────────────────────────────────────────────
    story += [
        KeepTogether([
            Paragraph("Quick Reference: Key Symbols and Formulas", S["h2"]),
            gold_thin_rule(),
            Paragraph(
                "A concise reference for the mathematical notation used throughout "
                "the site and in this guide.",
                S["body"]),
            sp(6),
        ]),
        styled_table([
            ["Symbol / Term",           "Definition"],
            ["lambda_h",                "Expected home goals (rate parameter for home team's Poisson process)"],
            ["lambda_a",                "Expected away goals (rate parameter for away team's Poisson process)"],
            ["lambda_3",                "Shared intensity parameter in Bivariate Poisson = Cov(H,A). Currently 0.170."],
            ["lambda_h_rem",            "Expected remaining home goals from current minute to 90+"],
            ["lambda_a_rem",            "Expected remaining away goals from current minute to 90+"],
            ["PMF",                     "Probability Mass Function — the full grid of P(h,a) values"],
            ["T (temperature)",         "Calibration parameter. T=1.089 currently. T>1 flattens distribution."],
            ["SHIN normalization",       "Method to remove bookmaker margin from quoted odds"],
            ["KL divergence",           "Kullback-Leibler divergence — measures how far a distribution moved"],
            ["SLSQP",                   "Sequential Least Squares Programming — constrained optimizer"],
            ["NLL",                     "Negative Log-Likelihood — primary model selection criterion"],
            ["CLV",                     "Closing Line Value — model probability vs. closing market price"],
            ["Edge",                    "(Model prob - Market prob) / Market prob. Positive = model above market."],
            ["f* (Kelly fraction)",     "Edge / (Decimal odds - 1). Optimal growth-maximizing bet size."],
            ["RPS",                     "Ranked Probability Score — calibration metric for 1X2 market"],
            ["ECE",                     "Expected Calibration Error — direct probability vs. frequency measure"],
        ], [1.5*inch, BODY_WIDTH-1.5*inch], S),
        sp(10),
    ]

    story += [
        KeepTogether([
            Paragraph("Comparing Model vs. Market: A Step-by-Step Example", S["h2"]),
            gold_thin_rule(),
            Paragraph(
                "A concrete walkthrough of how to use the Edge Report in practice. "
                "This example is illustrative but representative of real output.",
                S["body"]),
        ]),
        sp(4),
        Paragraph("Scenario: USA vs. Portugal, hypothetical group stage match.", S["h4"]),
        Paragraph(
            "You open Page 1 and see USA vs. Portugal listed with a Best Edge of +8.3% "
            "on 'Over 2.5 Goals'. You expand the row and read the Edge Report. "
            "Here is how to interpret each column:",
            S["body"]),
        sp(4),
        styled_table([
            ["Column",              "Value",    "What It Means"],
            ["Market",              "Over 2.5", "Total regulation-time goals >= 3"],
            ["Model Probability",   "58.2%",    "Sum of all PMF cells where h+a >= 3, after calibration"],
            ["Market Implied",      "53.7%",    "No-vig probability from 6 bookmakers, SHIN-normalized"],
            ["Edge",                "+8.3%",    "(0.582 - 0.537) / 0.537 = 8.4% (proportional, not additive)"],
            ["Fair Odds",           "-139 Am",  "1/0.582 - 1 expressed as American: +72 / -72... approx -139"],
            ["Market Odds",         "-120 Am",  "Typical current bookmaker line for Over 2.5"],
            ["CI Lower Bound",      "54.1%",    "With lambda perturbed -12%: still above market's 53.7%"],
            ["Kelly Stake",         "2.1%",     "Half-Kelly at default setting: f* = 8.3%/(1.833-1)/2"],
        ], [1.15*inch, 0.85*inch, BODY_WIDTH-2.0*inch], S),
        sp(6),
        Paragraph(
            "This market passes all three filters: edge (8.3% >= 4%), CI lower bound "
            "(54.1% > 53.7%), and market implied (53.7% > 2%). The Kelly Stake of 2.1% "
            "means the tool recommends betting 2.1% of your bankroll at the half-Kelly "
            "fraction. At a $500 bankroll, that is $10.50.",
            S["body"]),
        Paragraph(
            "Critical step before acting: verify the current Over 2.5 odds at your "
            "book. If the market has moved to -130 since the model ran, the new "
            "implied probability is 1/(1+100/130) ≈ 56.5%, and the edge narrows to "
            "(58.2% - 56.5%) / 56.5% = 3.0% — below the 4% threshold. The bet no "
            "longer qualifies. This is why you always check current odds.",
            S["body"]),
        sp(8),
        KeepTogether([
            Paragraph("Reading the Heatmap: What Each Region Tells You", S["h2"]),
            gold_thin_rule(),
            Paragraph(
                "A quick guide to what different regions of the Joint Score PMF "
                "Heatmap mean for different betting markets.",
                S["body"]),
            sp(4),
            styled_table([
                ["Heatmap Region",           "Market It Represents",             "What to Look For"],
                ["Top-left cell (0,0)",       "Nil-nil draw probability",         "A bright cell = meaningful probability of a goalless draw"],
                ["First row (h=0, all a)",    "Away team scores; home clean sheet","Sum of first row = P(home scores 0)"],
                ["First column (a=0, all h)", "Home team scores; away clean sheet","Sum of first column = P(away scores 0)"],
                ["Main diagonal cells",       "Draw probability",                 "Sum of (0,0),(1,1),(2,2)... = total draw %"],
                ["Upper-left 3x3 corner",    "Matches with 0-2 total goals",     "Bright here = strong Under 2.5 lean"],
                ["Upper-right region",        "Over 2.5 goals",                   "Sum of cells where h+a >= 3 = Over 2.5 %"],
                ["Top few cells of column 0", "P(Away=0, Home=1,2,3...)",        "Home win by clean sheet probability"],
                ["Single bright cell",        "Dominant most-likely scoreline",   "Correct score value — compare to book's odds"],
            ], [1.7*inch, 1.7*inch, BODY_WIDTH-3.4*inch], S),
        ]),
        sp(10),
    ]

    story += [
        KeepTogether([
            Paragraph("How the Three Pages Work Together", S["h2"]),
            gold_thin_rule(),
            Paragraph(
                "The three pages are designed to be used sequentially, from macro to micro:",
                S["body"]),
        ]),
        sp(4),
        styled_table([
            ["Page",        "Purpose",          "Start Here When"],
            ["Page 1 (Pre-Game)",
             "Overview of today's matches. KPI cards, match table with probabilities, "
             "edge report for all markets.",
             "You want to know: which matches today have value? What are today's "
             "key probability estimates? What are the flagged edge opportunities?"],
            ["Page 2 (Distributions)",
             "Full probability distribution for one selected match. Heatmap, "
             "marginals, total goals, goal difference, top scorelines.",
             "You've found a match of interest on Page 1 and want the full picture: "
             "how is probability distributed? Where are the correct-score values?"],
            ["Page 3 (Live)",
             "Conditional live PMF during an in-progress match. Score-state "
             "multipliers, win probability bar and sparkline, next goal probabilities.",
             "A match is in progress and you want to track live probabilities, "
             "evaluate live betting markets, or monitor how the distribution "
             "shifts with each goal."],
        ], [1.2*inch, 2.5*inch, BODY_WIDTH-3.7*inch], S),
        sp(10),
    ]

    # ── Power User Tips ─────────────────────────────────────────────────────────
    story += [
        KeepTogether([
            Paragraph("Tips for Getting the Most from the Prediction Pages", S["h2"]),
            gold_thin_rule(),
        ]),
        Paragraph(
            "<b>Bookmark the correct page for your workflow.</b> If you primarily want "
            "edge alerts, bookmark Page 1. If you regularly evaluate correct-score markets, "
            "bookmark Page 2. If you watch live matches with live betting open, "
            "pre-load Page 3 before kickoff so the browser session's sparkline "
            "captures the full match arc from minute 0.",
            S["body"]),
        Paragraph(
            "<b>Use the marginal charts to evaluate team-level markets.</b> The marginal "
            "distributions on Page 2 show P(home team scores exactly k goals) and "
            "P(away team scores exactly k goals) directly. These are exactly the "
            "distributions for team-total over/under markets — for example, "
            "Home Team Over 1.5 is P(home scores 0) + P(home scores 1) subtracted "
            "from 1.0.",
            S["body"]),
        Paragraph(
            "<b>The goal difference chart is the fastest read for result markets.</b> "
            "On Page 2, the goal difference distribution plots show P(home wins by "
            "1 goal), P(home wins by 2), P(draw), P(away wins by 1) etc. directly. "
            "These are the same as Asian handicap probabilities. P(difference = +1) "
            "is the probability the home team wins by exactly one goal — directly "
            "relevant for Asian handicap -1 markets.",
            S["body"]),
        Paragraph(
            "<b>The live page's win probability sparkline resets on reload.</b> If you "
            "want to track the full match arc, do not reload the page mid-match. "
            "Open the live page before kickoff and let it accumulate. The sparkline "
            "data lives only in your browser session's memory.",
            S["body"]),
        Paragraph(
            "<b>Treat the Top 20 Scorelines chart as a correct-score value scanner.</b> "
            "The fair American odds shown next to each bar on Page 2 have zero margin. "
            "If you can find a book offering better odds than shown for a high-probability "
            "scoreline, that is genuine value. Compare the fair odds column to what your "
            "book shows on their correct score market. Differences of more than 30 American "
            "odds points on a scoreline with 8-15% probability are worth investigating further.",
            S["body"]),
        Paragraph(
            "<b>The Data Age indicator on Page 3 is your health check.</b> Under 2 minutes "
            "means the pipeline is healthy and running normally. Between 2 and 10 minutes "
            "can occur during high-demand periods or between live match windows. Above "
            "10 minutes triggers the health warning banner and means the live page data "
            "may be stale. Do not make live betting decisions based on data that is "
            "more than 5 minutes old in a fast-moving match.",
            S["body"]),
        sp(10),
    ]

    # ── Limitations ────────────────────────────────────────────────────────────
    story += [
        Paragraph("Scope and Limitations — All Pages", S["h2"]),
        gold_thin_rule(),
        Paragraph(
            "These limitations are real. Read them before using any number from this site "
            "to inform a betting decision.",
            S["body"]),
        sp(4),
        Paragraph(
            "<b>Regulation time only.</b> All probabilities on all three pages represent "
            "90 minutes plus stoppage time. Extra time and penalty shootouts are not "
            "included. For knockout matches that go to extra time, the regulation-time "
            "distribution is not the complete picture.",
            S["bullet"]),
        sp(2),
        Paragraph(
            "<b>lambda_3 = 0.170 reduces but does not eliminate the independence "
            "approximation.</b> The Bivariate Poisson captures average correlation across "
            "all match types. Live score-state multipliers handle tactical dynamics in "
            "real time. But the pre-game prior is still a parametric approximation, "
            "not a complete model of football's complexity.",
            S["bullet"]),
        sp(2),
        Paragraph(
            "<b>Live pipeline latency.</b> The target of under 200 ms for WebSocket "
            "updates applies under normal conditions. Network latency and server load "
            "can affect real-time delivery. During peak periods (multiple simultaneous "
            "live matches), latency may increase.",
            S["bullet"]),
        sp(2),
        Paragraph(
            "<b>Small calibration sample.</b> Calibration temperature T and the "
            "WC_AVG scaling factor are estimated from limited completed 2026 match "
            "data. All parameters will stabilize as the tournament progresses to 48 "
            "and then 64 total matches.",
            S["bullet"]),
        sp(2),
        Paragraph(
            "<b>Odds move between prediction and kickoff.</b> Predictions are generated "
            "at 8:00 AM UTC daily. By the time you read the edge report, hours may have "
            "passed and market prices may have shifted significantly. Always verify "
            "current odds at your book before acting on any signal shown here.",
            S["bullet"]),
        sp(2),
        Paragraph(
            "<b>Edge estimates are not profit guarantees.</b> The model is probabilistic. "
            "Over a large sample of well-identified value bets, a model with genuine "
            "edge should show positive returns. Over any individual bet or short run, "
            "anything can happen. Never bet more than you can afford to lose.",
            S["bullet"]),
        sp(14),
        thin_rule(),
        sp(4),
        Paragraph(
            "All probabilities represent regulation time (90 minutes + stoppage time) only. "
            "Extra time and penalties are excluded. This guide is for informational and "
            "educational purposes only. Please gamble responsibly.",
            S["disclaimer"]),
    ]

    return story


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    styles = make_styles()

    print("Generating PDFs...")
    render(
        build_article1(styles),
        OUT_DIR / "wc2026-how-the-model-works.pdf",
        title="How the WC 2026 Prediction Model Works — Wizard of Odds",
        short_title="How the Model Works",
    )
    render(
        build_article2(styles),
        OUT_DIR / "wc2026-page-guide.pdf",
        title="A Guide to the WC 2026 Prediction Pages — Wizard of Odds",
        short_title="WC 2026 Page Guide",
    )
    print("Done.")
