"""
Produces a Word (.docx) with tracked changes for the Sports Prediction Tools hub page.

Philosophy: this is a TIMELESS parent hub page.
  - It establishes WoO as the authority on probability-based sports analysis.
  - It converts users to sportsbooks — the revenue mechanism.
  - It should stay relevant for months/years regardless of which specific tools
    are live or which sport is in season.

Changes made:
  1. One sentence added to the intro tying the model output to sportsbook comparison.
  2. One sportsbook CTA banner placed before "Explore Our Prediction Tools."
  3. Market X-Ray heading: CLV performance badge added (trust signal, not sport-specific).
  4. One CTA line added after "Why Use" section before "Play responsibly!"
  5. New "Recommended Sportsbooks" section added (general, not sport-specific).
  6. 3 new FAQ questions (sport-agnostic, conversion-focused).
  7. FAQ formatting bug flagged (Heading 2 on a body paragraph).

What was intentionally NOT done:
  - No sport-specific CTAs at every paragraph.
  - No links to tools/pages that may or may not exist.
  - No "coming soon" notes that belong in internal docs, not on a published page.
  - No hyper-focus on any one sport or tool — content will outlive any single season.
"""

import copy, os, shutil
from lxml import etree
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ── Config ─────────────────────────────────────────────────────────────────────
SRC  = "/tmp/sports_prediction_tools.docx"
DST  = "/tmp/Sports_Prediction_Tools_TRACKED.docx"
DEST_FOLDER = ("/Users/josephshackelford/Desktop/"
               "Desktop - Joseph's MacBook Air copy/"
               "WizardOfOdds_Portfolio/casino_games")

AUTHOR = "Revenue Optimization Review"
DATE   = "2026-07-07T17:30:00Z"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

_ins_counter = [1]

def next_id():
    v = _ins_counter[0]
    _ins_counter[0] += 1
    return str(v)

# ── XML helpers ────────────────────────────────────────────────────────────────

def w(tag):
    return f"{{{W}}}{tag}"

def make_ins_element():
    """<w:ins w:id=... w:author=... w:date=...>"""
    ins = OxmlElement("w:ins")
    ins.set(w("id"),     next_id())
    ins.set(w("author"), AUTHOR)
    ins.set(w("date"),   DATE)
    return ins

def make_run(text, bold=False, italic=False, color=None, size=None, font_name=None):
    """Build a <w:r> element."""
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    if bold:
        b = OxmlElement("w:b"); rpr.append(b)
    if italic:
        i = OxmlElement("w:i"); rpr.append(i)
    if color:
        c = OxmlElement("w:color")
        c.set(w("val"), color)
        rpr.append(c)
    if size:
        sz = OxmlElement("w:sz");  sz.set(w("val"), str(size * 2)); rpr.append(sz)
        szCs = OxmlElement("w:szCs"); szCs.set(w("val"), str(size * 2)); rpr.append(szCs)
    if font_name:
        rFonts = OxmlElement("w:rFonts")
        rFonts.set(w("ascii"), font_name)
        rFonts.set(w("hAnsi"), font_name)
        rpr.append(rFonts)
    if len(rpr):
        r.append(rpr)
    t = OxmlElement("w:t")
    t.text = text
    if text.startswith(" ") or text.endswith(" "):
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    r.append(t)
    return r

def make_inserted_run(text, bold=False, italic=False, color=None, size=None,
                      font_name=None):
    """Wrap a <w:r> in <w:ins>."""
    ins = make_ins_element()
    ins.append(make_run(text, bold=bold, italic=italic, color=color,
                        size=size, font_name=font_name))
    return ins

def make_paragraph(style_name, *segments, ppr_extra=None):
    """
    Build a full <w:p> where every run is wrapped in <w:ins>.
    segments: list of (text, kwargs_dict) tuples
    The paragraph mark is also tracked via <w:pPr><w:rPr><w:ins/></w:rPr></w:pPr>.
    """
    p = OxmlElement("w:p")
    pPr = OxmlElement("w:pPr")

    if style_name:
        pStyle = OxmlElement("w:pStyle")
        pStyle.set(w("val"), style_name)
        pPr.append(pStyle)

    if ppr_extra:
        for el in ppr_extra:
            pPr.append(el)

    # Track the paragraph mark itself
    pRpr = OxmlElement("w:rPr")
    para_ins = OxmlElement("w:ins")
    para_ins.set(w("id"),     next_id())
    para_ins.set(w("author"), AUTHOR)
    para_ins.set(w("date"),   DATE)
    pRpr.append(para_ins)
    pPr.append(pRpr)

    p.append(pPr)

    for text, kwargs in segments:
        ins = make_ins_element()
        ins.append(make_run(text, **kwargs))
        p.append(ins)

    return p

def make_heading(level, text, badge=None):
    """H1=Heading1, H2=Heading2, H3=Heading3 — all tracked inserted."""
    style_map = {1: "Heading1", 2: "Heading2", 3: "Heading3"}
    segs = [(text, {})]
    if badge:
        segs.append(("  ", {}))
        segs.append((badge, {"bold": True, "color": "7B3F00"}))  # dark amber
    return make_paragraph(style_map[level], *segs)

