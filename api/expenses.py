from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ai.parse import parse_user_command
from api.deps import get_db, get_current_user
from schemas.expense import ExpenseCreate
from schemas.ai import AIQuery
from services.expense_service import (
    add_expense,
    list_expenses,
    total_expense,
    category_total
)
from models.user import User
from services.expense_service import category_breakdown
from services.ai_insight_service import generate_insight_from_summary

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.post("/")
def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return add_expense(
        db,
        current_user.id,
        expense.title,
        expense.amount,
        expense.category
    )


@router.get("/")
def get_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return list_expenses(db, current_user.id)


@router.get("/total")
def get_total(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return {"total": total_expense(db, current_user.id)}


@router.get("/category-summary")
def get_category_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return category_total(db, current_user.id)

@router.post("/ai")
def ai_expense_handler(
    user_input: AIQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    parsed = parse_user_command(user_input.query)

    action = parsed.get("action")

    if action == "add":
        return add_expense(
            db,
            current_user.id,
            parsed.get("title"),
            parsed.get("amount"),
            parsed.get("category")
        )

    if action == "total":
        return {"total": total_expense(db, current_user.id)}

    if action == "list":
        return list_expenses(db, current_user.id)

    if action == "category":
        return category_total(db, current_user.id)

    if action == "set_budget":
        from models.budget import Budget

        budget = Budget(
            user_id=current_user.id,
            category=parsed.get("category"),
            monthly_limit=parsed.get("amount")
        )
        db.add(budget)
        db.commit()

        return {"message": "Budget set successfully"}

    if action == "budget_status":
        from sqlalchemy import func
        from models.expense import Expense
        from models.budget import Budget
        from datetime import datetime

        month_start = datetime.now().replace(day=1)

        total_spent = db.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            Expense.category == parsed.get("category"),
            Expense.date >= month_start
        ).scalar() or 0

        budget = db.query(Budget).filter(
            Budget.user_id == current_user.id,
            Budget.category == parsed.get("category")
        ).first()

        if not budget:
            return {"message": "No budget set for this category"}

        remaining = budget.monthly_limit - total_spent

        return {
            "spent": total_spent,
            "budget": budget.monthly_limit,
            "remaining": remaining
        }

    if action == "filter":
        from models.expense import Expense

        query = db.query(Expense).filter(
            Expense.user_id == current_user.id
        )

        if parsed.get("category"):
            query = query.filter(
                Expense.category == parsed.get("category")
            )

        if parsed.get("min_amount"):
            query = query.filter(
                Expense.amount >= parsed.get("min_amount")
            )

        if parsed.get("max_amount"):
            query = query.filter(
                Expense.amount <= parsed.get("max_amount")
            )

        results = query.all()
        return results
    
    if action == "insights":
        breakdown = category_breakdown(db, current_user.id)

        if not breakdown:
            return {"messege": "No Expense Found."}
        
        summary = "\n".join(
            [f"{category}: {amount}" for category, amount in breakdown]
        )

        insight = generate_insight_from_summary(summary)

        return {"insight": insight}
        
    
    return {"message": "Unknown action"}