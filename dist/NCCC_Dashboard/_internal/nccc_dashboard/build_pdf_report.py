import json, time, math
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
from reportlab.pdfgen import canvas as rl_canvas

# ─────────────────────────────────────────────
# COLOUR PALETTE
# ─────────────────────────────────────────────
DARK_NAVY   = colors.HexColor("#0D1B2A")
MID_NAVY    = colors.HexColor("#1B2A3B")
ACCENT_BLUE = colors.HexColor("#1E6FA8")
ACCENT_CYAN = colors.HexColor("#00B4D8")
ACCENT_RED  = colors.HexColor("#E63946")
ACCENT_AMBER= colors.HexColor("#F4A261")
LIGHT_GREY  = colors.HexColor("#F0F4F8")
MID_GREY    = colors.HexColor("#8D99AE")
WHITE       = colors.white
BLACK       = colors.black

CHART_COLORS = ["#1E6FA8","#00B4D8","#E63946","#F4A261","#2A9D8F",
                "#E9C46A","#264653","#A8DADC","#457B9D","#F1FAEE"]

PAGE_W, PAGE_H = A4
MARGIN = 1.5 * cm

# ─────────────────────────────────────────────
# HEADER / FOOTER CANVAS
# ─────────────────────────────────────────────
def header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4

    # Top bar
    canvas.setFillColor(DARK_NAVY)
    canvas.rect(0, h - 18*mm, w, 18*mm, fill=1, stroke=0)

    canvas.setFillColor(ACCENT_CYAN)
    canvas.rect(0, h - 19.5*mm, w, 1.5*mm, fill=1, stroke=0)

    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(WHITE)
    canvas.drawString(MARGIN, h - 12*mm, "NCCC- TRAFFIC MONITORING & ANALYSIS REPORT")

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(ACCENT_CYAN)
    canvas.drawRightString(w - MARGIN, h - 12*mm, "RESTRICTED // OFFICIAL USE ONLY")

    # Bottom bar
    canvas.setFillColor(DARK_NAVY)
    canvas.rect(0, 0, w, 10*mm, fill=1, stroke=0)
    canvas.setFillColor(ACCENT_CYAN)
    canvas.rect(0, 10*mm, w, 0.8*mm, fill=1, stroke=0)

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MID_GREY)
    ts = time.strftime("%d %B %Y  |  %H:%M UTC")
    canvas.drawString(MARGIN, 3.5*mm, f"Generated: {ts}")
    canvas.drawCentredString(w/2, 3.5*mm, "National Command & Control Centre — Cyber")
    canvas.drawRightString(w - MARGIN, 3.5*mm, f"Page {doc.page}")

    canvas.restoreState()


# ─────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()

    def S(name, **kw):
        return ParagraphStyle(name, **kw)

    return {
        "cover_title": S("cover_title",
            fontSize=32, textColor=WHITE, fontName="Helvetica-Bold",
            alignment=TA_CENTER, leading=38, spaceAfter=6),

        "cover_sub": S("cover_sub",
            fontSize=13, textColor=ACCENT_CYAN, fontName="Helvetica",
            alignment=TA_CENTER, leading=18),

        "section_label": S("section_label",
            fontSize=7, textColor=ACCENT_CYAN, fontName="Helvetica-Bold",
            spaceBefore=14, spaceAfter=2, letterSpacing=2),

        "h1": S("h1",
            fontSize=16, textColor=DARK_NAVY, fontName="Helvetica-Bold",
            spaceBefore=4, spaceAfter=4, leading=20),

        "h2": S("h2",
            fontSize=11, textColor=ACCENT_BLUE, fontName="Helvetica-Bold",
            spaceBefore=10, spaceAfter=4, leading=14),

        "body": S("body",
            fontSize=9, textColor=colors.HexColor("#2C3E50"), fontName="Helvetica",
            leading=13, spaceAfter=4, alignment=TA_JUSTIFY),

        "kpi_value": S("kpi_value",
            fontSize=22, textColor=ACCENT_BLUE, fontName="Helvetica-Bold",
            alignment=TA_CENTER, leading=26),

        "kpi_label": S("kpi_label",
            fontSize=7, textColor=MID_GREY, fontName="Helvetica",
            alignment=TA_CENTER, leading=9),

        "table_header": S("table_header",
            fontSize=8, textColor=WHITE, fontName="Helvetica-Bold",
            alignment=TA_CENTER),

        "table_cell": S("table_cell",
            fontSize=8, textColor=DARK_NAVY, fontName="Helvetica",
            alignment=TA_LEFT),

        "caption": S("caption",
            fontSize=7, textColor=MID_GREY, fontName="Helvetica",
            alignment=TA_CENTER, spaceAfter=8),

        "bullet": S("bullet",
            fontSize=9, textColor=colors.HexColor("#2C3E50"), fontName="Helvetica",
            leading=14, leftIndent=14, spaceAfter=3),

        "severity_high": S("sev_h",
            fontSize=8, textColor=WHITE, fontName="Helvetica-Bold",
            alignment=TA_CENTER),

        "toc_entry": S("toc",
            fontSize=9, textColor=DARK_NAVY, fontName="Helvetica", leading=14),
    }


# ─────────────────────────────────────────────
# CHART HELPERS
# ─────────────────────────────────────────────
def save_chart(fig, path):
    fig.patch.set_facecolor("#F7F9FC")
    fig.savefig(path, bbox_inches="tight", dpi=140, facecolor=fig.get_facecolor())
    plt.close(fig)


