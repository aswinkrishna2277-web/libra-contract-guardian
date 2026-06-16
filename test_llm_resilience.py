import re, json
# Copy of parse_json_response logic to test in isolation
def parse_json_response(raw, _mode=""):
    if not raw: return None
    if raw.startswith("[Error") or raw.startswith("[Local LLM") or raw.startswith("[Ollama") or raw.startswith("[Removed"):
        return None
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    start = cleaned.find("{"); end = cleaned.rfind("}")
    if start != -1 and end != -1:
        try: return json.loads(cleaned[start:end+1])
        except Exception: pass
    try: return json.loads(cleaned)
    except Exception: return None

cases = [
    ("Ollama down",        "[Local LLM error: Connection refused]",          None),
    ("Ollama not running", "[Ollama not running]",                           None),
    ("generic error",      "[Error: timeout]",                               None),
    ("empty",              "",                                              None),
    ("None",               None,                                            None),
    ("garbage text",       "I cannot help with that",                       None),
    ("truncated json",     '{"risk": 70, "level":',                         None),
    ("valid json",         '{"risk": 70, "level": "High"}',                 {"risk":70,"level":"High"}),
    ("json in fences",     '```json\n{"a": 1}\n```',                        {"a":1}),
    ("json with preamble", 'Here is the result: {"a": 2} hope it helps',    {"a":2}),
    ("model returns int",  '{"score": "70"}',                               {"score":"70"}),
]
fails = 0
for label, raw, expected in cases:
    try:
        got = parse_json_response(raw)
        ok = (got == expected)
    except Exception as e:
        ok = False; got = f"CRASHED: {e}"
    fails += not ok
    print(f"  {'✓' if ok else '✗'} {label:20} -> {got}")
print()
print("ALL LLM-RESILIENCE TESTS PASSED" if fails==0 else f"{fails} FAILED")
