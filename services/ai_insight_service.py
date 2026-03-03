from openai import OpenAI
import os

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

def generate_insight_from_summary(summary: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a financial advisor. Give short, practical insights and suggestions."
            },
            {
                "role": "user",
                "content": f"User spending summary:\n{summary}\n\nGive insights."
            }
        ],
        temperature=0.5
    )

    return response.choices[0].message.content