def chart_hourly(hours: dict, path):
    x = list(range(24))
    y = [hours.get(str(i), 0) for i in x]

    fig, ax = plt.subplots(figsize=(5, 2.4))
    fig.patch.set_facecolor("#F7F9FC")
    ax.set_facecolor("#F7F9FC")

    bar_colors = [CHART_COLORS[2] if v == max(y) else CHART_COLORS[0] for v in y]
    bars = ax.bar(x, y, color=bar_colors, width=0.7, zorder=3)
    ax.set_xticks(range(0, 24, 2))
    ax.set_xticklabels([f"{i:02d}h" for i in range(0, 24, 2)], fontsize=6)
    ax.yaxis.set_tick_params(labelsize=6)
    ax.set_title("Attack Volume by Hour (UTC)", fontsize=8, fontweight="bold", pad=6)
    ax.set_xlabel("Hour", fontsize=6)
    ax.set_ylabel("Events", fontsize=6)
    ax.grid(axis="y", linestyle="--", alpha=0.5, zorder=0)
    ax.spines[["top","right"]].set_visible(False)

    peak = max(y)
    peak_h = y.index(peak)
    ax.annotate(f"Peak\n{peak:,}", xy=(peak_h, peak),
                xytext=(peak_h + 1.5, peak * 0.85),
                fontsize=6, color="#E63946",
                arrowprops=dict(arrowstyle="->", color="#E63946", lw=0.8))

    save_chart(fig, path)


def chart_protocol(proto: dict, path):
    labels = list(proto.keys())
    vals   = list(proto.values())
    explode = [0.04] * len(vals)

    fig, ax = plt.subplots(figsize=(3.8, 2.6))
    fig.patch.set_facecolor("#F7F9FC")
    ax.set_facecolor("#F7F9FC")

    wedges, texts, autotexts = ax.pie(
        vals, labels=None, autopct="%1.1f%%",
        colors=CHART_COLORS[:len(vals)],
        explode=explode, startangle=140,
        textprops={"fontsize": 7},
        pctdistance=0.75, wedgeprops={"linewidth": 0.5, "edgecolor": "white"}
    )
    for at in autotexts:
        at.set_fontsize(6.5)
        at.set_color("white")
        at.set_fontweight("bold")

    ax.legend(wedges, labels, loc="lower center", bbox_to_anchor=(0.5, -0.22),
              ncol=3, fontsize=6.5, frameon=False)
    ax.set_title("Protocol Distribution", fontsize=8, fontweight="bold", pad=6)
    save_chart(fig, path)


def chart_countries(countries: dict, path):
    items = sorted(countries.items(), key=lambda x: x[1], reverse=True)[:8]
    labels = [k for k, _ in items]
    vals   = [v for _, v in items]

    fig, ax = plt.subplots(figsize=(5, 2.6))
    fig.patch.set_facecolor("#F7F9FC")
    ax.set_facecolor("#F7F9FC")

    cmap = plt.colormaps.get_cmap("RdYlGn_r")
    bar_cols = [matplotlib_color(cmap(i / max(len(vals)-1, 1))) for i in range(len(vals))]

    bars = ax.barh(labels[::-1], vals[::-1], color=bar_cols[::-1], height=0.55, zorder=3)
    ax.set_xlabel("Event Count", fontsize=6)
    ax.set_title("Top Attacker Countries (external)", fontsize=8, fontweight="bold", pad=6)
    ax.xaxis.set_tick_params(labelsize=6)
    ax.yaxis.set_tick_params(labelsize=7)
    ax.grid(axis="x", linestyle="--", alpha=0.5, zorder=0)
    ax.spines[["top","right","left"]].set_visible(False)

    for bar, val in zip(bars, vals[::-1]):
        ax.text(bar.get_width() + max(vals)*0.01, bar.get_y() + bar.get_height()/2,
                f"{val:,}", va="center", fontsize=6, color="#2C3E50")

    save_chart(fig, path)


def matplotlib_color(rgba):
    return rgba  # matplotlib already returns compatible tuple


def chart_top_ips(ips: dict, path):
    items = sorted(ips.items(), key=lambda x: x[1], reverse=True)[:10]
    labels = [k for k, _ in items]
    vals   = [v for _, v in items]

    fig, ax = plt.subplots(figsize=(5, 2.8))
    fig.patch.set_facecolor("#F7F9FC")
    ax.set_facecolor("#F7F9FC")

    bars = ax.barh(labels[::-1], vals[::-1],
                   color=CHART_COLORS[0], height=0.55, zorder=3)
    bars[len(bars)-1].set_color(CHART_COLORS[2])  # highlight top IP

    ax.set_xlabel("Hit Count", fontsize=6)
    ax.set_title("Top 10 Source IPs by Event Count", fontsize=8, fontweight="bold", pad=6)
    ax.xaxis.set_tick_params(labelsize=6)
    ax.yaxis.set_tick_params(labelsize=6.5)
    ax.grid(axis="x", linestyle="--", alpha=0.5, zorder=0)
    ax.spines[["top","right","left"]].set_visible(False)

    for bar, val in zip(bars, vals[::-1]):
        ax.text(bar.get_width() + max(vals)*0.01, bar.get_y() + bar.get_height()/2,
                f"{val:,}", va="center", fontsize=6)

    save_chart(fig, path)


