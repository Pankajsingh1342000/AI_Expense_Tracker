import openai
from config import OPENROUTER_API_KEY
import json

openai.api_key = OPENROUTER_API_KEY

def parse_user_command(command: str):
    prompt = f"""
You are an AI assistant for an expense tracker.
User command: "{command}"
Extract action, title, amount, category, date if available.
Respond strictly as JSON like:
{{"action": "add" or "get", "title": "...", "amount": 0, "category": "...", "date": "YYYY-MM-DD"}}.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    try:
        return json.loads(response.choices[0].message.content)
    except:
        return {"error": "Could not parse command"}