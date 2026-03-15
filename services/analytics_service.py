from sqlalchemy.orm import Session
from sqlalchemy import func
# --- CHANGE IS HERE ---
from models.expense import Expense  # Direct import from the specific file
# --- END CHANGE ---
from datetime import datetime, date
from typing import List, Dict, Any, Tuple

def get_category_breakdown(db: Session, user_id: int) -> List[Tuple[str, float]]:
    return db.query(
        Expense.category,
        func.sum(Expense.amount)
    ).filter(
        Expense.user_id == user_id
    ).group_by(Expense.category).all()

def get_monthly_summary(db: Session, user_id: int) -> Dict[str, Any]:
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id, Expense.date >= month_start
    ).scalar() or 0

    categories = db.query(
        Expense.category, func.sum(Expense.amount)
    ).filter(
        Expense.user_id == user_id, Expense.date >= month_start
    ).group_by(Expense.category).all()

    return {
        "month_total": total,
        "categories": [{"category": c, "amount": a} for c, a in categories]
    }

def get_daily_spending(db: Session, user_id: int) -> Dict[str, Any]:
    today = date.today()
    total = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        func.date(Expense.date) == today
    ).scalar() or 0
    return {"date": str(today), "total_spent": total}

def get_top_spending_category(db: Session, user_id: int) -> Dict[str, Any]:
    result = db.query(
        Expense.category, func.sum(Expense.amount).label("total")
    ).filter(
        Expense.user_id == user_id
    ).group_by(Expense.category).order_by(
        func.sum(Expense.amount).desc()
    ).first()

    if not result:
        return {"message": "No expenses found"}
    return {"top_category": result[0], "amount": result[1]}

def get_spending_trend(db: Session, user_id: int, days: int = 7) -> List[Dict[str, Any]]:
    trend = db.query(
        func.date(Expense.date), func.sum(Expense.amount)
    ).filter(
        Expense.user_id == user_id
    ).group_by(func.date(Expense.date)).order_by(
        func.date(Expense.date).desc()
    ).limit(days).all()
    return [{"date": str(d), "amount": a} for d, a in trend]