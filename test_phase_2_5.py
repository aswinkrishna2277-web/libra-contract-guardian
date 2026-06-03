"""
Phase 2.5 test suite — privacy guard / data-protection layer.

Verifies:
  1. Local-only mode blocks all non-local hosts
  2. Local hosts (127.0.0.1, localhost) are always allowed
  3. Outside local-only mode, calls still require consent + category flag
  4. Defence in depth: turning off local-only alone does not open the door
  5. Audit log records every attempt (allowed and blocked)
  6. Audit log never contains document content
  7. OneDrive / cloud-sync risk detection
  8. Policy round-trips correctly

Run: python test_phase_2_5.py
"""

import sys
import privacy_guard as pg


def t(label: str, passed: bool, reason: str = "") -> bool:
    if passed:
        print(f"  ✓ {label}" + (f" — {reason}" if reason else ""))
        return True
    print(f"  ✗ {label}" + (f" — {reason}" if reason else ""))
    return False


def reset_policy():
    """Reset to the safe default before each test group."""
    pg.set_policy(local_only=True, allow_link_check=False,
                  allow_trademark_web=False, consent_given=False)
    pg.clear_audit()


def run_all() -> int:
    failures = 0
    print("\nPhase 2.5 — Privacy Guard — Integration Tests")
    print("─" * 70)

    # ── [1] Local-only mode blocks non-local hosts ──────────────────────────
    print("\n[1] local-only mode blocks non-local hosts")
    reset_policy()

    blocked = False
    try:
        pg.guard_network("https://en.wikipedia.org/w/api.php", "trademark_web_search")
    except pg.NetworkBlocked:
        blocked = True
    failures += not t("Wikipedia call blocked in local-only mode", blocked)

    blocked = False
    try:
        pg.guard_network("https://duckduckgo.com/", "trademark_web_search")
    except pg.NetworkBlocked:
        blocked = True
    failures += not t("DuckDuckGo call blocked in local-only mode", blocked)

    blocked = False
    try:
        pg.guard_network("https://www.legislation.gov.uk/x", "link_check")
    except pg.NetworkBlocked:
        blocked = True
    failures += not t("Link-check call blocked in local-only mode", blocked)

    # ── [2] Local hosts always allowed ──────────────────────────────────────
    print("\n[2] local hosts always allowed (the on-device LLM)")
    reset_policy()

    allowed = True
    try:
        pg.guard_network("http://127.0.0.1:11434/api/generate", "local_llm")
    except pg.NetworkBlocked:
        allowed = False
    failures += not t("127.0.0.1 LLM call allowed even in local-only mode", allowed)

    allowed = True
    try:
        pg.guard_network("http://localhost:11434/api/tags", "local_llm")
    except pg.NetworkBlocked:
        allowed = False
    failures += not t("localhost call allowed in local-only mode", allowed)

    # ── [3] Outside local-only: consent + category flag both required ───────
    print("\n[3] defence in depth — disabling local-only alone is not enough")
    reset_policy()

    # Turn OFF local-only but grant nothing else
    pg.set_policy(local_only=False)
    blocked = False
    try:
        pg.guard_network("https://en.wikipedia.org/x", "trademark_web_search")
    except pg.NetworkBlocked:
        blocked = True
    failures += not t("local_only OFF but no consent → still blocked", blocked)

    # Grant consent but not the category flag
    pg.set_policy(local_only=False, consent_given=True)
    blocked = False
    try:
        pg.guard_network("https://en.wikipedia.org/x", "trademark_web_search")
    except pg.NetworkBlocked:
        blocked = True
    failures += not t("consent but no category flag → still blocked", blocked)

    # Grant both → now allowed
    pg.set_policy(local_only=False, consent_given=True, allow_trademark_web=True)
    allowed = True
    try:
        pg.guard_network("https://en.wikipedia.org/x", "trademark_web_search")
    except pg.NetworkBlocked:
        allowed = False
    failures += not t("local_only OFF + consent + category flag → allowed", allowed)

    # The OTHER category still blocked (link_check flag not set)
    blocked = False
    try:
        pg.guard_network("https://www.legislation.gov.uk/x", "link_check")
    except pg.NetworkBlocked:
        blocked = True
    failures += not t("unrelated category still blocked when not enabled", blocked)

    # ── [4] Audit log records attempts ──────────────────────────────────────
    print("\n[4] audit log records every attempt")
    reset_policy()

    try:
        pg.guard_network("https://en.wikipedia.org/x", "trademark_web_search")
    except pg.NetworkBlocked:
        pass
    pg.guard_network("http://127.0.0.1:11434/x", "local_llm")

    audit = pg.get_audit()
    failures += not t("Audit has at least 2 entries", len(audit) >= 2,
                      f"count: {len(audit)}")
    failures += not t("Audit records the blocked Wikipedia attempt",
                      any(a["host"] == "en.wikipedia.org" and not a["allowed"]
                          for a in audit))
    failures += not t("Audit records the allowed local attempt",
                      any(a["host"] == "127.0.0.1" and a["allowed"]
                          for a in audit))

    summary = pg.audit_summary()
    failures += not t("Summary counts blocked attempts",
                      summary["blocked"] >= 1)
    failures += not t("Summary reports local-only active",
                      summary["local_only_active"] is True)

    # ── [5] Audit log never contains document content ───────────────────────
    print("\n[5] audit log contains no document content")
    reset_policy()

    secret = "CONFIDENTIAL_CLIENT_CONTRACT_TEXT_12345"
    # Even if a URL somehow contained content, the audit records host+category
    try:
        pg.guard_network(f"https://evil.example.com/?doc={secret}", "trademark_web_search")
    except pg.NetworkBlocked:
        pass
    audit = pg.get_audit()
    audit_blob = str(audit)
    failures += not t("Secret document text NOT in audit (only host recorded)",
                      secret not in audit_blob)
    failures += not t("Audit records the host only",
                      any(a["host"] == "evil.example.com" for a in audit))

    # ── [6] OneDrive / cloud-sync risk detection ────────────────────────────
    print("\n[6] cloud-sync risk detection")

    risk = pg.assess_onedrive_risk(r"C:\Users\aswin\OneDrive\Desktop\Libra version 2")
    failures += not t("OneDrive path flagged as at-risk", risk["at_risk"])
    failures += not t("OneDrive risk names the service",
                      "OneDrive" in risk["service"])

    risk2 = pg.assess_onedrive_risk(r"C:\Users\aswin\Documents\Libra")
    failures += not t("Non-cloud path NOT flagged", not risk2["at_risk"])

    risk3 = pg.assess_onedrive_risk("/home/user/Dropbox/work/libra")
    failures += not t("Dropbox path flagged as at-risk", risk3["at_risk"])

    # ── [7] Policy round-trips ──────────────────────────────────────────────
    print("\n[7] policy get/set round-trips")
    reset_policy()

    p = pg.get_policy()
    failures += not t("Default policy: local_only True", p["local_only"] is True)
    failures += not t("Default policy: consent False", p["consent_given"] is False)

    pg.set_policy(local_only=False, consent_given=True)
    p2 = pg.get_policy()
    failures += not t("Policy update persists local_only",
                      p2["local_only"] is False)
    failures += not t("Policy update persists consent",
                      p2["consent_given"] is True)

    # ── [8] Privacy statement reflects current mode ─────────────────────────
    print("\n[8] privacy statement")
    reset_policy()

    stmt = pg.privacy_statement()
    failures += not t("Statement mentions local-only ON",
                      "Local-only mode: ON" in stmt)
    failures += not t("Statement mentions 127.0.0.1",
                      "127.0.0.1" in stmt)
    failures += not t("Statement warns about cloud-synced folders",
                      "OneDrive" in stmt or "cloud-synced" in stmt)
    failures += not t("Statement promises no document content leaves",
                      "leave" in stmt.lower() or "leaving" in stmt.lower())

    # ── [9] safe_request wrapper enforces policy ────────────────────────────
    print("\n[9] safe_request wrapper")
    reset_policy()

    call_made = {"done": False}
    def fake_get(url, **kwargs):
        call_made["done"] = True
        return "OK"

    # In local-only mode, safe_request to external host should block (not call)
    blocked = False
    try:
        pg.safe_request(fake_get, "https://en.wikipedia.org/x", "trademark_web_search")
    except pg.NetworkBlocked:
        blocked = True
    failures += not t("safe_request blocks external host in local-only mode",
                      blocked and not call_made["done"])

    # Local host should pass through and actually call
    call_made["done"] = False
    result = pg.safe_request(fake_get, "http://127.0.0.1:11434/x", "local_llm")
    failures += not t("safe_request permits local host and calls through",
                      call_made["done"] and result == "OK")

    # ── Summary ─────────────────────────────────────────────────────────────
    print()
    print("─" * 70)
    if failures == 0:
        print("✓ ALL TESTS PASSED")
    else:
        print(f"✗ {failures} test(s) failed")
    return failures


if __name__ == "__main__":
    sys.exit(run_all())
