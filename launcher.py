import threading
import webbrowser
import time
from tkinter import Tk, filedialog

def select_folder():
    root = Tk()
    root.withdraw()  # hide main window
    folder = filedialog.askdirectory(title="Select Input Folder")
    return folder

def run_backend(folder):
    from backend import process
    process(folder)

def run_dashboard():
    from app import app
    app.run_server(debug=False)

if __name__ == "__main__":
    # 👇 OPEN FOLDER PICKER
    folder = select_folder()

    if not folder:
        print("No folder selected. Exiting...")
        exit()

    print(f"Selected folder: {folder}")

    # 👇 RUN BACKEND
    threading.Thread(target=run_backend, args=(folder,), daemon=True).start()

    # 👇 WAIT A BIT
    time.sleep(5)

    # 👇 OPEN DASHBOARD
    webbrowser.open("http://127.0.0.1:8050")

    # 👇 RUN DASH APP
    run_dashboard()