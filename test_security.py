"""
test_security.py — Phase D security hardening checks.

Verifies the HTML-escaping helper and the docx decompression-bomb guard,
in isolation (no Streamlit needed).
"""

import io
import html as _html
import zipfile


# ---- Copies of the guards under test (kept in sync with app.py) -------------
def esc(value) -> str:
    if value is None:
        return ""
    return _html.escape(str(value), quote=True)


def _docx_is_safe(file_bytes: bytes) -> bool:
    MAX_UNCOMPRESSED = 200 * 1024 * 1024
    MAX_RATIO = 200
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            total = sum(i.file_size for i in z.infolist())
            comp = max(sum(i.compress_size for i in z.infolist()), 1)
            if total > MAX_UNCOMPRESSED:
                return False
            if (total / comp) > MAX_RATIO and total > 10 * 1024 * 1024:
                return False
        return True
    except zipfile.BadZipFile:
        return False
    except Exception:
        return False


def t(label, cond):
    print(f"  {'✓' if cond else '✗'} {label}")
    return bool(cond)


def run_all() -> int:
    fails = 0

    print("[1] HTML escaping neutralises injection")
    fails += not t("script tag is escaped",
                   "<script>" not in esc("<script>alert(1)</script>"))
    fails += not t("img onerror is escaped",
                   "<img" not in esc('<img src=x onerror=alert(1)>'))
    fails += not t("quotes are escaped",
                   '"' not in esc('" onmouseover="x'))
    fails += not t("None -> empty string", esc(None) == "")
    fails += not t("plain text passes through unchanged",
                   esc("CDPA 1988 s.29A") == "CDPA 1988 s.29A")
    fails += not t("ampersand escaped once",
                   esc("Tom & Jerry") == "Tom &amp; Jerry")

    print("\n[2] docx decompression-bomb guard")
    # A normal small docx-like zip
    good = io.BytesIO()
    with zipfile.ZipFile(good, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("word/document.xml", "<xml>" + ("real contract text " * 200) + "</xml>")
    fails += not t("normal document passes", _docx_is_safe(good.getvalue()) is True)

    # A decompression bomb: tiny compressed, enormous uncompressed
    bomb = io.BytesIO()
    with zipfile.ZipFile(bomb, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("word/document.xml", "A" * (250 * 1024 * 1024))  # 250 MB of 'A'
    fails += not t("decompression bomb is rejected", _docx_is_safe(bomb.getvalue()) is False)

    # Not a zip at all
    fails += not t("non-zip bytes rejected", _docx_is_safe(b"this is not a zip") is False)
    fails += not t("empty bytes rejected", _docx_is_safe(b"") is False)

    print()
    print("─" * 56)
    if fails == 0:
        print("✓ ALL TESTS PASSED")
    else:
        print(f"✗ {fails} test(s) failed")
    return fails


if __name__ == "__main__":
    import sys
    sys.exit(1 if run_all() else 0)
