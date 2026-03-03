import json
from openai import OpenAI
from ai.prompt import get_expense_prompt
import os

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

def parse_user_command(user_command: str) -> dict:
    """
    Sends user command to LLM and extracts structured JSON.
    """

    prompt = get_expense_prompt(user_command)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a financial assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    content = response.choices[0].message.content.strip()

    try:
        return json.loads(content)
    except:
        return {"action": "unknown"}