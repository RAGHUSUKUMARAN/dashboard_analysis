from dash import html, dcc
from nccc_dashboard.config import *
from nccc_dashboard.utils import empty_chart
from nccc_dashboard.utils import kpi_card
from nccc_dashboard.charts import threat_map


# ================= COMMON =================
def mono(size=11, color=TEXT, weight="normal"):
    return {
        "fontFamily": "'Courier New', monospace",
        "fontSize": f"{size + 2}px",
        "color": color,
        "fontWeight": weight,
    }


def card():
    return {
        "background": CARD,
        "border": f"1px solid {BORDER}",
        "borderRadius": "7px",
        "padding": "7px 8px",
    }


def graph_card():
    return {
        **card(),
        "display": "flex",
        "flexDirection": "column",
        "overflow": "hidden",
        "minHeight": "0",
        "height": "100%",
    }


def _threat_card(title, id_):
    return html.Div([
        html.Div(title, style=mono(9, MUTED)),
        html.Div(id=id_, style={
            **mono(12, ACCENT, "bold"),
            "overflow": "hidden",
            "textOverflow": "ellipsis",
            "whiteSpace": "nowrap"
        }),
    ], style={"textAlign": "center"})

def _mini_card():
    return {
        "border": "1px solid rgba(0,255,255,0.12)",
        "borderRadius": "6px",
        "padding": "4px",
        "background": "rgba(0,255,255,0.02)",
        "textAlign": "center"
    }

def home_page():
    return html.Div([
        kpi_row(),
        row_a(),
        row_b(),
        row_c(),
        row_d(),
    ])

def charts_page():
    # Hidden stubs for IDs that callbacks always write to but are only
    # rendered in row_a / kpi_row on home_page. Without these, Dash
    # raises "ID not found" and ALL chart callbacks silently abort.
    hidden_stubs = html.Div([
        html.Div(id="kpis",                    style={"display": "none"}),
        html.Div(id="top_attacker",            style={"display": "none"}),
        html.Div(id="attack_country",          style={"display": "none"}),
        html.Div(id="attack_protocol",         style={"display": "none"}),
        html.Div(id="target_unit",             style={"display": "none"}),
        html.Pre( id="logs",                   style={"display": "none"}),
        html.Div(id="run_icon",                style={"display": "none"}),
        html.Div(id="run_text",                style={"display": "none"}),
        html.Div(id="run_status_bottom",       style={"display": "none"}),
        html.Div(id="pdf_download_area_bottom",style={"display": "none"}),
        dcc.Graph(id="threat_map",             style={"display": "none"},
                  config={"displayModeBar": False}),
    ], style={"display": "none"})

    return html.Div([
        html.Div("◈ FULL CHARTS VIEW", style={
            **mono(14, ACCENT, "bold"),
            "padding": "8px 12px",
            "borderBottom": f"1px solid {BORDER}",
        }),
        hidden_stubs,
        row_b(),
        row_c(),
        row_d(),
    ])

def reports_page():
    return html.Div([
        html.H3("📋 DCyA Reports", style=mono(14, ACCENT, "bold")),
        html.Iframe(
            src="/reports",
            style={"width": "100%", "height": "80vh", "border": "none"}
        )
    ])


def json_page():
    return html.Div([
        html.H3("{ } JSON Files", style=mono(14, ACCENT, "bold")),
        html.Iframe(
            src="/json",
            style={"width": "100%", "height": "80vh", "border": "none"}
        )
    ])


def csv_page():
    return html.Div([
        html.H3("⊞ CSV Files", style=mono(14, ACCENT, "bold")),
        html.Iframe(
            src="/csv",
            style={"width": "100%", "height": "80vh", "border": "none"}
        )
    ])


def mail_page():
    return html.Div([
        html.H3("✉ IOC Mail Files", style=mono(14, ACCENT, "bold")),
        html.Iframe(
            src="/mail",
            style={"width": "100%", "height": "80vh", "border": "none"}
        )
    ])
# ================= BRANCH COLORS =================
BRANCH_COLORS = {
    "all": {"bg": ACCENT, "color": BG},
    "airforce": {"bg": "#00bfff", "color": BG},
    "navy": {"bg": "#f0f0f0", "color": "#000"},
    "red": {"bg": "#ff4d4d", "color": "#fff"},
    "white": {"bg": "#ffffff", "color": "#000"},
    "ids": {"bg": "#b266ff", "color": "#fff"},
    "nkn": {"bg": "#ff66cc", "color": "#fff"},
    "web": {"bg": "#33cc99", "color": BG},
}


