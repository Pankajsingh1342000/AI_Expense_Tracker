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

    if parsed["action"] == "add":
        return add_expense(
            db,
            current_user.id,
            parsed["title"],
            parsed["amount"],
            parsed["category"]
        )

    if parsed["action"] == "total":
        return {"total": total_expense(db, current_user.id)}

    if parsed["action"] == "list":
        return list_expenses(db, current_user.id)

    if parsed["action"] == "category":
        return category_total(db, current_user.id)

    return {"message": "Unknown action"}