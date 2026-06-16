# Standalone test of the extract_document_safe logic (copied, deps stubbed)
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MIN_USABLE_CHARS = 40

class ExtractionResult:
    __slots__ = ("ok","text","message","char_count")
    def __init__(self, ok, text="", message=""):
        self.text=text or ""; self.ok=ok; self.message=message; self.char_count=len(self.text)

def extract_pdf(b):  # stub: pretend valid PDFs yield text, image PDFs yield ''
    return b.decode('utf8', 'ignore') if b[:4]==b'%TXT' else ''
def extract_docx(b):
    return b.decode('utf8','ignore') if b[:4]==b'%TXT' else '[DOCX extraction error: bad]'

def extract_document_safe(uploaded_file):
    try: name=(getattr(uploaded_file,"name","") or "").strip()
    except Exception: name=""
    if not name: return ExtractionResult(False, message="no filename")
    lower=name.lower()
    if not (lower.endswith(".pdf") or lower.endswith(".docx")):
        return ExtractionResult(False, message="not supported type")
    try: raw=uploaded_file.getvalue() if hasattr(uploaded_file,"getvalue") else uploaded_file.read()
    except Exception: return ExtractionResult(False, message="could not read")
    if raw is None or len(raw)==0: return ExtractionResult(False, message="empty 0 bytes")
    if len(raw)>MAX_UPLOAD_BYTES: return ExtractionResult(False, message="too large")
    try:
        text = extract_pdf(raw) if lower.endswith(".pdf") else extract_docx(raw)
    except Exception: return ExtractionResult(False, message="could not process")
    if text.startswith("[ERROR:") or text.startswith("[PDF extraction error") or text.startswith("[DOCX extraction error"):
        return ExtractionResult(False, message="scanned/protected")
    cleaned=(text or "").strip()
    if len(cleaned)<MIN_USABLE_CHARS:
        return ExtractionResult(False, message="no extractable text (scanned?)")
    return ExtractionResult(True, text=cleaned)

class FakeUpload:
    def __init__(self, name, data): self.name=name; self._d=data
    def getvalue(self): return self._d
class BadUpload:
    name="x.pdf"
    def getvalue(self): raise IOError("boom")
class NoName:
    name=""
    def getvalue(self): return b"data"

valid = b'%TXT' + b'This is a valid contract document with plenty of readable text content here.'
tests = [
    ("valid docx",      FakeUpload("c.docx", valid),                 True),
    ("valid pdf",       FakeUpload("c.pdf", valid),                  True),
    ("empty file",      FakeUpload("c.pdf", b""),                    False),
    ("oversized",       FakeUpload("c.pdf", b'%TXT'+b'x'*(26*1024*1024)), False),
    ("wrong type",      FakeUpload("c.txt", valid),                  False),
    ("scanned pdf",     FakeUpload("c.pdf", b'%IMG'+b'\x00'*100),    False),
    ("corrupt docx",    FakeUpload("c.docx", b'%IMG'+b'\x00'*100),   False),
    ("read raises",     BadUpload(),                                 False),
    ("no filename",     NoName(),                                    False),
    ("too short text",  FakeUpload("c.docx", b'%TXT'+b'hi'),         False),
]
fails=0
for label, up, expected_ok in tests:
    r = extract_document_safe(up)
    ok = (r.ok == expected_ok)
    fails += not ok
    print(f"  {'✓' if ok else '✗'} {label:18} ok={r.ok!s:5} expected={expected_ok!s:5} msg='{r.message}'")
print()
print("ALL EXTRACTION TESTS PASSED" if fails==0 else f"{fails} FAILED")