# ================= TOP BAR =================
def top_bar():
    return html.Div([
        html.Span("◈ NCCC // TRAFFIC MONITORING & ANALYSIS",
                  style=mono(14, ACCENT, "bold")),

        html.Div([
            dcc.Input(
                id="folder",
                placeholder="Enter data folder path...",
                style={
                    "width": "450px",
                    "background": CARD,
                    "border": f"1px solid {BORDER}",
                    "color": TEXT,
                    "padding": "5px 9px",
                    "borderRadius": "5px",
                    "fontFamily": "'Courier New', monospace",
                }
            ),
            html.Button("▶ ANALYZE", id="run", style={
                "background": ACCENT,
                "color": BG,
                "padding": "5px 12px",
                "border": "none",
                "borderRadius": "5px",
                "cursor": "pointer",
            }),
            html.Div(id="run_status", style=mono(10, ACCENT)),
            html.Div(id="pdf_download_area"),
        ], style={"display": "flex", "gap": "8px"}),

        html.Div([
            html.Div(id="live_clock", style=mono(10, ACCENT)),
            # ======= HAMBURGER BUTTON =======
            html.Button(
                [html.Span(style={
                    "display": "block", "width": "20px", "height": "2px",
                    "background": ACCENT, "margin": "4px 0",
                }) for _ in range(3)],
                id="nav_toggle",
                n_clicks=0,
                title="Navigation Menu",
                style={
                    "background": "transparent",
                    "border": f"1px solid {BORDER}",
                    "borderRadius": "5px",
                    "padding": "6px 8px",
                    "cursor": "pointer",
                    "display": "flex",
                    "flexDirection": "column",
                    "justifyContent": "center",
                    "alignItems": "center",
                    "height": "32px",
                    "width": "38px",
                    "marginLeft": "10px",
                }
            ),
        ], style={"display": "flex", "alignItems": "center", "gap": "10px"}),
    ], style={
        "display": "flex",
        "justifyContent": "space-between",
        "padding": "8px 12px",
        "borderBottom": f"1px solid {BORDER}",
        "background": CARD,
    })


# ================= BRANCH BAR =================
def branch_bar():
    return html.Div([
        html.Button(
            b.upper(),
            id=f"btn_{b}",
            style={
                "background": BRANCH_COLORS.get(b, {"bg": CARD})["bg"],
                "color": BRANCH_COLORS.get(b, {"color": TEXT})["color"],
                "border": "none",
                "padding": "3px 10px",
                "borderRadius": "4px",
                "cursor": "pointer",
                "fontFamily": "'Courier New', monospace",
            }
        )
        for b in BRANCHES
    ], style={
        "display": "flex",
        "gap": "5px",
        "padding": "5px 12px",
        "borderBottom": f"1px solid {BORDER}",
        "background": BG,
    })


# ================= KPI ROW =================
def kpi_row():
    return html.Div(
        id="kpis",
        style={
            "display": "grid",
            "gridTemplateColumns": "repeat(10, 1fr)",
            "gap": "5px",
            "padding": "6px 12px",
            "borderBottom": f"1px solid {BORDER}",
        }
    )



# ================= ROW A =================
def row_a():
    return html.Div([

        # ================= Threat Intelligence =================
        html.Div([
        
            html.Div("⚠ Threat Intelligence", style=mono(11, ACCENT, "bold")),

            # 🔥 TOP ATTACKER (PRIMARY)
            html.Div([
                html.Div("TOP ATTACKER", style=mono(8, MUTED)),
                html.Div(id="top_attacker", style=mono(13, "#00ffff", "bold")),
            ], style={
                "border": "1px solid rgba(0,255,255,0.15)",
                "borderRadius": "6px",
                "padding": "6px",
                "marginBottom": "4px",
                "background": "rgba(0,255,255,0.03)"
            }),

            # 🔥 GRID INFO
            html.Div([
            
                html.Div([
                    html.Div("COUNTRY", style=mono(8, MUTED)),
                    html.Div(id="attack_country", style=mono(11, ACCENT, "bold")),
                ], style=_mini_card()),

                html.Div([
                    html.Div("PROTOCOL", style=mono(8, MUTED)),
                    html.Div(id="attack_protocol", style=mono(11, ACCENT, "bold")),
                ], style=_mini_card()),

                html.Div([
                    html.Div("TARGET UNIT", style=mono(8, MUTED)),
                    html.Div(id="target_unit", style=mono(10, TEXT)),
                ], style={**_mini_card(), "gridColumn": "span 2"}),

            ], style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr",
                "gap": "4px",
                "flex": "1"
            }),

        ], style={
            **graph_card(),
            "width": "200px",
            "height": "100%",
            "display": "flex",
            "flexDirection": "column"
        }),

        # ================= Threat Map =================
        html.Div([
            html.Div("⊙ Threat Map — Global Origins", style=mono(11, ACCENT, "bold")),

            html.Div([   # 🔥 CRITICAL WRAPPER (fixes rendering)
                dcc.Graph(
                    id="threat_map",
                    figure=threat_map({}),
                    config={
                        "displayModeBar": False,
                        "staticPlot": False
                    },
                    style={
                        "height": "100%",
                        "width": "100%",
                        "minHeight": "320px"
                    },
                    clear_on_unhover=True
                ),
            ], style={
                "height": "100%",
                "width": "100%",
                "flex": "1",
                "minHeight": "0"
            }),

        ], style={
            **graph_card(),
            "flex": "1",
            "height": "100%",
            "display": "flex",
            "flexDirection": "column"
        }),

        # ================= Processing Logs =================
        html.Div([
            html.Div("⌥ Processing Logs", style=mono(11, ACCENT, "bold")),

            html.Div(
                html.Pre(
                    id="logs",
                    style={
                        "color": "lime",
                        "fontSize": "10px",
                        "margin": "0"
                    }
                ),
                style={
                    "flex": "1",
                    "overflowY": "auto",
                }
            ),

        ], style={
            **graph_card(),
            "width": "240px",
            "height": "100%",
            "display": "flex",
            "flexDirection": "column"
        }),

    ], style={
        "display": "flex",
        "gap": "6px",
        "height": "320px",   # ✅ fixed height for geo rendering
        "minHeight": "300px",
    })


