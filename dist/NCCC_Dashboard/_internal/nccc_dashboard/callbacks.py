from dash import Input, Output, State, ctx, html, no_update
import pandas as pd
from datetime import datetime
import json
from pathlib import Path
from nccc_dashboard.backend_runner import start_backend
from nccc_dashboard.config import *
from nccc_dashboard.charts import *
from nccc_dashboard.utils import kpi_card
from nccc_dashboard.layout import (
    home_page,
    charts_page,
    reports_page,
    json_page,
    csv_page,
    mail_page
)


# ==============EMPTY CHART======================
def empty_chart(title=""):
    import plotly.graph_objects as go

    fig = go.Figure()

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=CARD,   # unified with all chart backgrounds
        plot_bgcolor=CARD,

        xaxis=dict(visible=False),
        yaxis=dict(visible=False),

        annotations=[
            dict(
                text="Awaiting Data",
                x=0.5, y=0.5,
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=14, color="#6c7a89")
            )
        ],

        margin=dict(l=10, r=10, t=10, b=10),
        height=220
    )

    return fig


# ==============DARK THEME======================
def apply_dark_theme(fig, title):
    if fig is None:
        return empty_chart(title)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=CARD,   # unified — same as all charts in charts.py
        plot_bgcolor=CARD,
        font={"color": "#ffffff"},
        margin=dict(l=10, r=10, t=40, b=10)
    )

    return fig


