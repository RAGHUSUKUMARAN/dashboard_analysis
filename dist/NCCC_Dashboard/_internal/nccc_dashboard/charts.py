import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
pio.renderers.default = "browser"
from nccc_dashboard.utils import empty_chart
from nccc_dashboard.config import (
    BG, CARD, BORDER, TEXT, MUTED,
    ACCENT
)

import pycountry
import os

BASE_DIR = os.path.dirname(__file__)
CENTROID_FILE = os.path.join(BASE_DIR, "data", "country_centroids.csv")

if os.path.exists(CENTROID_FILE):
    centroids_df = pd.read_csv(CENTROID_FILE)
    centroid_map = dict(zip(centroids_df["iso3"], zip(centroids_df["lon"], centroids_df["lat"])))
else:
    print("[MAP ERROR] centroid file missing")
    centroid_map = {}

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN CONSTANTS  (single source of truth for all chart backgrounds)
# ─────────────────────────────────────────────────────────────────────────────
_PAPER = CARD          # outer chart background  — same for every chart
_PLOT  = CARD          # inner plot area         — same for every chart
_MAP_BG = "#020617"    # geo map ocean / paper   — kept dark for contrast


# ================= BASE =================
def base_layout(fig, title="", height=220):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=_PAPER,
        plot_bgcolor=_PLOT,
        font=dict(color=TEXT, family="'Courier New', monospace", size=12),
        margin=dict(l=20, r=20, t=45, b=30),
        height=height,
        showlegend=False,
        title=None
    )
    fig.update_xaxes(
        gridcolor=BORDER, zeroline=False,
        color=TEXT, showline=True, linecolor=BORDER
    )
    fig.update_yaxes(
        gridcolor=BORDER, zeroline=False,
        color=TEXT, showline=True, linecolor=BORDER
    )
    return fig


# ================= EMPTY =================
def empty(title=""):
    fig = go.Figure()
    fig = base_layout(fig, title)
    fig.add_annotation(
        text="No data available",
        x=0.5, y=0.5,
        xref="paper", yref="paper",
        showarrow=False,
        font=dict(size=13, color=MUTED)
    )
    fig.update_xaxes(showgrid=True, gridcolor=BORDER, zeroline=False, range=[0, 5])
    fig.update_yaxes(showgrid=True, gridcolor=BORDER, zeroline=False, range=[0, 5])
    return fig



# ================= BAR =================
def bar(df, col, title, max_items=10):
    if df is None or df.empty or col not in df.columns:
        return empty(title)

    df = df.copy()
    df[col] = df[col].astype(str)

    if "count" in df.columns:
        grp = df.groupby(col)["count"].sum()
    else:
        grp = df[col].value_counts()

    grp = grp.sort_values().tail(max_items).reset_index()
    grp.columns = [col, "count"]

    fig = go.Figure(go.Bar(
        x=grp["count"],
        y=grp[col],
        orientation="h",
        marker=dict(color=ACCENT),
        text=grp["count"],
        textposition="outside",
    ))
    return base_layout(fig, title)


# ================= HOURLY =================
def hourly(df):
    if df is None or df.empty:
        return empty("Attacks by Hour")

    fig = go.Figure(go.Bar(
        x=df["hour"],
        y=df["count"],
        marker=dict(color=ACCENT),
    ))
    return base_layout(fig, "Attacks by Hour")


# ================= TIMELINE =================
def timeline(df):
    if df is None or df.empty:
        return empty("Attack Timeline")

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).copy()
    df["count"] = pd.to_numeric(df["count"], errors="coerce")
    df = df.dropna(subset=["count"])

    if df.empty:
        return empty("Attack Timeline")

    df = df.groupby("date", as_index=False)["count"].sum()
    df = df.sort_values("date")

    fig = go.Figure(go.Scatter(
        x=df["date"],
        y=df["count"],
        mode="lines+markers",
        line=dict(color=ACCENT, width=2, shape="spline"),
        marker=dict(size=6),
        fill="tozeroy",
        fillcolor="rgba(0,255,255,0.08)"
    ))
    fig.update_xaxes(tickformat="%b %d", tickangle=-30)
    return base_layout(fig, "Attack Timeline", height=190)


# ================= PROTOCOL =================
def protocol(df):
    if df is None or df.empty:
        return empty("Protocol Distribution")

    fig = go.Figure(go.Pie(
        labels=df["protocol"],
        values=df["count"],
        hole=0.6
    ))
    fig = base_layout(fig, "Protocol Distribution")
    fig.update_layout(paper_bgcolor=_PAPER, plot_bgcolor=_PLOT)
    return fig


# ================= SEVERITY =================
def severity_gauge(_, total_attacks=0):
    value = min(total_attacks / 1000, 100) if total_attacks else 0

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        gauge=dict(
            axis=dict(range=[0, 100]),
            bar=dict(color="lime")
        )
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=_PAPER,
        plot_bgcolor=_PLOT,
        height=200,
        font=dict(color=TEXT)
    )
    return fig


