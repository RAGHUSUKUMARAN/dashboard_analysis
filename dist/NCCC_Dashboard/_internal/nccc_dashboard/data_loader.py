"""
data_loader.py

Loads dashboard data from the ioc_hits_mail/ folder that the pipeline writes.
Returns {"df": DataFrame, "summary_map": dict}.
"""

from pathlib import Path
from nccc_dashboard.config import progress
import pandas as pd
import json


def _log(msg: str):
    progress["logs"].append(msg)


RENAME_MAP = {
    "dstn ip":               "destination ip",
    "destination ip":        "destination ip",
    "dstn country":          "destination country",
    "destination country":   "destination country",
    "dstn port":             "destination port",
    "destination port":      "destination port",
    "source ip":             "source ip",
    "source country":        "source country",
    "source port":           "source port",
    "tcp flag":              "tcp flag",
    "pkt count":             "pkt count",
    "pkt size":              "pkt size",
    "protocol":              "protocol",
    "unit":                  "unit",
    "branch":                "branch",
}


def load(folder: str) -> dict | None:
    _log("📥 Loading dashboard data...")

    try:
        path        = Path(folder)
        summary_dir = path / "ioc_hits_mail"

        if not summary_dir.exists():
            _log("❌ ioc_hits_mail not found — pipeline may not have run yet")
            return None

        # ── 1. Summary JSON ──────────────────────────────────────────
        master = summary_dir / "summary_all_branches.json"
        if master.exists():
            with open(master, "r", encoding="utf-8") as fh:
                summary_map = json.load(fh)
            _log(f"✅ Summary loaded | branches: {list(summary_map.keys())}")
        else:
            # Try stitching individual branch files
            _log("⚠️  Master summary missing — trying per-branch fallback")
            summary_map = {}
            for f in summary_dir.glob("summary_*.json"):
                try:
                    key = f.stem.replace("summary_", "")
                    with open(f, encoding="utf-8") as fh:
                        summary_map[key] = json.load(fh)
                except Exception as e:
                    _log(f"  ⚠️  {f.name}: {e}")
            if not summary_map:
                _log("❌ No summary data found")
                return None

        # ── 2. IOC hit CSVs (for raw df / timeline / filters) ───────
        # Prefer the consolidated file the pipeline writes
        consolidated = summary_dir / "all_ioc_hits_mail.csv"
        csv_files    = []

        if consolidated.exists():
            csv_files = [consolidated]
        else:
            csv_files = sorted(summary_dir.rglob("*_ioc_hits_mail.csv"))[:20]

        if not csv_files:
            _log("⚠️  No IOC CSV files — charts will use summary only")
            df = pd.DataFrame()
        else:
            dfs = []
            for f in csv_files:
                try:
                    temp = pd.read_csv(
                        f, dtype=str, nrows=5000,
                        encoding="latin1", on_bad_lines="skip"
                    )
                    temp.columns = temp.columns.str.lower().str.strip()
                    temp.rename(columns=RENAME_MAP, inplace=True)

                    for col in ["branch", "unit", "source ip", "source country",
                                "destination ip", "protocol"]:
                        if col not in temp.columns:
                            temp[col] = "unknown"

                    dfs.append(temp)
                except Exception as e:
                    _log(f"  ⚠️  {f.name}: {e}")

            df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

        # ── Parse time in df ─────────────────────────────────────────
        if not df.empty:
            for tc in ["time", "timestamp", "date", "flow start"]:
                if tc in df.columns:
                    numeric = pd.to_numeric(df[tc], errors="coerce")
                    if numeric.notna().sum() > len(df) * 0.5:
                        unit = "ms" if numeric.median() > 1e10 else "s"
                        df["time"] = pd.to_datetime(numeric, unit=unit, errors="coerce")
                    else:
                        df["time"] = pd.to_datetime(df[tc], errors="coerce", dayfirst=True)
                    break

        _log(f"✅ Data ready | rows: {len(df)}")
        return {"df": df, "summary_map": summary_map}

    except Exception as e:
        _log(f"❌ Loader crashed: {e}")
        return None
