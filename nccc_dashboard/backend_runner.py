import threading
import json
from pathlib import Path

from nccc_dashboard.backend import process
from nccc_dashboard.config import progress


# ================= THREAD RUNNER =================
def start_backend(folder):

    def _run():
        try:
            print("🚀 Starting NCCC pipeline...", flush=True)

            # 🔥 IMPORTANT: store folder for dashboard
            progress["folder"] = folder
            progress["done"] = False

            summaries = process(folder)

            progress["done"] = True

            print("🎯 Pipeline finished", flush=True)

        except Exception as e:
            print("❌ Critical error:", e, flush=True)
            import traceback
            traceback.print_exc()
            progress["done"] = True

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()


# ================= DATA LOADER =================
def get_data():

    folder = progress.get("folder")

    if not folder:
        print("⚠ No folder set")
        return None, 0

    base = Path(folder)

    # 🔥 NEW CORRECT PATH
    summary_file = base / "reports" / "json" / "summary_all.json"

    if not summary_file.exists():
        print("⚠ Master summary missing — trying fallback")

        # fallback: check any branch file
        json_dir = base / "reports" / "json"
        if json_dir.exists():
            files = list(json_dir.glob("summary_*.json"))
            if files:
                summary_file = files[0]
            else:
                print("❌ No summary files found")
                return None, 0
        else:
            print("❌ JSON folder missing")
            return None, 0

    try:
        with open(summary_file, "r") as f:
            summary = json.load(f)

        print("✅ Summary loaded")

        return {
            "summary_map": summary
        }, summary.get("all", {}).get("total_attacks", 0)

    except Exception as e:
        print("❌ Failed to load summary:", e)
        return None, 0