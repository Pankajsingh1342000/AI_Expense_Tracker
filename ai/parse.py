import json
import os
from openai import OpenAI
from pydantic import ValidationError
from ai.prompt import get_expense_prompt
from schemas.ai import AIResponse

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

def parse_user_command(user_command: str) -> dict:
    """
    Sends user command to LLM, extracts structured JSON, and validates it.
    """
    prompt = get_expense_prompt(user_command)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a financial assistant. Always respond in valid JSON only. Do not include explanations."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    try:
        # First, load the string into a Python dict
        raw_json = json.loads(response.choices[0].message.content)
        # Then, validate it with Pydantic
        validated_data = AIResponse(**raw_json)
        # Return it as a dictionary
        return validated_data.model_dump()
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"ERROR: LLM output failed validation. Error: {e}. Output: {response.choices[0].message.content}")
        return {"action": "unknown", "title": "Error in parsing command"}
    except Exception as e:
        print(f"An unexpected error occurred during parsing: {e}")
        return {"action": "unknown", "title": "Unexpected error"}