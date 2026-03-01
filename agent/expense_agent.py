import os
import requests
import json
from dotenv import load_dotenv
from agent.prompts import SYSTEM_PROMPT
from agent.tools import add_expense, get_total_expense

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def process_query(user_input: str):
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0.2
        }

        response = requests.post(url, headers=headers, json=payload)

        result = response.json()

        if "choices" not in result:
            return f"OpenRouter Error: {result}"

        reply = result["choices"][0]["message"]["content"].strip()

        parsed = json.loads(reply)

        print("MODEL RAW REPLY:", reply)
        print("PARSED JSON:", parsed)

        action = parsed.get("action")

        if action == "add_expense":
            return add_expense(
                parsed["note"],
                float(parsed["amount"]),
                parsed["category"]
            )

        elif action in ["get_total", "get_total_expense", "get_total_expenses"]:
            return get_total_expense()

        else:
            return "Unknown action"

    except Exception as e:
        return f"ERROR OCCURRED: {str(e)}"