# ================= GENERIC PANEL =================
def _chart_panel(title, chart_id):
    return html.Div([
        html.Div(title, style=mono(11, ACCENT, "bold")),
        dcc.Graph(
            id=chart_id,
            figure=empty_chart(""),
            config={"displayModeBar": False},
            style={"flex": "1", "backgroundColor": BG},
        ),
    ], style={**graph_card()})


# ================= ROW B =================
def row_b():
    charts = [
        ("▲ Top Attacking IPs", "top_ips"),
        ("▲ Top Destination IPs", "top_dst_ips"),
        ("⊞ Attack Origin Countries", "top_country"),
        ("⊞ Destination Countries", "top_dst_country"),
        ("◉ Top Units", "top_units"),
    ]
    return html.Div([_chart_panel(t, i) for t, i in charts], style={
        "display": "grid",
        "gridTemplateColumns": "repeat(5, 1fr)",
        "gap": "5px",
    })


# ================= ROW C =================
def row_c():
    charts = [
        ("◎ Traffic Protocol Breakdown", "protocol"),
        ("⇅ Source Ports", "top_src_ports"),
        ("⇅ Destination Ports", "top_dst_ports"),
        ("≋ Packet Size Dist", "pkt_size"),
        ("◈ Severity Distribution", "severity"),
    ]
    return html.Div([_chart_panel(t, i) for t, i in charts], style={
        "display": "grid",
        "gridTemplateColumns": "repeat(5, 1fr)",
        "gap": "5px",
    })


# ================= ROW D =================
def row_d():
    return html.Div([

        _chart_panel("∿ Attack Activity Timeline", "timeline"),
        _chart_panel("⊡ Hourly Pattern", "hourly"),
        _chart_panel("⊟ Top Bandwidth Applications", "top_apps"),
        _chart_panel("☣ Detected Malware Traffic", "top_malware"),

        html.Div([
            html.Div("⬡ Run Status", style=mono(9, ACCENT, "bold")),
            html.Div(id="run_icon", style={"fontSize": "30px", "textAlign": "center"}),
            html.Div(id="run_text", style=mono(9, MUTED)),
            html.Div(id="run_status_bottom", style=mono(10, ACCENT)),
            html.Div(id="pdf_download_area_bottom"),
        ], style={**graph_card()}),

    ], style={
        "display": "grid",
        "gridTemplateColumns": "2fr 1fr 1fr 1fr 1fr",
        "gap": "5px",
        "minHeight": "220px",
        "height": "auto",
    })


# ================= STATUS BAR =================
def _status_bar():
    return html.Div([
        html.Span("LIVE — AUTO-REFRESH 1500ms", style=mono(9, MUTED)),
        html.Span("NCCC TRAFFIC MONITORING SYSTEM v2.1", style=mono(9, MUTED)),
        html.Span(id="status_date", style=mono(9, MUTED)),
    ], style={
        "display": "flex",
        "justifyContent": "space-between",
        "padding": "4px 12px",
        "borderTop": f"1px solid {BORDER}",
        "background": CARD,
    })


