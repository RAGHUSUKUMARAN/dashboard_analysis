from pathlib import Path
import sys

# ================= UI THEME (SOC Dark) =================
BG      = "#050A14"        # near-black deep navy
CARD    = "#0A1628"        # dark card
CARD2   = "#0D1F3C"        # slightly lighter card
BORDER  = "#1B3A6B"        # subtle blue border
TEXT    = "#CBD5E1"        # primary text
MUTED   = "#64748B"        # muted / secondary text
ACCENT  = "#00D4FF"        # cyan accent
GREEN   = "#10B981"        # safe / green
YELLOW  = "#F59E0B"        # warning
RED     = "#EF4444"        # critical / alert
ORANGE  = "#F97316"        # high severity

SEVERITY_COLORS = {
    "critical": RED,
    "high":     ORANGE,
    "medium":   YELLOW,
    "low":      GREEN,
}

# ================= PATHS =================
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_SCRIPT = BASE_DIR / "NCCC_AUTOMATION_test.py"
BACKEND_PYTHON = sys.executable

# ================= RUNTIME STATE =================
progress = {
    "logs":    [],
    "running": False,
    "percent": 0,
    "done":    False,
    "folder":  None,
}

# ================= BRANCHES =================
BRANCHES = ["all", "airforce", "navy", "ids", "nkn", "web", "white", "red"]
BRANCH_LABELS = {
    "all":      "ALL",
    "airforce": "AIR FORCE",
    "navy":     "NAVY",
    "ids":      "IDS",
    "nkn":      "NKN",
    "web":      "WEB",
    "white":    "WHITE",
    "red":      "RED",
}
