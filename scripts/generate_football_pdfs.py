"""
Elite Sagarin Model — 2026 College Football PDF Generator v4
============================================================
PDFs produced:
  01  FBS + FCS Combined Rankings  (all teams together, Division column)
  02  FCS vs FCS Matchups
  03  FCS vs FBS Matchups
  04  FBS vs FBS Matchups

Updated: July 2, 2026
Key v4 changes:
  - All 50+ FBS vs FBS Vegas lines updated (July 2026 board)
  - Texas Tech flagged as major change (QB Sorsby gambling scandal; Hammond ACL)
  - LSU Leavitt cleared — composite bump applied
  - 6 new games added (Troy/SHU, ARK St/MEM, UNLV@HAW, WKU@NEV, CMU@NM, WAS/WAST)
  - Fixed edge direction: lean labels corrected (Home/Fav vs Away/Dog)
  - New ★★★ best bets: JMU -6, Ohio +23.5, WMU +26.5, Troy -16.5
  - Ole Miss line updated -6.5 → -7.5; ND line -20 → -20.5

Composite Rating (2026) = 70% SP+_scaled + 30% Sagarin  (FBS standard)
                        = 80% SP+_scaled + 20% Sagarin  (major change teams)
                        = Sagarin 2025 adjusted          (FCS teams)
SP+_scaled = 71.0 + 0.90 × sp_plus
Home advantage = 2.80 pts  (validated against opened lines)
"""

import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../reports/football-2026")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Colours ───────────────────────────────────────────────────────────────────
NAVY     = colors.HexColor("#0D1B2A")
GOLD     = colors.HexColor("#C9A84C")
L_GRAY   = colors.HexColor("#F4F5F6")
MID_GRAY = colors.HexColor("#D0D3D8")
DKGRAY   = colors.HexColor("#444B54")
GREEN    = colors.HexColor("#1A6B3C")
RED      = colors.HexColor("#8B1A1A")
AMBER    = colors.HexColor("#E65C00")
BLUE     = colors.HexColor("#1B4F99")
WHITE    = colors.white
GOLD_BG  = colors.HexColor("#FFF8E7")
GREEN_BG = colors.HexColor("#E8F5E9")
RED_BG   = colors.HexColor("#FFEBEE")
BLUE_BG  = colors.HexColor("#E3F2FD")
FBS_COL  = colors.HexColor("#EEF2FF")   # subtle blue tint for FBS rows
FCS_COL  = colors.HexColor("#F0FFF4")   # subtle green tint for FCS rows

HOME_ADV = 2.80

# ── Maths ─────────────────────────────────────────────────────────────────────
def sp_to_sag(sp): return 71.0 + 0.90 * sp

def comp_fbs(sp, sag, mc=False):
    w = 0.80 if mc else 0.70
    return w * sp_to_sag(sp) + (1 - w) * sag

def model_spread(home_c, away_c, neutral=False):
    return (home_c - away_c) + (0 if neutral else HOME_ADV)

def fmt_spread(ms, home, away):
    if abs(ms) < 0.5: return "PICK"
    fav, pts = (home, ms) if ms > 0 else (away, -ms)
    return f"{fav} -{pts:.1f}"

# ── Style helpers ─────────────────────────────────────────────────────────────
def ps(name, **kw):
    d = dict(fontName='Helvetica', fontSize=8, textColor=DKGRAY, leading=10, spaceAfter=0)
    d.update(kw)
    return ParagraphStyle(name, **d)

P_TITLE = ps('t', fontName='Helvetica-Bold', fontSize=20, textColor=WHITE, alignment=TA_CENTER, leading=26)
P_SUB   = ps('s', fontSize=9, textColor=GOLD, alignment=TA_CENTER, leading=12)
P_DISC  = ps('d', fontName='Helvetica-Oblique', fontSize=6.5, textColor=MID_GRAY, alignment=TA_CENTER, leading=8)
P_SECT  = ps('sc', fontName='Helvetica-Bold', fontSize=11, textColor=NAVY, spaceBefore=8, spaceAfter=3)
P_NOTE  = ps('n', fontName='Helvetica-Oblique', fontSize=7, textColor=DKGRAY, spaceAfter=3)

def c(txt, bold=False, align=TA_CENTER, col=DKGRAY, sz=7.5):
    fn = 'Helvetica-Bold' if bold else 'Helvetica'
    return Paragraph(str(txt), ps(f'x{id(txt)}', fontName=fn, fontSize=sz,
                                   textColor=col, alignment=align))
def ch(*labels):
    return [Paragraph(f"<b>{l}</b>",
            ps('h', fontName='Helvetica-Bold', fontSize=7.5, textColor=WHITE,
               alignment=TA_CENTER)) for l in labels]

def banner(title, subtitle, note=None):
    tbl = Table([[Paragraph(title, P_TITLE)],[Paragraph(subtitle, P_SUB)]], colWidths=['100%'])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),NAVY),
        ('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9),
        ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),
    ]))
    items = [tbl, Spacer(1,5)]
    if note: items.append(Paragraph(note, P_DISC))
    items.append(HRFlowable(width='100%', thickness=2, color=GOLD, spaceAfter=7))
    return items

def make_table(rows, cw, green=(), red=(), amber=(), gold=(), blue=()):
    n = len(rows)
    cmds = [
        ('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),WHITE),
        ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3),
        ('GRID',(0,0),(-1,-1),0.25,MID_GRAY),
    ]
    for r in range(1, n):
        cmds.append(('BACKGROUND',(0,r),(-1,r), L_GRAY if r%2==1 else WHITE))
    for r in green:  cmds.append(('BACKGROUND',(0,r),(-1,r),GREEN_BG))
    for r in red:    cmds.append(('BACKGROUND',(0,r),(-1,r),RED_BG))
    for r in amber:  cmds.append(('BACKGROUND',(0,r),(-1,r),colors.HexColor('#FFF3E0')))
    for r in gold:   cmds.append(('BACKGROUND',(0,r),(-1,r),GOLD_BG))
    for r in blue:   cmds.append(('BACKGROUND',(0,r),(-1,r),BLUE_BG))
    t = Table(rows, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle(cmds))
    return t

