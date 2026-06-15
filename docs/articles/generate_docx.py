"""
Generate Word (.docx) articles for wizardofodds.com.
Run: python3.10 docs/articles/generate_docx.py
"""
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy
from pathlib import Path

OUT_DIR = Path(__file__).parent

# ── Colors ────────────────────────────────────────────────────────────────────
GOLD      = RGBColor(0xD4, 0xAF, 0x37)
DARK_NAVY = RGBColor(0x0A, 0x0E, 0x1A)
BLUE_ACC  = RGBColor(0x1A, 0x3A, 0x6B)
BODY_CLR  = RGBColor(0x11, 0x11, 0x11)
MUTED_CLR = RGBColor(0x55, 0x55, 0x55)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRY = RGBColor(0xF0, 0xF0, 0xF0)
MID_GRY   = RGBColor(0xDD, 0xDD, 0xDD)
FORMULA_B = RGBColor(0xEE, 0xF2, 0xFF)
CALLOUT_B = RGBColor(0xFD, 0xF8, 0xED)


def new_doc():
    doc = Document()
    # Page margins: 1 inch all sides
    for section in doc.sections:
        section.page_width  = Inches(8.5)
        section.page_height = Inches(11)
        section.left_margin   = Inches(1.1)
        section.right_margin  = Inches(1.1)
        section.top_margin    = Inches(1.0)
        section.bottom_margin = Inches(1.0)
    # Remove default empty paragraph
    for p in doc.paragraphs:
        p._element.getparent().remove(p._element)
    return doc


def set_cell_bg(cell, rgb: RGBColor):
    """Set table cell background color via XML."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    hex_color = str(rgb)  # RGBColor.__str__ returns hex like '0A0E1A'
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)


def set_cell_border(cell, **kwargs):
    """Set borders on a table cell."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        if edge in kwargs:
            tag = OxmlElement(f'w:{edge}')
            for k, v in kwargs[edge].items():
                tag.set(qn(f'w:{k}'), v)
            tcBorders.append(tag)
    tcPr.append(tcBorders)


def para_keep_with_next(para):
    """Mark paragraph to keep with next (prevents orphan headings)."""
    pPr = para._p.get_or_add_pPr()
    kwn = OxmlElement('w:keepWithNext')
    pPr.append(kwn)
    kl = OxmlElement('w:keepLines')
    pPr.append(kl)


def add_site_header(doc, article_title):
    """Top branding bar: WIZARDOFODDS.COM | Article Title."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(4)
    run = p.add_run("WIZARDOFODDS.COM")
    run.bold = True
    run.font.size = Pt(9)
    run.font.color.rgb = GOLD
    run2 = p.add_run(f"     |     {article_title}")
    run2.font.size = Pt(9)
    run2.font.color.rgb = MUTED_CLR
    # Gold bottom border on paragraph
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '12')
    bottom.set(qn('w:space'), '4')
    bottom.set(qn('w:color'), 'D4AF37')
    pBdr.append(bottom)
    pPr.append(pBdr)


def add_h1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after  = Pt(6)
    para_keep_with_next(p)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(22)
    run.font.color.rgb = BODY_CLR
    return p


def add_subtitle(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(10)
    run = p.add_run(text)
    run.italic = True
    run.font.size = Pt(11)
    run.font.color.rgb = MUTED_CLR
    return p


def add_h2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after  = Pt(3)
    p.paragraph_format.keep_with_next = True
    para_keep_with_next(p)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(14)
    run.font.color.rgb = BODY_CLR
    # Gold bottom border
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '3')
    bottom.set(qn('w:color'), 'D4AF37')
    pBdr.append(bottom)
    pPr.append(pBdr)
    return p


def add_h3(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after  = Pt(3)
    para_keep_with_next(p)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(11)
    run.font.color.rgb = BLUE_ACC
    return p


def add_body(doc, text, space_after=Pt(7), justify=True):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = space_after
    if justify:
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    # Handle simple bold markup: **text** or split on markers
    # We'll use a simple approach: bold segments wrapped in **
    run = p.add_run(text)
    run.font.size = Pt(10)
    run.font.color.rgb = BODY_CLR
    return p


def add_body_rich(doc, segments, space_after=Pt(7), justify=True):
    """segments = list of (text, bold) tuples."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = space_after
    if justify:
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for text, bold in segments:
        run = p.add_run(text)
        run.bold = bold
        run.font.size = Pt(10)
        run.font.color.rgb = BODY_CLR
    return p


def add_formula(doc, text):
    """Monospace formula box with light blue background."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after  = Pt(6)
    p.paragraph_format.left_indent  = Inches(0.3)
    p.paragraph_format.right_indent = Inches(0.3)
    run = p.add_run(text)
    run.font.name = 'Courier New'
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x1A, 0x20, 0x60)
    # Light blue shading on paragraph
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), 'EEF2FF')
    pPr.append(shd)
    return p


def add_callout(doc, label, text):
    """Gold left-border callout box."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.style = 'Table Grid'
    cell = tbl.cell(0, 0)
    # Label
    lp = cell.add_paragraph()
    lp.paragraph_format.space_before = Pt(2)
    lp.paragraph_format.space_after  = Pt(2)
    lr = lp.add_run(label)
    lr.bold = True
    lr.font.size = Pt(9)
    lr.font.color.rgb = GOLD
    # Body
    bp = cell.add_paragraph()
    bp.paragraph_format.space_before = Pt(0)
    bp.paragraph_format.space_after  = Pt(4)
    bp.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    br = bp.add_run(text)
    br.font.size = Pt(9.5)
    br.font.color.rgb = RGBColor(0x33, 0x33, 0x55)
    br.italic = True
    # Remove default empty paragraph added by add_paragraph inside cell
    for spare in cell.paragraphs[:1]:
        spare._element.getparent().remove(spare._element)
    set_cell_bg(cell, CALLOUT_B)
    # Gold left border
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ('top', 'right', 'bottom', 'insideH', 'insideV'):
        tag = OxmlElement(f'w:{edge}')
        tag.set(qn('w:val'), 'none')
        tcBorders.append(tag)
    left = OxmlElement('w:left')
    left.set(qn('w:val'), 'single')
    left.set(qn('w:sz'), '18')
    left.set(qn('w:color'), 'D4AF37')
    tcBorders.append(left)
    tcPr.append(tcBorders)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)
    return tbl