def chart_timeline(timeline: dict, path):
    if not timeline:
        return False
    items = sorted(timeline.items())[-14:]  # last 14 days
    labels = [k for k, _ in items]
    vals   = [v for _, v in items]

    fig, ax = plt.subplots(figsize=(10.5, 2.2))
    fig.patch.set_facecolor("#F7F9FC")
    ax.set_facecolor("#F7F9FC")

    ax.fill_between(range(len(vals)), vals, alpha=0.25, color=CHART_COLORS[0])
    ax.plot(range(len(vals)), vals, color=CHART_COLORS[0], lw=1.8, marker="o",
            markersize=3.5, zorder=3)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=6)
    ax.yaxis.set_tick_params(labelsize=6)
    ax.set_title("Daily Attack Trend", fontsize=8, fontweight="bold", pad=6)
    ax.set_ylabel("Events", fontsize=6)
    ax.grid(axis="y", linestyle="--", alpha=0.5, zorder=0)
    ax.spines[["top","right"]].set_visible(False)
    save_chart(fig, path)
    return True


def chart_units(unit_data: dict, path):
    items = sorted(unit_data.items(), key=lambda x: x[1], reverse=True)[:8]
    labels = [k for k, _ in items]
    vals   = [v for _, v in items]

    fig, ax = plt.subplots(figsize=(5, 2.6))
    fig.patch.set_facecolor("#F7F9FC")
    ax.set_facecolor("#F7F9FC")

    bars = ax.bar(labels, vals,
                  color=[CHART_COLORS[i % len(CHART_COLORS)] for i in range(len(vals))],
                  width=0.55, zorder=3)
    ax.set_xticklabels(labels, rotation=25, ha="right", fontsize=6.5)
    ax.yaxis.set_tick_params(labelsize=6)
    ax.set_title("Events by Targeted Unit", fontsize=8, fontweight="bold", pad=6)
    ax.set_ylabel("Events", fontsize=6)
    ax.grid(axis="y", linestyle="--", alpha=0.5, zorder=0)
    ax.spines[["top","right"]].set_visible(False)
    save_chart(fig, path)


# ─────────────────────────────────────────────
# SECTION DIVIDER
# ─────────────────────────────────────────────
def section_heading(label, title, styles):
    return [
        Paragraph(label.upper(), styles["section_label"]),
        Paragraph(title, styles["h1"]),
        HRFlowable(width="100%", thickness=1.5, color=ACCENT_BLUE,
                   spaceAfter=6, spaceBefore=0),
    ]


# ─────────────────────────────────────────────
# KPI CARDS (row of 4)
# ─────────────────────────────────────────────
def kpi_row(metrics, styles):
    """metrics = list of (value, label, color_hex)"""
    cells = []
    for val, label, hex_col in metrics:
        inner = Table(
            [[Paragraph(str(val), styles["kpi_value"])],
             [Paragraph(label,    styles["kpi_label"])]],
            colWidths=[None]
        )
        inner.setStyle(TableStyle([
            ("ALIGN",    (0,0),(-1,-1),"CENTER"),
            ("VALIGN",   (0,0),(-1,-1),"MIDDLE"),
            ("TOPPADDING",(0,0),(-1,-1),10),
            ("BOTTOMPADDING",(0,0),(-1,-1),10),
            ("BACKGROUND",(0,0),(-1,-1), colors.HexColor("#EBF4FB")),
            ("LINEABOVE", (0,0),(-1,0), 3, colors.HexColor(hex_col)),
            ("ROUNDEDCORNERS", [4]),
        ]))
        cells.append(inner)

    row = Table([cells], colWidths=[(PAGE_W - 2*MARGIN) / len(metrics)] * len(metrics))
    row.setStyle(TableStyle([
        ("LEFTPADDING",  (0,0),(-1,-1), 4),
        ("RIGHTPADDING", (0,0),(-1,-1), 4),
        ("TOPPADDING",   (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
    ]))
    return row


# ─────────────────────────────────────────────
# STYLED DATA TABLE
# ─────────────────────────────────────────────
def styled_table(headers, rows, col_widths=None):
    header_row = [Paragraph(h, ParagraphStyle(
        "th", fontSize=8, textColor=WHITE, fontName="Helvetica-Bold",
        alignment=TA_CENTER)) for h in headers]

    data = [header_row]
    for i, row in enumerate(rows):
        styled = []
        for j, cell in enumerate(row):
            p = Paragraph(str(cell), ParagraphStyle(
                "td", fontSize=8, textColor=DARK_NAVY, fontName="Helvetica",
                alignment=TA_LEFT if j == 0 else TA_CENTER))
            styled.append(p)
        data.append(styled)

    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  ACCENT_BLUE),
        ("BACKGROUND",    (0,1),(-1,-1), colors.white),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [colors.white, LIGHT_GREY]),
        ("GRID",          (0,0),(-1,-1), 0.4, colors.HexColor("#CBD5E0")),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 7),
        ("RIGHTPADDING",  (0,0),(-1,-1), 7),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("LINEBELOW",     (0,0),(-1,0),  1, colors.HexColor("#1558A0")),
    ]))
    return t


# ─────────────────────────────────────────────
# SEVERITY BADGE
# ─────────────────────────────────────────────
def severity_badge(level):
    col_map = {"CRITICAL": "#E63946", "HIGH": "#F4A261",
               "MEDIUM": "#2A9D8F",   "LOW": "#8D99AE"}
    bg = colors.HexColor(col_map.get(level, "#8D99AE"))
    p  = Paragraph(level, ParagraphStyle(
        "badge", fontSize=7, textColor=WHITE, fontName="Helvetica-Bold",
        alignment=TA_CENTER))
    t  = Table([[p]], colWidths=[50])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), bg),
        ("TOPPADDING",    (0,0),(-1,-1), 3),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3),
        ("ROUNDEDCORNERS",[4]),
    ]))
    return t


