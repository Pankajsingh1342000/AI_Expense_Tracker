from sqlalchemy.orm import Session
from sqlalchemy import func
from models.budget import Budget
from models.expense import Expense
from datetime import datetime
from typing import List, Dict, Any
from decimal import Decimal

def set_or_update_budget(db: Session, user_id: int, category: str, amount: float) -> Budget:
    budget = db.query(Budget).filter(
        Budget.user_id == user_id,
        func.lower(Budget.category) == category.lower()
    ).first()

    decimal_amount = Decimal(str(amount))

    if budget:
        budget.monthly_limit = decimal_amount
    else:
        budget = Budget(user_id=user_id, category=category, monthly_limit=decimal_amount)
        db.add(budget)
    
    db.commit()
    db.refresh(budget)
    return budget

def get_budget(db: Session, user_id: int, category: str) -> Budget:
    return db.query(Budget).filter(
        Budget.user_id == user_id,
        func.lower(Budget.category) == category.lower()
    ).first()

def delete_budget(db: Session, budget: Budget) -> None:
    db.delete(budget)
    db.commit()

def get_all_budgets(db: Session, user_id: int) -> List[Budget]:
    return db.query(Budget).filter(Budget.user_id == user_id).all()

def get_monthly_spent_for_category(db: Session, user_id: int, category: str) -> float:
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        func.lower(Expense.category) == category.lower(),
        Expense.date >= month_start
    ).scalar() or 0

def get_budget_warnings(db: Session, user_id: int, threshold: int = 80) -> List[Dict[str, Any]]:
    warnings = []
    budgets = get_all_budgets(db, user_id)
    
    for budget in budgets:
        if budget.monthly_limit == 0:
            continue
        
        spent = get_monthly_spent_for_category(db, user_id, budget.category)
        percent = (spent / budget.monthly_limit) * 100

        if percent >= threshold:
            warnings.append({
                "category": budget.category,
                "spent": spent,
                "budget": budget.monthly_limit,
                "usage_percent": round(percent, 2)
            })
    return warnings