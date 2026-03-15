from schemas.expense import ExpenseResponse
from sqlalchemy.orm import Session
from models.user import User
from fastapi import Response
import json
from datetime import datetime
from services import (
    expense_service,
    budget_service,
    analytics_service,
    ai_insight_service
)

def create_clarification_response(items, item_type="expense"):
    return {
        "status": "clarification_needed",
        "message": f"I found multiple {item_type}s. Please specify which one.",
        "options": [ExpenseResponse.model_validate(item).model_dump(mode='json') for item in items]
    }

def handle_add(db: Session, current_user: User, parsed: dict):
    expense_payload = parsed.copy()

    if expense_payload.get("date") is None:
        expense_payload["date"] = datetime.now()

    db_expense = expense_service.add_expense(db, current_user.id, expense_payload)
    return ExpenseResponse.model_validate(db_expense)

def handle_list(db: Session, current_user: User, parsed: dict):
    expenses_from_db = expense_service.list_expenses(db, current_user.id)
    return [ExpenseResponse.model_validate(expense) for expense in expenses_from_db]
    
    return response_models

def handle_update(db: Session, current_user: User, parsed: dict):
    expense_id = parsed.get("id")
    title = parsed.get("title")
    
    if expense_id:
        expense = expense_service.get_expense_by_id(db, current_user.id, expense_id)
        if not expense: return {"error": "Expense not found"}
    elif title:
        expenses = expense_service.get_expenses_by_title(db, current_user.id, title)
        if not expenses: return {"error": "Expense not found"}
        if len(expenses) > 1: return create_clarification_response(expenses)
        expense = expenses[0]
    else:
        return {"error": "Expense ID or title is required for an update."}

    update_data = {k: v for k, v in parsed.items() if k in ["title", "amount", "category"]}
    updated_expense = expense_service.update_expense(db, expense, update_data)
    return {"message": "Expense updated successfully", "expense": ExpenseResponse.model_validate(updated_expense)}

def handle_delete(db: Session, current_user: User, parsed: dict):
    expense_id = parsed.get("id")
    title = parsed.get("title")

    if expense_id:
        expense = expense_service.get_expense_by_id(db, current_user.id, expense_id)
        if not expense: return {"error": "Expense not found"}
    elif title:
        expenses = expense_service.get_expenses_by_title(db, current_user.id, title)
        if not expenses: return {"error": "Expense not found"}
        if len(expenses) > 1: return create_clarification_response(expenses)
        expense = expenses[0]
    else:
        return {"error": "Expense ID or title is required for deletion."}
    
    expense_service.delete_expense(db, expense)
    return {"message": f"Expense '{expense.title}' deleted successfully."}

def handle_filter(db: Session, current_user: User, parsed: dict):
    return expense_service.filter_expenses(db, current_user.id, parsed)

def handle_total(db: Session, current_user: User, parsed: dict):

    total = expense_service.total_expense(db, current_user.id)

    response_data = {'total_expenses': str(total)}
    
    json_string_content = json.dumps(response_data)
    
    return Response(content=json_string_content, media_type="application/json")

def handle_category_total(db: Session, current_user: User, parsed: dict):
    # This action was called 'category' in the prompt
    category = parsed.get("category")
    if category:
        total = budget_service.get_monthly_spent_for_category(db, current_user.id, category)
        return {"category": category, "total_spent": total}
    # If no category specified, return breakdown
    breakdown = analytics_service.get_category_breakdown(db, current_user.id)
    return [{"category": c, "total": a} for c, a in breakdown]

def handle_set_budget(db: Session, current_user: User, parsed: dict):
    budget = budget_service.set_or_update_budget(db, current_user.id, parsed["category"], parsed["amount"])
    return {"message": f"Budget for '{budget.category}' set to {budget.monthly_limit}."}

def handle_budget_status(db: Session, current_user: User, parsed: dict):
    category = parsed.get("category")
    if not category: return {"error": "Category is required to check budget status."}
    
    budget = budget_service.get_budget(db, current_user.id, category)
    if not budget: return {"message": f"No budget set for '{category}'."}
    
    spent = budget_service.get_monthly_spent_for_category(db, current_user.id, category)
    return {
        "category": category,
        "budget": budget.monthly_limit,
        "spent": spent,
        "remaining": budget.monthly_limit - spent
    }

def handle_delete_budget(db: Session, current_user: User, parsed: dict):
    category = parsed.get("category")
    if not category: return {"error": "Category required to delete budget."}
    
    budget = budget_service.get_budget(db, current_user.id, category)
    if not budget: return {"message": f"No budget found for '{category}'."}

    budget_service.delete_budget(db, budget)
    return {"message": f"Budget for '{category}' deleted."}

def handle_budget_overview(db: Session, current_user: User, parsed: dict):
    budgets = budget_service.get_all_budgets(db, current_user.id)
    if not budgets: return {"message": "No budgets have been set."}

    overview = []
    for budget in budgets:
        spent = budget_service.get_monthly_spent_for_category(db, current_user.id, budget.category)
        overview.append({
            "category": budget.category,
            "budget": budget.monthly_limit,
            "spent": spent,
            "remaining": budget.monthly_limit - spent
        })
    return {"budgets": overview}

def handle_budget_warning(db: Session, current_user: User, parsed: dict):
    warnings = budget_service.get_budget_warnings(db, current_user.id)
    return {"warnings": warnings}

def handle_insights(db: Session, current_user: User, parsed: dict):
    breakdown = analytics_service.get_category_breakdown(db, current_user.id)
    if not breakdown: return {"message": "Not enough data for insights. Add some expenses first."}
    
    summary = "\n".join(f"- {category}: {amount:.2f}" for category, amount in breakdown)
    insight = ai_insight_service.generate_insight_from_summary(summary)
    return {"insight": insight}

# --- Analytics Handlers ---
def handle_monthly_summary(db: Session, current_user: User, parsed: dict):
    return analytics_service.get_monthly_summary(db, current_user.id)

def handle_daily_spending(db: Session, current_user: User, parsed: dict):
    return analytics_service.get_daily_spending(db, current_user.id)

def handle_top_category(db: Session, current_user: User, parsed: dict):
    return analytics_service.get_top_spending_category(db, current_user.id)

def handle_spending_trend(db: Session, current_user: User, parsed: dict):
    return analytics_service.get_spending_trend(db, current_user.id)

# The Dispatcher Dictionary
ACTION_HANDLERS = {
    "add": handle_add,
    "list": handle_list,
    "update": handle_update,
    "delete": handle_delete,
    "filter": handle_filter,
    "total": handle_total,
    "category": handle_category_total,
    "set_budget": handle_set_budget,
    "update_budget": handle_set_budget, # Same as set_budget
    "delete_budget": handle_delete_budget,
    "budget_status": handle_budget_status,
    "budget_overview": handle_budget_overview,
    "budget_warning": handle_budget_warning,
    "insights": handle_insights,
    "monthly_summary": handle_monthly_summary,
    "daily_spending": handle_daily_spending,
    "top_category": handle_top_category,
    "spending_trend": handle_spending_trend,
}