def add_bullet(doc, text, bold_prefix=None):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after  = Pt(2)
    p.paragraph_format.left_indent  = Inches(0.3)
    if bold_prefix:
        r1 = p.add_run(bold_prefix + ": ")
        r1.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = BODY_CLR
        r2 = p.add_run(text)
        r2.font.size = Pt(10)
        r2.font.color.rgb = BODY_CLR
    else:
        r = p.add_run(text)
        r.font.size = Pt(10)
        r.font.color.rgb = BODY_CLR
    return p


def add_spacer(doc, pts=8):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(pts)
    return p


def add_page_break(doc):
    doc.add_page_break()


def dark_table_header(tbl, headers):
    """Style the first row of a table as a dark navy header with gold text."""
    hdr_row = tbl.rows[0]
    for i, cell in enumerate(hdr_row.cells):
        cell.text = ''
        p = cell.paragraphs[0]
        run = p.add_run(headers[i])
        run.bold = True
        run.font.size = Pt(9)
        run.font.color.rgb = GOLD
        set_cell_bg(cell, DARK_NAVY)


def style_data_row(tbl, row_idx, alt=False):
    row = tbl.rows[row_idx]
    bg = LIGHT_GRY if alt else WHITE
    for cell in row.cells:
        set_cell_bg(cell, bg)
        for p in cell.paragraphs:
            for run in p.runs:
                run.font.size = Pt(9)
                run.font.color.rgb = BODY_CLR


def add_disclaimer(doc):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(16)
    run = p.add_run(
        "All probabilities represent regulation time (90 minutes + stoppage time) only. "
        "Extra time and penalties are excluded. "
        "This article is for informational and educational purposes. Please gamble responsibly. "
        "WizardOfOdds.com"
    )
    run.italic = True
    run.font.size = Pt(8)
    run.font.color.rgb = MUTED_CLR


# =============================================================================
# ARTICLE 1 -- How the Model Works
# =============================================================================