# ─────────────────────────────────────────────
# TWO-COLUMN CHART ROW
# ─────────────────────────────────────────────
def two_chart_row(img1, img2, w=245):
    row = [[img1, img2]]
    t   = Table(row, colWidths=[w, w])
    t.setStyle(TableStyle([
        ("ALIGN",  (0,0),(-1,-1),"CENTER"),
        ("VALIGN", (0,0),(-1,-1),"MIDDLE"),
        ("LEFTPADDING",  (0,0),(-1,-1), 4),
        ("RIGHTPADDING", (0,0),(-1,-1), 4),
    ]))
    return t


# ─────────────────────────────────────────────
# COVER PAGE
# ─────────────────────────────────────────────
def build_cover(canvas, doc, summary, ts):
    """
    WHITE / LIGHT professional cover page.
    Background: white with a navy header band and a thin cyan accent line.
    All body text is dark — clean, print-friendly design.
    """
    canvas.saveState()
    w, h = A4

    # ── White background ─────────────────────
    canvas.setFillColor(WHITE)
    canvas.rect(0, 0, w, h, fill=1, stroke=0)

    # ── Top header band (dark navy) ──────────
    header_h = 38 * mm
    canvas.setFillColor(DARK_NAVY)
    canvas.rect(0, h - header_h, w, header_h, fill=1, stroke=0)

    # Cyan accent stripe under header
    canvas.setFillColor(ACCENT_CYAN)
    canvas.rect(0, h - header_h - 3*mm, w, 3*mm, fill=1, stroke=0)

    # Classification ribbon inside header (top-right)
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(ACCENT_CYAN)
    canvas.drawRightString(w - MARGIN, h - 7*mm,
                           "RESTRICTED  //  OFFICIAL USE ONLY  //  NOT FOR PUBLIC RELEASE")

    # Organisation name (top-left in header)
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#A8DADC"))
    canvas.drawString(MARGIN, h - 7*mm, "National Command & Control Centre — Cyber")

    # Large NCCC acronym centred in header
    canvas.setFont("Helvetica-Bold", 38)
    canvas.setFillColor(WHITE)
    canvas.drawCentredString(w / 2, h - header_h + 14*mm, "NCCC")

    # ── Left accent bar (thin cyan vertical stripe) ──
    canvas.setFillColor(ACCENT_CYAN)
    canvas.rect(MARGIN - 2*mm, h * 0.20, 3, h * 0.54, fill=1, stroke=0)

    # ── Report title block ───────────────────
    canvas.setFont("Helvetica-Bold", 34)
    canvas.setFillColor(DARK_NAVY)
    canvas.drawString(MARGIN + 5*mm, h * 0.67, "CYBER THREAT")

    canvas.setFont("Helvetica-Bold", 34)
    canvas.setFillColor(ACCENT_BLUE)
    canvas.drawString(MARGIN + 5*mm, h * 0.61, "REPORT")

    # Subtitle
    canvas.setFont("Helvetica", 11)
    canvas.setFillColor(colors.HexColor("#4A5568"))
    canvas.drawString(MARGIN + 5*mm, h * 0.565,
                      "JCOCC  ·  Traffic Analysis Summary")

    # Thin horizontal rule below subtitle
    canvas.setStrokeColor(colors.HexColor("#CBD5E0"))
    canvas.setLineWidth(0.8)
    canvas.line(MARGIN + 5*mm, h * 0.548, w - MARGIN, h * 0.548)

    # ── KPI pills (light card style) ─────────
    total  = summary.get("total_attacks", 0)
    unique = len(summary.get("top_ips", {}))
    units  = len(summary.get("top_unit", {}))

    pills = [
        (f"{total:,}", "Total Events"),
        (f"{unique}",  "Unique IPs"),
        (f"{units}",   "Targeted Units"),
    ]
    pill_w, pill_h = 108, 44
    gap            = 10
    total_pill_w   = len(pills) * pill_w + (len(pills) - 1) * gap
    start_x        = MARGIN + 5*mm

    for i, (val, lbl) in enumerate(pills):
        px = start_x + i * (pill_w + gap)
        py = h * 0.445

        # Light card background
        canvas.setFillColor(colors.HexColor("#EBF4FB"))
        canvas.roundRect(px, py, pill_w, pill_h, 6, fill=1, stroke=0)

        # Top accent border
        canvas.setFillColor(ACCENT_BLUE)
        canvas.rect(px, py + pill_h - 3, pill_w, 3, fill=1, stroke=0)

        # Value
        canvas.setFont("Helvetica-Bold", 20)
        canvas.setFillColor(ACCENT_BLUE)
        canvas.drawCentredString(px + pill_w / 2, py + 20, val)

        # Label
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#718096"))
        canvas.drawCentredString(px + pill_w / 2, py + 8, lbl)

    # ── Meta info ────────────────────────────
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#4A5568"))
    canvas.drawString(MARGIN + 5*mm, h * 0.395, f"Report Generated:  {ts}")
    canvas.drawString(MARGIN + 5*mm, h * 0.365,
                      "Classification: RESTRICTED  |  Handling: OFFICIAL")

    # ── Bottom footer bar ────────────────────
    canvas.setFillColor(DARK_NAVY)
    canvas.rect(0, 0, w, 14*mm, fill=1, stroke=0)
    canvas.setFillColor(ACCENT_CYAN)
    canvas.rect(0, 14*mm, w, 1*mm, fill=1, stroke=0)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#A8DADC"))
    canvas.drawString(MARGIN, 5.5*mm, "NCCC-JCOCC  ·  Traffic Monitoring & Analysis Branch")
    canvas.drawRightString(w - MARGIN, 5.5*mm, "Page 1")

    canvas.restoreState()


