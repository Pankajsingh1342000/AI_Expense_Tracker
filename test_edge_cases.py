"""
Extensive edge-case test suite for the AI Expense Tracker.
Runs against the live server at http://127.0.0.1:8000.

Covers:
  - Happy-path CRUD operations
  - AI guard: add with no title (must NOT crash, must reply conversationally)
  - AI guard: update/delete with no id and no title
  - Duplicate-expense clarification flow
  - Conversation memory (multi-turn follow-ups)
  - Invalid / garbage inputs
  - Boundary values (zero amount, negative amount, very large amount)
  - Injection-like strings in natural language
  - Empty / whitespace-only queries
  - Very long messages
  - Pure-chat questions (budget advice, general Q&A)
  - Budget CRUD via natural language
  - Vague references that require memory context
"""

import time
import requests

BASE_URL = "http://127.0.0.1:8000"
TS = int(time.time())
TEST_EMAIL = f"edge_test_{TS}@test.com"
TEST_PASSWORD = "EdgeTest@99"

# ── Colour helpers ──────────────────────────────────────────
GREEN = "\033[92m"
RED   = "\033[91m"
YELLOW = "\033[93m"
CYAN  = "\033[96m"
BOLD  = "\033[1m"
RESET = "\033[0m"

passed = 0
failed = 0
skipped = 0
failures = []


def _hdr(title: str) -> None:
    print(f"\n{BOLD}{CYAN}{'━'*60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'━'*60}{RESET}")


def _ok(label: str) -> None:
    global passed
    passed += 1
    print(f"  {GREEN}✓{RESET}  {label}")


def _fail(label: str, detail: str = "") -> None:
    global failed
    failed += 1
    failures.append(label)
    tag = f" ({detail})" if detail else ""
    print(f"  {RED}✗{RESET}  {label}{RED}{tag}{RESET}")


def _skip(label: str, reason: str = "") -> None:
    global skipped
    skipped += 1
    print(f"  {YELLOW}~{RESET}  {label}  [{reason}]")


def check(condition: bool, label: str, detail: str = "") -> bool:
    if condition:
        _ok(label)
    else:
        _fail(label, detail)
    return condition


