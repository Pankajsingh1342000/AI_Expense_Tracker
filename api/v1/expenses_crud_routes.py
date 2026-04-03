from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from models.user import User
from schemas.expense import ExpenseCreate, ExpenseResponse, ExpenseUpdate
from services import expense_service
from services.query_cache import invalidate_user_cache

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payload = expense.model_dump()
    if payload.get("date") is None:
        payload["date"] = datetime.now()
    created = expense_service.add_expense(db, current_user.id, payload)
    invalidate_user_cache(current_user.id)
    return ExpenseResponse.model_validate(created)


@router.get("", response_model=list[ExpenseResponse])
def get_expenses(
    category: Optional[str] = Query(default=None),
    min_amount: Optional[float] = Query(default=None, gt=0),
    max_amount: Optional[float] = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if category is not None or min_amount is not None or max_amount is not None:
        expenses = expense_service.filter_expenses(
            db,
            current_user.id,
            {"category": category, "min_amount": min_amount, "max_amount": max_amount},
        )
    else:
        expenses = expense_service.list_expenses(db, current_user.id)
    return [ExpenseResponse.model_validate(expense) for expense in expenses]


@router.get("/summary/total")
def get_total_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total = expense_service.total_expense(db, current_user.id)
    return {"total_expenses": str(total)}


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expense = expense_service.get_expense_by_id(db, current_user.id, expense_id)
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return ExpenseResponse.model_validate(expense)


@router.put("/{expense_id}")
def update_expense(
    expense_id: int,
    expense_update: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expense = expense_service.get_expense_by_id(db, current_user.id, expense_id)
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    updated = expense_service.update_expense(db, expense, expense_update.model_dump(exclude_none=True))
    invalidate_user_cache(current_user.id)
    return {"message": "Expense updated successfully", "expense": ExpenseResponse.model_validate(updated)}


@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    expense = expense_service.get_expense_by_id(db, current_user.id, expense_id)
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    expense_service.delete_expense(db, expense)
    invalidate_user_cache(current_user.id)
    return {"message": f"Expense '{expense.title}' deleted successfully."}