def build_article1():
    doc = new_doc()
    TITLE = "How the 2026 World Cup Prediction Model Works"

    add_site_header(doc, TITLE)
    add_spacer(doc, 6)
    add_h1(doc, TITLE)
    add_subtitle(doc, "A complete guide to the mathematics behind the joint score probability engine -- WizardOfOdds.com -- June 2026")

    # ── Introduction ──────────────────────────────────────────────────────────
    add_h2(doc, "Introduction")
    add_body(doc,
        "Predicting the outcome of a football match is an exercise in structured humility. "
        "A match produces roughly two or three goals, arriving from a chaotic sequence of "
        "decisions and individual brilliance that no model can fully capture. Even the best "
        "football models in the world -- the ones running inside sharp sportsbooks -- are "
        "wrong more often than they are right about any individual game.")
    add_body(doc,
        "What a well-built model can do is get the probabilities right over a large number "
        "of matches. Assign 30% probability to outcomes that happen 30% of the time. Be "
        "faster than the public market in incorporating new information. Identify specific "
        "markets where the bookmaker's price does not reflect the available evidence. That "
        "is a narrower ambition than predicting winners -- but it is the one that produces "
        "long-run results.")
    add_body(doc,
        "This model produces a full joint probability distribution over every possible final "
        "score for every 2026 FIFA World Cup match. It runs six competing parametric models "
        "daily, blends them with a composite rating system built from six independent data "
        "sources, reconciles the result against live bookmaker prices, and runs every output "
        "through an automated calibration framework. The pipeline runs without human "
        "intervention 24 hours a day.")

    # ── What a PMF Is ────────────────────────────────────────────────────────
    add_h2(doc, "What a Joint Score PMF Actually Is")
    add_body(doc,
        "Before describing the engine, it helps to understand precisely what it produces. "
        "A PMF -- Probability Mass Function -- is a complete assignment of probability to "
        "every possible discrete outcome. For a football match, the joint score PMF is a "
        "two-dimensional grid. Each cell (h, a) holds P(Home = h, Away = a): the probability "
        "that the home team scores exactly h goals and the away team scores exactly a goals "
        "in regulation time.")
    add_body(doc,
        "The grid runs from (0, 0) through 8 or 9 goals per team, plus an explicit tail-mass "
        "bucket for extreme scores beyond the boundary. Every cell including the tail sums to "
        "exactly 1.0. This is a hard constraint enforced at every stage of the pipeline.")
    add_body(doc,
        "Every betting market is simply a different question about this same grid. There is "
        "no separate model for Over/Under, no separate model for BTTS -- every number flows "
        "from one source of truth:")

    # Markets table
    tbl = doc.add_table(rows=9, cols=2)
    tbl.style = 'Table Grid'
    tbl.columns[0].width = Inches(1.8)
    tbl.columns[1].width = Inches(4.4)
    dark_table_header(tbl, ["Market", "How It Is Calculated from the PMF Grid"])
    rows_data = [
        ("Over 2.5 goals",      "Sum all cells where h + a >= 3"),
        ("Under 2.5 goals",     "Sum all cells where h + a <= 2"),
        ("Both Teams to Score", "All cells where h >= 1 AND a >= 1"),
        ("Home Win",            "All cells where h > a"),
        ("Draw",                "All cells on the main diagonal: (0,0), (1,1), (2,2), ..."),
        ("Away Win",            "All cells where a > h"),
        ("Correct score 2-1",   "The single cell P(h=2, a=1) -- one number read directly"),
        ("Home clean sheet",    "Sum entire column a=0: P(0,0) + P(1,0) + P(2,0) + ..."),
    ]
    for i, (mkt, calc) in enumerate(rows_data, 1):
        row = tbl.rows[i]
        row.cells[0].text = mkt
        row.cells[1].text = calc
        style_data_row(tbl, i, alt=(i % 2 == 0))
    add_spacer(doc, 6)
    add_callout(doc, "The Internal Consistency Guarantee",
        "There is no separate model for each market type. The PMF is the entire model, and "
        "all markets are different questions about the same distribution. This guarantees "
        "internal consistency -- a property that does not hold on sites that blend data from "
        "different sources or use different models for different markets.")

    # ── Step 1: Composite Prior ───────────────────────────────────────────────
    add_h2(doc, "Step 1: Rating Every Team -- The Composite Prior")
    add_body(doc,
        "The first task is assigning each of the 48 World Cup teams an attack lambda and "
        "a defense lambda -- the expected goals scored and conceded against an average "
        "opponent on a neutral pitch. No single rating system is good enough to trust "
        "entirely. Club data does not transfer cleanly to international football. FIFA "
        "rankings can lag months behind a team's actual form. Bookmaker odds contain genuine "
        "signal but can be distorted by public betting flow on marquee matches. The solution "
        "is a composite prior blended from six independent data sources.")

    # Rating sources table
    add_h3(doc, "The Six Rating Sources")
    add_body(doc, "Weights shown are for matches where bookmaker odds are available:", space_after=Pt(4))
    tbl2 = doc.add_table(rows=7, cols=4)
    tbl2.style = 'Table Grid'
    col_widths = [1.5, 1.9, 0.7, 2.1]
    for i, w in enumerate(col_widths):
        for cell in tbl2.columns[i].cells:
            cell.width = Inches(w)
    dark_table_header(tbl2, ["Source", "Primary Data", "Weight", "Key Strength"])
    sources = [
        ("1. Market-Implied",         "1X2 odds from up to 6 bookmakers",    "30%",  "Late team news, sharp money, all available information"),
        ("2. FIFA Ranking",           "March 2026 points snapshot",          "~12%", "Long-run international performance across all competitions"),
        ("3. Qualifying Record",      "Attack/defense efficiency, shrunk",   "~10%", "Campaign-specific form, recent competitive history"),
        ("4. Pi Rating (penaltyblog)","Goal-margin Elo, goal-sensitive",     "~18%", "Fast form updates, responds to margin of victory"),
        ("5. Elo Rating (penaltyblog)","Win/loss/draw outcomes",             "~35%", "Stability and long-run signal, not distorted by flukes"),
        ("6. Confederation Baseline", "Historical WC averages by region",   "~5%",  "Soft floor preventing impossible extreme estimates"),
    ]
    for i, (src, data, wt, strength) in enumerate(sources, 1):
        row = tbl2.rows[i]
        row.cells[0].text = src
        row.cells[1].text = data
        row.cells[2].text = wt
        row.cells[3].text = strength
        style_data_row(tbl2, i, alt=(i % 2 == 0))
    add_spacer(doc, 8)

    add_h3(doc, "Source 1: Market-Implied Strength (30% weight)")
    add_body(doc,
        "When bookmaker odds are available, they encode information no rating system can "
        "access: late team news, undisclosed injuries, sharp professional money, and the "
        "aggregate view of every serious analyst who has looked at the match. The model "
        "reverse-engineers what attack and defense lambdas would produce the bookmaker's "
        "observed 1X2 probabilities. Before doing this, the bookmaker margin must be removed. "
        "SHIN normalization is applied to all odds from all bookmakers to convert them to "
        "fair (no-margin) probabilities. Using raw odds as fair probabilities would "
        "consistently bias every market comparison -- this step is not optional. Up to 6 "
        "sportsbooks contribute: FanDuel, DraftKings, BetMGM, BetRivers, Caesars, and "
        "Fanatics. Their no-vig probabilities are averaged to produce a consensus view.")

    add_h3(doc, "Host Advantage and Altitude Adjustments")
    add_body(doc,
        "USA, Canada, and Mexico each receive +0.10 to attack lambda and -0.10 to defense "
        "lambda as co-hosts. All other matches are treated as neutral venue. Three Mexican "
        "venues sit at elevations that materially reduce scoring for unacclimated players. "
        "Both teams' lambdas are scaled equally since neither side has an acclimatization "
        "advantage:")
    add_bullet(doc, "Estadio Azteca, Mexico City (2,230m): 0.93x multiplier -- approximately 7% scoring reduction")
    add_bullet(doc, "Estadio Akron, Guadalajara (1,560m): 0.97x multiplier -- approximately 3% reduction")
    add_bullet(doc, "Estadio BBVA, Monterrey (530m): no adjustment")

    add_h3(doc, "Tournament Adjustment: Learning from 2026 Results")
    add_body(doc,
        "Once WC2026 matches complete, their results feed back into each team's composite "
        "rating through a Bayesian shrinkage mechanism. For a team with n completed WC2026 "
        "matches, the shrinkage factor is n / (n + 3). This means one match contributes "
        "25% weight, two matches contribute 40%, three matches 50% -- preventing overreaction "
        "to a single result while genuinely updating on multiple games. Adjustments are "
        "capped at +/- 30%. Currently 22 teams have active tournament adjustments from "
        "11 completed WC2026 matches. Expected goals data from BallDontLie is blended in "
        "for all 22 teams (40% actual goals / 60% xG) to reduce noise.")

    add_h3(doc, "Dynamic WC_AVG Scaling")
    add_body(doc,
        "This World Cup is playing at a historically high scoring rate. The historical "
        "average from 2018 and 2022 was 1.30 goals per team per match. Through 11 completed "
        "2026 matches, the observed rate is 1.455 goals per team per match. The model applies "
        "a scaling factor of 1.119x to all 52 team lambdas after the composite prior is "
        "built, ensuring predictions reflect the actual tournament environment rather than "
        "being anchored to historical baselines.")
    add_callout(doc, "Current Status -- June 2026",
        "22 teams have active tournament adjustments from 11 completed WC2026 matches. "
        "The WC_AVG scale factor is 1.119x (observed 1.455 goals/team vs historical 1.30). "
        "xG blend is active for all 22 teams with completed matches.")

    # ── Step 2: Bivariate Poisson ─────────────────────────────────────────────
    add_h2(doc, "Step 2: How P(Home=h, Away=a) Is Calculated -- The Bivariate Poisson")
    add_body(doc,
        "This is the most technically interesting stage of the model -- the one that "
        "separates it from the standard approach found in most public football forecasters.")

    add_h3(doc, "The Standard Approach and Its Flaw")
    add_body(doc,
        "The naive approach assumes home and away goals are independent Poisson random "
        "variables. Under this assumption, the joint probability of a final score is simply "
        "the product of two independent probabilities:")
    add_formula(doc,
        "P(H=h, A=a) = P(H=h) * P(A=a)\n"
        "           = [e^(-lam_h) * lam_h^h / h!] * [e^(-lam_a) * lam_a^a / a!]")
    add_body(doc,
        "This is the textbook starting point and it is wrong in a subtle but important way. "
        "Goals are not independent. When a goal goes in at the 25th minute, everything "
        "changes -- the losing team pushes forward, the winning team may sit deeper, the "
        "tactical picture reshapes entirely. High-intensity, open matches tend to produce "
        "more goals for both teams simultaneously. The correlation between home and away "
        "goals in football is small but real and positive.")

    add_h3(doc, "The Bivariate Poisson: Three Latent Processes")
    add_body(doc,
        "The Bivariate Poisson model handles this properly. The mathematical intuition: "
        "instead of two independent processes, model the goals as arising from THREE "
        "independent Poisson processes:")
    add_bullet(doc, "Z1 ~ Poisson(lambda_1): goals generated by the home team independently")
    add_bullet(doc, "Z2 ~ Poisson(lambda_2): goals generated by the away team independently")
    add_bullet(doc, "Z3 ~ Poisson(lambda_3): a shared 'match intensity' component -- extra goals that tend to occur simultaneously in high-energy matches")
    add_body(doc, "Then: H = Z1 + Z3,   A = Z2 + Z3")
    add_body(doc,
        "Z3 is the key innovation. It creates positive correlation between home and away "
        "goals through a shared latent process. A match with high Z3 is one where both "
        "teams are pushed into an open, attacking game -- think a Champions League quarter "
        "final at 2-1 in the 70th minute with both teams going for it.")

    add_h3(doc, "The Joint Probability Formula")
    add_body(doc,
        "The joint probability of observing exactly h home goals and a away goals under "
        "the Bivariate Poisson model is:")
    add_formula(doc,
        "P(H=h, A=a) = e^(-(lam_1 + lam_2 + lam_3))\n"
        "              * SUM_{k=0}^{min(h,a)}\n"
        "                  [lam_1^(h-k) / (h-k)!]\n"
        "                * [lam_2^(a-k) / (a-k)!]\n"
        "                * [lam_3^k     / k!    ]")
    add_body(doc,
        "When lambda_3 = 0, the sum has only one term (k=0) and the formula reduces "
        "exactly to the independent Poisson product. The Bivariate Poisson IS the "
        "independent Poisson when the data does not support correlation -- it never "
        "breaks, it only adds information when it is there.")
    add_callout(doc, "Current Calibrated Value",
        "lambda_3 = 0.170, calibrated from 11 completed WC2026 matches. "
        "Positive and meaningful -- this World Cup is showing exactly the mutual intensity "
        "correlation the model was built to capture. Cov(H, A) = lambda_3 = 0.170.")

    add_h3(doc, "The Six Parametric Competitors")
    add_body(doc,
        "The model does not simply use the Bivariate Poisson. It runs six competing "
        "parametric models daily, selects the winner by negative log-likelihood on "
        "held-out WC2026 data, and uses the champion for all predictions. The winner "
        "is reselected daily as more matches accumulate:", space_after=Pt(4))

    tbl3 = doc.add_table(rows=7, cols=3)
    tbl3.style = 'Table Grid'
    for cell in tbl3.columns[0].cells: cell.width = Inches(0.4)
    for cell in tbl3.columns[1].cells: cell.width = Inches(1.8)
    for cell in tbl3.columns[2].cells: cell.width = Inches(4.0)
    dark_table_header(tbl3, ["#", "Model", "What It Captures"])
    models = [
        ("1", "Independent Poisson",   "Classical baseline. Goals independent. Useful benchmark."),
        ("2", "Dixon-Coles",           "Low-score correction via rho parameter. Currently rho ~ 0."),
        ("3", "Bivariate Poisson",     "Shared intensity lambda_3 = 0.170. Current log-loss champion."),
        ("4", "Weibull Copula",        "Heavier tails than Poisson. More high-scoring outliers."),
        ("5", "Negative Binomial",     "Overdispersion: variance > mean. Common in real football data."),
        ("6", "Zero-Inflated Poisson", "Excess 0-0 draws beyond what Poisson predicts."),
    ]
    for i, (num, name, desc) in enumerate(models, 1):
        row = tbl3.rows[i]
        row.cells[0].text = num
        row.cells[1].text = name
        row.cells[2].text = desc
        style_data_row(tbl3, i, alt=(i % 2 == 0))
    add_spacer(doc, 8)

    # ── Step 3: Market Reconciliation ────────────────────────────────────────
    add_h2(doc, "Step 3: Market Reconciliation (SLSQP Optimization)")
    add_body(doc,
        "Even the Bivariate Poisson cannot know about a goalkeeper injury announced 90 "
        "minutes before kickoff. Market reconciliation solves this. For each match, the "
        "model extracts fair market probabilities from all available bookmakers after SHIN "
        "normalization across as many market types as the API carries: 1X2, Over/Under 0.5 "
        "through 6.5, BTTS, Draw No Bet, Double Chance, and correct score lines.")
    add_body(doc,
        "A constrained optimization algorithm -- SLSQP (Sequential Least Squares "
        "Programming) -- then adjusts the parametric PMF grid to satisfy these market "
        "constraints while minimizing KL divergence from the original distribution. KL "
        "divergence measures how far the adjusted distribution has moved from the starting "
        "point, ensuring the optimizer only moves as far as the market evidence requires. "
        "Constraints are hard: all cell values must be non-negative and sum to 1.0.")
    add_body(doc,
        "When SLSQP converges to a better solution than a simple weighted-average blend, "
        "SLSQP is used. In practice, SLSQP dominates for virtually all matches -- currently "
        "only 1 non-convergence out of 63 matches, and even that case passes the "
        "plausibility check.")

    # ── Step 4: Calibration ────────────────────────────────────────────────
    add_h2(doc, "Step 4: Calibration (Temperature Scaling)")
    add_body(doc,
        "A model is calibrated when the probabilities it outputs match observed frequencies. "
        "When it says 30%, outcomes should occur 30% of the time. Calibration is distinct "
        "from accuracy -- an overconfident model assigns 80% to outcomes that only occur "
        "65% of the time.")
    add_body(doc,
        "The model uses temperature scaling: a single parameter T fitted by minimizing "
        "exact-score log loss on out-of-sample predictions from the 2018 and 2022 World "
        "Cups. The calibrated probability for each cell is:")
    add_formula(doc,
        "p_calibrated[h,a]  proportional to  p_raw[h,a] ^ (1/T)\n"
        "\n"
        "Then renormalized so all cells sum to 1.0.\n"
        "\n"
        "Current calibrated temperature: T = 1.089\n"
        "(T > 1 flattens the distribution, correcting for mild overconfidence)")
    add_body(doc,
        "Five calibration metrics are evaluated on out-of-sample predictions only: "
        "exact-score negative log-likelihood (primary metric), Ranked Probability Score "
        "for 1X2, multiclass Brier score, Expected Calibration Error, and the ignorance "
        "score. T = 1.089 indicates the model is mildly overconfident -- a common pattern "
        "in football models trained on limited data -- and the temperature correction is "
        "a modest fine-tuning rather than a major revision.")

    # ── Step 5: Edge Screening ─────────────────────────────────────────────
    add_h2(doc, "Step 5: Edge Screening and Kelly Sizing")
    add_body(doc,
        "With a calibrated PMF for each match, the model compares its probability "
        "estimates against the bookmaker's no-vig prices. An edge exists when the model's "
        "estimate is higher than the market's:")
    add_formula(doc,
        "Edge = (Model probability - Market implied probability) / Market implied probability")
    add_body(doc,
        "A market is flagged as a value opportunity only when all three conditions hold "
        "simultaneously:")
    add_bullet(doc, "Edge >= 4% (minimum threshold for signal above estimation noise)")
    add_bullet(doc, "90% confidence interval lower bound still exceeds market implied probability. CI computed by varying each team's lambda by +/- 12% and measuring the resulting range of PMF probabilities.")
    add_bullet(doc, "Market implied probability > 2% (excludes thin liquidity markets)")
    add_body(doc, "Bets passing all three filters are sized using the Kelly criterion:")
    add_formula(doc,
        "Full Kelly:   f* = Edge / (Decimal odds - 1)\n"
        "Half Kelly:   f* / 2    [default -- recommended]\n"
        "Hard cap:     5% of bankroll regardless of computed value")

    # ── Step 6: CLV ───────────────────────────────────────────────────────
    add_h2(doc, "Step 6: Closing Line Value (CLV) -- The Edge Litmus Test")
    add_body(doc,
        "Counting wins and losses is a poor way to evaluate a prediction model. The "
        "industry-standard measure that strips luck away from skill is Closing Line "
        "Value, or CLV.")
    add_body(doc,
        "The closing line is the bookmaker's final odds immediately before kickoff -- "
        "specifically the no-vig probability after removing the bookmaker margin. This "
        "represents the market's best collective estimate of the true probability, having "
        "absorbed every piece of publicly available information.")
    add_body(doc,
        "A model that consistently beats the closing line across a large sample is not "
        "getting lucky. It is providing information the market was slow to price in. "
        "Consistently losing to the closing line means the market was consistently smarter "
        "than the model, and the positive edges were illusions.")
    add_body(doc,
        "For every scheduled match the model tracks 15 markets: the three 1X2 outcomes, "
        "BTTS Yes and No, Over/Under at 0.5, 1.5, 2.5, 3.5, 4.5, 5.5, and 6.5 goals. "
        "Closing odds are captured automatically at T-3 minutes before each kickoff via "
        "a dedicated pre-match pipeline.")

    # ── Pipeline ──────────────────────────────────────────────────────────
    add_h2(doc, "The Automated Pipeline: A Living System")
    add_body(doc,
        "Every stage described above runs automatically, without human intervention, "
        "around the clock:")
    add_bullet(doc, "8:00 AM UTC -- Daily retraining", bold_prefix=None)
    add_body(doc,
        "Full data fetch from BallDontLie API: match results, bookmaker odds from up to "
        "6 vendors, team statistics, expected goals, shot data, match events, and group "
        "standings. All six parametric models retrained. Composite prior rebuilt. "
        "Predictions regenerated for every upcoming fixture. Calibration metrics logged. "
        "Updated JSONs deployed to the WizardOfOdds server.", space_after=Pt(4))
    add_bullet(doc, "Hourly -- Odds refresh and CLV tracking", bold_prefix=None)
    add_body(doc,
        "Lighter refresh capturing odds movements, updating CLV records, and re-running "
        "predictions if newly completed matches have appeared since the daily run.", space_after=Pt(4))
    add_bullet(doc, "Every 2 minutes during match hours (9 AM - 3 AM ET) -- Live snapshots", bold_prefix=None)
    add_body(doc,
        "During match hours a live snapshot pipeline runs every 2 minutes. When a match "
        "is detected in progress, the pipeline self-chains -- each completed run immediately "
        "triggers the next -- ensuring near-continuous updates.", space_after=Pt(4))
    add_bullet(doc, "T-3 minutes before kickoff -- Closing odds capture", bold_prefix=None)
    add_body(doc,
        "A dedicated watcher checks the schedule every 15 minutes. When a match is within "
        "15 minutes, it sleeps until exactly 3 minutes before kickoff, fetches final market "
        "odds across all 15 tracked markets, applies SHIN normalization, records closing "
        "probabilities, and commits updated CLV records.")

    # ── Limitations ────────────────────────────────────────────────────────
    add_h2(doc, "Honest Limitations")
    add_bullet(doc,
        "Regulation time only. All probabilities cover 90 minutes plus stoppage time. "
        "Extra time and penalty shootouts are not modeled.")
    add_bullet(doc,
        "lambda_3 = 0.170 is an average across match types. A match in stoppage time "
        "with a team pressing for an equalizer has dramatically different dynamics than "
        "a settled 3-0. The pre-game model uses a global calibrated value; the live model "
        "accounts for this via score-state multipliers.")
    add_bullet(doc,
        "11 completed WC2026 matches is still a small sample. lambda_3, the calibration "
        "temperature T, and the dynamic WC_AVG scaling factor will all stabilize as the "
        "tournament progresses.")
    add_bullet(doc,
        "Lambda uncertainty is fixed at +/- 12% for all teams. Per-team confidence "
        "intervals would require a fully Bayesian treatment.")
    add_bullet(doc,
        "Odds move between prediction time and kickoff. Edge estimates are calculated at "
        "the time the pipeline runs. Always verify current odds at your book before acting.")
    add_bullet(doc,
        "Positive expected value does not guarantee positive returns in any finite sample. "
        "Even a well-calibrated model with genuine edge will experience losing streaks.")

    add_spacer(doc, 12)
    add_disclaimer(doc)
    return doc