# ─────────────────────────────────────────────
# MAIN BUILD
# ─────────────────────────────────────────────
def build_pdf_report_v2(summary_path, pdf_dir):
    pdf_dir = Path(pdf_dir)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    with open(summary_path) as f:
        summary = json.load(f)

    ts = time.strftime("%d %B %Y  %H:%M UTC")

    styles = make_styles()

    pdf_path = pdf_dir / "JCOCC_REPORT_EXEC.pdf"

    # ── Build charts ──────────────────────────
    img_dir = pdf_dir / "charts"
    img_dir.mkdir(exist_ok=True)

    p_hourly   = img_dir / "hourly.png"
    p_proto    = img_dir / "protocol.png"
    p_country  = img_dir / "countries.png"
    p_ips      = img_dir / "ips.png"
    p_timeline = img_dir / "timeline.png"
    p_units    = img_dir / "units.png"

    hours = summary.get("attacks_by_hour", {})
    if hours:
        chart_hourly(hours, p_hourly)

    proto = {k: v for k, v in summary.get("protocol_dist", {}).items() if v > 0}
    if proto:
        chart_protocol(proto, p_proto)

    countries = {k: v for k, v in summary.get("top_countries", {}).items()
                 if k.upper() != "IN"}
    if countries:
        chart_countries(countries, p_country)

    ips = summary.get("top_ips", {})
    if ips:
        chart_top_ips(ips, p_ips)

    has_timeline = chart_timeline(summary.get("timeline", {}), p_timeline)

    units = {k: v for k, v in summary.get("top_unit", {}).items()
             if k.lower() != "unknown"}
    if units:
        chart_units(units, p_units)

    # ── Helpers ──────────────────────────────
    def get_top(d, exclude=None):
        if not isinstance(d, dict) or not d:
            return "-", 0
        filt = {k: v for k, v in d.items()
                if not exclude or k.upper() not in [x.upper() for x in exclude]}
        if not filt:
            return "-", 0
        k = max(filt, key=filt.get)
        return k, filt[k]

    total     = summary.get("total_attacks", 0)
    top_ctry, top_ctry_cnt = get_top(summary.get("top_countries", {}), exclude=["IN"])
    top_proto, top_proto_cnt = get_top(summary.get("protocol_dist", {}))
    peak_hour, peak_cnt = get_top(summary.get("attacks_by_hour", {}))
    top_ip, top_ip_cnt  = get_top(summary.get("top_ips", {}))
    top_port, top_port_cnt = get_top(summary.get("top_dst_ports", {}))
    unique_ips = len(summary.get("top_ips", {}))
    targeted   = len(summary.get("top_unit", {}))

    # ── Document setup ───────────────────────
    content = []
    usable_w = PAGE_W - 2 * MARGIN

    from reportlab.platypus import NextPageTemplate

    def on_first_page(canvas, doc):
        build_cover(canvas, doc, summary, ts)

    def on_later_pages(canvas, doc):
        header_footer(canvas, doc)

    doc = BaseDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=2.2*cm, bottomMargin=1.6*cm,
    )

    cover_frame = Frame(MARGIN, 1.6*cm, usable_w, PAGE_H - 3.8*cm,
                        id="cover_frame", showBoundary=0)
    main_frame  = Frame(MARGIN, 1.6*cm, usable_w, PAGE_H - 3.8*cm,
                        id="main", showBoundary=0)

    cover_template = PageTemplate(id="cover", frames=[cover_frame],
                                  onPage=on_first_page)
    main_template  = PageTemplate(id="main",  frames=[main_frame],
                                  onPage=on_later_pages)

    doc.addPageTemplates([cover_template, main_template])

    # Blank spacer fills the cover frame; cover is painted by on_first_page
    content.append(NextPageTemplate("main"))
    content.append(PageBreak())

    # ═══════════════════════════════════════
    # PAGE 2 — EXECUTIVE SUMMARY
    # ═══════════════════════════════════════
    content += section_heading("01", "Executive Summary", styles)

    # Threat level banner
    threat_level = "HIGH" if total > 50000 else "MEDIUM" if total > 10000 else "LOW"
    tl_color = {"HIGH":"#E63946","MEDIUM":"#F4A261","LOW":"#2A9D8F"}[threat_level]

    banner_text = Paragraph(
        f"<b>THREAT LEVEL: {threat_level}</b>  ·  "
        f"{total:,} suspicious events detected over the reporting period. "
        f"Primary external origin: <b>{top_ctry}</b>. "
        f"Dominant protocol: <b>{top_proto}</b>. "
        f"Peak activity at <b>{peak_hour}:00 UTC</b>.",
        ParagraphStyle("banner", fontSize=9, textColor=WHITE,
                       fontName="Helvetica", leading=14,
                       leftIndent=8, rightIndent=8)
    )
    banner_tbl = Table([[banner_text]], colWidths=[usable_w])
    banner_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,-1), colors.HexColor(tl_color)),
        ("TOPPADDING",   (0,0),(-1,-1), 9),
        ("BOTTOMPADDING",(0,0),(-1,-1), 9),
        ("LINEABOVE",    (0,0),(-1,0),  2, colors.HexColor("#A0000A")),
    ]))
    content.append(banner_tbl)
    content.append(Spacer(1, 10))

    # KPI row 1
    content.append(kpi_row([
        (f"{total:,}",    "Total Events Detected",  "#1E6FA8"),
        (str(unique_ips), "Unique Source IPs",       "#E63946"),
        (str(targeted),   "Targeted Units",          "#F4A261"),
        (str(peak_hour)+"h", "Peak Attack Hour",     "#2A9D8F"),
    ], styles))
    content.append(Spacer(1, 8))

    # KPI row 2
    content.append(kpi_row([
        (top_ctry,             "Top Attacker Country",  "#1E6FA8"),
        (top_proto,            "Most-Used Protocol",    "#E63946"),
        (str(top_port),        "Most-Targeted Port",    "#F4A261"),
        (f"{top_ip_cnt:,}",    "Max Hits from Single IP","#2A9D8F"),
    ], styles))
    content.append(Spacer(1, 14))

    # Narrative
    content.append(Paragraph(
        f"During the reporting period, the NCCC Security Operations Centre recorded "
        f"<b>{total:,}</b> malicious events matching indicators of compromise (IOCs) "
        f"across monitored network segments. "
        f"The majority of external attack traffic originated from <b>{top_ctry}</b>, "
        f"with <b>{top_proto}</b> accounting for the dominant share of malicious traffic. "
        f"Activity peaked at hour <b>{peak_hour}:00 UTC</b>, suggesting coordinated "
        f"or automated attack patterns. A total of <b>{unique_ips}</b> unique source IPs "
        f"were observed targeting <b>{targeted}</b> distinct organisational units.",
        styles["body"]
    ))
    content.append(Spacer(1, 14))

    # ═══════════════════════════════════════
    # SECTION 02 — ATTACK TIMELINE & HOURLY
    # ═══════════════════════════════════════
    content += section_heading("02", "Attack Timeline & Volume Analysis", styles)

    if has_timeline and p_timeline.exists():
        tl_img = Image(str(p_timeline), width=usable_w, height=80)
        content.append(tl_img)
        content.append(Paragraph("Figure 1 — Daily event volume over the reporting period", styles["caption"]))

    if p_hourly.exists():
        h_img = Image(str(p_hourly), width=usable_w, height=95)
        content.append(h_img)
        content.append(Paragraph("Figure 2 — Event distribution by hour (UTC)", styles["caption"]))

    content.append(Spacer(1, 6))

    # ═══════════════════════════════════════
    # SECTION 03 — GEO & PROTOCOL
    # ═══════════════════════════════════════
    content += section_heading("03", "Geographic Origin & Protocol Analysis", styles)

    chart_cells = []
    if p_country.exists():
        chart_cells.append(Image(str(p_country), width=245, height=105))
    if p_proto.exists():
        chart_cells.append(Image(str(p_proto),   width=245, height=105))

    if len(chart_cells) == 2:
        content.append(two_chart_row(*chart_cells))
        content.append(Paragraph(
            "Figure 3 — Top attacker countries (IN excluded)   |   Figure 4 — Protocol distribution",
            styles["caption"]))

    content.append(Paragraph(
        f"External traffic dominates the threat landscape with <b>{top_ctry}</b> accounting for "
        f"the highest volume of malicious events. <b>{top_proto}</b> traffic represents the primary "
        f"attack vector, consistent with automated scanning and exploitation tools.",
        styles["body"]
    ))
    content.append(Spacer(1, 14))

    # ═══════════════════════════════════════
    # SECTION 04 — TOP ATTACKER IPs & PORTS
    # ═══════════════════════════════════════
    content += section_heading("04", "Threat Actor Intelligence — IPs & Ports", styles)

    if p_ips.exists():
        content.append(Image(str(p_ips), width=usable_w, height=105))
        content.append(Paragraph("Figure 5 — Top 10 source IPs by event count", styles["caption"]))

    # IP table + Port table side by side
    ip_items   = sorted(ips.items(), key=lambda x: x[1], reverse=True)[:10]
    port_items = sorted(summary.get("top_dst_ports", {}).items(),
                        key=lambda x: x[1], reverse=True)[:10]

    ip_rows   = [[ip, f"{cnt:,}"] for ip, cnt in ip_items]
    port_rows = [[str(p), f"{cnt:,}"] for p, cnt in port_items]

    ip_tbl   = styled_table(["Source IP", "Events"], ip_rows,   col_widths=[130, 60])
    port_tbl = styled_table(["Port", "Events"],       port_rows, col_widths=[80,  60])

    side = Table([[ip_tbl, Spacer(10,1), port_tbl]])
    side.setStyle(TableStyle([
        ("VALIGN",(0,0),(-1,-1),"TOP"),
        ("LEFTPADDING",(0,0),(-1,-1),0),
        ("RIGHTPADDING",(0,0),(-1,-1),0),
    ]))
    content.append(side)
    content.append(Spacer(1, 14))

    # ═══════════════════════════════════════
    # SECTION 05 — TARGETED UNITS
    # ═══════════════════════════════════════
    content += section_heading("05", "Targeted Units & Internal Exposure", styles)

    if p_units.exists() and units:
        content.append(Image(str(p_units), width=usable_w, height=100))
        content.append(Paragraph("Figure 6 — Events per targeted unit (unknown excluded)", styles["caption"]))

    unit_items = sorted(summary.get("top_unit", {}).items(),
                        key=lambda x: x[1], reverse=True)[:10]
    unit_rows  = [[u, f"{cnt:,}", "HIGH" if cnt > 5000 else "MEDIUM" if cnt > 500 else "LOW"]
                  for u, cnt in unit_items]

    sev_color_map = {"HIGH":"#E63946","MEDIUM":"#F4A261","LOW":"#2A9D8F"}

    # Build table with coloured severity column
    hdr = [Paragraph(h, ParagraphStyle("th",fontSize=8,textColor=WHITE,
                     fontName="Helvetica-Bold",alignment=TA_CENTER))
           for h in ["Unit", "Events", "Severity"]]
    rows_data = [hdr]
    for u, cnt, sev in unit_rows:
        bg = colors.HexColor(sev_color_map[sev])
        p_sev = Paragraph(sev, ParagraphStyle("sev",fontSize=7,textColor=WHITE,
                          fontName="Helvetica-Bold",alignment=TA_CENTER))
        rows_data.append([
            Paragraph(u,   ParagraphStyle("td",fontSize=8,fontName="Helvetica",textColor=DARK_NAVY)),
            Paragraph(cnt, ParagraphStyle("td",fontSize=8,fontName="Helvetica",textColor=DARK_NAVY,alignment=TA_CENTER)),
            p_sev
        ])

    unit_tbl = Table(rows_data, colWidths=[180, 80, 80])
    ts_style = [
        ("BACKGROUND",    (0,0),(-1,0),  ACCENT_BLUE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, LIGHT_GREY]),
        ("GRID",          (0,0),(-1,-1), 0.4, colors.HexColor("#CBD5E0")),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 7),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("LINEBELOW",     (0,0),(-1,0),  1, colors.HexColor("#1558A0")),
    ]
    for i, (_, _, sev) in enumerate(unit_rows, start=1):
        ts_style.append(("BACKGROUND", (2,i),(2,i), colors.HexColor(sev_color_map[sev])))

    unit_tbl.setStyle(TableStyle(ts_style))
    content.append(unit_tbl)
    content.append(Spacer(1, 14))

    # ═══════════════════════════════════════
    # SECTION 06 — THREAT ANALYSIS
    # ═══════════════════════════════════════
    content += section_heading("06", "Threat Analysis & Assessment", styles)

    findings = [
        ("Automated Intrusion Patterns",
         f"Traffic characteristics — high volume, repetitive source IPs, consistent port targeting — "
         f"are strongly indicative of automated scanning or botnet-driven exploitation tools."),

        ("Peak Hour Exploitation",
         f"Concentrated activity at hour <b>{peak_hour}:00 UTC</b> may reflect attacker time-zone "
         f"preferences or scheduled automation. Defensive posture should be heightened during "
         f"hours {int(peak_hour)-1}–{int(peak_hour)+2}."),

        ("Protocol Abuse",
         f"<b>{top_proto}</b> dominates at the protocol level. This is consistent with "
         f"exploitation of web-facing services, remote administration, or unencrypted data "
         f"channels that represent easy targets for credential harvesting."),

        ("Geographic Concentration",
         f"The majority of external threats originate from <b>{top_ctry}</b>. "
         f"Geo-blocking or enhanced monitoring rules for this origin may significantly "
         f"reduce the attack surface."),

        ("Internal Unit Exposure",
         f"Several internal units — notably those with high event counts — show "
         f"persistent targeting, indicating possible prior reconnaissance or known vulnerabilities "
         f"being actively exploited."),
    ]

    for title, body in findings:
        inner = Table([
            [Paragraph(f"<b>{title}</b>",
                       ParagraphStyle("ft",fontSize=9,textColor=ACCENT_BLUE,
                                      fontName="Helvetica-Bold",leading=12))],
            [Paragraph(body, styles["body"])],
        ], colWidths=[usable_w - 20])
        inner.setStyle(TableStyle([
            ("LEFTPADDING",  (0,0),(-1,-1), 10),
            ("RIGHTPADDING", (0,0),(-1,-1), 10),
            ("TOPPADDING",   (0,0),(-1,-1), 5),
            ("BOTTOMPADDING",(0,0),(-1,-1), 5),
            ("LINEABOVE",    (0,0),(-1,0),  1, ACCENT_CYAN),
            ("BACKGROUND",   (0,0),(-1,-1), LIGHT_GREY),
        ]))
        content.append(inner)
        content.append(Spacer(1, 5))

    content.append(Spacer(1, 10))

    # ═══════════════════════════════════════
    # SECTION 07 — RECOMMENDATIONS
    # ═══════════════════════════════════════
    content += section_heading("07", "Recommendations & Mitigations", styles)

    recs = [
        ("CRITICAL", "Immediate IP Blocklist Deployment",
         f"Block the top {min(10,unique_ips)} source IPs at perimeter firewalls. "
         f"Priority: {top_ip} ({top_ip_cnt:,} events)."),

        ("HIGH", "Geographic Filtering",
         f"Implement geo-blocking rules for {top_ctry} and other high-volume "
         f"source countries identified in Section 03."),

        ("HIGH", "Service Hardening on Port " + str(top_port),
         f"Port {top_port} is the most-targeted destination port. "
         f"Review exposed services, enforce strict allow-lists, and apply latest patches."),

        ("MEDIUM", "IDS/IPS Signature Update",
         f"Push updated signatures reflecting the IOCs from this reporting period. "
         f"Ensure {top_proto} deep-packet inspection is active."),

        ("MEDIUM", "Enhanced Unit Monitoring",
         "Units with HIGH severity ratings require heightened SIEM alerting thresholds "
         "and dedicated analyst attention for the next 72 hours."),

        ("LOW", "Internal Lateral Movement Review",
         "Investigate internal traffic anomalies; validate that no internal IPs are "
         "relaying external attack traffic or have been compromised."),

        ("LOW", "Threat Intelligence Feed Refresh",
         "Synchronise IOC database with current feeds (MISP, STIX/TAXII). "
         "Validate all matched IPs against geolocation and ASN reputation sources."),
    ]

    sev_order = {"CRITICAL":0,"HIGH":1,"MEDIUM":2,"LOW":3}
    for sev, title, detail in sorted(recs, key=lambda x: sev_order[x[0]]):
        bg = colors.HexColor(sev_color_map.get(sev, "#8D99AE"))
        sev_p = Paragraph(sev, ParagraphStyle("s",fontSize=7,textColor=WHITE,
                          fontName="Helvetica-Bold",alignment=TA_CENTER))
        title_p  = Paragraph(f"<b>{title}</b>",
                             ParagraphStyle("rt",fontSize=9,textColor=DARK_NAVY,
                                            fontName="Helvetica-Bold",leading=12))
        detail_p = Paragraph(detail, styles["body"])

        row_tbl = Table(
            [[sev_p, Table([[title_p],[detail_p]], colWidths=[usable_w - 80])]],
            colWidths=[60, usable_w - 68]
        )
        row_tbl.setStyle(TableStyle([
            ("BACKGROUND",   (0,0),(0,-1), bg),
            ("BACKGROUND",   (1,0),(1,-1), WHITE),
            ("VALIGN",       (0,0),(-1,-1),"MIDDLE"),
            ("TOPPADDING",   (0,0),(-1,-1), 6),
            ("BOTTOMPADDING",(0,0),(-1,-1), 6),
            ("LEFTPADDING",  (0,0),(-1,-1), 8),
            ("GRID",         (0,0),(-1,-1), 0.4, colors.HexColor("#CBD5E0")),
        ]))
        content.append(row_tbl)
        content.append(Spacer(1, 4))

    content.append(Spacer(1, 14))

    # ═══════════════════════════════════════
    # SECTION 08 — APPENDIX: RAW DATA TABLES
    # ═══════════════════════════════════════
    content += section_heading("08", "Appendix — Raw Intelligence Tables", styles)

    # Full IP table
    content.append(Paragraph("<b>A. Top Source IPs</b>", styles["h2"]))
    full_ip_rows = [[ip, f"{cnt:,}"] for ip, cnt in
                    sorted(ips.items(), key=lambda x: x[1], reverse=True)[:15]]
    content.append(styled_table(["Source IP", "Event Count"], full_ip_rows,
                                col_widths=[200, 100]))
    content.append(Spacer(1, 10))

    # Port table
    content.append(Paragraph("<b>B. Top Destination Ports</b>", styles["h2"]))
    full_port_rows = [[str(p), f"{cnt:,}"] for p, cnt in
                      sorted(summary.get("top_dst_ports", {}).items(),
                             key=lambda x: x[1], reverse=True)[:15]]
    content.append(styled_table(["Destination Port", "Event Count"], full_port_rows,
                                col_widths=[200, 100]))
    content.append(Spacer(1, 10))

    # Country table
    content.append(Paragraph("<b>C. Top Source Countries</b>", styles["h2"]))
    ctry_rows = [[c, f"{cnt:,}"] for c, cnt in
                 sorted(countries.items(), key=lambda x: x[1], reverse=True)[:15]]
    content.append(styled_table(["Country Code", "Event Count"], ctry_rows,
                                col_widths=[200, 100]))

    # ── Build ─────────────────────────────
    doc.build(content)
    print(f"PDF saved: {pdf_path}")
    return pdf_path


