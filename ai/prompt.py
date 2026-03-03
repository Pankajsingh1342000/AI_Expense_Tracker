def get_expense_prompt(user_command: str) -> str:
    return f"""
You are an AI expense manager.

User command: "{user_command}"

Determine intent:
- add expense
- list expenses
- total expense
- category summary

If adding:
Extract:
- title
- amount
- category

Respond ONLY in valid JSON format:

{{
  "action": "add" | "list" | "total" | "category",
  "title": "",
  "amount": 0,
  "category": ""
}}
"""