# ════════════════════════════════════════════════════════════════════════════
#  MASTER TEAM DATABASE
# ════════════════════════════════════════════════════════════════════════════
# FBS: (conf, sp_plus, sagarin_2025, major_change, record_2025)
FBS = {
    # ── Big Ten ───────────────────────────────────────────────────────────
    "Ohio State":       ("Big Ten",  31.8, 95.16, False, "12-2"),
    "Oregon":           ("Big Ten",  28.3, 94.27, False, "13-2"),
    "Notre Dame":       ("I-A Ind.", 25.8, 94.60, False, "10-2"),
    "Indiana":          ("Big Ten",  24.5,100.06, False, "16-0"),
    "Michigan":         ("Big Ten",  16.1, 80.89, False, "9-4"),
    "Penn State":       ("Big Ten",  15.7, 86.46, False, "7-6"),
    "USC":              ("Big Ten",  16.8, 83.43, False, "9-4"),
    "Washington":       ("Big Ten",  14.5, 85.20, False, "9-4"),
    "Iowa":             ("Big Ten",  13.6, 86.07, False, "9-4"),
    "Illinois":         ("Big Ten",   9.3, 79.28, False, "9-4"),
    "Minnesota":        ("Big Ten",   5.2, 73.35, False, "8-5"),
    "Northwestern":     ("Big Ten",   4.6, 72.98, False, "7-6"),
    "Rutgers":          ("Big Ten",   1.8, 71.80, False, "5-7"),
    "Wisconsin":        ("Big Ten",   1.8, 73.99, False, "4-8"),
    "Maryland":         ("Big Ten",   3.8, 66.22, False, "4-8"),
    "Michigan State":   ("Big Ten",   0.4, 71.31, False, "4-8"),
    "Nebraska":         ("Big Ten",   7.7, 73.22, False, "7-6"),
    "Purdue":           ("Big Ten",  -2.9, 63.58, False, "2-10"),
    "UCLA":             ("Big Ten",   5.1, 67.71, True,  "3-9"),
    # ── SEC ───────────────────────────────────────────────────────────────
    "Texas":            ("SEC",      23.7, 86.35, False, "10-3"),
    "Texas A&M":        ("SEC",      20.3, 85.87, False, "11-2"),
    "LSU":              ("SEC",      20.2, 79.14, True,  "7-6"),
    "Alabama":          ("SEC",      18.2, 85.61, False, "11-4"),
    "Oklahoma":         ("SEC",      17.2, 83.67, False, "10-3"),
    "Tennessee":        ("SEC",      16.0, 80.32, False, "8-5"),
    "Ole Miss":         ("SEC",      15.9, 88.84, False, "13-2"),
    "Missouri":         ("SEC",      14.8, 80.49, False, "8-5"),
    "Georgia":          ("SEC",      25.5, 89.07, False, "12-2"),
    "Texas Tech":       ("Big 12",   23.1, 90.88, True,  "12-2"),  # QB CRISIS: Sorsby gone (gambling), Hammond ACL
    "Florida":          ("SEC",      14.9, 76.94, True,  "4-8"),
    "South Carolina":   ("SEC",      12.1, 77.59, False, "4-8"),
    "Vanderbilt":       ("SEC",      10.0, 85.49, False, "10-3"),
    "Auburn":           ("SEC",      11.2, 79.03, False, "5-7"),
    "Mississippi State":("SEC",       3.9, 69.95, False, "5-8"),
    "Arkansas":         ("SEC",       5.0, 72.40, False, "2-10"),
    "Kentucky":         ("SEC",       3.8, 72.64, False, "5-7"),
    # ── Big 12 ────────────────────────────────────────────────────────────
    "Miami":            ("ACC",      21.0, 93.02, False, "13-3"),
    "Texas Tech":       ("Big 12",   23.1, 90.88, False, "12-2"),
    "BYU":              ("Big 12",   15.5, 81.85, False, "12-2"),
    "Oklahoma State":   ("Big 12",    7.1, 58.25, True,  "1-11"),
    "Arizona":          ("Big 12",   10.2, 78.60, False, "9-4"),
    "Arizona State":    ("Big 12",    6.4, 75.33, False, "8-5"),
    "Houston":          ("Big 12",    8.2, 74.43, False, "10-3"),
    "Kansas State":     ("Big 12",   10.4, 76.06, False, "6-6"),
    "Iowa State":       ("Big 12",    1.0, 76.11, False, "8-4"),
    "TCU":              ("Big 12",    9.1, 77.31, False, "9-4"),
    "Kansas":           ("Big 12",    3.7, 70.84, False, "5-7"),
    "Baylor":           ("Big 12",    4.5, 69.76, False, "5-7"),
    "West Virginia":    ("Big 12",    0.8, 65.82, False, "4-8"),
    "Colorado":         ("Big 12",    0.9, 64.90, True,  "3-9"),
    "UCF":              ("Big 12",    2.3, 66.51, False, "5-7"),
    "UNLV":             ("Mtn West",  2.8, 68.30, False, "10-4"),
    "Cincinnati":       ("Big 12",    4.5, 70.10, False, "7-6"),
    # ── ACC ───────────────────────────────────────────────────────────────
    "Clemson":          ("ACC",      12.8, 79.32, False, "7-6"),
    "SMU":              ("ACC",      10.9, 83.00, False, "9-4"),
    "Louisville":       ("ACC",      11.0, 79.95, False, "9-4"),
    "Virginia Tech":    ("ACC",       9.4, 68.05, True,  "3-9"),
    "Virginia":         ("ACC",       6.6, 78.95, False, "11-3"),
    "Florida State":    ("ACC",       8.8, 75.80, False, "5-7"),
    "Pittsburgh":       ("ACC",       6.5, 77.68, False, "8-5"),
    "NC State":         ("ACC",       4.9, 78.11, False, "8-5"),
    "Georgia Tech":     ("ACC",       6.0, 76.82, False, "9-4"),
    "Duke":             ("ACC",       5.7, 76.71, False, "9-5"),
    "Wake Forest":      ("ACC",       3.6, 73.91, False, "9-4"),
    "North Carolina":   ("ACC",       3.8, 65.57, True,  "4-8"),
    "Stanford":         ("ACC",       -1.9,67.74, True,  "4-8"),
    "California":       ("ACC",       3.7, 67.89, False, "7-6"),
    "Boston College":   ("ACC",      -1.5, 65.92, False, "2-10"),
    "Syracuse":         ("ACC",      -0.7, 61.15, False, "3-9"),
    # ── Mountain West ─────────────────────────────────────────────────────
    "Boise State":      ("Mtn West",  6.8, 72.26, False, "9-5"),
    "Fresno State":     ("Mtn West", -2.3, 66.85, False, "9-4"),
    "San Diego State":  ("Mtn West", -1.3, 69.42, False, "9-4"),
    "Hawaii":           ("Mtn West", -3.9, 66.48, False, "9-4"),
    "Utah State":       ("Mtn West", -7.7, 65.39, False, "6-7"),
    "Nevada":           ("Mtn West",-12.2, 55.19, False, "3-9"),
    "Wyoming":          ("Mtn West", -9.6, 56.93, False, "4-8"),
    "Colorado State":   ("Mtn West", -8.3, 53.59, False, "2-10"),
    "Air Force":        ("Mtn West", -2.4, 60.90, False, "4-8"),
    "New Mexico":       ("Mtn West", -0.5, 66.81, False, "9-4"),
    "SJSU":             ("Mtn West",-15.5, 54.34, False, "3-9"),
    # ── AAC / American ────────────────────────────────────────────────────
    "East Carolina":    ("AAC",      -2.0, 73.52, False, "9-4"),
    "Tulane":           ("AAC",      -5.5, 73.98, True,  "11-3"),
    "North Texas":      ("AAC",     -11.8, 75.44, True,  "12-2"),
    "Toledo":           ("AAC",     -11.5, 73.01, True,  "8-5"),
    "Memphis":          ("AAC",      -1.1, 68.97, False, "8-5"),
    "Navy":             ("AAC",       1.1, 72.43, False, "11-2"),
    "Army":             ("AAC",      -3.0, 68.76, False, "7-6"),
    "Tulsa":            ("AAC",      -7.6, 55.23, False, "4-8"),
    "South Florida":    ("AAC",      -2.8, 77.58, True,  "9-4"),
    "UTSA":             ("AAC",      -1.5, 71.18, False, "7-6"),
    "Temple":           ("AAC",      -8.7, 59.18, False, "5-7"),
    "Rice":             ("AAC",     -14.7, 50.52, False, "5-8"),
    "Charlotte":        ("AAC",     -32.4, 48.44, False, "1-11"),
    # ── Sun Belt ──────────────────────────────────────────────────────────
    "James Madison":    ("Sun Belt", -2.1, 80.06, True,  "12-2"),
    "Old Dominion":     ("Sun Belt", -5.8, 74.31, True,  "10-3"),
    "Georgia Southern": ("Sun Belt", -8.9, 60.94, False, "7-6"),
    "App State":        ("Sun Belt",-12.1, 54.61, False, "5-8"),
    "Coastal Carolina": ("Sun Belt",-13.8, 56.06, False, "6-7"),
    "Georgia State":    ("Sun Belt",-25.1, 50.22, False, "1-11"),
    "South Alabama":    ("Sun Belt",-13.3, 57.56, False, "4-8"),
    "Louisiana":        ("Sun Belt", -9.1, 58.62, False, "6-7"),
    "Arkansas State":   ("Sun Belt", -8.5, 59.88, False, "7-6"),
    "Texas State":      ("Sun Belt", -5.9, 67.79, False, "7-6"),
    "Troy":             ("Sun Belt", -6.0, 61.83, False, "8-6"),
    # ── CUSA ──────────────────────────────────────────────────────────────
    "Liberty":          ("C-USA",    -6.4, 57.99, False, "4-8"),
    "Kennesaw State":   ("C-USA",    -9.3, 59.85, False, "10-4"),
    "Delaware":         ("C-USA",   -13.0, 56.45, False, "7-6"),
    "Jacksonville State":("C-USA",  -7.7, 60.00, False, "9-5"),
    "Sam Houston":      ("C-USA",   -26.3, 43.48, False, "2-10"),
    "Louisiana Tech":   ("C-USA",    -8.3, 62.17, False, "8-5"),
    "Missouri State":   ("C-USA",   -18.7, 57.08, False, "7-6"),
    "New Mexico State": ("C-USA",   -16.4, 50.89, False, "4-8"),
    "Western Kentucky": ("C-USA",    -5.3, 63.73, False, "9-4"),
    "FIU":              ("C-USA",   -13.7, 58.40, False, "7-6"),
    "Middle Tennessee": ("C-USA",   -26.0, 50.90, False, "3-9"),
    "UTEP":             ("C-USA",   -20.5, 49.16, False, "2-10"),
    # ── MAC ───────────────────────────────────────────────────────────────
    "Ohio":             ("MAC",     -13.6, 66.00, False, "9-4"),
    "Western Michigan": ("MAC",      -7.2, 68.87, False, "10-4"),
    "Miami (OH)":       ("MAC",      -2.9, 62.83, False, "7-7"),
    "Northern Illinois":("MAC",     -18.2, 52.76, False, "3-9"),
    "Ball State":       ("MAC",     -25.2, 49.87, False, "4-8"),
    "Akron":            ("MAC",     -19.5, 52.40, False, "5-7"),
    "Buffalo":          ("MAC",     -11.9, 54.60, False, "5-7"),
    "Bowling Green":    ("MAC",     -13.3, 54.34, False, "4-8"),
    "Kent State":       ("MAC",     -20.1, 50.31, False, "5-7"),
    "Eastern Michigan": ("MAC",     -15.0, 55.45, False, "4-8"),
    "Central Michigan": ("MAC",     -12.4, 59.10, False, "7-6"),
    "UMass":            ("MAC",     -30.9, 35.60, False, "1-11"),
    # ── FBS Independents + new FBS ────────────────────────────────────────
    "NDSU":             ("FBS-new",  -1.4, 76.17, False, "12-1"),  # moved from FCS
    "Sacramento State": ("FBS-new", -22.7, 56.88, False, "7-5"),  # moved from FCS
    "UConn":            ("I-A Ind.",-11.2, 64.96, False, "9-4"),
    "UAB":              ("AAC",     -18.1, 54.17, False, "4-8"),
    # ── Pac-12 ────────────────────────────────────────────────────────────
    "Utah":             ("Pac-12",  11.9, 86.80, False, "11-2"),
    "Washington State": ("Pac-12",  -5.3, 72.91, False, "7-6"),
    "Oregon State":     ("Pac-12",  -6.3, 57.02, False, "2-10"),
    "Fresno State":     ("Pac-12",  -2.3, 66.85, False, "9-4"),   # duplicate removed below
}