def make_body_para(text, bold=False):
    return make_paragraph("Normal", (text, {"bold": bold}))

def make_cta_para(label, url):
    """→ Label: url  — styled as a distinct CTA line."""
    p = OxmlElement("w:p")
    pPr = OxmlElement("w:pPr")
    # Indent slightly
    ind = OxmlElement("w:ind")
    ind.set(w("left"), "360")
    pPr.append(ind)
    pRpr = OxmlElement("w:rPr")
    para_ins = OxmlElement("w:ins")
    para_ins.set(w("id"),     next_id())
    para_ins.set(w("author"), AUTHOR)
    para_ins.set(w("date"),   DATE)
    pRpr.append(para_ins)
    pPr.append(pRpr)
    p.append(pPr)

    arrow_ins = make_ins_element()
    arrow_ins.append(make_run("→ ", bold=True, color="1F5C99"))
    p.append(arrow_ins)

    label_ins = make_ins_element()
    label_ins.append(make_run(label, bold=True, color="1F5C99"))
    p.append(label_ins)

    sep_ins = make_ins_element()
    sep_ins.append(make_run(":  ", color="444444"))
    p.append(sep_ins)

    url_ins = make_ins_element()
    url_ins.append(make_run(url, italic=True, color="1F5C99"))
    p.append(url_ins)

    return p

def make_highlight_para(text, color_hex="E8F4F0", text_color="0A5C44"):
    """A shaded callout paragraph — used for CTA banners."""
    p = OxmlElement("w:p")
    pPr = OxmlElement("w:pPr")
    shd = OxmlElement("w:shd")
    shd.set(w("val"),   "clear")
    shd.set(w("color"), "auto")
    shd.set(w("fill"),  color_hex)
    pPr.append(shd)
    pRpr = OxmlElement("w:rPr")
    para_ins = OxmlElement("w:ins")
    para_ins.set(w("id"),     next_id())
    para_ins.set(w("author"), AUTHOR)
    para_ins.set(w("date"),   DATE)
    pRpr.append(para_ins)
    pPr.append(pRpr)
    p.append(pPr)

    ins = make_ins_element()
    ins.append(make_run(text, bold=True, color=text_color))
    p.append(ins)
    return p

def insert_paragraphs_after(body, ref_para_el, new_paras):
    """Insert list of <w:p> elements immediately after ref_para_el in body."""
    idx = list(body).index(ref_para_el)
    for i, np in enumerate(new_paras):
        body.insert(idx + 1 + i, np)

def append_run_to_para(para_el, text, bold=False, italic=False, color=None):
    """Add an inserted run to an existing paragraph (e.g. to add a badge)."""
    ins = make_ins_element()
    ins.append(make_run(" ", {}.__class__()))  # space spacer
    ins2 = make_ins_element()
    ins2.append(make_run(text, bold=bold, italic=italic, color=color))
    para_el.append(ins)
    para_el.append(ins2)