# ================= MAP =================
def threat_map(data):
    import plotly.graph_objects as go
    import pandas as pd
    import base64
    import os
    import math
    import numpy as np

    # ---------------- PERFECT PROJECTION ----------------
    def project_to_map(lon, lat):
        x = (lon + 180) / 360
        lat_rad = math.radians(lat)
        y = 0.5 - (math.log(math.tan(math.pi/4 + lat_rad/2)) / (2 * math.pi))
        x = x * 360 - 180
        y = (1 - y) * 180 - 90
        return x, y

    # ---------------- COUNTRY → ISO ----------------
    def to_iso3(code):
        try:
            return pycountry.countries.get(alpha_2=code.upper()).alpha_3
        except:
            return code

    # ---------------- DATA ----------------
    if isinstance(data, dict):
        df = pd.DataFrame([
            {"country": to_iso3(k), "count": v}
            for k, v in data.items()
        ])
    else:
        return go.Figure()

    if df.empty:
        df = pd.DataFrame(columns=["country", "count"])

    # ---------------- TARGET COUNTRY ----------------
    DEST_COUNTRY = "IND"

    raw_lon, raw_lat = centroid_map.get(DEST_COUNTRY, (78, 21))
    dest_lon, dest_lat = project_to_map(raw_lon, raw_lat)

    # ---------------- MAP TO COORDS ----------------
    def get_coord(c):
        return centroid_map.get(c, (0, 0))

    coords = df["country"].map(get_coord)

    df["lon"] = coords.map(lambda c: project_to_map(c[0], c[1])[0])
    df["lat"] = coords.map(lambda c: project_to_map(c[0], c[1])[1])

    df = df[(df["lon"] != 0) & (df["lat"] != 0)]

    max_count = df["count"].max() if not df.empty else 1

    fig = go.Figure()

    # ---------------- MICRO ALIGNMENT FIX ----------------
    X_SHIFT = -3.5   # ← tweak this
    Y_SHIFT = 0

    df["lon"] += X_SHIFT
    df["lat"] += Y_SHIFT

    dest_lon += X_SHIFT
    dest_lat += Y_SHIFT
    
    # ---------------- NO DATA ----------------
    if df.empty:
        fig.update_layout(
            xaxis=dict(range=[-180, 180], visible=False),
            yaxis=dict(range=[-90, 90], visible=False),
            paper_bgcolor="#020617",
            plot_bgcolor="#020617",
            margin=dict(l=0, r=0, t=0, b=0),
        )

        fig.add_annotation(
            text="Awaiting Data...",
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(color="#00ffff", size=14)
        )

    else:

        # ---------------- FLOW LINES (CURVED) ----------------
        for _, row in df.iterrows():

            if row["country"] == DEST_COUNTRY:
                continue

            src_lon = row["lon"]
            src_lat = row["lat"]

            if pd.isna(src_lon) or pd.isna(src_lat):
                continue

            width = max(1, ((row["count"] / max_count) ** 0.5) * 5)

            num_points = 30

            lons = np.linspace(src_lon, dest_lon, num_points)
            lats = np.linspace(src_lat, dest_lat, num_points)

            mid_lon = (src_lon + dest_lon) / 2
            mid_lat = (src_lat + dest_lat) / 2

            curve_strength = 0.2 * abs(src_lon - dest_lon)

            for i in range(num_points):
                t = i / (num_points - 1)

                lons[i] = (1 - t)**2 * src_lon + 2*(1 - t)*t * mid_lon + t**2 * dest_lon
                lats[i] = (1 - t)**2 * src_lat + 2*(1 - t)*t * (mid_lat + curve_strength) + t**2 * dest_lat

            fig.add_trace(go.Scatter(
                x=lons,
                y=lats,
                mode="lines",
                line=dict(width=width, color="rgba(0,255,255,0.25)"),
                hoverinfo="skip",
                showlegend=False
            ))

        # ---------------- TARGET NODE ----------------
        fig.add_trace(go.Scatter(
            x=[dest_lon],
            y=[dest_lat],
            mode="markers+text",
            text=["TARGET"],
            textposition="bottom center",
            marker=dict(
                size=18,
                color="#ff3b3b",
                line=dict(color="white", width=1.5)
            ),
            hovertemplate="<b>Target</b><extra></extra>"
        ))

        # ---------------- GLOW ----------------
        fig.add_trace(go.Scatter(
            x=df["lon"],
            y=df["lat"],
            mode="markers",
            marker=dict(
                size=((df["count"] / max_count) ** 0.5) * 50 + 10,
                color="rgba(0,255,255,0.15)"
            ),
            hoverinfo="skip",
            showlegend=False
        ))

        # ---------------- MAIN POINTS ----------------
        fig.add_trace(go.Scatter(
            x=df["lon"],
            y=df["lat"],
            mode="markers",
            customdata=df[["country", "count"]],
            marker=dict(
                size=((df["count"] / max_count) ** 0.4) * 30 + 8,
                color=df["count"],
                colorscale=[
                    [0.0, "#003f5c"],
                    [0.3, "#00bcd4"],
                    [0.6, "#00ffff"],
                    [1.0, "#00ff9f"]
                ],
                showscale=True,
                colorbar=dict(title="Attacks"),
                line=dict(color="#ffffff", width=0.6)
            ),
            hovertemplate="<b>%{customdata[0]}</b><br>Attacks: %{customdata[1]:,}<extra></extra>"
        ))

    # ---------------- BACKGROUND MAP ----------------
    BASE_DIR = os.path.dirname(__file__)
    img_path = os.path.join(BASE_DIR, "assets", "world_map.png")

    if not os.path.exists(img_path):
        print("[MAP ERROR] world_map.png not found:", img_path)
        return fig

    with open(img_path, "rb") as f:
        encoded_image = base64.b64encode(f.read()).decode()

    fig.update_layout(
        xaxis=dict(range=[-180, 180], visible=False),
        yaxis=dict(range=[-90, 90], visible=False),
        paper_bgcolor="#020617",
        plot_bgcolor="#020617",
        margin=dict(l=0, r=0, t=0, b=0),
        images=[dict(
            source=f"data:image/png;base64,{encoded_image}",
            xref="x",
            yref="y",
            x=-180,
            y=90,
            sizex=360,
            sizey=180,
            sizing="stretch",
            opacity=0.18,
            layer="below"
        )]
    )

    return fig