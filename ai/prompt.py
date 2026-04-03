def get_expense_prompt(user_command: str) -> str:
    return f"""
Convert the user command into JSON for an expense tracker.

Command:
"{user_command}"

Allowed actions:
add, list, total, category, set_budget, update_budget, delete_budget,
budget_status, budget_overview, budget_warning, filter, insights,
monthly_summary, daily_spending, top_category, spending_trend, update, delete

Rules:
- Return JSON only.
- Use null for missing values.
- Amount must be a positive number.
- Category must be lowercase when present.
- Use action="update" for expense edits like:
  "update pizza amount to 300 and category to food"
  "update expense id 1 to 300"
- Use action="delete" for expense deletions like:
  "delete lunch expense"
  "delete expense id 1"
- Use action="add" for expense creation like:
  "spent 200 on food"
  "bought coffee for 50"
  "paid 180 for uber"
- Use action="filter" for requests like:
  "show food expenses"
  "show expenses above 500"
- Use action="budget_status" for:
  "what is my food budget"
- Use action="budget_overview" for:
  "show budgets"
- Use action="budget_warning" for:
  "am I near my budget limit"
- Use action="monthly_summary", "daily_spending", "top_category",
  "spending_trend", or "insights" for direct analytics requests.

Return this exact shape:
{{
  "action": "",
  "id": null,
  "title": null,
  "amount": null,
  "category": null,
  "min_amount": null,
  "max_amount": null
}}
"""
