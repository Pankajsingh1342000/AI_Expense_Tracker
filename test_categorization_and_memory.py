"""
Tests for Conversational Memory and Categorization improvements.
Runs against the live server at http://127.0.0.1:8000.
"""

import time
import requests

BASE_URL = "http://127.0.0.1:8000"
TEST_EMAIL = f"conv_test_{int(time.time())}@test.com"
TEST_PASSWORD = "Test@12345"

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"

def register_and_login():
    for i in range(10):
        try:
            r = requests.post(f"{BASE_URL}/api/v1/auth/register", json={"email": TEST_EMAIL, "password": TEST_PASSWORD}, timeout=5)
            break
        except requests.exceptions.ConnectionError:
            print(f"  Wait for server... ({i+1}/10)")
            time.sleep(2)
    else:
        raise Exception("Could not connect to server")
    
    assert r.status_code in [200, 201], f"Register failed: {r.text}"
    r = requests.post(f"{BASE_URL}/api/v1/auth/login", data={"username": TEST_EMAIL, "password": TEST_PASSWORD})
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["access_token"]

def chat(token, message):
    r = requests.post(
        f"{BASE_URL}/api/v1/expenses/agent",
        json={"query": message},
        headers={"Authorization": f"Bearer {token}"},
    )
    return r.status_code, r.json()

failures = []

def check(step, condition, label):
    if condition:
        print(f"  [{PASS}] {label}")
    else:
        print(f"  [{FAIL}] {label}")
        failures.append(f"Step {step}: {label}")

def section(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")

def turn(step, you, status, res):
    reply = res.get("reply", "[no reply]")
    print(f"\n  >> Step {step}")
    print(f"     You : {you}")
    print(f"     HTTP: {status}")
    if "data" in res and res["data"].get("action"):
        print(f"     Act : {res['data'].get('action')} | Title: {res['data'].get('title')} | Cat: {res['data'].get('category')}")
    elif res.get("action"):
        print(f"     Act : {res.get('action')} | Title: {res.get('title')} | Cat: {res.get('category')}")
    print(f"     AI  : {reply[:250]}{'...' if len(reply) > 250 else ''}")

def run():
    section("SETUP — Register & Login")
    token = register_and_login()
    print(f"  Logged in as {TEST_EMAIL}")

    # --------------------------------------------------
    section("SCENARIO 1 — Strict Categorization & Title Extraction")
    # --------------------------------------------------
    # Test 1: Slang / Unclear phrasing
    status, res = chat(token, "spent 500 on an uber ride")
    turn("1.1", "spent 500 on an uber ride", status, res)
    check("1.1", status == 200, "Added uber")
    # In some response formats, data is nested
    data = res.get("data", res)
    check("1.1", data.get("category") == "transport", "Category mapped to transport")
    check("1.1", data.get("title", "").lower() == "uber", "Clean title extracted (uber)")
    time.sleep(2)

    # Test 2: Hallucinated categories like "electricity" should become "bills"
    status, res = chat(token, "paid 1200 for electricity")
    turn("1.2", "paid 1200 for electricity", status, res)
    check("1.2", status == 200, "Added electricity")
    data = res.get("data", res)
    check("1.2", data.get("category") == "bills", "Category mapped to bills")
    time.sleep(2)

    # Test 3: Complex phrasing
    status, res = chat(token, "bought dinner on swiggy for 450")
    turn("1.3", "bought dinner on swiggy for 450", status, res)
    check("1.3", status == 200, "Added swiggy")
    data = res.get("data", res)
    check("1.3", data.get("category") == "food", "Category mapped to food")
    check("1.3", data.get("title", "").lower() in ["swiggy", "dinner"], "Clean title extracted")
    time.sleep(2)

    # --------------------------------------------------
    section("SCENARIO 2 — Conversational Memory (Drill-down)")
    # --------------------------------------------------
    status, res = chat(token, "what are my total expenses?")
    turn("2.1", "what are my total expenses?", status, res)
    check("2.1", status == 200, "Total expenses answered")
    time.sleep(2)

    status, res = chat(token, "how much of that is just food?")
    turn("2.2", "how much of that is just food?", status, res)
    check("2.2", status == 200, "Follow-up question answered with context")
    data = res.get("data", res)
    # The AI should either return the amount for food or do a chat
    check("2.2", data.get("action") in ["category", "filter", "chat"], "AI understood follow-up intent")
    time.sleep(2)

    status, res = chat(token, "and what about bills?")
    turn("2.3", "and what about bills?", status, res)
    check("2.3", status == 200, "Second follow-up question answered with context")
    time.sleep(2)

    # --------------------------------------------------
    section("RESULTS")
    # --------------------------------------------------
    if failures:
        print(f"\n  \033[91mFAILED — {len(failures)} check(s) failed:\033[0m")
        for f in failures:
            print(f"    - {f}")
    else:
        print(f"\n  \033[92mALL CHECKS PASSED!\033[0m")
    print()

if __name__ == "__main__":
    run()