# De-duplicate (keep first occurrence)
_seen = set()
FBS_DEDUP = {}
for nm, dat in FBS.items():
    if nm not in _seen:
        _seen.add(nm)
        FBS_DEDUP[nm] = dat

def get_fbs(name):
    d = FBS_DEDUP.get(name)
    if d: return d[1], d[2], d[3]   # sp, sag, mc
    return 0.0, 70.0, False

def comp_for(name, div):
    if div == "FBS":
        sp, sag, mc = get_fbs(name)
        return comp_fbs(sp, sag, mc)
    return FCS_COMP.get(name, 40.0)

# FCS teams: (conf, sagarin_2025, comp_2026, record_2025)
FCS_RAW = {
    "Montana State":     ("Big Sky",  74.42, 75.5, "14-2"),
    "Montana":           ("Big Sky",  68.36, 69.0, "13-2"),
    "Tarleton State":    ("WAC",      66.62, 67.5, "12-2"),
    "Illinois State":    ("MVFC",     65.99, 66.0, "12-5"),
    "North Dakota":      ("MVFC",     63.67, 64.0, "8-6"),
    "South Dakota State":("MVFC",     62.08, 63.0, "9-5"),
    "Stephen F. Austin": ("Southland",61.99, 62.0, "11-3"),
    "Villanova":         ("CAA",      61.47, 62.0, "12-3"),
    "UC Davis":          ("Big Sky",  60.37, 61.0, "9-4"),
    "Southern Illinois": ("MVFC",     60.35, 61.5, "7-5"),
    "South Dakota":      ("MVFC",     60.33, 60.5, "10-5"),
    "Yale":              ("Ivy",      59.17, 59.5, "9-3"),
    "Lehigh":            ("Patriot",  59.01, 59.5, "12-1"),
    "Youngstown State":  ("MVFC",     58.81, 59.0, "8-5"),
    "Abilene Christian": ("WAC",      58.34, 58.5, "9-5"),
    "Tennessee Tech":    ("OVC",      53.60, 54.0, "11-2"),
    "Rhode Island":      ("CAA",      54.35, 55.5, "11-3"),
    "Sacramento State":  ("Big Sky",  56.88, 57.0, "7-5"),   # now FBS 2026
    "Idaho State":       ("Big Sky",  55.76, 56.0, "6-6"),
    "SE Louisiana":      ("Southland",55.85, 56.0, "9-4"),
    "Austin Peay":       ("WAC",      55.00, 55.5, "7-5"),
    "Alabama State":     ("SWAC",     52.25, 52.5, "10-2"),
    "SC State":          ("MEAC",     50.80, 51.0, "10-3"),
    "Monmouth":          ("CAA",      52.26, 53.0, "9-3"),
    "Northern Arizona":  ("Big Sky",  52.67, 53.0, "7-5"),
    "West Georgia":      ("WAC",      51.23, 53.0, "8-3"),
    "Western Carolina":  ("SoCon",    51.53, 52.0, "7-5"),
    "ETSU":              ("SoCon",    50.83, 51.5, "7-5"),
    "UTRGV":             ("Southland",51.17, 51.5, "9-3"),
    "New Hampshire":     ("CAA",      50.94, 51.0, "8-5"),
    "Prairie View A&M":  ("SWAC",     50.05, 50.5, "10-4"),
    "Eastern Kentucky":  ("WAC",      50.21, 50.5, "5-7"),
    "Jackson State":     ("SWAC",     50.16, 50.5, "9-3"),
    "ETSU":              ("SoCon",    50.83, 51.5, "7-5"),   # dup removed
    "Idaho":             ("Big Sky",  50.54, 51.0, "4-8"),
    "North Alabama":     ("ASUN",     49.00, 49.5, "6-5"),
    "Cal Poly":          ("Big Sky",  49.17, 49.5, "4-8"),
    "Fordham":           ("Patriot",  49.00, 49.5, "6-6"),
    "William & Mary":    ("CAA",      48.96, 49.0, "7-5"),
    "Eastern Washington":("Big Sky",  48.87, 49.0, "5-7"),
    "Lafayette":         ("Patriot",  48.63, 49.0, "8-4"),
    "Northern Iowa":     ("MVFC",     48.51, 49.0, "3-9"),
    "Towson":            ("CAA",      46.35, 46.5, "6-6"),
    "Maine":             ("CAA",      46.21, 46.5, "6-6"),
    "Lindenwood":        ("OVC",      46.15, 46.5, "6-6"),
    "Stony Brook":       ("CAA",      46.80, 47.0, "6-6"),
    "St. Thomas":        ("Pioneer",  46.56, 47.0, "7-5"),
    "Chattanooga":       ("SoCon",    43.95, 44.0, "5-7"),
    "Indiana State":     ("MVFC",     43.38, 44.0, "3-9"),
    "Furman":            ("SoCon",    43.14, 43.5, "6-6"),
    "SE Missouri State": ("OVC",      42.86, 43.0, "4-8"),
    "The Citadel":       ("SoCon",    43.50, 44.0, "4-8"),
    "Duquesne":          ("NEC",      43.52, 44.0, "7-5"),
    "Samford":           ("SoCon",    36.14, 36.5, "1-11"),
    "LIU":               ("NEC",      41.61, 42.0, "6-6"),
    "NC A&T":            ("CAA",      28.35, 29.0, "2-9"),
    "Merrimack":         ("NEC",      37.64, 38.0, "5-6"),
    "Bryant":            ("NEC",      38.50, 39.0, "5-6"),
    "Eastern Illinois":  ("OVC",      38.38, 38.5, "3-9"),
    "UAlbany":           ("CAA",      36.72, 37.5, "2-10"),
    "Alcorn State":      ("SWAC",     35.50, 35.5, "5-6"),
    "Bethune-Cookman":   ("SWAC",     38.79, 39.0, "6-6"),
    "Florida A&M":       ("SWAC",     40.50, 41.0, "6-5"),
    "Texas Southern":    ("SWAC",     32.00, 32.5, "4-7"),
    "Tennessee State":   ("OVC",      34.25, 34.5, "2-10"),
    "Ark.-Pine Bluff":   ("SWAC",     29.53, 30.0, "3-8"),
    "Missouri State":    ("MVFC",     47.50, 48.0, "6-6"),  # separate from FBS Missouri State
    "Norfolk State":     ("MEAC",     36.00, 36.5, "4-7"),
    "Nicholls":          ("Southland",45.34, 45.5, "4-8"),
    "SE Louisiana":      ("Southland",55.85, 56.0, "9-4"),  # dup
}