# =============================================================================
# ARTICLE 2 -- Page Guide
# =============================================================================

def build_article2():
    doc = new_doc()
    TITLE = "A Guide to the WC 2026 Prediction Pages"

    add_site_header(doc, TITLE)
    add_spacer(doc, 6)
    add_h1(doc, TITLE)
    add_subtitle(doc, "What every number, chart, and indicator means -- WizardOfOdds.com -- June 2026")

    add_body(doc,
        "There are three pages in the WC 2026 prediction section. Each draws from the same "
        "underlying joint score PMF engine. The PMF is a two-dimensional grid where each "
        "cell (h, a) holds P(Home = h, Away = a) -- the probability that the home team "
        "scores exactly h goals and the away team scores exactly a goals in regulation time. "
        "Every market on every page flows from this single grid. The numbers cannot "
        "contradict each other by construction.")

    # ── Page 1 ────────────────────────────────────────────────────────────────
    add_h2(doc, "Page 1 -- Pre-Game Predictions")
    add_body(doc,
        "URL: sportsodds.wizardofodds.com/tools/odds-scanner/predictions/world%20cup/pre%20match.html",
        space_after=Pt(8))
    add_body(doc,
        "This is the command center. Every World Cup match scheduled for today appears in "
        "the main table with the model's probability estimates, expected goals, and edge "
        "analysis against live bookmaker prices. The data refreshes automatically. A red "
        "banner appears if the underlying prediction file is more than four hours old.")

    add_h3(doc, "The KPI Cards")
    add_bullet(doc, "The number of regulation kickoffs scheduled for today's date in Eastern Time.", bold_prefix="Matches Today")
    add_bullet(doc, "Individual betting markets across all today's matches passing all three edge filters simultaneously: raw edge >= 4%, 90% CI lower bound above market no-vig price, and market implied > 2%. This is a strict filter -- the count is frequently zero or very small. That is correct behavior. A well-calibrated model should not find edge everywhere in a sharp market.", bold_prefix="Value Bets")
    add_bullet(doc, "The single largest edge percentage found across all today's markets, with the specific market and match identified. An edge of +12% means the model estimates that outcome is 12% more likely than the bookmaker's no-vig price implies. It does not mean the bet will win -- it means the price is favorable at the time of prediction.", bold_prefix="Best Edge")
    add_bullet(doc, "The average total expected goals across today's fixtures -- the model's best estimate of how many goals each match will produce under current conditions.", bold_prefix="Avg xG / Match")

    add_h3(doc, "The Bankroll Sizing Tool")
    add_body(doc,
        "Enter a bankroll amount and select a Kelly fraction. For every market passing all "
        "three edge filters, the tool computes a recommended dollar stake.")
    add_bullet(doc, "Theoretically optimal under the Kelly criterion. Produces large drawdowns when edge estimates contain error. Not recommended unless confidence in the edge estimate is very high.", bold_prefix="Full Kelly")
    add_bullet(doc, "Bet size divided by two. Substantially reduces variance while retaining most of the theoretical compounding advantage. The default and standard recommendation.", bold_prefix="Half Kelly")
    add_bullet(doc, "Conservative setting. Appropriate when acknowledging significant uncertainty in the model's probability estimates.", bold_prefix="Quarter Kelly")
    add_body(doc, "All three fractions are hard-capped at 5% of entered bankroll regardless of what the formula computes.")

    add_h3(doc, "The Match Table")
    add_bullet(doc, "Home vs away. All matches treated as neutral venue except USA, Canada, and Mexico which carry a small host-advantage adjustment (+0.10 attack, -0.10 defense).", bold_prefix="Match")
    add_bullet(doc, "Three-segment bar showing Home Win (gold), Draw (gray), Away Win (blue) probabilities for regulation time. Derived by summing the appropriate cells of the joint PMF grid.", bold_prefix="1X2 Probability Bars")
    add_bullet(doc, "Probability that total regulation goals exceed 2.5 -- i.e., three or more goals are scored. Sum of all PMF cells where home_goals + away_goals >= 3.", bold_prefix="O/U 2.5")
    add_bullet(doc, "Both Teams to Score. Sum of all cells where home_goals >= 1 AND away_goals >= 1.", bold_prefix="BTTS")
    add_bullet(doc, "The single most probable final scoreline and its probability -- the peak cell of the joint grid.", bold_prefix="Top Score")
    add_bullet(doc, "The model's expected goals for home and away separately after market reconciliation -- the Poisson mean parameters lambda_home and lambda_away.", bold_prefix="xG (H-A)")
    add_bullet(doc, "Highest-edge market for this match passing all three value filters. If no market passes, this cell is blank.", bold_prefix="Best Edge / Fair Odds")

    add_h3(doc, "The Expanded Row")
    add_body(doc, "Click any match row to reveal three additional panels:")
    add_bullet(doc, "All non-trivial scorelines ranked from most to least likely, with proportion bars. These are raw joint grid values read directly from the PMF.", bold_prefix="Full Scoreline Distribution")
    add_bullet(doc, "Every market the engine has priced from the joint grid: 1X2, BTTS, Over/Under at every standard line from 0.5 through 6.5, Draw No Bet, Double Chance, Win to Nil, Asian Handicap, and team-level totals. All from the same single distribution.", bold_prefix="All Markets")
    add_bullet(doc, "For each market: model probability, market no-vig implied probability, edge %, fair odds, and current market odds. Rows highlighted in gold have passed all three value filters.", bold_prefix="Edge Report")

    # ── Page 2 ────────────────────────────────────────────────────────────────
    add_h2(doc, "Page 2 -- Probability Distributions")
    add_body(doc,
        "URL: sportsodds.wizardofodds.com/tools/odds-scanner/predictions/world-cup/pre-match/Probability%20Distributions.html",
        space_after=Pt(8))
    add_body(doc,
        "Where Page 1 compresses the model output into a single row per match, this page "
        "opens it up completely. Select a match using the navigation chips at the top and "
        "every chart updates immediately to show the full probability landscape.")

    add_h3(doc, "Chart 1 -- Joint Score PMF Heatmap")
    add_body(doc,
        "The heatmap is the model in its purest form. Every cell (h, a) shows the "
        "probability that the home team scores exactly h goals and the away team scores "
        "exactly a goals. Home goals increase along the vertical axis, away goals along "
        "the horizontal. The color scale uses the square root of each cell's probability "
        "relative to the grid maximum -- without this transformation, cells above 8% would "
        "dominate and everything else would appear uniformly dark. Every betting market is "
        "readable directly from this heatmap.")

    add_h3(doc, "Chart 2 -- Marginal Goal Distributions")
    add_body(doc,
        "Two bar charts showing the probability each team scores exactly k goals. The "
        "marginal for the home team is obtained by summing across all away goal counts:")
    add_formula(doc, "P(Home = h) = SUM over all a of  P(Home = h, Away = a)")
    add_body(doc,
        "A team with a very tall bar at k=0 is frequently expected to be shut out. The "
        "tallest bar for most group-stage matches sits at k=1 for both teams.")

    add_h3(doc, "Chart 3 -- Total Goals Distribution")
    add_body(doc,
        "Shows P(total goals = k) for k = 0, 1, 2, ... Computed by summing all joint PMF "
        "cells along each anti-diagonal where h + a = k. Standard over/under lines (0.5, "
        "1.5, 2.5, 3.5, 4.5, 5.5) appear as vertical dividers. The probability to the "
        "right of any divider is the Over probability for that line.")

    add_h3(doc, "Chart 4 -- Goal Difference Distribution")
    add_body(doc,
        "Centered on zero. Gold bars are home wins (positive difference), gray is draw, "
        "blue is away wins. The height of the gray bar relative to gold and blue tells you "
        "how likely a draw is given the specific attacking and defensive qualities of these "
        "two teams.")

    add_h3(doc, "Chart 5 -- Top 20 Most Likely Scorelines")
    add_body(doc,
        "A ranked bar chart of the 20 highest-probability individual final scores with "
        "exact percentages and fair American odds. The top cell in most group-stage matches "
        "carries between 12% and 20% probability. If your sportsbook offers better odds "
        "than the fair odds shown, you may have found a value opportunity.")

    add_h3(doc, "O/U Lines Table")
    add_body(doc,
        "Over and Under probabilities for every standard total line from 0.5 through 6.5, "
        "all in one place. Every number is computed by summing the appropriate region of "
        "the joint PMF -- no approximations.")

    # ── Page 3 ────────────────────────────────────────────────────────────────
    add_h2(doc, "Page 3 -- Live In-Play PMF")
    add_body(doc,
        "URL: sportsodds.wizardofodds.com/tools/odds-scanner/predictions/world-cup/live/Probability%20Distributions.html",
        space_after=Pt(8))
    add_body(doc,
        "This page activates when a World Cup match is in progress. When no match is live, "
        "it shows the next scheduled kickoff time. All probabilities are regulation time only.")

    add_h3(doc, "How the Live Model Differs From Pre-Game")
    add_body(doc,
        "The pre-game model asks: what will the final score be from kickoff? The live model "
        "asks: given that the current score is H-A at minute t, what will the final score "
        "be at 90+ minutes? This is conditional probability. Any score lower than the "
        "current score is impossible -- those cells of the PMF grid are locked at zero. "
        "The remaining probability redistributes entirely across reachable scores.")
    add_body(doc,
        "The live model uses a non-homogeneous hazard model -- goal-scoring rate varies "
        "by match minute, calibrated from 2018 and 2022 World Cup data. Rates are below "
        "average in the opening minutes, rise through the mid-half, spike just after "
        "half-time, and peak in the final ten minutes. On top of this temporal baseline, "
        "score-state multipliers adjust each team's rate based on the current scoreline:")

    # Score-state multipliers table
    tbl4 = doc.add_table(rows=6, cols=2)
    tbl4.style = 'Table Grid'
    for cell in tbl4.columns[0].cells: cell.width = Inches(2.5)
    for cell in tbl4.columns[1].cells: cell.width = Inches(3.75)
    dark_table_header(tbl4, ["Score State", "Effect on Goal Rates"])
    mult_data = [
        ("Draw at minute 60+",         "Both teams x1.10 -- games open up in the final 30 minutes"),
        ("Home team losing by 1",       "Home x1.25, Away x1.05 -- counter-attack risk increases"),
        ("Home team losing by 2+",      "Home x1.40, Away x1.10"),
        ("Home team winning by 1",      "Home x0.90, Away x1.10 -- away team pushes forward"),
        ("Home team winning by 2+",     "Home x0.80, Away x1.15"),
    ]
    for i, (state, effect) in enumerate(mult_data, 1):
        row = tbl4.rows[i]
        row.cells[0].text = state
        row.cells[1].text = effect
        style_data_row(tbl4, i, alt=(i % 2 == 0))
    add_spacer(doc, 6)
    add_body(doc,
        "When live expected goals (xG) data is available from BallDontLie, the model blends "
        "the live xG rate (60% weight) with the pre-game prior (40% weight) starting from "
        "minute 15. Before minute 15, live xG is too noisy to be useful.")

    add_h3(doc, "Connection Badge")
    add_bullet(doc, "Active push connection. When a goal or status change is reported, the server recomputes the full conditional PMF and pushes it to connected browsers. Target latency: under 200 milliseconds.", bold_prefix="WebSocket (green)")
    add_bullet(doc, "Push connection unavailable. The page fetches updated data from a static JSON file every 60 seconds. Updates arrive with up to a one-minute delay. Automatic fallback -- no user action needed.", bold_prefix="Polling (yellow)")

    add_h3(doc, "Live KPI Cards")
    add_bullet(doc, "Number of World Cup matches currently in progress.", bold_prefix="Matches Live")
    add_bullet(doc, "Next scheduled match with Eastern Time kickoff.", bold_prefix="Next Kickoff")
    add_bullet(doc, "Total goals scored across all live and recently completed matches.", bold_prefix="Goals Today")
    add_bullet(doc, "Time since the last live snapshot. Under 2 minutes is normal. Above 10 minutes during a live match triggers a health warning banner.", bold_prefix="Data Age")

    add_h3(doc, "Win Probability Bar and Shift Table")
    add_body(doc,
        "The same three-segment bar as on Page 1 -- Home Win (gold), Draw (gray), Away Win "
        "(blue) -- but now conditional on the current score and minute. These are not the "
        "probabilities from kickoff. Directly below the bar, the Pre-Game to Live Shift "
        "table shows, for each main market, the pre-game probability, the current live "
        "probability, and the arithmetic difference. A large shift tells you how significantly "
        "the match state has altered the distribution.")

    add_h3(doc, "Win Probability Sparkline")
    add_body(doc,
        "A compact line chart showing the home team's win probability from kickoff to the "
        "current minute. Sharp upward jumps are home goals; sharp downward drops are away "
        "goals. This history accumulates within your browser session and resets on page reload.")

    add_h3(doc, "Live Joint Score PMF Heatmap")
    add_body(doc,
        "The same heatmap as on Page 2, updated with every live snapshot. The cell "
        "corresponding to the current live score is outlined in red. All unreachable cells "
        "are forced to zero and appear dark. As the match progresses, the dark region grows "
        "and probability concentrates into fewer and fewer bright cells. In stoppage time "
        "of a 1-0 match, the heatmap may assign 85-90% probability to the single 1-0 cell.")

    add_h3(doc, "Next Goal Probabilities")
    add_body(doc, "Three numbers derived from remaining expected goals lambda_h_rem and lambda_a_rem:")
    add_formula(doc,
        "Home scores next: lambda_h_rem / (lambda_h_rem + lambda_a_rem)\n"
        "Away scores next: lambda_a_rem / (lambda_h_rem + lambda_a_rem)\n"
        "No more goals:   e^(-lambda_h_rem) * e^(-lambda_a_rem)")
    add_body(doc,
        "As the match enters stoppage time with small remaining expected goals, the "
        "'No more goals' value typically climbs above 80-90%.")

    add_h3(doc, "Top 10 Most Likely Final Scores (Live)")
    add_body(doc,
        "Same ranked list as Page 2, restricted to reachable outcomes only. The current "
        "live score is marked. As the match approaches the final whistle, the probability "
        "on the leading score climbs rapidly -- in an 88th-minute 1-0 match, the 1-0 cell "
        "may carry 8 or 9 times the probability it held before kickoff.")

    # ── Limitations ────────────────────────────────────────────────────────
    add_h2(doc, "Scope and Limitations -- All Pages")
    add_bullet(doc, "All probabilities represent regulation time (90 minutes plus stoppage time) only. Extra time and penalty shootouts are not modeled.")
    add_bullet(doc, "The Bivariate Poisson substantially reduces the independence assumption (lambda_3 = 0.170 captures positive correlation), but it remains an approximation. Score-state multipliers in the live model provide additional correction.")
    add_bullet(doc, "Calibration rests on 128 World Cup matches from 2018 and 2022, growing as 2026 results accumulate. Metrics carry meaningful statistical uncertainty at this sample size.")
    add_bullet(doc, "Edge estimates are outputs of a probabilistic model. Market odds move between prediction time and kickoff. Always verify current prices at your book before acting.")
    add_bullet(doc, "WebSocket update speed is subject to network latency and server load. The stated target of under 200 milliseconds applies under normal conditions.")

    add_spacer(doc, 12)
    add_disclaimer(doc)
    return doc


# =============================================================================
# RENDER
# =============================================================================

if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating Word documents...")

    doc1 = build_article1()
    p1 = OUT_DIR / "wc2026-how-the-model-works.docx"
    doc1.save(str(p1))
    print(f"  {p1.name}  ({p1.stat().st_size // 1024} KB)")

    doc2 = build_article2()
    p2 = OUT_DIR / "wc2026-page-guide.docx"
    doc2.save(str(p2))
    print(f"  {p2.name}  ({p2.stat().st_size // 1024} KB)")

    print("Done.")
