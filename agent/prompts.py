def get_expense_prompt(user_command: str) -> str:
    """
    Prompt for AI to parse user input and choose action.
    """
    return f"""
You are an AI assistant for managing expenses.
User command: "{user_command}"
Decide the user's intent: add expense, get total expense, or list expenses.
If adding, extract title, amount, category.
Respond strictly in JSON format:
{{"action": "add" or "total" or "list", "title": "...", "amount": 0, "category": "..."}}
"""