# ── Main ───────────────────────────────────────────────────────────────────────
def build():
    shutil.copy2(SRC, DST)
    doc = Document(DST)
    body = doc.element.body

    def find_para(text_fragment):
        for p in body.iterchildren(w("p")):
            full = "".join(t.text or "" for t in p.iter(w("t")))
            if text_fragment.lower() in full.lower():
                return p
        return None

    # ── 1. Intro: add one sentence tying model output to sportsbook comparison ─
    # Insert after the paragraph ending "...before and during games."
    intro_last = find_para("before and during games")
    if intro_last is not None:
        added_sentence = make_ins_element()
        added_sentence.append(make_run(
            " To get the most from these tools, compare what the model shows against "
            "the lines available at your sportsbook — that comparison is where value "
            "is found.",
            color="000000"
        ))
        intro_last.append(added_sentence)

    # ── 2. Sportsbook CTA banner — placed once, before tool listings ──────────
    explore_h2 = find_para("Explore Our Prediction Tools")
    if explore_h2 is not None:
        new_paras = [
            make_highlight_para(
                "Before you use any of these tools, find competitive lines to compare "
                "against. The Wizard's sportsbook guide rates hundreds of books on odds "
                "quality, market depth, and prop availability.",
                color_hex="E8F5E9", text_color="1A6B3C"
            ),
            make_cta_para(
                "Compare Sportsbooks at WizardOfOdds",
                "wizardofodds.com/online-sports-betting/"
            ),
        ]
        idx = list(body).index(explore_h2)
        for i, np in enumerate(new_paras):
            body.insert(idx + i, np)

    # ── 3. Market X-Ray heading: add CLV badge (proof point, not sport-specific)
    xray_h3 = find_para("Market X-Ray")
    if xray_h3 is not None:
        badge_ins = make_ins_element()
        badge_ins.append(make_run(
            "  [+10.9% Rolling CLV · 25 Markets Evaluated]",
            bold=True, color="7B3F00"
        ))
        xray_h3.append(badge_ins)

    # ── 4b. New section: Expanding Across Sports ──────────────────────────────
    # Placed after World Cup models, before "How to Use These Prediction Tools."
    # Describes all upcoming models in the same editorial voice — no links, no dates.
    how_to_h2 = find_para("How to Use These Prediction Tools")
    if how_to_h2 is not None:
        expansion_paras = [
            make_heading(2, "Expanding Across Sports"),
            make_body_para(
                "The prediction suite is being built out to cover a wider range of sports "
                "and market types. Each new model follows the same probability-based "
                "framework used across all the tools on this page — estimating full "
                "distributions of outcomes and comparing those distributions against "
                "sportsbook pricing to identify where model expectations differ from "
                "market-implied probabilities."
            ),
            make_heading(3, "NCAAB & NCAAW Team Totals and Margin of Victory Models"),
            make_body_para(
                "These models will produce full probability distributions over team totals "
                "and margin of victory for NCAA men's and women's basketball. Rather than "
                "projecting a single expected score, the models estimate the complete range "
                "of possible outcomes and how likely each one is, allowing structured "
                "comparison against totals, spreads, and team prop markets across both the "
                "men's and women's divisions."
            ),
            make_heading(3, "NBA Player Props Predictive Model"),
            make_body_para(
                "This model will estimate full probability mass functions over individual "
                "player statistical outcomes — points, rebounds, assists, and other target "
                "categories. Rather than producing a single projected stat line, it assigns "
                "a probability to every possible outcome count. Those probabilities are then "
                "compared directly against sportsbook over/under lines to measure the gap "
                "between model probability and market-implied probability."
            ),
            make_heading(3, "NFL Player Props Predictive Model"),
            make_body_para(
                "Following the same distribution-based approach as the NBA model, this "
                "system will estimate full PMF distributions for NFL player prop targets. "
                "Rushing yards, receiving yards, touchdowns, and other key stat categories "
                "will each be modelled as a probability distribution across the full range "
                "of possible outcomes, allowing direct and consistent comparison against "
                "posted lines across all available player markets."
            ),
            make_heading(3, "MLB Player Props Predictive Model"),
            make_body_para(
                "This model applies the same framework to baseball player props, covering "
                "categories such as strikeouts, hits, total bases, and runs. The output is "
                "a full probability distribution over each target stat, which is compared "
                "against sportsbook pricing in the same way as the basketball and football "
                "models. The goal is a consistent, sport-agnostic method for evaluating "
                "player prop markets across all major American sports."
            ),
            make_heading(3, "Soccer League Predictive Models"),
            make_body_para(
                "The joint score probability mass function framework developed for the "
                "World Cup will be extended to major domestic soccer leagues. Each model "
                "produces match-level probability distributions over home and away team "
                "totals, covering match result, both teams to score, over/under goal "
                "totals, and correct score markets. The same underlying model structure "
                "applies across competitions, keeping outputs consistent and comparable "
                "regardless of which league is being analysed."
            ),
            make_heading(3, "Tennis Set and Match Winner Predictive Model"),
            make_body_para(
                "This model will extend the existing tennis prediction framework to produce "
                "explicit probability estimates for set-by-set outcomes and match winners "
                "across professional tournaments. By modelling the full distribution of "
                "possible set scores rather than only the match result, it will provide a "
                "more granular view of match competitiveness and allow comparison against "
                "set betting and game spread markets in addition to outright winner lines."
            ),
            make_heading(3, "College Baseball Team Totals Model"),
            make_body_para(
                "This model will produce joint probability mass functions over team totals "
                "for college baseball games, providing a distribution-based view of run "
                "scoring for both teams. The joint PMF approach allows every possible "
                "combination of home and away run totals to be assigned a probability, "
                "from which over/under markets, run lines, and first-five-inning totals "
                "can be derived consistently from a single underlying distribution."
            ),
        ]
        idx = list(body).index(how_to_h2)
        for i, np in enumerate(expansion_paras):
            body.insert(idx + i, np)


    # The last "Why Use" paragraph ends "...where they don't."
    why_last = find_para("where things line up and where they don")
    if why_last is not None:
        insert_paragraphs_after(body, why_last, [
            make_cta_para(
                "Find the Best Sportsbooks for Your Sport at WizardOfOdds",
                "wizardofodds.com/online-sports-betting/"
            ),
        ])

    # ── 5. "Recommended Sportsbooks" section — general, timeless ─────────────
    play_resp = find_para("Play responsibly")
    if play_resp is not None:
        new_section = [
            make_heading(2, "Recommended Sportsbooks"),
            make_body_para(
                "The Wizard has evaluated hundreds of sportsbooks for odds quality, "
                "market depth across different sports, live betting availability, and "
                "payout reliability. The prediction tools on this page are most useful "
                "when you have access to competitive lines — these sportsbooks consistently "
                "rank highest on the metrics the models are designed to measure."
            ),
            make_cta_para(
                "See the Full Sportsbook Rankings at WizardOfOdds",
                "wizardofodds.com/online-sports-betting/"
            ),
            make_highlight_para(
                "Availability varies by region. Always check your local regulations "
                "before placing wagers.",
                color_hex="FFF8E7", text_color="7B3F00"
            ),
        ]
        idx = list(body).index(play_resp)
        for i, np in enumerate(new_section):
            body.insert(idx + i, np)

    # ── 6. Three new FAQ questions — sport-agnostic, conversion-focused ───────
    avail_para = find_para(
        "Availability may vary depending on the sport, event, and stage"
    )
    if avail_para is not None:
        new_faqs = [
            make_body_para(
                "Where can I bet on the sports covered by these tools?",
                bold=True
            ),
            make_body_para(
                "The Wizard's sportsbook comparison page lists the top-rated books "
                "across every major sport, rated on odds quality, market depth, and "
                "prop availability. The same criteria the models use to identify value "
                "are the criteria used to rank the books."
            ),
            make_cta_para(
                "Find the best sportsbook for your sport",
                "wizardofodds.com/online-sports-betting/"
            ),
            make_body_para(
                "How do I turn a model probability into a betting decision?",
                bold=True
            ),
            make_body_para(
                "Take the model's probability for an outcome and convert it to implied "
                "odds. If the sportsbook is offering a higher price than the model "
                "implies, the difference is your edge. A positive edge over many bets "
                "is what produces long-term value — not picking winners on individual "
                "games. The model output is the starting point; the sportsbook line is "
                "what you compare it against."
            ),
            make_body_para(
                "Do these tools cover all major sports?",
                bold=True
            ),
            make_body_para(
                "The suite currently covers football, basketball, tennis, soccer, and "
                "baseball, with models across professional and collegiate levels in "
                "development. Upcoming additions include player prop models for the NBA, "
                "NFL, and MLB, team total and margin models for NCAAB and NCAAW, a tennis "
                "set and match winner model, soccer league joint PMF models, and a college "
                "baseball team totals model. The underlying probability framework is the "
                "same across all sports — only the data inputs and calibration change. "
                "New tools will be added to this page as they become available."
            ),
        ]
        insert_paragraphs_after(body, avail_para, new_faqs)

    # ── 7. Flag the FAQ heading formatting bug (internal note, red) ──────────
    free_tools_h = find_para("Are these tools free to use?")
    if free_tools_h is not None:
        note_ins = make_ins_element()
        note_ins.append(make_run(
            "  [FORMATTING NOTE: This FAQ entry is styled as Heading 2 — "
            "change to Normal/Body style to match the other FAQ questions]",
            italic=True, color="CC0000"
        ))
        free_tools_h.append(note_ins)

    # ── Save ──────────────────────────────────────────────────────────────────
    doc.save(DST)
    print(f"  ✓  Saved: {DST}")

    final_path = None
    for root, dirs, files in os.walk('/Users/josephshackelford/Desktop'):
        for f in files:
            if 'sports prediction tools powered' in f.lower():
                final_path = os.path.join(
                    root,
                    "Sports Prediction Tools Powered by Probability Models [TRACKED].docx"
                )
                break
        if final_path:
            break

    if final_path:
        shutil.copy2(DST, final_path)
        print(f"  ✓  Copied: {final_path}")
    return final_path or DST

    # ── 1. Before "Explore Our Prediction Tools":
    #    a) Sportsbook CTA banner (live — wizardofodds.com/online-sports-betting/ exists)
    #    b) NOTE about the live-edges widget needing dev work before publish
    explore_h2 = find_para("Explore Our Prediction Tools")
    if explore_h2 is not None:
        new_paras = [
            make_dev_note_para(
                "The 'Today's Top Model Edges' live widget (showing real-time BET/LEAN "
                "signals from wc-xray.json) is a high-value conversion element but requires "
                "a JavaScript fetch() implementation before it can go live. "
                "Do not publish this section until the widget is built and tested. "
                "Once built, place it here — directly above the tool listings."
            ),
            make_highlight_para(
                "Before You Bet — Compare Lines at the Wizard's Recommended Sportsbooks",
                color_hex="E8F5E9", text_color="1A6B3C"
            ),
            make_body_para(
                "The tools show you where the value is. The sportsbooks below are where "
                "you act on it. The Wizard's sportsbook guide rates each book on odds "
                "quality, market depth, and prop availability — the same factors the "
                "models measure."
            ),
            make_cta_para(
                "Compare Sportsbooks at WizardOfOdds",
                "wizardofodds.com/online-sports-betting/"
            ),
        ]
        idx = list(body).index(explore_h2)
        for i, np in enumerate(new_paras):
            body.insert(idx + i, np)

    # ── 2. Badge on Market X-Ray heading (performance stat, not a link — safe) ─
    xray_h3 = find_para("Market X-Ray")
    if xray_h3 is not None:
        space_ins = make_ins_element()
        space_ins.append(make_run("  ", {}.__class__()))
        badge_ins = make_ins_element()
        badge_ins.append(make_run(
            "[+10.9% Rolling CLV · 25 Markets Evaluated]",
            bold=True, color="7B3F00"
        ))
        xray_h3.append(space_ins)
        xray_h3.append(badge_ins)

    # ── 3. CTAs after Market X-Ray (LIVE page) ────────────────────────────────
    clv_para = find_para("Consistent positive CLV is used as a long-term")
    if clv_para is not None:
        insert_paragraphs_after(body, clv_para, [
            make_cta_para(
                "Launch Market X-Ray",
                "wizardofodds.com/sports-odds/world-cup-market-xray/"
            ),
            make_cta_para(
                "Compare Sportsbook Lines",
                "wizardofodds.com/online-sports-betting/"
            ),
        ])

    # ── 4. CTAs after WNBA (ALL THREE pages are LIVE) ─────────────────────────
    wnba_last = find_para(
        "objective is not exact prediction of results, but identification"
    )
    if wnba_last is not None:
        insert_paragraphs_after(body, wnba_last, [
            make_cta_para(
                "WNBA Pre-Game Edge Board",
                "wizardofodds.com/sports-odds/wnba-predictions/"
            ),
            make_cta_para(
                "WNBA PMF Distributions",
                "wizardofodds.com/sports-odds/wnba-distributions/"
            ),
            make_cta_para(
                "WNBA Live Edges",
                "wizardofodds.com/sports-odds/wnba-live-edges/"
            ),
            make_cta_para(
                "Best WNBA Prop Sportsbooks",
                "wizardofodds.com/online-sports-betting/"
            ),
        ])

    # ── 5. NFL/College Football — tool page doesn't exist yet.
    #    Link to existing WoO NFL/CFB pages (real). No prediction tool CTA. ────
    nfl_last = find_para(
        "This allows for a more stable and consistent view of team strength"
    )
    if nfl_last is not None:
        insert_paragraphs_after(body, nfl_last, [
            make_cta_para(
                "NFL Betting Guide",
                "wizardofodds.com/games/sports-betting/nfl/"
            ),
            make_cta_para(
                "College Football Betting Guide",
                "wizardofodds.com/games/sports-betting/college-football/"
            ),
            make_coming_soon_para(
                "NFL & College Football Prediction Tool",
                note="The interactive ranking and spread tool is in development."
            ),
        ])

    # ── 6. Tennis — tool doesn't exist. "Coming soon" only. ──────────────────
    tennis_last = find_para(
        "consistent framework for understanding both expected results"
    )
    if tennis_last is not None:
        insert_paragraphs_after(body, tennis_last, [
            make_coming_soon_para(
                "Tennis Prediction Tool",
                note="Pre-match and live tennis model — in development."
            ),
            make_cta_para(
                "Tennis Betting Guide",
                "wizardofodds.com/online-sports-betting/"
            ),
        ])

    # ── 7. Full Outcome PMF — no WoO shell page yet. "Coming soon." ───────────
    pmf_last = find_para(
        "unified approach produces a complete, internally consistent probabilistic"
    )
    if pmf_last is not None:
        insert_paragraphs_after(body, pmf_last, [
            make_dev_note_para(
                "The WoO shell page for this tool "
                "(wizardofodds.com/sports-odds/world-cup-2026-predictions/probability-model/) "
                "does not exist yet. Build deploy/pages/world-cup-pmf.html before linking here."
            ),
            make_coming_soon_para(
                "World Cup PMF Distributions page",
                note="Shell page needs to be built before this link goes live."
            ),
            make_cta_para(
                "Best World Cup Betting Sites",
                "wizardofodds.com/online-sports-betting/"
            ),
        ])

    # ── 8. Today's WC Predictions — no WoO shell page yet ────────────────────
    wcp_last = find_para(
        "transparent view of the model's expectations for each match"
    )
    if wcp_last is not None:
        insert_paragraphs_after(body, wcp_last, [
            make_dev_note_para(
                "The WoO shell page for Today's World Cup Predictions "
                "(wizardofodds.com/sports-odds/world-cup-2026-predictions/) "
                "does not exist yet. Build deploy/pages/world-cup-predictions.html first."
            ),
            make_coming_soon_para(
                "Today's World Cup Predictions page",
                note="Shell page needs to be built before this link goes live."
            ),
            make_cta_para(
                "World Cup Odds & Sportsbooks",
                "wizardofodds.com/online-sports-betting/"
            ),
        ])

    # ── 9. Live PMF Engine — no WoO shell page yet ────────────────────────────
    livepmf_last = find_para(
        "translates live match conditions into a full probabilistic forecast"
    )
    if livepmf_last is not None:
        insert_paragraphs_after(body, livepmf_last, [
            make_dev_note_para(
                "The WoO shell page for the Live PMF Engine "
                "(wizardofodds.com/sports-odds/world-cup-2026-predictions/live/) "
                "does not exist yet. Build deploy/pages/world-cup-live-pmf.html first."
            ),
            make_coming_soon_para(
                "Live PMF Engine page",
                note="Shell page needs to be built before this link goes live."
            ),
            make_cta_para(
                "Live Betting Sportsbooks",
                "wizardofodds.com/online-sports-betting/"
            ),
        ])

    # ── 10. Live Pitch — no WoO shell page yet ───────────────────────────────
    pitch_last = find_para("what are the most likely outcomes")
    if pitch_last is not None:
        insert_paragraphs_after(body, pitch_last, [
            make_dev_note_para(
                "The WoO shell page for the Live Pitch "
                "(wizardofodds.com/sports-odds/world-cup-2026-predictions/live-pitch/) "
                "does not exist yet. Build deploy/pages/world-cup-live-pitch.html first."
            ),
            make_coming_soon_para(
                "World Cup Live Pitch page",
                note="Shell page needs to be built before this link goes live."
            ),
            make_cta_para(
                "World Cup Live Betting",
                "wizardofodds.com/online-sports-betting/"
            ),
        ])

    # ── 11. "Recommended Sportsbooks" section before "Play responsibly!" ──────
    #    Uses only the main /online-sports-betting/ URL which is live.
    play_resp = find_para("Play responsibly")
    if play_resp is not None:
        new_section = [
            make_heading(2, "Recommended Sportsbooks"),
            make_body_para(
                "The Wizard has evaluated hundreds of sportsbooks for odds quality, "
                "prop market depth, live betting availability, and payout reliability. "
                "The tools on this page are most useful when you have access to "
                "competitive lines — the sportsbooks below consistently rank highest "
                "on the metrics the model measures."
            ),
            make_highlight_para(
                "Availability varies by region. Always check local regulations before "
                "placing wagers.",
                color_hex="FFF8E7", text_color="7B3F00"
            ),
            make_cta_para(
                "See the Full Sportsbook Rankings at WizardOfOdds",
                "wizardofodds.com/online-sports-betting/"
            ),
        ]
        idx = list(body).index(play_resp)
        for i, np in enumerate(new_section):
            body.insert(idx + i, np)

    # ── 12. 3 new FAQ questions — only link to live pages ────────────────────
    avail_para = find_para(
        "Availability may vary depending on the sport, event, and stage"
    )
    if avail_para is not None:
        new_faqs = [
            make_body_para(
                "Where can I bet on World Cup 2026 matches?",
                bold=True
            ),
            make_body_para(
                "The Wizard's sportsbook guide lists the top-rated books for World Cup "
                "betting, rated on odds quality, market depth, and reliability."
            ),
            make_cta_para(
                "View World Cup sportsbook recommendations",
                "wizardofodds.com/online-sports-betting/"
            ),
            make_body_para(
                "Which sportsbooks offer the best player prop markets?",
                bold=True
            ),
            make_body_para(
                "Prop market depth varies significantly between books. The Wizard's "
                "sportsbook comparison page ranks books specifically on prop availability "
                "and line quality."
            ),
            make_cta_para(
                "Find the best prop sportsbooks",
                "wizardofodds.com/online-sports-betting/"
            ),
            make_body_para(
                "How do I use these model outputs to identify value bets?",
                bold=True
            ),
            make_body_para(
                "Start with any tool's model probability for an outcome, then compare "
                "it to the implied probability from your sportsbook's odds. When the "
                "model's probability is meaningfully higher than the market-implied "
                "probability, that difference is the edge. The Market X-Ray tool does "
                "this comparison automatically across all available markets."
            ),
            make_cta_para(
                "Launch Market X-Ray",
                "wizardofodds.com/sports-odds/world-cup-market-xray/"
            ),
        ]
        insert_paragraphs_after(body, avail_para, new_faqs)

    # ── 13. Flag the "Are these tools free?" heading-style bug ───────────────
    free_tools_h = find_para("Are these tools free to use?")
    if free_tools_h is not None:
        note_ins = make_ins_element()
        note_ins.append(make_run(
            "  [FORMATTING NOTE: This FAQ entry is styled as Heading 2 — "
            "should be Normal/Body style to match the other FAQ questions above it]",
            italic=True, color="CC0000"
        ))
        free_tools_h.append(note_ins)

    # ── Save ──────────────────────────────────────────────────────────────────
    doc.save(DST)
    print(f"  ✓  Saved: {DST}")

    # Find original folder via os.walk to get exact bytes of path
    final_path = None
    for root, dirs, files in os.walk('/Users/josephshackelford/Desktop'):
        for f in files:
            if 'sports prediction tools powered' in f.lower():
                final_path = os.path.join(
                    root,
                    "Sports Prediction Tools Powered by Probability Models [TRACKED].docx"
                )
                break
        if final_path:
            break

    if final_path:
        shutil.copy2(DST, final_path)
        print(f"  ✓  Copied: {final_path}")
    return final_path or DST

    # ── 1. Add "Today's Top Model Edges" + sportsbook banner
    #    After the last intro paragraph (before "Explore Our Prediction Tools")
    explore_h2 = find_para("Explore Our Prediction Tools")
    if explore_h2 is not None:
        new_paras = [
            # --- Today's Top Model Edges section ---
            make_heading(2, "Today's Top Model Edges"),
            make_body_para(
                "Place this live widget immediately after the opening paragraph — "
                "before the tools list. It shows users proof of model value instantly, "
                "driving both tool engagement and sportsbook referral clicks."
            ),
            make_body_para(
                "Implementation: JavaScript fetch() against wc-xray.json "
                "(?t=Date.now() cache-bust). Display the top 3 current BET/LEAN signals "
                "in a compact table: Match | Model Prob | Market Implied | Edge | Signal. "
                "Each row links to the relevant tool page. Falls back to a static "
                "'Check back on match days' message when no live data is available."
            ),
            # --- Sportsbook CTA Banner ---
            make_highlight_para(
                "Before You Bet — Compare Lines at the Wizard's Recommended Sportsbooks",
                color_hex="E8F5E9", text_color="1A6B3C"
            ),
            make_body_para(
                "The tools show you where the value is. The sportsbooks below are where "
                "you act on it. The Wizard's sportsbook guide rates each book on odds "
                "quality, market depth, and prop availability — the same factors the "
                "models measure."
            ),
            make_cta_para(
                "Compare Sportsbooks at WizardOfOdds",
                "wizardofodds.com/online-sports-betting/"
            ),
        ]
        # Insert before the "Explore Our Prediction Tools" heading
        idx = list(body).index(explore_h2)
        for i, np in enumerate(new_paras):
            body.insert(idx + i, np)

    # ── 2. Add performance badge to Market X-Ray heading ──────────────────────
    xray_h3 = find_para("Market X-Ray")
    if xray_h3 is not None:
        # Add inserted badge run to existing heading paragraph
        space_ins = make_ins_element()
        space_ins.append(make_run("  ", {}.__class__()))
        badge_ins = make_ins_element()
        badge_ins.append(make_run(
            "[+10.9% Rolling CLV · 25 Markets Evaluated]",
            bold=True, color="7B3F00"
        ))
        xray_h3.append(space_ins)
        xray_h3.append(badge_ins)

    # ── 3. Add CTA after Market X-Ray section ─────────────────────────────────
    #    The last paragraph of Market X-Ray is about "consistent positive CLV"
    clv_para = find_para("Consistent positive CLV is used as a long-term")
    if clv_para is not None:
        insert_paragraphs_after(body, clv_para, [
            make_cta_para(
                "Launch Market X-Ray",
                "wizardofodds.com/sports-odds/world-cup-market-xray/"
            ),
            make_cta_para(
                "Compare Sportsbook Lines",
                "wizardofodds.com/online-sports-betting/"
            ),
        ])

    # ── 4. Add CTAs after WNBA section ────────────────────────────────────────
    wnba_last = find_para(
        "objective is not exact prediction of results, but identification"
    )
    if wnba_last is not None:
        insert_paragraphs_after(body, wnba_last, [
            make_cta_para(
                "WNBA Pre-Game Edge Board",
                "wizardofodds.com/sports-odds/wnba-predictions/"
            ),
            make_cta_para(
                "WNBA PMF Distributions",
                "wizardofodds.com/sports-odds/wnba-distributions/"
            ),
            make_cta_para(
                "WNBA Live Edges",
                "wizardofodds.com/sports-odds/wnba-live-edges/"
            ),
            make_cta_para(
                "Best WNBA Prop Sportsbooks",
                "wizardofodds.com/online-sports-betting/"
            ),
        ])

    # ── 5. Add CTAs after NFL/College Football section ────────────────────────
    nfl_last = find_para(
        "This allows for a more stable and consistent view of team strength"
    )
    if nfl_last is not None:
        insert_paragraphs_after(body, nfl_last, [
            make_cta_para(
                "NFL Rankings & Predictions",
                "wizardofodds.com/games/sports-betting/nfl/"
            ),
            make_cta_para(
                "College Football Predictions",
                "wizardofodds.com/games/sports-betting/college-football/"
            ),
            make_cta_para(
                "Best NFL Sportsbooks",
                "wizardofodds.com/online-sports-betting/"
            ),
        ])

    # ── 6. Add CTA after Tennis section ──────────────────────────────────────
    tennis_last = find_para(
        "consistent framework for understanding both expected results"
    )
    if tennis_last is not None:
        insert_paragraphs_after(body, tennis_last, [
            make_cta_para(
                "Best Tennis Betting Sites",
                "wizardofodds.com/online-sports-betting/"
            ),
        ])

    # ── 7. Add CTAs after Full Outcome PMF section ────────────────────────────
    pmf_last = find_para(
        "unified approach produces a complete, internally consistent probabilistic"
    )
    if pmf_last is not None:
        insert_paragraphs_after(body, pmf_last, [
            make_cta_para(
                "View World Cup PMF Distributions",
                "wizardofodds.com/sports-odds/world-cup-2026-predictions/probability-model/"
            ),
            make_cta_para(
                "Best World Cup Betting Sites",
                "wizardofodds.com/online-sports-betting/"
            ),
        ])

    # ── 8. Add CTAs after Today's World Cup Predictions section ──────────────
    wcp_last = find_para(
        "transparent view of the model's expectations for each match"
    )
    if wcp_last is not None:
        insert_paragraphs_after(body, wcp_last, [
            make_cta_para(
                "Today's World Cup Predictions",
                "wizardofodds.com/sports-odds/world-cup-2026-predictions/"
            ),
            make_cta_para(
                "World Cup Odds & Sportsbooks",
                "wizardofodds.com/online-sports-betting/"
            ),
        ])

    # ── 9. Add CTAs after Live PMF Engine section ─────────────────────────────
    livepmf_last = find_para(
        "translates live match conditions into a full probabilistic forecast"
    )
    if livepmf_last is not None:
        insert_paragraphs_after(body, livepmf_last, [
            make_cta_para(
                "Launch Live PMF Engine",
                "wizardofodds.com/sports-odds/world-cup-2026-predictions/live/"
            ),
            make_cta_para(
                "Live Betting Sportsbooks",
                "wizardofodds.com/online-sports-betting/"
            ),
        ])

    # ── 10. Add CTAs after Live Pitch section ─────────────────────────────────
    pitch_last = find_para(
        "what are the most likely outcomes"
    )
    if pitch_last is not None:
        insert_paragraphs_after(body, pitch_last, [
            make_cta_para(
                "Launch World Cup Live Pitch",
                "wizardofodds.com/sports-odds/world-cup-2026-predictions/live-pitch/"
            ),
            make_cta_para(
                "World Cup Live Betting",
                "wizardofodds.com/online-sports-betting/"
            ),
        ])

    # ── 11. Add "Recommended Sportsbooks" section before "Play responsibly!" ──
    play_resp = find_para("Play responsibly")
    if play_resp is not None:
        new_section = [
            make_heading(2, "Recommended Sportsbooks"),
            make_body_para(
                "The Wizard has evaluated hundreds of sportsbooks for odds quality, "
                "prop market depth, live betting availability, and payout reliability. "
                "The tools on this page are most useful when you have access to "
                "competitive lines — the sportsbooks below consistently rank highest "
                "on the metrics the model measures."
            ),
            make_highlight_para(
                "Availability varies by region. Always check local regulations before "
                "placing wagers.",
                color_hex="FFF8E7", text_color="7B3F00"
            ),
            make_cta_para(
                "See the Full Sportsbook Rankings at WizardOfOdds",
                "wizardofodds.com/online-sports-betting/"
            ),
        ]
        idx = list(body).index(play_resp)
        for i, np in enumerate(new_section):
            body.insert(idx + i, np)

    # ── 12. Add 3 new FAQ questions at the end ────────────────────────────────
    #    Find the last paragraph of the document's FAQ section
    avail_para = find_para(
        "Availability may vary depending on the sport, event, and stage"
    )
    if avail_para is not None:
        new_faqs = [
            # Q9
            make_body_para(
                "Where can I bet on World Cup 2026 matches?",
                bold=True
            ),
            make_body_para(
                "The Wizard's sportsbook guide lists the top-rated books for World Cup "
                "betting, rated on odds quality, market depth, and reliability."
            ),
            make_cta_para(
                "View World Cup sportsbook recommendations",
                "wizardofodds.com/online-sports-betting/"
            ),
            # Q10
            make_body_para(
                "Which sportsbooks offer the best player prop markets?",
                bold=True
            ),
            make_body_para(
                "Prop market depth varies significantly between books. The Wizard's "
                "sportsbook comparison page ranks books specifically on prop availability "
                "and line quality."
            ),
            make_cta_para(
                "Find the best prop sportsbooks",
                "wizardofodds.com/online-sports-betting/"
            ),
            # Q11
            make_body_para(
                "How do I use these model outputs to identify value bets?",
                bold=True
            ),
            make_body_para(
                "Start with any tool's model probability for an outcome, then compare "
                "it to the implied probability from your sportsbook's odds. When the "
                "model's probability is meaningfully higher than the market-implied "
                "probability, that difference is the edge. The Market X-Ray tool does "
                "this comparison automatically across all available markets."
            ),
            make_cta_para(
                "Launch Market X-Ray",
                "wizardofodds.com/sports-odds/world-cup-market-xray/"
            ),
        ]
        insert_paragraphs_after(body, avail_para, new_faqs)

    # ── 13. Fix: "Are these tools free to use?" is styled as Heading 2 — flag it
    #    Add an inserted comment-like note by appending an inserted run to that para
    free_tools_h = find_para("Are these tools free to use?")
    if free_tools_h is not None:
        note_ins = make_ins_element()
        note_ins.append(make_run(
            "  [NOTE: This FAQ entry appears as a Heading 2 — should be Normal style "
            "to match other FAQ questions]",
            italic=True, color="FF0000"
        ))
        free_tools_h.append(note_ins)

    # ── Save ──────────────────────────────────────────────────────────────────
    doc.save(DST)
    print(f"  ✓  Saved: {DST}")

    # Copy back to original folder
    os.makedirs(DEST_FOLDER, exist_ok=True)
    final_path = os.path.join(
        DEST_FOLDER,
        "Sports Prediction Tools Powered by Probability Models [TRACKED].docx"
    )
    shutil.copy2(DST, final_path)
    print(f"  ✓  Copied: {final_path}")
    return final_path


if __name__ == "__main__":
    print("Building tracked-changes Word document …")
    p = build()
    print(f"\nFile ready: {p}")
