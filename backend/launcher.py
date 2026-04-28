"""
StagicOSINT - Launcher
Entry point for the compiled .exe (PyInstaller).
Starts FastAPI + opens a browser window automatically.
"""
import sys
import os
import threading
import webbrowser
import time

# ── PyInstaller setup ──────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    # Add the bundle's extraction folder to sys.path so all modules resolve
    sys.path.insert(0, sys._MEIPASS)
    # Write ogi.db next to the .exe, not into the temp extraction folder
    os.chdir(os.path.dirname(sys.executable))

# ── Import the app OBJECT (not a string) so uvicorn can find it when frozen ─
from main import app  # noqa: E402  (must come after sys.path is patched)
import uvicorn        # noqa: E402

HOST = "127.0.0.1"
PORT = 8000
URL  = f"http://{HOST}:{PORT}"


def _open_browser():
    time.sleep(2.5)
    webbrowser.open(URL)


if __name__ == "__main__":
    print(f"  StagicOSINT starting at {URL}")
    print("  Press Ctrl+C to stop.\n")

    t = threading.Thread(target=_open_browser, daemon=True)
    t.start()

    # Pass the app object directly — avoids the "cannot import module main" error
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="warning",
        access_log=False,
    )
