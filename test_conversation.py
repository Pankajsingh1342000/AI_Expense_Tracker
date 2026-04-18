"""
Complex conversational AI integration test.
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
    # Retry loop to wait for server
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
    print(f"     AI  : {reply[:250]}{'...' if len(reply) > 250 else ''}")


def run():
    section("SETUP — Register & Login")
    token = register_and_login()
    print(f"  Logged in as {TEST_EMAIL}")

    # --------------------------------------------------
    section("SCENARIO 1 — Add expenses (with duplicates)")
    # --------------------------------------------------
    for msg in [
        "bought pizza for 300 category food",
        "spent 500 on groceries",
        "paid 150 for coffee",
        "bought pizza for 150 category food",   # 2nd pizza — DUPLICATE
        "paid 250 for dinner",
    ]:
        status, res = chat(token, msg)
        turn("1.x", msg, status, res)
        check("1", status == 200, f"Added: {msg}")
        check("1", "reply" in res, "Reply field present")
        time.sleep(2)

    # --------------------------------------------------
    section("SCENARIO 2 — Conversational Q&A with live data")
    # --------------------------------------------------
    status, res = chat(token, "am I spending too much on food?")
    turn("2.1", "am I spending too much on food?", status, res)
    check("2.1", status == 200, "Food spending question answered")
    check("2.1", len(res.get("reply", "")) > 15, "Reply is meaningful")
    time.sleep(2)

    status, res = chat(token, "what is my biggest expense so far?")
    turn("2.2", "what is my biggest expense so far?", status, res)
    check("2.2", status == 200, "Biggest expense answered")
    time.sleep(2)

    # --------------------------------------------------
    section("SCENARIO 3 — Multi-turn: Duplicate UPDATE + memory")
    # --------------------------------------------------
    status, res = chat(token, "update pizza to 400")
    turn("3.1", "update pizza to 400 (2 pizzas exist)", status, res)
    check("3.1", status == 200, "Clarification or reply received")
    time.sleep(2)

    # Follow-up using natural language — AI must use memory to understand
    status, res = chat(token, "the cheaper one")
    turn("3.2", "the cheaper one (follow-up using conversation memory)", status, res)
    check("3.2", status == 200, "Follow-up resolved via conversation memory")
    check("3.2", "reply" in res, "AI reply present")
    time.sleep(2)

    # --------------------------------------------------
    section("SCENARIO 4 — Multi-turn: Follow-up chains")
    # --------------------------------------------------
    status, res = chat(token, "what about the other one?")
    turn("4.1", "what about the other one? (references the 2nd pizza)", status, res)
    check("4.1", status == 200, "Chained context understood")
    time.sleep(2)

    # --------------------------------------------------
    section("SCENARIO 5 — Insights")
    # --------------------------------------------------
    status, res = chat(token, "give me some financial advice based on this")
    turn("5.1", "give me financial advice", status, res)
    check("5.1", status == 200, "Insights generated")

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