# De-duplicate FCS
FCS_COMP = {}
for nm, dat in FCS_RAW.items():
    if nm not in FCS_COMP:
        FCS_COMP[nm] = dat[2]

FCS_DATA_DEDUP = {}
for nm, dat in FCS_RAW.items():
    if nm not in FCS_DATA_DEDUP:
        FCS_DATA_DEDUP[nm] = dat


# ════════════════════════════════════════════════════════════════════════════
#  PDF 1 — COMBINED RANKINGS
# ════════════════════════════════════════════════════════════════════════════

def build_rankings_pdf():
    path = os.path.join(OUTPUT_DIR, "01_Combined_FBS_FCS_Rankings.pdf")
    doc = SimpleDocTemplate(path, pagesize=letter,
                            leftMargin=0.45*inch, rightMargin=0.45*inch,
                            topMargin=0.38*inch, bottomMargin=0.38*inch)
    story = []
    story += banner(
        "ELITE SAGARIN MODEL",
        "FBS + FCS Combined Power Rankings — 2026 Preseason",
        "FBS Composite = 70% SP+ scaled + 30% Sagarin 2025.  "
        "FCS Composite = Sagarin 2025 with preseason poll adjustments.  "
        "Green = FCS team.  Gold = FBS top 25.  Teams ranked best-to-worst by Composite 2026.",
    )
    story.append(Paragraph("All Teams — FBS + FCS Combined (Best to Worst by 2026 Composite)", P_SECT))

    # Build combined list
    all_teams = []
    for nm, (conf, sp, sag, mc, rec) in FBS_DEDUP.items():
        comp = comp_fbs(sp, sag, mc)
        all_teams.append((nm, "FBS", conf, sp, sag, comp, rec))
    for nm, (conf, sag25, comp26, rec) in FCS_DATA_DEDUP.items():
        # Skip teams that moved to FBS
        if nm in ("Sacramento State", "NDSU"): continue
        sp_show = "N/A"
        all_teams.append((nm, "FCS", conf, sp_show, sag25, comp26, rec))

    all_teams.sort(key=lambda x: x[5], reverse=True)

    hdr = ch("Rank","Team","Div","Conference","SP+ '26","Sagarin '25","Comp. '26","2025 W-L")
    rows = [hdr]
    gold_rows, fcs_rows = [], []

    for i, (nm, div, conf, sp, sag, comp, rec) in enumerate(all_teams):
        rank = i + 1
        sp_disp = f"{sp:+.1f}" if sp != "N/A" else "N/A"
        sp_col  = GREEN if (sp != "N/A" and sp > 10) else (RED if (sp != "N/A" and sp < -5) else DKGRAY)
        div_col = BLUE if div == "FBS" else GREEN
        row = [
            c(str(rank), bold=(rank<=25)),
            c(nm, align=TA_LEFT, bold=(rank<=25), sz=8),
            c(div, col=div_col, bold=True, sz=7.5),
            c(conf, sz=7),
            c(sp_disp, col=sp_col, sz=7.5),
            c(f"{sag:.2f}", sz=7.5),
            c(f"{comp:.1f}", bold=True, col=(NAVY if rank<=25 else DKGRAY), sz=8),
            c(rec, sz=7.5),
        ]
        rows.append(row)
        if div == "FCS":
            fcs_rows.append(rank)
        if rank <= 25 and div == "FBS":
            gold_rows.append(rank)

    cw = [0.40*inch, 1.80*inch, 0.42*inch, 0.88*inch,
          0.65*inch, 0.82*inch, 0.70*inch, 0.70*inch]
    story.append(make_table(rows, cw, green=fcs_rows, gold=[r for r in gold_rows]))
    story.append(Spacer(1,6))
    story.append(Paragraph(
        "★ Green rows = FCS teams.  Gold rows = FBS top 25.  "
        "FCS teams with Composite > 60.0 are competitive with lower-tier FBS programs — "
        "watch for those in FCS vs FBS matchups.",
        P_NOTE))

    doc.build(story)
    print(f"  ✓  {path}")
    return path


# ════════════════════════════════════════════════════════════════════════════
#  GAME DATA
# ════════════════════════════════════════════════════════════════════════════
# (date, tv, away, away_div, home, home_div, neutral, vegas_home_spread)
# vegas_home_spread: + = home favoured, - = away favoured, None = not posted

FCS_FCS_GAMES = [
    ("Thu 9/3",  "FloSports", "Lindenwood",    "FCS", "Stony Brook",      "FCS", False, None),
    ("Thu 9/3",  "ESPN+",     "Southern Illinois","FCS","Samford",         "FCS", False, None),
    ("Sun 9/6",  "ESPN2",     "Texas Southern", "FCS", "Prairie View A&M","FCS", False, None),
    ("Sun 9/6",  "ESPN",      "SC State",       "FCS", "Florida A&M",     "FCS", True,  None),
]