# ================= NAV DRAWER =================
def nav_drawer():
    """Slide-out navigation panel from the right side."""

    def nav_link(icon, label, href, description="", target="_blank"):
        return html.A(
            href=href,
            target=target,
            style={"textDecoration": "none"},
            children=html.Div([
                html.Div([
                    html.Span(icon, style={
                        "fontSize": "18px",
                        "width": "28px",
                        "textAlign": "center",
                        "flexShrink": "0",
                    }),
                    html.Div([
                        html.Div(label, style={
                            "fontFamily": "'Courier New', monospace",
                            "fontSize": "13px",
                            "color": TEXT,
                            "fontWeight": "bold",
                        }),
                        html.Div(description, style={
                            "fontFamily": "'Courier New', monospace",
                            "fontSize": "10px",
                            "color": MUTED,
                            "marginTop": "1px",
                        }) if description else None,
                    ]),
                ], style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "12px",
                }),
            ], style={
                "padding": "10px 14px",
                "borderRadius": "6px",
                "border": f"1px solid {BORDER}",
                "background": "rgba(0,255,255,0.02)",
                "cursor": "pointer",
                "transition": "all 0.2s ease",
                "marginBottom": "6px",
            })
        )

    def section_label(text):
        return html.Div(text, style={
            "fontFamily": "'Courier New', monospace",
            "fontSize": "9px",
            "color": MUTED,
            "letterSpacing": "2px",
            "textTransform": "uppercase",
            "marginTop": "16px",
            "marginBottom": "6px",
            "paddingLeft": "4px",
            "borderLeft": f"2px solid {ACCENT}",
            "paddingLeft": "8px",
        })

    return html.Div([

        # ── Dark overlay (click to close) ──────────────────────────────
        html.Div(
            id="nav_overlay",
            n_clicks=0,
            style={
                "position": "fixed",
                "top": "0", "left": "0",
                "width": "100vw", "height": "100vh",
                "background": "rgba(0,0,0,0.55)",
                "zIndex": "1000",
                "display": "none",
                "cursor": "pointer",
            }
        ),

        # ── Drawer panel ───────────────────────────────────────────────
        html.Div([

            # Header
            html.Div([
                html.Span("◈ NCCC NAVIGATOR", style={
                    "fontFamily": "'Courier New', monospace",
                    "fontSize": "13px",
                    "color": ACCENT,
                    "fontWeight": "bold",
                    "letterSpacing": "1px",
                }),
                html.Button("✕", id="nav_close", n_clicks=0, style={
                    "background": "transparent",
                    "border": "none",
                    "color": MUTED,
                    "fontSize": "16px",
                    "cursor": "pointer",
                    "padding": "0 4px",
                    "lineHeight": "1",
                }),
            ], style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "paddingBottom": "12px",
                "marginBottom": "8px",
                "borderBottom": f"1px solid {BORDER}",
            }),

            # ── Links ───────────────────────────────────────────────────
            section_label("Dashboard"),
            nav_link("⌂", "Home", "/", "Main dashboard view", target="_self"),
            nav_link("◈", "Charts View", "/charts", "All charts fullscreen", target="_self"),

            section_label("Reports"),
            nav_link("📋", "DCyA Reports for SOC",  "/reports",    "HTML & text reports"),
            nav_link("📄", "DCyA Report (PDF)",     "/download-pdf",      "Download executive PDF"),

            section_label("Data Files"),
            nav_link("{ }", "JSON Files",           "/json",       "Raw summary JSON"),
            nav_link("⊞",  "Cleaned CSV Files",    "/csv",        "Processed CSV tables"),
            nav_link("✉",  "IOC Hit Mail Files",   "/mail",       "IOC alert mail files"),

        ], id="nav_drawer", style={
            "position": "fixed",
            "top": "0",
            "right": "-320px",          # hidden off-screen initially
            "width": "300px",
            "height": "100vh",
            "background": CARD,
            "borderLeft": f"1px solid {BORDER}",
            "zIndex": "1001",
            "overflowY": "auto",
            "padding": "16px 14px",
            "boxSizing": "border-box",
            "transition": "right 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
        }),

    ])


# ================= MAIN =================
def serve_layout():
    return html.Div([

        dcc.Location(id="url", refresh=False),   # ✅ ADD THIS

        top_bar(),
        branch_bar(),

        # 👇 REPLACE everything below with page container
        html.Div(id="page_content", style={
            "display": "flex",
            "flexDirection": "column",
            "gap": "5px",
            "padding": "5px 12px",
            "overflowY": "auto",
            "flex": "1",
        }),

        _status_bar(),

        dcc.Store(id="data_store"),
        dcc.Store(id="branch_store", data="all"),
        dcc.Interval(id="interval", interval=1500),
        dcc.Interval(id="clock_interval", interval=1000),

        nav_drawer(),

    ], style={
        "background": BG,
        "minHeight": "100vh",
        "display": "flex",
        "flexDirection": "column",
    })