def register_callbacks(app):
    # ==============HOME PAGE======================
    @app.callback(
        Output("page_content", "children"),
        Input("url", "pathname")
    )
    def route_pages(pathname):
        # Flask serves /reports /json /csv /mail /download-pdf directly.
        # Dash only needs to handle the two SPA pages: / and /charts.
        if pathname == "/charts":
            return charts_page()
        return home_page()

    # ================= NAV DRAWER TOGGLE =================
    # Single callback owns both outputs — no duplicate conflict.
    # Triggers: hamburger open | X close | overlay click | URL change (auto-close)
    _DRAWER_BASE = {
        "position": "fixed",
        "top": "0",
        "right": "-320px",          # default: hidden
        "width": "300px",
        "height": "100vh",
        "background": CARD,
        "borderLeft": f"1px solid {BORDER}",
        "zIndex": "1001",
        "overflowY": "auto",
        "padding": "16px 14px",
        "boxSizing": "border-box",
        "transition": "right 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
    }
    _OVERLAY_BASE = {
        "position": "fixed",
        "top": "0", "left": "0",
        "width": "100vw", "height": "100vh",
        "background": "rgba(0,0,0,0.55)",
        "zIndex": "1000",
        "cursor": "pointer",
    }

    @app.callback(
        Output("nav_drawer",  "style"),
        Output("nav_overlay", "style"),
        Input("nav_toggle",   "n_clicks"),
        Input("nav_close",    "n_clicks"),
        Input("nav_overlay",  "n_clicks"),
        Input("url",          "pathname"),   # auto-close on navigation
        prevent_initial_call=True,
    )
    def toggle_nav_drawer(open_clicks, close_clicks, overlay_clicks, pathname):
        from dash import ctx as _ctx
        triggered = _ctx.triggered_id

        if triggered == "nav_toggle":
            # Open drawer
            return (
                {**_DRAWER_BASE, "right": "0px"},
                {**_OVERLAY_BASE, "display": "block"},
            )
        else:
            # Close: X button, overlay click, or URL changed
            return (
                {**_DRAWER_BASE, "right": "-320px"},
                {**_OVERLAY_BASE, "display": "none"},
            )

    # ================= CLOCK =================
    @app.callback(Output("live_clock", "children"),
                  Input("clock_interval", "n_intervals"))
    def clock(_):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")

    # ================= RUN =================
    @app.callback(
        Output("run_status", "children"),
        Input("run", "n_clicks"),
        State("folder", "value"),
        prevent_initial_call=True
    )
    def run_backend_cb(n, folder):

        if not folder:
            return html.Span("Enter folder", style={"color": YELLOW})

        progress["logs"] = []
        progress["done"] = False
        progress["status"] = "running"   # ✅ ADDED
        progress["folder"] = folder
        progress["pdf_path"] = None

        start_backend(folder)

        return html.Span("Pipeline running...", style={"color": ACCENT})

    # ================= LIVE PROGRESS =================
    @app.callback(
        Output("run_status", "children", allow_duplicate=True),
        Input("interval", "n_intervals"),
        prevent_initial_call=True
    )
    def update_run_status(_):

        if progress.get("done"):
            progress["status"] = "completed"   # ✅ ADDED
            return html.Span("Pipeline completed", style={"color": "lime"})

        elif progress.get("folder"):
            progress["status"] = "running"     # ✅ ADDED
            return html.Span("Pipeline running...", style={"color": ACCENT})

        progress["status"] = "idle"            # ✅ ADDED
        return html.Span("Idle", style={"color": "#888"})

    # ================= LOG STREAM =================
    @app.callback(
        Output("logs", "children"),
        Input("interval", "n_intervals")
    )
    def update_logs(_):

        logs = progress.get("logs", [])

        if not logs:
            if progress.get("done"):
                return "Completed"
            return "Starting pipeline..."

        return "\n".join(logs[-30:])

    # ================= PROGRESS BAR =================
    @app.callback(
        Output("progress_bar_inner", "style"),
        Input("interval", "n_intervals")
    )
    def update_progress(_):

        if progress.get("done"):
            percent = 100
        else:
            logs = progress.get("logs", [])
            if not logs:
                percent = 0
            else:
                total_steps = 120
                current = len(logs)
                percent = min(int((current / total_steps) * 100), 95)

        return {
            "height": "6px",
            "width": f"{percent}%",
            "background": ACCENT,
            "borderRadius": "4px",
            "transition": "width 0.4s ease"
        }

    # ================= POLL =================
    # FIX: loads summary_all.json (merged "all" key) + per-branch files
    #      and stores them all under data["summary"] so KPI/charts can use
    #      both branch == "all" and specific branches.
    @app.callback(Output("data_store", "data"),
                  Input("interval", "n_intervals"))
    def poll(_):

        if not progress.get("done"):
            return no_update

        folder = progress.get("folder")
        if not folder:
            return no_update

        json_dir = Path(folder) / "output" / "reports" / "json"

        if not json_dir.exists():
            return no_update

        summary = {}

        # Load the merged "all" summary
        all_file = json_dir / "summary_all.json"
        if all_file.exists():
            try:
                with open(all_file) as fh:
                    summary["all"] = json.load(fh)
            except Exception as e:
                print(f"[WARN] Could not load summary_all.json: {e}")

        # Load per-branch summaries
        for f in json_dir.glob("summary_*.json"):
            branch_key = f.stem.replace("summary_", "")
            if branch_key == "all":
                continue  # already loaded above
            try:
                with open(f) as fh:
                    summary[branch_key] = json.load(fh)
            except Exception as e:
                print(f"[WARN] Could not load {f.name}: {e}")

        if not summary:
            return no_update

        return {"summary": summary}

    # ================= PDF DOWNLOAD LINK =================
    @app.callback(
        Output("pdf_download_area", "children"),
        Input("interval", "n_intervals")
    )
    def pdf_download_link(_):

        pdf_path = progress.get("pdf_path")

        if not pdf_path or not Path(pdf_path).exists():
            return ""

        return html.A(
            "⬇  Download Executive PDF Report",
            href="/download-pdf",
            target="_blank",
            style={
                "display":        "inline-block",
                "marginTop":      "10px",
                "padding":        "8px 18px",
                "background":     ACCENT,
                "color":          "#fff",
                "borderRadius":   "5px",
                "textDecoration": "none",
                "fontWeight":     "bold",
                "fontSize":       "13px",
            }
        )

    # ================= BRANCH =================
    @app.callback(Output("branch_store", "data"),
                  [Input(f"btn_{b}", "n_clicks") for b in BRANCHES])
    def branch_select(*_):
        trig = ctx.triggered_id or "btn_all"
        return trig.replace("btn_", "")

    # ================= KPI =================
    @app.callback(Output("kpis", "children"),
                  Input("data_store", "data"),
                  Input("branch_store", "data"))
    def kpi(data, branch):

        if not data:
            return [
                kpi_card("IOC HITS", "...", ACCENT),
                kpi_card("THREAT SCORE", "...", ACCENT),
                kpi_card("INTENSITY", "...", ACCENT),
                kpi_card("TOP PROTOCOL", "...", ACCENT),
                kpi_card("PEAK HOUR", "...", ACCENT),
                kpi_card("TOP COUNTRY", "...", ACCENT),
                kpi_card("TOP UNIT", "...", ACCENT),
                kpi_card("UNIQUE IPS", "...", ACCENT),
                kpi_card("COUNTRY COUNT", "...", ACCENT),
                kpi_card("MATCH RATE", "...", ACCENT),
            ]

        if branch == "all":
            s = data["summary"].get("all", {})
        else:
            s = data["summary"].get(branch, {})

        def safe_max(d):
            return max(d, key=d.get) if d else "-"

        def safe_len(d):
            return len(d) if d else 0

        def pct(a, b):
            return f"{round((a / b) * 100, 1)}%" if b else "0%"

        def classify_intensity(total):
            if total < 100:
                return "LOW"
            elif total < 1000:
                return "MEDIUM"
            else:
                return "HIGH"

        total       = s.get("total_attacks", 0)
        countries   = s.get("top_countries", {})
        unique_ips  = safe_len(s.get("top_ips", {}))
        country_count = safe_len(countries)

        # Exclude India from top attacker country display
        ext_countries = {k: v for k, v in countries.items()
                         if k not in ["IN", "INDIA", "India"]}
        top_country = safe_max(ext_countries) if ext_countries else safe_max(countries)

        match_rate  = pct(total, total) if total else "0%"

        return [
            kpi_card("IOC HITS",      f"{total:,}", ACCENT),
            kpi_card("THREAT SCORE",  f"{min(int(total/100),999)}", RED if total > 5000 else YELLOW),
            kpi_card("INTENSITY",     classify_intensity(total), RED if total >= 1000 else YELLOW),
            kpi_card("TOP PROTOCOL",  safe_max(s.get("protocol_dist", {})), ACCENT),
            kpi_card("PEAK HOUR",     f"{safe_max(s.get('attacks_by_hour', {}))}h", ACCENT),
            kpi_card("TOP COUNTRY",   top_country, ACCENT),
            kpi_card("TOP UNIT",      safe_max(s.get("top_unit", {})), ACCENT),
            kpi_card("UNIQUE IPS",    unique_ips, ACCENT),
            kpi_card("COUNTRY COUNT", country_count, ACCENT),
            kpi_card("MATCH RATE",    match_rate, GREEN),
        ]

    # -------- THREAT PANEL --------
    @app.callback(
        Output("top_attacker", "children"),
        Output("target_unit", "children"),
        Output("attack_country", "children"),
        Output("attack_protocol", "children"),
        Input("data_store", "data"),
        Input("branch_store", "data"),
    )
    def update_threat_panel(data, branch):

        if not data or "summary" not in data:
            return "-", "-", "-", "-"

        if branch == "all":
            s = data["summary"].get("all", {})
        else:
            s = data["summary"].get(branch, {})

        if not s:
            return "-", "-", "-", "-"

        def top_key(d):
            return max(d, key=d.get) if d else "-"

        def top_country_excluding_india(d):
            if not d:
                return "-"
            filtered = {k: v for k, v in d.items()
                        if k not in ["IN", "INDIA", "India"]}
            if not filtered:
                return "-"
            return max(filtered, key=filtered.get)

        return (
            top_key(s.get("top_ips", {})),
            top_key(s.get("top_unit", {})),
            top_country_excluding_india(s.get("top_countries", {})),
            top_key(s.get("protocol_dist", {})),
        )

    # =========== APPLICATION & MALWARE ===============
    def load_app_malware(folder):
        """
        Load application_table.csv and topmalware_table.csv.

        Handles:
        - BOM characters in CSV headers (encoding="utf-8-sig")
        - Bandwidth strings: "68.2 Gbps", "320.2 Kbps", "1.2 Mbps", "775 bps"
          are converted to plain float (bps) for numeric sorting / bar chart display
        - Searches root folder first, then subfolders (skips output/ pipeline files)
        """
        base = Path(folder)
        app_df = pd.DataFrame()
        mal_df = pd.DataFrame()

        # ── bandwidth string → float (bps) ──────────────────────────
        def parse_bandwidth(val):
            if val is None:
                return None
            s = str(val).strip()
            multipliers = {
                "gbps": 1e9, "mbps": 1e6, "kbps": 1e3, "bps": 1.0,
            }
            low = s.lower().replace(" ", "")
            for unit, mult in multipliers.items():
                if low.endswith(unit):
                    try:
                        return float(low[: -len(unit)]) * mult
                    except ValueError:
                        return None
            try:
                return float(s.replace(",", ""))
            except ValueError:
                return None

        # ── column name normaliser ───────────────────────────────────
        def normalize_columns(df):
            # Strip BOM (﻿), surrounding quotes, whitespace from col names
            clean = {
                c.strip().lstrip("\ufeff").strip('"').strip().lower(): c
                for c in df.columns
            }
            name_col  = None
            value_col = None
            for key in ["applications", "application", "app",
                        "malwares", "malware", "name", "category"]:
                if key in clean:
                    name_col = clean[key]
                    break
            for key in ["avg", "average", "mean", "count", "hits", "total", "events"]:
                if key in clean:
                    value_col = clean[key]
                    break
            return name_col, value_col

        # ── collect CSV candidates ───────────────────────────────────
        root_csv = list(base.glob("*.csv"))
        sub_csv  = [
            f for f in base.rglob("*.csv")
            if f not in root_csv and "output" not in str(f).lower()
        ]
        all_csv = root_csv + sub_csv

        for f in all_csv:
            fname = f.name.lower()
            if not any(x in fname for x in
                       ["app", "application", "mal", "malware", "threat", "topmal"]):
                continue

            try:
                # utf-8-sig automatically strips the Excel BOM
                df = pd.read_csv(f, dtype=str, encoding="utf-8-sig", on_bad_lines="skip")
                if df.empty:
                    continue
            except Exception as e:
                print(f"[APP/MAL] Cannot read {f.name}: {e}")
                continue

            name_col, value_col = normalize_columns(df)
            if name_col is None or value_col is None:
                print(f"[APP/MAL] Column not found in {f.name} | cols={list(df.columns)}")
                continue

            temp = df[[name_col, value_col]].copy()
            temp.columns = ["name", "avg"]

            # Parse bandwidth strings ("68.2 Gbps" etc.) → numeric
            temp["avg"] = temp["avg"].apply(parse_bandwidth)
            temp = temp.dropna(subset=["avg"])
            temp["avg"] = pd.to_numeric(temp["avg"], errors="coerce")
            temp = temp.dropna(subset=["avg"])

            if temp.empty:
                print(f"[APP/MAL] All rows dropped after parse in {f.name}")
                continue

            print(f"[APP/MAL] Loaded {f.name} — {len(temp)} rows")

            if any(x in fname for x in ["app", "application", "top_app"]):
                if app_df.empty:
                    app_df = temp
            elif any(x in fname for x in ["mal", "malware", "threat", "topmal"]):
                if mal_df.empty:
                    mal_df = temp

        return app_df, mal_df

    # ================= APP + MALWARE =================
    @app.callback(
        Output("top_apps", "figure"),
        Output("top_malware", "figure"),
        Input("data_store", "data"),
    )
    def app_malware_charts(_):
        import plotly.graph_objects as go

        folder = progress.get("folder")
        if not folder:
            return empty_chart("Top Applications"), empty_chart("Top Malware")

        app_df, mal_df = load_app_malware(folder)

        # ---------------- FORMAT ----------------
        def fmt_bw(bps):
            try:
                bps = float(bps)
            except Exception:
                return str(bps)

            if bps >= 1e9:
                return f"{bps/1e9:.1f} Gbps"
            elif bps >= 1e6:
                return f"{bps/1e6:.1f} Mbps"
            elif bps >= 1e3:
                return f"{bps/1e3:.1f} Kbps"
            else:
                return f"{bps:.0f} bps"

        # ---------------- BAR BUILDER ----------------
        def bw_bar(df, title):
            df = df.sort_values("avg")

            fig = go.Figure(go.Bar(
                x=df["avg"],
                y=df["name"],
                orientation="h",

                # 🔥 Neon cyan bars
                marker=dict(
                    color="rgba(0,255,255,0.85)",
                    line=dict(color="rgba(0,255,255,1)", width=1.2),
                ),

                # 🔥 Clean labels
                text=[fmt_bw(v) for v in df["avg"]],
                textposition="outside",
                textfont=dict(color="#bffcff", size=11),

                # 🔥 Smooth hover
                hovertemplate="<b>%{y}</b><br>%{text}<extra></extra>",
            ))

            # ✅ Base theme
            fig = base_layout(fig,"")

            # 🔥 SOC glow styling
            fig.update_layout(
            
                template="plotly_dark",
                paper_bgcolor=CARD,
                plot_bgcolor=CARD,
                
                font=dict(color=TEXT),

                margin=dict(l=20, r=60, t=45, b=20),

                # 🔥 Grid glow effect
                xaxis=dict(
                    gridcolor="rgba(0,255,255,0.08)",
                    zeroline=False,
                    color=TEXT,
                    tickformat=".2s",
                ),

                yaxis=dict(
                    gridcolor="rgba(0,255,255,0.05)",
                    zeroline=False,
                    color=TEXT,
                ),
            )

            # 🔥 Add subtle glow overlay (hack using shadow-like effect)
            fig.update_traces(
                marker=dict(
                    color="rgba(0,255,255,0.9)",
                )
            )
            # fake glow via duplicate trace
            fig.add_trace(go.Bar(
                x=df["avg"],
                y=df["name"],
                orientation="h",
                marker=dict(color="rgba(0,255,255,0.15)"),
                hoverinfo="skip",
                showlegend=False
            ))

            return fig

        # ---------------- APPLICATIONS ----------------
        if not app_df.empty and {"name", "avg"}.issubset(app_df.columns):
            app_df = app_df.nlargest(5, "avg")
            fig1 = bw_bar(app_df, "Top Applications")
        else:
            fig1 = empty_chart("Top Applications")

        # ---------------- MALWARE ----------------
        if not mal_df.empty and {"name", "avg"}.issubset(mal_df.columns):
            mal_df = mal_df.nlargest(5, "avg")
            fig2 = bw_bar(mal_df, "Top Malware")
        else:
            fig2 = empty_chart("Top Malware")

        # ✅ FINAL GLOBAL ENFORCEMENT (last line of defense)
        fig1 = apply_dark_theme(fig1, "Top Applications")
        fig2 = apply_dark_theme(fig2, "Top Malware")

        return fig1, fig2

    @app.callback(
        Output("run_icon", "children"),
        Output("run_text", "children"),
        Input("interval", "n_intervals"),
    )
    def update_run_status_ui(_):
    
        status = progress.get("status", "idle")
    
        if status == "running":
            return (
                html.Span("⏳", style={"color": "#ffc107"}),
                "Processing..."
            )
    
        elif status == "completed":
            return (
                html.Span("✓", style={"color": "#00e5a0"}),
                "Analysis complete"
            )
    
        elif status == "error":
            return (
                html.Span("✖", style={"color": "#ff4d4d"}),
                "Error occurred"
            )
    
        else:
            return (
                html.Span("●", style={"color": "#888"}),
                "Idle"
            )
    # ================= CHARTS =================
    @app.callback(
        Output("top_ips", "figure"),
        Output("top_country", "figure"),
        Output("top_units", "figure"),
        Output("hourly", "figure"),
        Output("protocol", "figure"),
        Output("top_dst_ips", "figure"),
        Output("threat_map", "figure"),
        Output("top_src_ports", "figure"),
        Output("top_dst_ports", "figure"),
        Output("pkt_size", "figure"),
        Output("timeline", "figure"),
        Output("severity", "figure"),
        Output("top_dst_country", "figure"),
        Input("data_store", "data"),
        Input("branch_store", "data"),
    )
    def charts(data, branch):

        if not data:
            return [
                empty_chart("Top Source IPs"),
                empty_chart("Countries"),
                empty_chart("Units"),
                empty_chart("Hourly Attacks"),
                empty_chart("Protocol Distribution"),
                empty_chart("Destination IPs"),
                threat_map({}),
                empty_chart("Source Ports"),
                empty_chart("Destination Ports"),
                empty_chart("Packet Size"),
                empty_chart("Attack Timeline"),
                empty_chart("Threat Severity"),
                empty_chart("Destination Countries"),
            ]

        if branch == "all":
            s = data["summary"].get("all", {})
        else:
            s = data["summary"].get(branch, {})

        def to_df(key, col):
            val = s.get(key)
            if not val:
                return pd.DataFrame(columns=[col, "count"])
            return pd.DataFrame(list(val.items()), columns=[col, "count"])

        return (
            apply_dark_theme(bar(to_df("top_ips", "ip"), "ip", "Top Source IPs"), "Top Source IPs"),
            apply_dark_theme(bar(to_df("top_countries", "country"), "country", "Countries"), "Countries"),
            apply_dark_theme(bar(to_df("top_unit", "unit"), "unit", "Units"), "Units"),
            apply_dark_theme(hourly(to_df("attacks_by_hour", "hour")), "Hourly Attacks"),
            apply_dark_theme(protocol(to_df("protocol_dist", "protocol")), "Protocol Distribution"),
            apply_dark_theme(bar(to_df("top_dst_ips", "ip"), "ip", "Dest IPs"), "Destination IPs"),
            threat_map(s.get("top_countries", {})),  # no apply_dark_theme — would overwrite geo bgcolor and blank the map
            apply_dark_theme(bar(to_df("top_src_ports", "port"), "port", "Src Ports"), "Source Ports"),
            apply_dark_theme(bar(to_df("top_dst_ports", "port"), "port", "Dst Ports"), "Destination Ports"),
            apply_dark_theme(bar(to_df("pkt_size_dist", "size"), "size", "Pkt Size"), "Packet Size"),
            apply_dark_theme(timeline(to_df("timeline", "date")), "Attack Timeline"),
            apply_dark_theme(severity_gauge(None, s.get("total_attacks", 0)), "Threat Severity"),
            apply_dark_theme(bar(to_df("top_dst_countries", "country"), "country", "Dest Country"), "Destination Countries"),
        )