FCS_FBS_GAMES = [
    # Wk 0
    ("Sat 8/29", "CBSSN",    "Jacksonville State","FCS","NDSU",           "FBS", False, None),
    # Thu 9/3
    ("Thu 9/3",  "ESPN+",    "UAlbany",          "FCS","Buffalo",         "FBS", False, None),
    ("Thu 9/3",  "ESPN+",    "Bethune-Cookman",   "FCS","UCF",            "FBS", False, None),
    ("Thu 9/3",  "ESPN+",    "Merrimack",         "FCS","Delaware",        "FBS", False, None),
    ("Thu 9/3",  "ESPN+",    "West Georgia",      "FCS","Kennesaw State",  "FBS", False, None),
    ("Thu 9/3",  "SEC Net.", "Ark.-Pine Bluff",   "FCS","Missouri",        "FBS", False, None),
    ("Thu 9/3",  "Peacock",  "Eastern Illinois",  "FCS","Minnesota",       "FBS", False, None),
    ("Thu 9/3",  "ESPN+",    "Idaho",             "FCS","Utah",            "FBS", False, None),
    # Fri 9/4
    ("Fri 9/4",  "ESPN+",    "NC A&T",            "FCS","Georgia State",   "FBS", False, None),
    ("Fri 9/4",  "Big Ten",  "Indiana State",     "FCS","Purdue",          "FBS", False, None),
    ("Fri 9/4",  "ESPNU",    "LIU",               "FCS","Kansas",          "FBS", False, None),
    # Sat 9/5
    ("Sat 9/5",  "N/A",      "Lafayette",         "FCS","UConn",           "FBS", False, None),
    ("Sat 9/5",  "CBSSN",    "Bryant",            "FCS","Army",            "FBS", False, None),
    ("Sat 9/5",  "MW+",      "Duquesne",          "FCS","Air Force",       "FBS", False, None),
    ("Sat 9/5",  "ESPN+",    "Tarleton State",    "FCS","Bowling Green",   "FBS", False, None),
    ("Sat 9/5",  "ESPN",     "New Hampshire",     "FCS","Syracuse",        "FBS", False, None),
    ("Sat 9/5",  "ESPN",     "Youngstown State",  "FCS","Kentucky",        "FBS", False, None),
    ("Sat 9/5",  "ESPN+",    "SE Missouri State", "FCS","Iowa State",      "FBS", False, None),
    ("Sat 9/5",  "ESPN+",    "Rhode Island",      "FCS","Temple",          "FBS", False, None),
    ("Sat 9/5",  "SEC+",     "Tennessee State",   "FCS","Georgia",         "FBS", False, None),
    ("Sat 9/5",  "ESPN",     "Furman",            "FCS","Tennessee",       "FBS", False, None),
    ("Sat 9/5",  "ESPN+",    "The Citadel",       "FCS","Charlotte",       "FBS", False, None),
    ("Sat 9/5",  "CBSSN",    "Towson",            "FCS","Navy",            "FBS", False, None),
    ("Sat 9/5",  "ESPN+",    "UTRGV",             "FCS","UTSA",            "FBS", False, None),
    ("Sat 9/5",  "CW Net.",  "Fordham",           "FCS","NDSU",            "FBS", False, None),
    ("Sat 9/5",  "ESPN+",    "Maine",             "FCS","App State",       "FBS", False, None),
    ("Sat 9/5",  "ESPN",     "North Alabama",     "FCS","Arkansas",        "FBS", False, None),
    ("Sat 9/5",  "ESPN+",    "Alcorn State",      "FCS","Southern Miss",   "FBS", False, None),
    ("Sat 9/5",  "ESPN",     "Austin Peay",       "FCS","Vanderbilt",      "FBS", False, None),
    ("Sat 9/5",  "FS1",      "Abilene Christian", "FCS","Texas Tech",      "FBS", False, None),
    ("Sat 9/5",  "ESPN+",    "Nicholls",          "FCS","Kansas State",    "FBS", False, None),
    ("Sat 9/5",  "ESPN",     "Missouri State",    "FCS","Texas A&M",       "FBS", False, -38.5),
    ("Sat 9/5",  "ESPN+",    "Norfolk State",     "FCS","Old Dominion",    "FBS", False, None),
]

FBS_FBS_GAMES = [
    # ── Week 0 (Aug 29) ───────────────────────────────────────────────────
    ("Sat 8/29",  "ESPN",    "North Carolina",   "FBS","TCU",             "FBS", True,  -6.5),  # Dublin neutral
    ("Sat 8/29",  "NBC",     "San Jose State",   "FBS","USC",             "FBS", False, None),
    ("Sat 8/29",  "ESPN",    "NC State",         "FBS","Virginia",        "FBS", False, +4.5),  # Virginia -4.5
    ("Sat 8/29",  "CBSSN",   "Sacramento State", "FBS","Eastern Michigan","FBS", False, +8.5),  # EMU -8.5
    ("Sat 8/29",  "ESPN+",   "Hawaii",           "FBS","Stanford",        "FBS", False, +3.0),  # Stanford -3
    ("Sat 8/29",  "CW Net.", "New Mexico State",  "FBS","Florida State",  "FBS", False, None),
    ("Sat 8/29",  "FOX",     "Memphis",          "FBS","UNLV",            "FBS", False, +3.0),  # UNLV -3 home
    # ── Thursday Sep 3 ────────────────────────────────────────────────────
    ("Thu 9/3",   "Big Ten", "UMass",            "FBS","Rutgers",         "FBS", False, None),
    ("Thu 9/3",   "ACC Net.","Akron",            "FBS","Wake Forest",     "FBS", False, None),
    ("Thu 9/3",   "ESPN",    "Colorado",         "FBS","Georgia Tech",    "FBS", False, +7.0),  # GT -7
    ("Thu 9/3",   "Big Ten", "UAB",              "FBS","Illinois",        "FBS", False, +27.5), # Illinois -27.5
    # ── Friday Sep 4 ──────────────────────────────────────────────────────
    ("Fri 9/4",   "ESPN+",   "SJSU",             "FBS","Eastern Michigan","FBS", False, None),
    ("Fri 9/4",   "ESPNU",   "Toledo",           "FBS","Michigan State",  "FBS", False, None),
    ("Fri 9/4",   "ESPN",    "Miami",            "FBS","Stanford",        "FBS", False, -21.5), # Miami -21.5 road fav
    ("Fri 9/4",   "FOX",     "Fresno State",     "FBS","USC",             "FBS", False, None),
    # ── Saturday Sep 5 ────────────────────────────────────────────────────
    ("Sat 9/5",   "ESPN",    "UTEP",             "FBS","Oklahoma",        "FBS", False, +40.5), # OU -40.5
    ("Sat 9/5",   "ABC",     "East Carolina",    "FBS","Alabama",         "FBS", False, +25.5), # Alabama -25.5 (moved from -26.5)
    ("Sat 9/5",   "ESPN",    "Oregon State",     "FBS","Houston",         "FBS", False, +18.5), # Houston -18.5
    ("Sat 9/5",   "TNT",     "Coastal Carolina", "FBS","West Virginia",   "FBS", False, +17.5), # WVU -17.5
    ("Sat 9/5",   "CW Net.", "Miami (OH)",        "FBS","Pittsburgh",     "FBS", False, +16.5), # Pitt -16.5
    ("Sat 9/5",   "FOX",     "North Texas",      "FBS","Indiana",         "FBS", False, +40.5), # Indiana -40.5
    ("Sat 9/5",   "FS1",     "Ohio",             "FBS","Nebraska",        "FBS", False, +23.5), # Nebraska -23.5
    ("Sat 9/5",   "Big Ten", "Ball State",       "FBS","Ohio State",      "FBS", False, +49.5), # OSU -49.5
    ("Sat 9/5",   "ESPN",    "Kent State",       "FBS","South Carolina",  "FBS", False, +33.5), # SC -33.5
    ("Sat 9/5",   "ABC",     "Baylor",           "FBS","Auburn",          "FBS", True,  -7.0),  # Auburn -7 neutral (Atlanta)
    ("Sat 9/5",   "CBS",     "Boise State",      "FBS","Oregon",          "FBS", False, +24.5), # Oregon -24.5
    ("Sat 9/5",   "ESPN",    "Texas State",      "FBS","Texas",           "FBS", False, +30.5), # Texas -30.5
    ("Sat 9/5",   "ACC Net.","Tulane",           "FBS","Duke",            "FBS", False, +8.5),  # Duke -8.5
    ("Sat 9/5",   "ESPNU",   "Oklahoma State",   "FBS","Tulsa",           "FBS", False, -12.0), # OkSt -12 road fav
    ("Sat 9/5",   "ESPN+",   "FIU",              "FBS","South Florida",   "FBS", False, +12.5), # USF -12.5
    ("Sat 9/5",   "ABC",     "Clemson",          "FBS","LSU",             "FBS", False, +11.0), # LSU -11 (updated; Leavitt cleared)
    ("Sat 9/5",   "NBC",     "Western Michigan", "FBS","Michigan",        "FBS", False, +26.5), # Michigan -26.5
    ("Sat 9/5",   "SEC Net.","FAU",              "FBS","Florida",         "FBS", False, +25.5), # Florida -25.5
    ("Sat 9/5",   "ESPN",    "UCLA",             "FBS","California",      "FBS", False, -1.5),  # Cal -1.5 home
    ("Sat 9/5",   "FS1",     "Marshall",         "FBS","Penn State",      "FBS", False, +23.5), # PSU -23.5
    ("Sat 9/5",   "ESPNU",   "Liberty",          "FBS","James Madison",   "FBS", False, +6.0),  # JMU -6
    ("Sat 9/5",   "USA Net.","Wyoming",          "FBS","Colorado State",  "FBS", False, +4.0),  # CSU -4
    ("Sat 9/5",   "Big Ten", "Northern Illinois","FBS","Iowa",            "FBS", False, +29.5), # Iowa -29.5
    ("Sat 9/5",   "FOX",     "Boston College",   "FBS","Cincinnati",      "FBS", False, +9.5),  # Cinci -9.5
    ("Sat 9/5",   "ESPN",    "Sam Houston",      "FBS","Troy",            "FBS", False, +16.5), # Troy -16.5
    ("Sat 9/5",   "ESPN",    "Arkansas State",   "FBS","Memphis",         "FBS", False, +10.5), # Memphis -10.5
    ("Sat 9/5",   "CW Net.", "UNLV",             "FBS","Hawaii",          "FBS", False, -1.5),  # UNLV -1.5 road (Week 1)
    ("Sat 9/5",   "FS1",     "Western Kentucky", "FBS","Nevada",          "FBS", False, -4.0),  # WKU -4 road
    ("Sat 9/5",   "ESPN+",   "Central Michigan", "FBS","New Mexico",      "FBS", False, +12.5), # NM -12.5
    # ── Sunday Sep 6 ──────────────────────────────────────────────────────
    ("Sun 9/6",   "NBC",     "Washington State", "FBS","Washington",      "FBS", False, +21.5), # Washington -21.5
    ("Sun 9/6",   "ABC",     "Louisville",       "FBS","Ole Miss",        "FBS", True,  -7.5),  # Ole Miss -7.5 neutral Nashville (updated)
    ("Sun 9/6",   "NBC",     "Wisconsin",        "FBS","Notre Dame",      "FBS", True,  -20.5), # ND -20.5 neutral Lambeau (updated)
    # ── Monday Sep 7 ──────────────────────────────────────────────────────
    ("Mon 9/7",   "ESPN",    "SMU",              "FBS","Florida State",   "FBS", False, -2.5),  # SMU -2.5 road fav
]

