from dash import html


def kpi_card(title, value, color):

    # ===== SAFE VALUE HANDLING =====
    if value is None or value == "":
        value = "-"

    return html.Div(
        [

            # ===== VALUE =====
            html.Div(
                str(value),
                style={
                    "fontSize": "20px",          # 🔥 slightly tighter
                    "fontWeight": "600",        # 🔥 cleaner than bold
                    "color": color,
                    "whiteSpace": "nowrap",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                }
            ),

            # ===== TITLE =====
            html.Div(
                title,
                style={
                    "fontSize": "10px",
                    "color": "#9CA3AF",
                    "marginTop": "2px",
                    "letterSpacing": "0.3px"   # 🔥 premium touch
                }
            ),

        ],
        style={
            "background": "#111827",            # 🔥 match dashboard cards
            "padding": "6px",
            "borderRadius": "8px",

            # 🔥 softer border (not loud color)
            "border": "1px solid #1f2937",

            # 🔥 subtle glow instead of heavy shadow
            "boxShadow": "0 0 4px rgba(0,0,0,0.4)",

            # ===== LAYOUT =====
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "center",

            # ===== SIZE CONTROL =====
            "minWidth": "110px",
            "maxWidth": "100%",

            # 🔥 micro interaction (feels premium)
            "transition": "0.2s",
            "cursor": "default"
        }
    )