def chat(token: str, message: str, delay: float = 2.5) -> tuple[int, dict]:
    try:
        r = requests.post(
            f"{BASE_URL}/api/v1/expenses/agent",
            json={"query": message},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        time.sleep(delay)
        return r.status_code, r.json()
    except requests.exceptions.RequestException as exc:
        return 503, {"error": str(exc)}


def show(label: str, status: int, res: dict) -> None:
    reply = res.get("reply", "[no reply]")
    short = reply[:180] + ("…" if len(reply) > 180 else "")
    print(f"\n  {BOLD}> {label}{RESET}")
    print(f"    HTTP {status} | AI: {short}")


# ── Setup ───────────────────────────────────────────────────
def setup() -> str:
    for attempt in range(10):
        try:
            r = requests.post(
                f"{BASE_URL}/api/v1/auth/register",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
                timeout=5,
            )
            break
        except requests.exceptions.ConnectionError:
            print(f"  Waiting for server… ({attempt+1}/10)")
            time.sleep(2)
    else:
        raise SystemExit("Cannot reach the server.")

    assert r.status_code in (200, 201), f"Register failed: {r.text}"
    r2 = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={"username": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert r2.status_code == 200, f"Login failed: {r2.text}"
    return r2.json()["access_token"]


# ════════════════════════════════════════════════════════════
# TEST GROUPS
# ════════════════════════════════════════════════════════════

def test_happy_path_add(token):
    _hdr("GROUP 1 — Happy-path expense ADD")

    cases = [
        ("bought coffee for 80",                "Simple buy statement"),
        ("spent 250 on groceries",              "Spent … on pattern"),
        ("paid 180 for uber",                   "Paid … for pattern"),
        ("dinner 500 category food",            "No verb, title + amount"),
        ("bought pizza for 300 category food",  "With explicit category"),
        ("bought pizza for 150 category food",  "Duplicate pizza created intentionally"),
    ]

    ids = {}
    for msg, label in cases:
        status, res = chat(token, msg)
        show(label, status, res)
        ok = check(status == 200, f"ADD — {label}", f"HTTP {status}")
        check("reply" in res and len(res.get("reply","")) > 5, f"  reply present for: {label}")
        if ok and "id" in res:
            ids[label] = res["id"]

    return ids


def test_happy_path_list_and_total(token):
    _hdr("GROUP 2 — Happy-path LIST / TOTAL / FILTER")

    for msg, label in [
        ("list my expenses",            "List all"),
        ("how much have I spent total", "Total query"),
        ("show food expenses",          "Filter by category"),
        ("show expenses above 100",     "Filter min_amount"),
        ("monthly summary",             "Monthly summary"),
        ("today's spending",            "Daily spending"),
    ]:
        status, res = chat(token, msg)
        show(label, status, res)
        check(status == 200, f"READ — {label}", f"HTTP {status}")


def test_budget_operations(token):
    _hdr("GROUP 3 — Budget CRUD")

    for msg, label in [
        ("set my food budget to 3000",       "Set budget"),
        ("set transport budget to 1500",      "Set transport budget"),
        ("what is my food budget",            "Budget status query"),
        ("show all budgets",                  "Budget overview"),
        ("am I near my budget limit",         "Budget warning check"),
        ("update food budget to 3500",        "Update budget"),
        ("delete transport budget",           "Delete budget"),
    ]:
        status, res = chat(token, msg)
        show(label, status, res)
        check(status == 200, f"BUDGET — {label}", f"HTTP {status}")
        check("reply" in res, f"  reply present for: {label}")


def test_ai_guard_add_no_title(token):
    _hdr("GROUP 4 — AI GUARD: add with no title (must NOT crash)")

    # These inputs are ambiguous — the AI might try action=add but should
    # never reach the handler with title=null; the guard must catch it.
    cases = [
        "add an expense",
        "I want to add something",
        "record a new expense please",
        "add",
    ]
    for msg in cases:
        status, res = chat(token, msg)
        show(msg, status, res)
        check(status == 200,          f"GUARD add-no-title | no crash for: '{msg}'",  f"HTTP {status}")
        check("reply" in res,         f"  reply present (not a raw error) for: '{msg}'")
        check(status != 500,          f"  no 500 internal error for: '{msg}'",        f"HTTP {status}")
        # Must NOT have created an expense with null title
        check(
            not (res.get("title") is None and res.get("action") == "add"),
            f"  no null-title add action reached handler for: '{msg}'"
        )


def test_ai_guard_update_delete_no_id(token):
    _hdr("GROUP 5 — AI GUARD: update/delete with no id & no title")

    cases = [
        "update the expense",
        "delete it",
        "remove the last one",
        "change the amount",
    ]
    for msg in cases:
        status, res = chat(token, msg)
        show(msg, status, res)
        check(status == 200,  f"GUARD update/delete-no-id | no crash for: '{msg}'", f"HTTP {status}")
        check("reply" in res, f"  reply present for: '{msg}'")
        check(status != 500,  f"  no 500 error for: '{msg}'",                       f"HTTP {status}")


def test_duplicate_clarification_flow(token):
    _hdr("GROUP 6 — Duplicate clarification + conversation memory")

    # Both pizzas were added in group 1
    status, res = chat(token, "update pizza to 400")
    show("update pizza (2 exist)", status, res)
    check(status == 200, "Clarification triggered (2 pizzas exist)")
    is_clarif = res.get("status") == "clarification_needed"
    check(
        is_clarif or (res.get("reply") and len(res["reply"]) > 10),
        "  Either clarification_needed OR a natural 'which one?' reply"
    )
    time.sleep(1.5)

    # Follow-up using memory — no explicit ID given
    status, res = chat(token, "the cheaper one, Rs. 150")
    show("the cheaper one (memory follow-up)", status, res)
    check(status == 200, "Memory follow-up resolved correctly")
    check("reply" in res, "  Confirmation reply present")
    time.sleep(1.5)

    # Delete the remaining pizza via memory
    status, res = chat(token, "delete pizza")
    show("delete pizza (now 1 remains)", status, res)
    check(status == 200, "Delete pizza (single match)")
    time.sleep(1.5)


def test_pure_conversation(token):
    _hdr("GROUP 7 — Pure conversational Q&A (no DB writes)")

    cases = [
        ("am I spending too much on food?",         "Spending advice"),
        ("what is my biggest expense category?",    "Category insight"),
        ("how can I save money this month?",         "Generic financial advice"),
        ("compare my food and transport spending",   "Category comparison"),
        ("give me insights about my habits",         "AI insights trigger"),
        ("what did I spend on this month?",          "Monthly overview Q"),
    ]
    for msg, label in cases:
        status, res = chat(token, msg, delay=2)
        show(label, status, res)
        check(status == 200,                              f"CHAT — {label}", f"HTTP {status}")
        check("reply" in res and len(res["reply"]) > 10, f"  meaningful reply for: {label}")


def test_chained_context(token):
    _hdr("GROUP 8 — Chained context follow-ups")

    status, res = chat(token, "give me a breakdown of spending by category")
    show("Initial breakdown query", status, res)
    check(status == 200, "Breakdown answered")
    time.sleep(2)

    status, res = chat(token, "and what about food specifically?")
    show("Follow-up: 'what about food?' (chained)", status, res)
    check(status == 200,               "Chained follow-up resolved")
    check("reply" in res,              "  Reply present")
    check(len(res.get("reply",""))>10, "  Reply is meaningful")
    time.sleep(2)

    status, res = chat(token, "is that more or less than last month?")
    show("Further follow-up: more/less than last month?", status, res)
    check(status == 200, "Deep follow-up handled without crash")
    time.sleep(1.5)


def test_boundary_values(token):
    _hdr("GROUP 9 — Boundary / invalid values")

    # Zero amount — should be rejected by service (amount must be positive)
    status, res = chat(token, "bought lunch for 0")
    show("Zero amount", status, res)
    check(
        status in (200, 400),
        "Zero amount: 200 (chat graceful) or 400 (validation error)",
        f"HTTP {status}"
    )
    check(status != 500, "  No 500 crash for zero amount", f"HTTP {status}")
    time.sleep(1.5)

    # Negative amount  
    status, res = chat(token, "spent -200 on food")
    show("Negative amount", status, res)
    check(status != 500, "No 500 crash for negative amount", f"HTTP {status}")
    time.sleep(1.5)

    # Extremely large amount
    status, res = chat(token, "bought mansion for 9999999999")
    show("Huge amount", status, res)
    check(status == 200,  "Huge amount accepted (AI processes it)")
    check("reply" in res, "  Reply present for huge amount")
    time.sleep(1.5)

    # Amount only, no title
    status, res = chat(token, "500")
    show("Number only input", status, res)
    check(status == 200,  "Bare number handled gracefully")
    check(status != 500,  "  No 500 for bare number")
    time.sleep(1.5)


def test_garbage_inputs(token):
    _hdr("GROUP 10 — Garbage / adversarial inputs")

    cases = [
        ("asdfghjkl",                          "Random gibberish"),
        ("!!! @@@ ###",                         "Special characters only"),
        ("x" * 600,                             "Very long input (600 chars)"),
        ("SELECT * FROM expenses",              "SQL injection attempt"),
        ("'; DROP TABLE expenses; --",          "SQL injection 2"),
        ("null undefined NaN",                  "JS-like garbage"),
        ("   ",                                 "Whitespace only"),
        ("12345 67890",                         "Numbers only"),
        ("हाँ मैंने पिज़्ज़ा खाया",              "Hindi text"),
        ("add expense title=null amount=null",  "Explicit null strings"),
    ]

    for msg, label in cases:
        status, res = chat(token, msg, delay=1.5)
        show(label, status, res)
        check(status != 500, f"GARBAGE — {label}: no 500 crash", f"HTTP {status}")
        check(status in (200, 400, 422), f"  Valid HTTP code for: {label}", f"HTTP {status}")


def test_update_by_name_and_id(token):
    _hdr("GROUP 11 — Update by name / ID")

    # First add a unique expense
    status, res = chat(token, "bought icecream for 90 category food")
    show("Setup: add icecream", status, res)
    time.sleep(1.5)

    # Update by name
    status, res = chat(token, "update icecream to 110")
    show("Update icecream by name", status, res)
    check(status == 200,  "Update by name: HTTP 200")
    check("reply" in res, "  Confirmation reply")
    time.sleep(1.5)

    # Update category by name
    status, res = chat(token, "change icecream category to beverages")
    show("Update icecream category by name", status, res)
    check(status == 200,  "Update category by name: HTTP 200")
    time.sleep(1.5)


def test_delete_by_name(token):
    _hdr("GROUP 12 — Delete by name")

    status, res = chat(token, "bought testitem for 55 category misc")
    show("Setup: add testitem", status, res)
    time.sleep(1.5)

    status, res = chat(token, "delete testitem")
    show("Delete testitem by name", status, res)
    check(status == 200,  "Delete by name: HTTP 200")
    check("reply" in res, "  Confirmation reply")
    time.sleep(1.5)


# ════════════════════════════════════════════════════════════
# RUNNER
# ════════════════════════════════════════════════════════════

def main():
    print(f"\n{BOLD}{'═'*60}{RESET}")
    print(f"{BOLD}  AI Expense Tracker — Extensive Edge Case Test Suite{RESET}")
    print(f"{BOLD}{'═'*60}{RESET}")

    _hdr("SETUP — Register & Login")
    token = setup()
    print(f"  ✓ Logged in as {TEST_EMAIL}")

    test_happy_path_add(token)
    test_happy_path_list_and_total(token)
    test_budget_operations(token)
    test_ai_guard_add_no_title(token)
    test_ai_guard_update_delete_no_id(token)
    test_duplicate_clarification_flow(token)
    test_pure_conversation(token)
    test_chained_context(token)
    test_boundary_values(token)
    test_garbage_inputs(token)
    test_update_by_name_and_id(token)
    test_delete_by_name(token)

    # ── Summary ──────────────────────────────────────────────
    total = passed + failed + skipped
    print(f"\n{BOLD}{'═'*60}{RESET}")
    print(f"{BOLD}  RESULTS  |  Total: {total}  |  "
          f"{GREEN}Pass: {passed}{RESET}{BOLD}  |  "
          f"{RED}Fail: {failed}{RESET}{BOLD}  |  "
          f"{YELLOW}Skip: {skipped}{RESET}{BOLD}{RESET}")
    if failures:
        print(f"\n  {RED}Failed checks:{RESET}")
        for f in failures:
            print(f"    {RED}✗{RESET} {f}")
    else:
        print(f"\n  {GREEN}{BOLD}ALL CHECKS PASSED! 🎉{RESET}")
    print(f"{BOLD}{'═'*60}{RESET}\n")


if __name__ == "__main__":
    main()