# Remove FCS teams incorrectly listed in FBS_FBS_GAMES
FBS_FBS_CLEAN = [
    g for g in FBS_FBS_GAMES
    if g[3] == "FBS" and g[5] == "FBS"
       and g[2] not in FCS_DATA_DEDUP
       and g[4] not in FCS_DATA_DEDUP
]


# ════════════════════════════════════════════════════════════════════════════
#  PDF 2 — FCS vs FCS MATCHUPS
# ════════════════════════════════════════════════════════════════════════════

def build_fcs_fcs_pdf():
    path = os.path.join(OUTPUT_DIR, "02_FCS_vs_FCS_Matchups.pdf")
    doc = SimpleDocTemplate(path, pagesize=letter,
                            leftMargin=0.5*inch, rightMargin=0.5*inch,
                            topMargin=0.38*inch, bottomMargin=0.38*inch)
    story = []
    story += banner(
        "ELITE SAGARIN MODEL",
        "FCS vs FCS  ·  Week 1 Matchups  ·  2026",
        "Model spread = Composite Home − Composite Away + 2.80 HFA (0 neutral). "
        "Composites based on Sagarin 2025 with 2026 preseason poll adjustments.",
    )
    story.append(Paragraph("All FCS vs FCS Week 1 Games", P_SECT))
    story.append(Paragraph(
        "Four FCS-vs-FCS games are currently scheduled for Week 1 2026. "
        "No Vegas lines are yet posted for pure FCS matchups — use model spread "
        "as your reference for sharp analysis.",
        P_NOTE))

    hdr = ch("Date","TV","Away (FCS)","Away Comp","Home (FCS)","Home Comp",
             "Neutral","Model Spread","Notes")
    rows = [hdr]

    for game in FCS_FCS_GAMES:
        date, tv, away, adiv, home, hdiv, neutral, vegas = game
        ca = comp_for(away, adiv)
        ch_ = comp_for(home, hdiv)
        ms  = model_spread(ch_, ca, neutral)
        spread = fmt_spread(ms, home, away)
        note = ""
        if away == "Lindenwood" and home == "Stony Brook":
            note = "Both CAA/OVC ~46-47 comp. Coin flip, slight Stony Brook edge at home."
        elif away == "Southern Illinois" and home == "Samford":
            note = "★★★ SIU comp 61.5 vs Samford 36.5. SIU dominates — lay SIU if -10 or less."
        elif away == "Texas Southern" and home == "Prairie View A&M":
            note = "★ Labor Day Classic. PVM comp 50.5 vs TSU 32.5. PVM strong at home."
        elif away == "SC State" and home == "Florida A&M":
            note = "★ Orange Blossom Classic (neutral Miami). SC State comp 51.0 vs FAMU 41.0."

        rows.append([
            c(date, sz=8),
            c(tv, sz=7),
            c(away, align=TA_LEFT, bold=True, sz=8),
            c(f"{ca:.1f}", col=NAVY, bold=True),
            c(home, align=TA_LEFT, bold=True, sz=8),
            c(f"{ch_:.1f}", col=NAVY, bold=True),
            c("Yes" if neutral else "No", col=AMBER if neutral else DKGRAY, sz=7.5),
            c(spread, bold=True, col=GREEN if ms > 7 else (RED if ms < -7 else DKGRAY)),
            c(note, align=TA_LEFT, sz=7, col=DKGRAY),
        ])

    cw = [0.65*inch, 0.68*inch, 1.3*inch, 0.72*inch, 1.3*inch, 0.72*inch,
          0.52*inch, 1.25*inch, 2.3*inch]
    story.append(make_table(rows, cw, gold=[2,3,4]))
    story.append(Spacer(1,8))
    story.append(Paragraph(
        "NOTE: SIU vs Samford is the highest-leverage FCS-vs-FCS bet of Week 1. "
        "SIU (61.5 composite, MVFC) vs Samford (36.5 composite, SoCon worst). "
        "25-point composite gap. Bet SIU to win comfortably if any line is posted.",
        P_NOTE))

    doc.build(story)
    print(f"  ✓  {path}")
    return path


# ════════════════════════════════════════════════════════════════════════════
#  PDF 3 — FCS vs FBS MATCHUPS  (LANDSCAPE — 10.1" usable width)
# ════════════════════════════════════════════════════════════════════════════

