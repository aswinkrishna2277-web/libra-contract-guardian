# Trademark Engine — Real Fix Deployment Guide

## What the previous test revealed

The output you sent back contains `[2020] UKSC 17` and `[2024] UKCA`. Both are v1 citations that exist in the OLD function body inside `app.py`. The v2 trademark engine cannot produce those strings.

Conclusion: **the v2 trademark engine is not being called.** Streamlit is running the old v1 code. Either:
1. The `app.py` edit (Step 5b in the earlier walkthrough) was not saved
2. The edit was applied to the wrong location
3. Streamlit was not restarted after the edit

This guide makes the edit foolproof.

---

## Step 1: Open `app.py` in an editor that shows line numbers

Recommended: **Notepad++** or **VS Code**. Plain Notepad will work but is harder to navigate.

In your `Libra version 2` folder, right-click `app.py` → Open with → Notepad++ (or VS Code).

## Step 2: Find the OLD function

Press Ctrl+F to open Find. Search for:

```
You are a senior UK trademark solicitor
```

You should land somewhere around **line 1436**. If you find this text, the v1 code is still there. ✓ (This confirms the diagnosis.)

## Step 3: Identify the start and end of what to delete

**START LINE** (the function definition):
Search for this exact text (Ctrl+F):
```
def generate_trademark_ai_opinion(your_mark: str, nice_class: str, description: str,
```

The line where this starts is what you'll delete from. It should be around line 1425.

**END LINE** (where to stop deleting):
Search for this exact text (Ctrl+F):
```
def _manual_search_links(your_mark: str, nice_class: str) -> dict:
```

The line where this starts is the line you must NOT delete. Delete everything ABOVE it back to (and including) the `def generate_trademark_ai_opinion` line.

In total, you are deleting **roughly 90 lines** between these two markers.

## Step 4: Select and delete the old function

1. Click at the very start of the line: `def generate_trademark_ai_opinion(your_mark: str, ...`
2. Hold Shift, scroll down to the line `def _manual_search_links(your_mark: str, nice_class: str) -> dict:`
3. Click at the very start of that `def _manual_search_links` line (do NOT include it in the selection)
4. Press Delete

Now there should be a gap between whatever function ended above `generate_trademark_ai_opinion` and the `def _manual_search_links` line.

## Step 5: Paste the replacement

Copy the entire block below (between the triple-backtick lines but not the backticks themselves), and paste it into the gap you just created:

```python
def generate_trademark_ai_opinion(your_mark: str, nice_class: str, description: str,
                                   ukipo_results: list[dict], dilution_rows: list[dict]) -> str:
    """
    Generate a structured UK trademark clearance opinion via the v2 engine.

    Phase 2C refactor: delegates to trademark_v2.py which:
      - uses the verified authority database for all citations
      - cites Sky v SkyKick as [2024] UKSC 36 (was [2020] UKSC 17 in v1)
      - cites Lidl v Tesco as [2024] EWCA Civ 262 (was [2024] UKCA in v1)
      - rejects any LLM output containing fabricated citations or raw IDs
    """
    from trademark_v2 import generate_trademark_opinion as _v2_opinion
    return _v2_opinion(your_mark, nice_class, description,
                        ukipo_results or [], dilution_rows or [])


```

CRITICAL formatting points:
- The line `def generate_trademark_ai_opinion(` must start at column 0 (no indentation)
- The body lines (`"""`, the imports, the return) must be indented exactly 4 spaces
- After the closing `return` line, there must be ONE blank line before `def _manual_search_links`

## Step 6: Save the file

Press Ctrl+S in your editor. Confirm the save went through (the title bar should stop showing the "modified" marker).

## Step 7: Verify the edit took effect

Open Command Prompt in the `Libra version 2` folder (click the address bar, type `cmd`, press Enter).

Run this exact command:

```
findstr /N "You are a senior UK trademark solicitor" app.py
```

**Expected output:** NOTHING. The prompt just returns with no result. ✓

If you see output like `1436: prompt = f"""You are a senior UK trademark solicitor...`, the old code is still there. Go back to Step 4 — you didn't delete the full function.

Then run:

```
findstr /N "[2020] UKSC 17" app.py
```

**Expected output:** NOTHING. ✓

If you see output, the old fallback template is still in `app.py`. Re-do Step 4.

Then run:

```
findstr /N "from trademark_v2 import" app.py
```

**Expected output:** ONE line, somewhere around 1430:
```
1430:    from trademark_v2 import generate_trademark_opinion as _v2_opinion
```

If you don't see this, your paste in Step 5 didn't go through. Re-do Step 5.

## Step 8: Restart Streamlit

In the terminal where Streamlit is running, press **Ctrl+C**. Wait for it to stop.

Then run:
```
venv\Scripts\activate
streamlit run app.py
```

Wait for the browser to reload.

## Step 9: Retest with BURRBERY

In the Trademark tab:
- Your mark: `BURRBERY`
- Nice class: `25`
- Description: `Clothing, footwear, headgear, scarves, and luxury fashion accessories`

This time also UPLOAD A COMPETITOR FILE so we can test the HIGH-risk path even though the live search is broken. Use the file `test_competitor_BURBERRY.txt` that I gave you alongside the other files — it tells the engine that `BURBERRY` is a competitor in class 25.

Run the analysis.

## Step 10: What to look for in the new opinion

**Section 3 should now read** (something like this):

```
3. LEGAL FRAMEWORK

Trade Marks Act 1994, s.10(2) prohibits registration of marks identical
or similar to an earlier mark covering identical or similar goods or
services where there exists a likelihood of confusion on the part of
the public. Trade Marks Act 1994, s.10(3) extends protection to marks
with a reputation in the UK, prohibiting use which would take unfair
advantage of, or be detrimental to, the distinctive character or repute
of the earlier mark (dilution). In SkyKick UK Ltd v Sky Ltd [2024] UKSC
36, the Supreme Court (Lord Kitchin, 13 November 2024) confirmed that
bad-faith filings and applications for goods or services in which the
applicant had no genuine intention to use the mark can invalidate
registrations wholly or partially. Lidl Great Britain Ltd v Tesco
Stores Ltd [2024] EWCA Civ 262 clarified the application of the
unfair-advantage and detriment limbs of section 10(3) in the context
of look-alike retail signage.
```

**Three checks** when you read the new opinion:

1. ✅ Does it contain `[2024] UKSC 36`?
2. ✅ Does it contain `[2024] EWCA Civ 262`?
3. ✅ Is `[2020] UKSC 17` completely absent?

If yes to all three, the v2 engine is finally live.

## If anything goes wrong

**Streamlit shows `ImportError: cannot import name 'generate_trademark_opinion' from 'trademark_v2'`:**
→ `trademark_v2.py` is missing or has the wrong name. Confirm it sits in the project folder as `trademark_v2.py` (exact spelling).

**Opinion looks identical to before with `[2020] UKSC 17`:**
→ The edit didn't save. Stop Streamlit, re-do Steps 3-6, run the `findstr` checks in Step 7, restart.

**Streamlit shows `IndentationError` or `SyntaxError`:**
→ The paste in Step 5 has bad indentation. Open `app.py`, find the new `generate_trademark_ai_opinion` function, make sure `def` is at column 0 and the body lines are at column 4.

## Then send me what you see

Copy section 3 of the new opinion and send it. If `[2024] UKSC 36` is there and `[2020] UKSC 17` is gone, the fix is live and we can move forward.
