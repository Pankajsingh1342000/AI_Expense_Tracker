def get_expense_prompt(user_command: str) -> str:
    return f"""
You are an AI financial assistant.

User command: "{user_command}"

Determine the intent.

Available actions:
- add
- list
- total
- category
- set_budget
- budget_status
- filter
- insights

If adding expense:
Extract:
- title
- amount
- category

If setting budget:
Extract:
- category
- amount

If checking budget:
Extract:
- category

If filtering:
Extract optional:
- category
- min_amount
- max_amount

Respond ONLY in valid JSON format.

Example format:

{{
  "action": "add" | "list" | "total" | "category" | "set_budget" | "budget_status" | "filter" | "insights",
  "title": "",
  "amount": 0,
  "category": "",
  "min_amount": null,
  "max_amount": null
}}
"""