def build_fcs_fbs_pdf():
    path = os.path.join(OUTPUT_DIR, "03_FCS_vs_FBS_Matchups.pdf")
    # Landscape: 11" x 8.5" — usable width = 11 - 2*0.45 = 10.10"
    doc = SimpleDocTemplate(path, pagesize=landscape(letter),
                            leftMargin=0.45*inch, rightMargin=0.45*inch,
                            topMargin=0.38*inch, bottomMargin=0.38*inch)
    story = []
    story += banner(
        "ELITE SAGARIN MODEL",
        "FCS vs FBS  ·  Week 1 Matchups  ·  2026",
        "Model spread = FBS Comp − FCS Comp + 2.80 HFA (FBS home).  "
        "Green = upset window (spread < 14).  Amber = soft FBS host (14–21).  "
        "FCS comp: Sagarin 2025 adj.  FBS comp: 70% SP+_scaled + 30% Sagarin.",
    )

    story.append(Paragraph("All FCS vs FBS Week 1 Games (33 matchups)", P_SECT))
    story.append(Paragraph(
        "Vegas does not post lines for most FCS-FBS games — model spread is your sharp reference.",
        P_NOTE))

    # Column widths — total = 10.10"
    # Date  TV   FCS Team  FC   FBS Team  FB   Neu  Spread  Vegas  Sharp Note
    # 0.62  0.58  1.45    0.58   1.38    0.58  0.42  1.22   0.90    2.37
    CW = [0.62*inch, 0.58*inch, 1.45*inch, 0.58*inch,
          1.38*inch, 0.58*inch, 0.42*inch, 1.22*inch,
          0.90*inch, 2.37*inch]

    hdr = ch("Date","TV","FCS Team","FCS\nComp",
             "FBS Team","FBS\nComp","Ntrl","Model Spread","Vegas","Sharp Note")
    rows = [hdr]
    green_r, amber_r = [], []

    # Concise notes (max ~180 chars so they wrap neatly in 2.37")
    sharp_notes = {
        "Tarleton State":     "★★★ TARLETON FAVOURED. BG home may open -7 to -14. 6-12 pt edge on WAC powerhouse.",
        "West Georgia":       "★★★ KSU (C-USA yr 1) comp 63.4. WG comp 53.0. If KSU -17+, WG +17 is value.",
        "Indiana State":      "★★  Purdue -25 model. Purdue Sag only 63.58. If market -28+, fade Purdue.",
        "Rhode Island":       "★★  RI comp 55.5 vs Temple 61.9. Model Temple -9. If -14+, RI +14 is value.",
        "Youngstown State":   "★   YSU comp 59 vs KY comp 74. Model KY -18. Standard cupcake.",
        "Abilene Christian":  "★★  QB CRISIS: Sorsby gone (gambling). Hammond ACL, Week 1 uncertain. "
                              "Backup Jones III likely starts. TT effective ~82. If Vegas -28+, ACU cover live.",
        "Missouri State":     "A&M -38.5 opened. Model A&M -36. Near model — pass.",
        "Idaho":              "★★  Utah SP+ 11.9, Sag 86.80. Model Utah -38. If -42+, Idaho has value.",
        "Fordham":            "NDSU (new FBS) model -12. Standard new-FBS test.",
        "UTRGV":              "UTSA -25 model. Blowout expected.",
        "Lafayette":          "UConn -21 model. Large gap.",
        "North Alabama":      "Arkansas -28 model.",
        "UAlbany":            "Buffalo -16 model.",
        "NC A&T":             "Georgia State -24 model.",
        "Tennessee State":    "Georgia -55+ model. Largest blowout of weekend.",
        "Ark.-Pine Bluff":    "Missouri -50 model.",
        "Austin Peay":        "Vanderbilt -33 model.",
        "Nicholls":           "Kansas State -33 model.",
    }

    for game in FCS_FBS_GAMES:
        date, tv, away, adiv, home, hdiv, neutral, vegas = game
        is_away_fcs = (adiv == "FCS")
        fcs_team = away if is_away_fcs else home
        fbs_team = home if is_away_fcs else away
        fcs_c = comp_for(fcs_team, "FCS")
        fbs_c = comp_for(fbs_team, "FBS")

        if is_away_fcs:
            ms = model_spread(fbs_c, fcs_c, neutral)
        else:
            ms = -model_spread(fcs_c, fbs_c, neutral)

        spread_str = f"{fbs_team} -{abs(ms):.1f}" if ms > 0 else f"{fcs_team} -{abs(ms):.1f}"
        note = sharp_notes.get(fcs_team, "—")
        vegas_str = f"{fbs_team} -{abs(vegas):.1f}" if vegas else "TBD"

        row_idx = len(rows)
        rows.append([
            c(date, sz=8),
            c(tv, sz=7.5),
            c(fcs_team, align=TA_LEFT, bold=True, sz=8.5, col=GREEN),
            c(f"{fcs_c:.1f}", col=GREEN if fcs_c > 55 else DKGRAY, bold=True, sz=8.5),
            c(fbs_team, align=TA_LEFT, sz=8.5),
            c(f"{fbs_c:.1f}", col=BLUE, sz=8.5),
            c("Y" if neutral else "N", col=AMBER if neutral else MID_GRAY, sz=8),
            c(spread_str, bold=True, col=NAVY, sz=8.5),
            c(vegas_str, sz=8, col=(AMBER if vegas else MID_GRAY)),
            c(note, align=TA_LEFT, sz=7.5, col=DKGRAY),
        ])

        if ms < 14:
            green_r.append(row_idx)
        elif ms < 21:
            amber_r.append(row_idx)

    story.append(make_table(rows, CW, green=green_r, amber=amber_r))

    story.append(Spacer(1, 8))
    story.append(HRFlowable(width='100%', thickness=1, color=GOLD, spaceAfter=6))
    story.append(Paragraph("Top FCS Upset Candidates", P_SECT))

    story.append(Paragraph(
        "★★★ Tarleton State at Bowling Green: Tarleton composite 67.5 (WAC powerhouse, 12-2 in 2025) "
        "vs Bowling Green composite 62.4 (MAC, 4-8). Model makes TARLETON the FAVOURITE even as a road team. "
        "If Vegas opens BG at home -7 to -14, this is the single largest FCS upset value play of the entire weekend.\n\n"
        "★★★ West Georgia at Kennesaw State: KSU (C-USA, first full FBS year) only rates 63.4 composite. "
        "WG composite 53.0 is a legitimate WAC FCS team. If market opens KSU -17+, West Georgia +17 is strong value.\n\n"
        "★★ Indiana State at Purdue: Purdue model spread -25. Purdue went 2-10 in 2025 with a Sagarin of only 63.58. "
        "If Vegas inflates to -30+, back Indiana State to cover.",
        P_NOTE))

    doc.build(story)
    print(f"  ✓  {path}")
    return path


# ════════════════════════════════════════════════════════════════════════════
#  PDF 4 — FBS vs FBS MATCHUPS  (LANDSCAPE — 10.1" usable width)
# ════════════════════════════════════════════════════════════════════════════

