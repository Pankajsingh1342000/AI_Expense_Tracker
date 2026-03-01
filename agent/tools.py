from db.models import Expense
from db.database import SessionLocal
from typing import List

def add_expense(title: str, amount: float, category: str) -> dict:
    db = SessionLocal()
    expense = Expense(title=title, amount=amount, category=category)
    db.add(expense)
    db.commit()
    db.refresh(expense)
    db.close()
    return {"id": expense.id, "title": expense.title, "amount": expense.amount, "category": expense.category}

def list_expenses() -> List[dict]:
    db = SessionLocal()
    expenses = db.query(Expense).all()
    db.close()
    return [{"title": e.title, "amount": e.amount, "category": e.category} for e in expenses]

def total_expense() -> float:
    db = SessionLocal()
    total = sum([e.amount for e in db.query(Expense).all()])
    db.close()
    return total