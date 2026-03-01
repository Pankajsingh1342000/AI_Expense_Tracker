import os
import requests
import json
from dotenv import load_dotenv
from .prompts import get_expense_prompt
from .tools import add_expense, list_expenses, total_expense

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def handle_user_command(command: str) -> dict:
    prompt = get_expense_prompt(command)
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0
        }
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                 headers=headers, json=data)
        response.raise_for_status()
        ai_text = response.json()["choices"][0]["message"]["content"]

        try:
            data = json.loads(ai_text)
        except json.JSONDecodeError:
            return {"error": "AI response could not be parsed", "raw": ai_text}

        action = data.get("action")
        if action == "add":
            return add_expense(
                title=data.get("title", "Unknown"),
                amount=data.get("amount", 0),
                category=data.get("category", "Other")
            )
        elif action == "list":
            return {"expenses": list_expenses()}
        elif action == "total":
            return {"total": total_expense()}
        else:
            return {"error": "Unknown action", "raw": data}

    except requests.exceptions.HTTPError as e:
        return {"error": "AI API call failed", "details": str(e), "response": response.text}
    except Exception as e:
        return {"error": "Unexpected error", "details": str(e)}