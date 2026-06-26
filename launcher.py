#!/usr/bin/env python3
"""
launcher.py — PyInstaller entry point for a bundled Libra build.

A Streamlit app cannot be frozen directly (it runs via the `streamlit run`
CLI, not as a plain script). This launcher boots Streamlit's runtime
programmatically against app.py, which IS freezable by PyInstaller.

When frozen, data files (app.py, the module files, .streamlit/) are unpacked to
a temporary directory exposed as sys._MEIPASS. We point Streamlit there.
"""

import os
import sys


def _resource_dir() -> str:
    # When frozen by PyInstaller, bundled files live under sys._MEIPASS.
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def main():
    base = _resource_dir()
    app_path = os.path.join(base, "app.py")

    # Make sure bundled local modules are importable.
    if base not in sys.path:
        sys.path.insert(0, base)

    # Streamlit reads config from CWD/.streamlit or env; force sane localhost-only
    # settings so the frozen app behaves like the launcher-run app.
    os.environ.setdefault("STREAMLIT_GLOBAL_DEVELOPMENT_MODE", "false")
    os.environ.setdefault("STREAMLIT_SERVER_ADDRESS", "localhost")
    os.environ.setdefault("STREAMLIT_SERVER_PORT", "8501")
    os.environ.setdefault("STREAMLIT_BROWSER_SERVER_ADDRESS", "localhost")
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    os.environ.setdefault("STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION", "false")
    os.environ.setdefault("STREAMLIT_SERVER_ENABLE_CORS", "true")

    # Open the browser ourselves at the correct URL, on a short delay, so the
    # user does not have to. (Headless is left off so Streamlit also tries.)
    import threading
    import webbrowser

    def _open_browser():
        import time
        time.sleep(3)
        try:
            webbrowser.open("http://localhost:8501")
        except Exception:
            pass

    try:
        threading.Thread(target=_open_browser, daemon=True).start()
    except Exception:
        pass

    # Boot Streamlit's CLI runtime against app.py.
    import streamlit.web.cli as stcli

    sys.argv = [
        "streamlit", "run", app_path,
        "--global.developmentMode=false",
        "--server.address=localhost",
        "--server.port=8501",
        "--browser.serverAddress=localhost",
        "--browser.serverPort=8501",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--server.enableXsrfProtection=false",
    ]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
