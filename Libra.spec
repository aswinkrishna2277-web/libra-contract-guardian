# -*- mode: python ; coding: utf-8 -*-
"""
Libra.spec — PyInstaller build specification for Libra Contract Guardian.

Build with:   pyinstaller Libra.spec --clean

This bundles the Streamlit app via launcher.py. Streamlit is awkward to freeze:
it has many hidden imports and ships data files (static assets, metadata) that
PyInstaller does not pick up automatically. We collect them explicitly below.

Known requirement: the END USER still needs Ollama installed separately
(https://ollama.com) — it is a separate local server and cannot be bundled.
"""

from PyInstaller.utils.hooks import (
    collect_all,
    collect_data_files,
    copy_metadata,
)
import os

block_cipher = None

# ── Collect Streamlit and its awkward dependencies wholesale ─────────────────
datas = []
binaries = []
hiddenimports = []

for pkg in ("streamlit", "altair", "pyarrow", "plotly", "pandas",
            "sklearn", "fitz", "docx", "reportlab"):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

# Streamlit needs its package metadata at runtime (version lookups).
for meta in ("streamlit", "altair", "pyarrow", "pandas", "numpy",
             "plotly", "scikit-learn", "PyMuPDF", "python-docx", "reportlab"):
    try:
        datas += copy_metadata(meta)
    except Exception:
        pass

# ── Bundle our own application files as data ─────────────────────────────────
# Bundle every .py and .css in the project EXCEPT the build tooling and tests,
# and only if it actually exists. This is resilient to files being added or
# removed without needing to edit this list.
import glob as _glob

_exclude = {
    "launcher.py",        # the entry point itself (handled by Analysis)
    "Build_Libra_EXE.bat",
}
for _f in sorted(_glob.glob("*.py")) + sorted(_glob.glob("*.css")):
    if _f in _exclude:
        continue
    if _f.startswith("test_"):   # don't bundle the test suite
        continue
    if os.path.exists(_f):
        datas.append((_f, "."))

# Bundle the .streamlit config directory if present.
if os.path.exists(os.path.join(".streamlit", "config.toml")):
    datas.append((".streamlit/config.toml", ".streamlit"))

# Extra hidden imports Streamlit/our app trigger dynamically.
hiddenimports += [
    "streamlit.web.cli",
    "streamlit.runtime.scriptrunner.magic_funcs",
    "sklearn.utils._typedefs",
    "sklearn.utils._heap",
    "sklearn.utils._sorting",
    "sklearn.utils._vector_sentinel",
    "sklearn.neighbors._partition_nodes",
]

a = Analysis(
    ["launcher.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "PyQt5", "PySide2"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Libra",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,   # keep a console window so users see status / can stop it
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Libra",
)
