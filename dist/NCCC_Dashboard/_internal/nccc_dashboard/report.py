from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

import os
import tempfile
import uuid

from nccc_dashboard.charts import (
    timeline, heatmap, bar, severity_gauge
)

styles = getSampleStyleSheet()


# ================= SAVE PLOTLY AS IMAGE =================
def save_fig(fig, name):
    try:
        unique_name = f"{name}_{uuid.uuid4().hex}.png"
        path = os.path.join(tempfile.gettempdir(), unique_name)

        fig.write_image(path, width=800, height=400)
        return path

    except Exception as e:
        return None


# ================= KPI TABLE =================
def kpi_table(df, total_rows):

    if df is None or df.empty:
        data = [["Metric", "Value"], ["No Data", "-"]]
    else:
        hit_ratio = (len(df) / total_rows) * 100 if total_rows else 0

        data = [
            ["Metric", "Value"],
            ["IOC Hits", len(df)],
            ["Total Rows", total_rows],
            ["Hit Ratio", f"{hit_ratio:.2f}%"],
            ["Unique IPs", df["source ip"].nunique() if "source ip" in df.columns else "-"]
        ]

    table = Table(data)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER")
    ]))

    return table


# ================= SAFE IMAGE ADD =================
def add_image(story, fig, title, width=450, height=250):

    story.append(Paragraph(title, styles["Heading2"]))

    img_path = save_fig(fig, title.replace(" ", "_"))

    if img_path and os.path.exists(img_path):
        story.append(Image(img_path, width=width, height=height))
    else:
        story.append(Paragraph("⚠️ Unable to render chart", styles["Normal"]))

    story.append(Spacer(1, 20))


# ================= MAIN REPORT =================
def generate_pdf(df, total_rows, output_path):

    doc = SimpleDocTemplate(output_path, pagesize=A4)
    story = []

    # ===== TITLE =====
    story.append(Paragraph("NCCC IOC Analysis Report", styles["Title"]))
    story.append(Spacer(1, 12))

    # ===== KPI =====
    story.append(Paragraph("Summary", styles["Heading2"]))
    story.append(kpi_table(df, total_rows))
    story.append(Spacer(1, 20))

    # ===== SAFETY =====
    if df is None or df.empty:
        story.append(Paragraph("No data available for report generation.", styles["Normal"]))
        doc.build(story)
        return

    # ===== SEVERITY =====
    add_image(story, severity_gauge(df, total_rows), "IOC Hit Severity", 400, 200)

    # ===== TIMELINE =====
    add_image(story, timeline(df), "Timeline")

    # ===== HEATMAP =====
    add_image(story, heatmap(df), "Heatmap")

    # ===== TOP CHARTS =====
    charts = [
        ("Top Source IP", bar(df, "source ip", "")),
        ("Top Destination IP", bar(df, "dstn ip", "")),
        ("Top Ports", bar(df, "source port", "")),
        ("Top Countries", bar(df, "source country", ""))
    ]

    for title, fig in charts:
        add_image(story, fig, title)

    # ===== BUILD =====
    doc.build(story)