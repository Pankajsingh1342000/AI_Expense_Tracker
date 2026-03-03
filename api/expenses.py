from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ai.parse import parse_user_command
from api.deps import get_db, get_current_user
from schemas.ai import AIQuery
from models.user import User
from services.expense_service import (
    add_expense,
    list_expenses,
    total_expense,
    category_total,
    category_breakdown
)
from services.ai_insight_service import generate_insight_from_summary
from datetime import datetime
from sqlalchemy import func
from models.expense import Expense
from models.budget import Budget

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.post("/agentic")
def agentic_expense_handler(
    user_input: AIQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fully agentic endpoint: AI decides what to do based on natural language input.
    """
    parsed = parse_user_command(user_input.query)
    action = parsed.get("action")

    # ------------------- Expense Operations -------------------
    if action == "add":
        return add_expense(
            db,
            current_user.id,
            parsed.get("title"),
            parsed.get("amount"),
            parsed.get("category")
        )

    if action == "list":
        return list_expenses(db, current_user.id)

    if action == "total":
        return {"total": total_expense(db, current_user.id)}

    if action == "category":
        return category_total(db, current_user.id)

    # ------------------- Budget Operations -------------------
    if action == "set_budget":
        category_name = parsed.get("category").lower()
        amount = parsed.get("amount")

        budget = db.query(Budget).filter(
            Budget.user_id == current_user.id,
            func.lower(Budget.category) == category_name
        ).first()

        if budget:
            budget.monthly_limit = amount
        else:
            budget = Budget(
                user_id=current_user.id,
                category=category_name,
                monthly_limit=amount
            )
            db.add(budget)
        db.commit()
        return {"message": f"Budget for '{category_name}' set successfully"}

    if action == "budget_status":
        category_name = parsed.get("category").lower()
        month_start = datetime.now().replace(day=1)

        total_spent = db.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            func.lower(Expense.category) == category_name,
            Expense.date >= month_start
        ).scalar() or 0

        budget = db.query(Budget).filter(
            Budget.user_id == current_user.id,
            func.lower(Budget.category) == category_name
        ).first()

        if not budget:
            return {"message": f"No budget set for category '{category_name}'"}

        remaining = budget.monthly_limit - total_spent
        return {
            "spent": total_spent,
            "budget": budget.monthly_limit,
            "remaining": remaining
        }

    # ------------------- Filtering -------------------
    if action == "filter":
        query = db.query(Expense).filter(Expense.user_id == current_user.id)

        if parsed.get("category"):
            query = query.filter(func.lower(Expense.category) == parsed.get("category").lower())

        if parsed.get("min_amount"):
            query = query.filter(Expense.amount >= parsed.get("min_amount"))

        if parsed.get("max_amount"):
            query = query.filter(Expense.amount <= parsed.get("max_amount"))

        return query.all()

    # ------------------- AI Insights -------------------
    if action == "insights":
        breakdown = category_breakdown(db, current_user.id)

        if not breakdown:
            return {"message": "No expenses found."}

        summary = "\n".join(f"{category}: {amount}" for category, amount in breakdown)
        insight = generate_insight_from_summary(summary)
        return {"insight": insight}

    return {"message": "Unknown action"}