import dash
from nccc_dashboard.layout import serve_layout
from nccc_dashboard.callbacks import register_callbacks, register_pdf_route
from dash import Input, Output
# ───────────────────────────────────────────
# Global CSS — fully offline, system monospace fonts only
# ───────────────────────────────────────────
CUSTOM_CSS = """
    * { box-sizing: border-box; }

    body {
        margin: 0;
        padding: 0;
        background: #050A14;
        font-family: 'Courier New', Courier, 'Lucida Console', monospace;
        color: #CBD5E1;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: #0A1628; }
    ::-webkit-scrollbar-thumb { background: #1B3A6B; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #00D4FF; }

    /* Plotly chart backgrounds */
    .js-plotly-plot .plotly .main-svg { border-radius: 6px; }

    /* Input focus */
    input:focus { outline: 1px solid #00D4FF !important; }

    /* Button hover states */
    button:hover { opacity: 0.85; }

    /* Card glow on hover */
    .soc-card:hover {
        border-color: #00D4FF !important;
        box-shadow: 0 0 12px rgba(0,212,255,0.12);
    }
"""

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    title="NCCC — SOC Dashboard",
    update_title=None,
)

server = app.server

# Inject custom CSS
app.index_string = f"""<!DOCTYPE html>
<html>
    <head>
        {{%metas%}}
        <title>{{%title%}}</title>
        {{%favicon%}}
        {{%css%}}
        <style>
            {CUSTOM_CSS}
        </style>
    </head>
    <body>
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
    </body>
</html>"""

app.layout = serve_layout

register_callbacks(app)
register_pdf_route(server)   # registers /reports /json /csv /mail /download-pdf

if __name__ == "__main__":
    app.run(
        debug=False,       # CRITICAL: debug=True forks a second process whose
                           # globals are isolated from the background worker thread.
        host="127.0.0.1",
        port=8050,
        use_reloader=False,
    )