# ─────────────────────────────────────────────
# ENTRY POINT (standalone test)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 3:
        summary_json = sys.argv[1]
        out_dir      = sys.argv[2]
    else:
        # Fallback: generate sample data for demo
        sample = {
            "total_attacks": 143407,
            "top_ips": {
                "176.65.149.30":923,"79.124.59.78":897,"199.232.210.172":265,
                "199.232.214.172":257,"204.76.203.83":22,"159.89.124.112":13,
                "14.139.106.226":7,"165.227.172.206":4,"139.59.170.85":3,
                "14.139.88.82":31
            },
            "top_countries": {"US":38000,"NL":12000,"CA":9000,"BG":7500,"DE":6200,
                              "GB":5000,"PT":4100,"RU":3800,"CN":2900,"SG":2100,"IN":500},
            "protocol_dist": {"TCP":79800,"UDP":61600,"ICMP":2007},
            "top_unit": {"Air Force":24362,"DCyA":21537,"CDM":10136,
                         "DGAFMS":4654,"Mgmt Pfsense DCyA":460,"NDA":18,"MILIT":21,"AFMC":18,
                         "DSSC WELLINGTON":6,"unknown":74900},
            "top_dst_ports": {"80":2564,"22":117,"8022":11,"52834":7,"64553":4,
                              "64584":2,"64554":2,"45031":2,"53130":1,"59652":1},
            "top_src_ports": {},
            "top_dst_ips": {},
            "pkt_size_dist": {},
            "top_dst_countries": {},
            "attacks_by_hour": {
                "0":800,"1":650,"2":700,"3":950,"4":1100,"5":1300,
                "6":2500,"7":8000,"8":28000,"9":22000,"10":15000,"11":12000,
                "12":9000,"13":8500,"14":7800,"15":7000,"16":5500,"17":4200,
                "18":3000,"19":2200,"20":1800,"21":1500,"22":1200,"23":900
            },
            "timeline": {
                "2026-03-25":4200,"2026-03-26":5100,"2026-03-27":3800,
                "2026-03-28":6200,"2026-03-29":9400,"2026-03-30":11000,
                "2026-03-31":18000,"2026-04-01":22000,"2026-04-02":19000,
                "2026-04-03":15000,"2026-04-04":12000,"2026-04-05":8500,
                "2026-04-06":7200,"2026-04-07":6800,"2026-04-08":5207,
            }
        }
        import tempfile, os
        tmp = tempfile.mkdtemp()
        summary_json = os.path.join(tmp, "summary_all.json")
        with open(summary_json, "w") as fp:
            json.dump(sample, fp)
        out_dir = "/home/claude/pdf_output"

    result = build_pdf_report_v2(summary_json, out_dir)
    print("Done:", result)
