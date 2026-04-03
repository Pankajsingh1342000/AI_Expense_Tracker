from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from models.user import User
from schemas.budget import BudgetCreate, BudgetResponse, BudgetUpdate
from services import budget_service
from services.query_cache import invalidate_user_cache

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    created = budget_service.set_or_update_budget(db, current_user.id, budget.category, budget.monthly_limit)
    invalidate_user_cache(current_user.id)
    return BudgetResponse.model_validate(created)


@router.get("", response_model=list[BudgetResponse])
def list_budgets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    budgets = budget_service.get_all_budgets(db, current_user.id)
    return [BudgetResponse.model_validate(budget) for budget in budgets]


@router.get("/status/warnings")
def get_budget_warnings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {"warnings": budget_service.get_budget_warnings(db, current_user.id)}


@router.get("/{category}")
def get_budget_status(
    category: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    budget = budget_service.get_budget(db, current_user.id, category)
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    spent = budget_service.get_monthly_spent_for_category(db, current_user.id, category)
    return {
        "category": budget.category,
        "budget": float(budget.monthly_limit),
        "spent": float(spent),
        "remaining": float(budget.monthly_limit - spent),
    }


@router.put("/{category}", response_model=BudgetResponse)
def update_budget(
    category: str,
    budget_update: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = budget_service.set_or_update_budget(db, current_user.id, category, budget_update.monthly_limit)
    invalidate_user_cache(current_user.id)
    return BudgetResponse.model_validate(updated)


@router.delete("/{category}")
def delete_budget(
    category: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    budget = budget_service.get_budget(db, current_user.id, category)
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    budget_service.delete_budget(db, budget)
    invalidate_user_cache(current_user.id)
    return {"message": f"Budget for '{category}' deleted."}