def build_fbs_fbs_pdf():
    path = os.path.join(OUTPUT_DIR, "04_FBS_vs_FBS_Matchups.pdf")
    # Landscape letter: usable width = 11 - 2*0.45 = 10.10"
    doc = SimpleDocTemplate(path, pagesize=landscape(letter),
                            leftMargin=0.45*inch, rightMargin=0.45*inch,
                            topMargin=0.38*inch, bottomMargin=0.38*inch)
    story = []
    story += banner(
        "ELITE SAGARIN MODEL",
        "FBS vs FBS  ·  Week 0 + Week 1 Matchups  ·  2026  ·  July 2 Update",
        "Composite = 70% SP+_scaled + 30% Sagarin (80/20 for major-change teams).  "
        "Edge = Model − Vegas  ( + = home/fav underpriced;  − = away/dog has value ).  "
        "Green = away/dog value ≥ 3 pts.  Red = home/fav underpriced ≥ 3 pts.  ★ = best bet.",
    )

    # Column widths — total = 10.10"
    # Date  TV    Away  AC    Home  HC    N    Spread  Vegas  Edge  ★     Lean
    # 0.68  0.54  1.18  0.58  1.18  0.58  0.28  1.22  1.10  0.56  0.42  0.78
    CW = [0.68*inch, 0.54*inch, 1.18*inch, 0.58*inch,
          1.18*inch, 0.58*inch, 0.28*inch, 1.22*inch,
          1.10*inch, 0.56*inch, 0.42*inch, 0.78*inch]

    def make_game_rows(games):
        hdr = ch("Date","TV","Away","Away\nComp","Home","Home\nComp",
                 "N","Model Spread","Vegas","Edge","★","Lean")
        rows = [hdr]
        green_r, red_r, amber_r, gold_r = [], [], [], []

        for game in games:
            date, tv, away, adiv, home, hdiv, neutral, vegas = game
            if adiv != "FBS" or hdiv != "FBS": continue
            c_away = comp_for(away, "FBS")
            c_home = comp_for(home, "FBS")
            ms = model_spread(c_home, c_away, neutral)
            spread_str = fmt_spread(ms, home, away)

            ri = len(rows)
            if vegas is None:
                v_str, edge_s, star_s, lean_s = "TBD", "—", "—", "—"
                e = None
            else:
                v = vegas
                if v < 0 and ms > 0 and abs(v) < 30:
                    v = -v
                e = ms - v
                sign = "+" if e > 0 else ""
                v_str = f"{home} -{abs(v):.1f}" if v > 0 else f"{away} -{abs(v):.1f}"
                edge_s = f"{sign}{e:.1f}"
                abs_e = abs(e)
                star_s = ("★★★★" if abs_e >= 6 else "★★★" if abs_e >= 4
                          else "★★" if abs_e >= 2.5 else "★" if abs_e >= 1.5 else "—")
                lean_s = ("Home/Fav" if e > 1.5 else "Away/Dog" if e < -1.5 else "—")

            rows.append([
                c(date, sz=8),
                c(tv, sz=7.5),
                c(away, align=TA_LEFT, sz=8.5),
                c(f"{c_away:.1f}", col=BLUE, sz=8.5),
                c(("(n) " if neutral else "") + home, align=TA_LEFT, sz=8.5),
                c(f"{c_home:.1f}", col=BLUE, sz=8.5),
                c("Y" if neutral else "N", col=AMBER if neutral else MID_GRAY, sz=8),
                c(spread_str, bold=True, col=NAVY, sz=8.5),
                c(v_str, sz=8, col=(AMBER if vegas else MID_GRAY)),
                c(edge_s, bold=(e is not None and abs(e) >= 2.5),
                  col=(RED if e and e > 0 else GREEN if e and e < 0 else MID_GRAY), sz=8.5),
                c(star_s, bold=True, col=(GOLD if star_s != "—" else MID_GRAY), sz=9),
                c(lean_s, col=(AMBER if lean_s != "—" else MID_GRAY), sz=8),
            ])

            if e is not None:
                if e >= 3:   red_r.append(ri)
                elif e <= -3: green_r.append(ri)
                if abs(e) >= 5: gold_r.append(ri)

        return rows, green_r, red_r, amber_r, gold_r

    story.append(Paragraph("Week 0 — Saturday August 29", P_SECT))
    wk0 = [g for g in FBS_FBS_CLEAN if g[0].startswith("Sat 8/29")]
    r0, gr0, rr0, ar0, gd0 = make_game_rows(wk0)
    story.append(make_table(r0, CW, green=gr0, red=rr0, amber=ar0, gold=gd0))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Thursday September 3 — Week 1", P_SECT))
    thu = [g for g in FBS_FBS_CLEAN if g[0].startswith("Thu 9/3")]
    r_t, gr_t, rr_t, ar_t, gd_t = make_game_rows(thu)
    story.append(make_table(r_t, CW, green=gr_t, red=rr_t, amber=ar_t, gold=gd_t))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Friday September 4 — Week 1", P_SECT))
    fri = [g for g in FBS_FBS_CLEAN if g[0].startswith("Fri 9/4")]
    r_f, gr_f, rr_f, ar_f, gd_f = make_game_rows(fri)
    story.append(make_table(r_f, CW, green=gr_f, red=rr_f, amber=ar_f, gold=gd_f))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Saturday September 5 — Week 1 (Main Slate)", P_SECT))
    sat = [g for g in FBS_FBS_CLEAN if g[0].startswith("Sat 9/5")]
    r_s, gr_s, rr_s, ar_s, gd_s = make_game_rows(sat)
    story.append(make_table(r_s, CW, green=gr_s, red=rr_s, amber=ar_s, gold=gd_s))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Sunday September 6 + Monday September 7", P_SECT))
    sun = [g for g in FBS_FBS_CLEAN if g[0].startswith("Sun") or g[0].startswith("Mon")]
    r_su, gr_su, rr_su, ar_su, gd_su = make_game_rows(sun)
    story.append(make_table(r_su, CW, green=gr_su, red=rr_su, amber=ar_su, gold=gd_su))
    story.append(Spacer(1, 8))

    # ── Best Bets callout ─────────────────────────────────────────────────────
    story.append(HRFlowable(width='100%', thickness=1.5, color=GOLD, spaceAfter=6))
    story.append(Paragraph("Top Market Edge Plays — FBS vs FBS  (July 2, 2026 Board)", P_SECT))

    best = [
        ("★★★", "ECU +25.5", "at Alabama",
         "ALA -19.2 | Vegas -25.5 | Edge -6.3",
         "Alabama SP+ only 18.2 (#11). ECU 9-4 in 2025, Sagarin 73.52. "
         "Vegas over-inflates the SEC brand. Model: Alabama wins by 19, not 26. Take ECU +25.5."),
        ("★★★", "N. Texas +40.5", "at Indiana",
         "IU -34.6 | Vegas -40.5 | Edge -5.9",
         "NT lost head coach Neal Brown + major portal exodus. Blend: IU -34.6. "
         "Market max-priced NT collapse. NT +40.5 is a 5.9-pt edge — take the big number."),
        ("★★★", "JMU -6", "vs Liberty",
         "JMU -11.6 | Vegas -6 | Edge +5.6",
         "JMU (12-2 in 2025) composite 71.8 vs Liberty composite 63.1. "
         "Model gap = 11.6 pts. Vegas only prices JMU at -6 at home. Largest home-side edge of the slate."),
        ("★★★", "WMU +26.5", "at Michigan",
         "MICH -21.1 | Vegas -26.5 | Edge -5.4",
         "WMU 10-4 in 2025, Sagarin 68.87. Michigan SP+ 16.1 (new HC Whittingham). "
         "Model: Michigan wins by 21. Vegas: -26.5. WMU +26.5 has 5.4 pts of value."),
        ("★★★", "Ohio +23.5", "at Nebraska",
         "NEB -18.4 | Vegas -23.5 | Edge -5.1",
         "Ohio MAC 9-4 in 2025, Sagarin 66.0. Nebraska SP+ 7.7, Sag 73.22. Model -18.4. "
         "Market inflates Big Ten brand by 5.1 pts. Ohio +23.5 is the play."),
        ("★★★", "Troy -16.5", "vs Sam Houston",
         "TROY -21.1 | Vegas -16.5 | Edge +4.6",
         "Sam Houston (C-USA): SP+ -26.3, Sagarin 43.48. Troy (Sun Belt): SP+ -6.0, Sag 61.83. "
         "Model: Troy wins by 21. Vegas -16.5 — Troy is 4.6 pts underpriced. Lay the Sun Belt team."),
        ("★★", "Iowa -29.5", "vs N. Illinois",
         "IOWA -32.8 | Vegas -29.5 | Edge +3.3",
         "Iowa SP+ 13.6, Sagarin 86.07. NIU SP+ -18.2. Model: Iowa -32.8. "
         "Iowa underpriced by 3.3 pts at Kinnick — lay the Hawkeyes."),
        ("★★", "Miami OH +16.5", "at Pittsburgh",
         "PITT -13.2 | Vegas -16.5 | Edge -3.3",
         "Miami OH 7-7 in 2025, Sag 62.83. Pitt comp 77.1. Model Pitt -13.2. "
         "Vegas inflates Pitt to -16.5. 3.3-pt edge on Miami OH +16.5."),
        ("★★", "Clemson +11", "at LSU",
         "LSU -8.6 | Vegas -11 | Edge -2.4",
         "Sagarin rates them nearly equal (79.32 vs 79.14). Leavitt cleared from injury (positive). "
         "Model: LSU -8.6. Market paying full Kiffin premium at -11. Take Clemson +11."),
        ("★", "UNLV -3", "vs Memphis (Wk0)",
         "UNLV -5.1 | Vegas -3 | Edge +2.1",
         "UNLV comp 72.0 vs Memphis 69.7. Model: UNLV -5.1 at home. Vegas only -3 — underpriced 2.1 pts."),
    ]

    # Best bets table — CW2 sums to 10.10"
    CW2 = [0.52*inch, 1.28*inch, 1.55*inch, 1.88*inch, 4.87*inch]
    hdr2 = ch("★", "Pick", "vs.", "Model vs Vegas", "Rationale")
    rows2 = [hdr2]
    for strs, pick, opp, mv, rat in best:
        rows2.append([
            c(strs, col=GOLD, bold=True, sz=10),
            c(pick, align=TA_LEFT, bold=True, col=NAVY, sz=9),
            c(opp, sz=8.5, align=TA_LEFT),
            c(mv, sz=8, col=DKGRAY),
            c(rat, align=TA_LEFT, sz=8.5, col=DKGRAY),
        ])
    story.append(make_table(rows2, CW2, gold=[1, 2, 3, 4, 5, 6]))

    doc.build(story)
    print(f"  ✓  {path}")
    return path


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating Elite Sagarin Model PDFs (v4 — July 2026 Update) …")
    p1 = build_rankings_pdf()
    p2 = build_fcs_fcs_pdf()
    p3 = build_fcs_fbs_pdf()
    p4 = build_fbs_fbs_pdf()
    print("\nAll files saved:")
    for p in (p1, p2, p3, p4):
        print(f"  {p}")