# ================= FLASK ROUTE FOR PDF DOWNLOAD =================
def register_pdf_route(flask_app):
    """Registers GET /download-pdf that streams the latest generated PDF."""
    from flask import send_file, abort, render_template_string, Response
    import mimetypes

    @flask_app.route("/download-pdf")
    def download_pdf():
        """Browse output/reports/pdf/ — lists all PDFs for viewing/download."""
        folder = progress.get("folder")
        base   = Path(folder) / "output" / "reports" / "pdf" if folder else None
        files, exists, bpath = _build_file_list(base, {".pdf"}, "/serve/pdf")
        return render_template_string(
            _BROWSER_TMPL,
            title="DCyA Report (PDF)",
            files=files,
            base_path=bpath,
            folder_exists=exists,
        )

    @flask_app.route("/serve/pdf-direct")
    def serve_pdf_direct():
        """Legacy: stream progress['pdf_path'] if pipeline sets it explicitly."""
        pdf_path = progress.get("pdf_path")
        if not pdf_path or not Path(pdf_path).exists():
            abort(404, "PDF not yet generated.")
        return send_file(
            pdf_path,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="SOC_REPORT_EXEC.pdf"
        )

    # ── shared file-browser HTML template ─────────────────────────────────
    _BROWSER_TMPL = """
<!DOCTYPE html><html lang="en">
<head>
<meta charset="UTF-8">
<title>NCCC // {{ title }}</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: #020c14;
    color: #c9d6e3;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    min-height: 100vh;
  }
  header {
    background: #0b1e2d;
    border-bottom: 1px solid rgba(0,255,255,0.15);
    padding: 12px 20px;
    display: flex;
    align-items: center;
    gap: 16px;
  }
  header a {
    color: #00ffff;
    text-decoration: none;
    font-size: 11px;
    border: 1px solid rgba(0,255,255,0.2);
    padding: 3px 10px;
    border-radius: 4px;
  }
  header a:hover { background: rgba(0,255,255,0.08); }
  h1 { color: #00ffff; font-size: 14px; letter-spacing: 1px; flex: 1; }
  .path-bar {
    background: rgba(0,255,255,0.04);
    border-bottom: 1px solid rgba(0,255,255,0.08);
    padding: 7px 20px;
    font-size: 11px;
    color: #4a6a8a;
    word-break: break-all;
  }
  .path-bar span { color: #00ffff; }
  .empty {
    text-align: center;
    padding: 60px 20px;
    color: #4a6a8a;
    font-size: 13px;
  }
  table { width: 100%; border-collapse: collapse; }
  thead tr {
    background: #0b1e2d;
    border-bottom: 1px solid rgba(0,255,255,0.12);
  }
  th {
    padding: 8px 16px;
    text-align: left;
    font-size: 10px;
    color: #4a6a8a;
    letter-spacing: 1px;
    text-transform: uppercase;
  }
  tbody tr {
    border-bottom: 1px solid rgba(0,255,255,0.05);
    transition: background 0.15s;
  }
  tbody tr:hover { background: rgba(0,255,255,0.04); }
  td { padding: 8px 16px; }
  td.icon { width: 32px; color: #00ffff; }
  td.name a {
    color: #c9d6e3;
    text-decoration: none;
  }
  td.name a:hover { color: #00ffff; }
  td.size { color: #4a6a8a; text-align: right; width: 90px; }
  td.date { color: #4a6a8a; font-size: 11px; width: 160px; }
  .badge {
    display: inline-block;
    padding: 1px 7px;
    border-radius: 3px;
    font-size: 10px;
    border: 1px solid rgba(0,255,255,0.2);
    color: #00ffff;
    margin-left: 6px;
    vertical-align: middle;
  }
</style>
</head>
<body>
<header>
  <h1>◈ NCCC // {{ title }}</h1>
  <a href="/">← Dashboard</a>
</header>
{% if base_path %}
<div class="path-bar">Path: <span>{{ base_path }}</span></div>
{% endif %}
{% if not files %}
<div class="empty">
  ⊘ No files found{% if not base_path or not folder_exists %} — run a pipeline first{% endif %}.
</div>
{% else %}
<table>
  <thead><tr>
    <th></th><th>Name</th><th class="size">Size</th><th class="date">Modified</th>
  </tr></thead>
  <tbody>
  {% for f in files %}
  <tr>
    <td class="icon">{{ f.icon }}</td>
    <td class="name">
      <a href="{{ f.href }}" {% if f.new_tab %}target="_blank"{% endif %}>
        {{ f.name }}
      </a>
      <span class="badge">{{ f.ext }}</span>
    </td>
    <td class="size">{{ f.size }}</td>
    <td class="date">{{ f.mtime }}</td>
  </tr>
  {% endfor %}
  </tbody>
</table>
{% endif %}
</body></html>
"""

    def _fmt_size(b):
        for unit in ["B", "KB", "MB", "GB"]:
            if b < 1024:
                return f"{b:.0f} {unit}"
            b /= 1024
        return f"{b:.1f} TB"

    def _file_icon(ext):
        return {
            ".pdf": "📄", ".json": "{ }", ".csv": "⊞",
            ".html": "🌐", ".htm": "🌐", ".txt": "📋",
            ".eml": "✉", ".msg": "✉", ".png": "🖼",
        }.get(ext.lower(), "◻")

    def _build_file_list(folder, exts=None, download_prefix=""):
        """Scan folder recursively and return list of file dicts for template."""
        if not folder:
            return [], False, ""
        base = Path(folder)
        if not base.exists():
            return [], False, str(base)

        results = []
        for p in sorted(base.rglob("*")):
            if not p.is_file():
                continue
            if exts and p.suffix.lower() not in exts:
                continue
            try:
                stat = p.stat()
                from datetime import datetime as _dt
                mtime = _dt.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                size  = _fmt_size(stat.st_size)
            except Exception:
                mtime, size = "—", "—"

            ext = p.suffix.lower()
            # Build download href
            rel = p.relative_to(base)
            href = f"{download_prefix}/{rel}"

            results.append({
                "icon":    _file_icon(ext),
                "name":    p.name,
                "ext":     ext.lstrip(".").upper() or "FILE",
                "href":    href,
                "size":    size,
                "mtime":   mtime,
                "new_tab": True,
            })
        return results, True, str(base)

    # ── /reports  →  output/reports/dcya ──────────────────────────────────
    @flask_app.route("/reports")
    def browse_reports():
        folder = progress.get("folder")
        base   = Path(folder) / "output" / "reports" / "dcya" if folder else None
        exts   = {".html", ".htm", ".txt", ".pdf"}
        files, exists, bpath = _build_file_list(base, exts, "/serve/reports")
        return render_template_string(
            _BROWSER_TMPL,
            title="DCyA Reports for SOC",
            files=files,
            base_path=bpath,
            folder_exists=exists,
        )

    # ── /json  →  output/reports/json ─────────────────────────────────────
    @flask_app.route("/json")
    def browse_json():
        folder = progress.get("folder")
        base   = Path(folder) / "output" / "reports" / "json" if folder else None
        files, exists, bpath = _build_file_list(base, {".json"}, "/serve/json")
        return render_template_string(
            _BROWSER_TMPL,
            title="JSON Files",
            files=files,
            base_path=bpath,
            folder_exists=exists,
        )

    # ── /csv  →  output/csv_cleaned ───────────────────────────────────────
    @flask_app.route("/csv")
    def browse_csv():
        folder = progress.get("folder")
        base   = Path(folder) / "output" / "csv_cleaned" if folder else None
        files, exists, bpath = _build_file_list(base, {".csv"}, "/serve/csv")
        return render_template_string(
            _BROWSER_TMPL,
            title="Cleaned CSV Files",
            files=files,
            base_path=bpath,
            folder_exists=exists,
        )

    # ── /mail  →  output/ioc_hits_mail ────────────────────────────────────
    @flask_app.route("/mail")
    def browse_mail():
        folder = progress.get("folder")
        base   = Path(folder) / "output" / "ioc_hits_mail" if folder else None
        files, exists, bpath = _build_file_list(base, {".eml", ".msg", ".txt", ".csv", ".html"}, "/serve/mail")
        return render_template_string(
            _BROWSER_TMPL,
            title="IOC Hit Mail Files",
            files=files,
            base_path=bpath,
            folder_exists=exists,
        )

    # NOTE: /charts is handled by Dash's dcc.Location + route_pages callback.
    # Do NOT add a Flask route for /charts — it would intercept before Dash.

    # ── Generic file servers (serve actual file for download/view) ─────────
    def _make_server(base_getter, prefix_strip=""):
        def _server(filepath):
            folder = progress.get("folder")
            if not folder:
                abort(404)
            base = base_getter(folder)
            full = (Path(base) / filepath).resolve()
            # Security: ensure path stays inside base
            try:
                full.relative_to(Path(base).resolve())
            except ValueError:
                abort(403)
            if not full.exists():
                abort(404)
            mime, _ = mimetypes.guess_type(str(full))
            mime = mime or "application/octet-stream"
            return send_file(str(full), mimetype=mime)
        _server.__name__ = f"_server_{prefix_strip}"
        return _server

    flask_app.add_url_rule(
        "/serve/reports/<path:filepath>",
        view_func=_make_server(
            lambda f: Path(f) / "output" / "reports" / "dcya", "reports"
        )
    )
    flask_app.add_url_rule(
        "/serve/json/<path:filepath>",
        view_func=_make_server(
            lambda f: Path(f) / "output" / "reports" / "json", "json"
        )
    )
    flask_app.add_url_rule(
        "/serve/csv/<path:filepath>",
        view_func=_make_server(
            lambda f: Path(f) / "output" / "csv_cleaned", "csv"
        )
    )
    flask_app.add_url_rule(
        "/serve/mail/<path:filepath>",
        view_func=_make_server(
            lambda f: Path(f) / "output" / "ioc_hits_mail", "mail"
        )
    )
    flask_app.add_url_rule(
        "/serve/pdf/<path:filepath>",
        view_func=_make_server(
            lambda f: Path(f) / "output" / "reports" / "pdf", "pdf"
        )
    )
