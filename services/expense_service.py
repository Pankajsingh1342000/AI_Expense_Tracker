from sqlalchemy.orm import Session
from models.expense import Expense
from sqlalchemy import func
from datetime import datetime

def add_expense(db: Session, user_id: int, title: str, amount: float, category: str):
    expense = Expense(
        title=title,
        amount=amount,
        category=category,
        user_id=user_id
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense

def list_expenses(db: Session, user_id: int):
    return db.query(Expense).filter(Expense.user_id == user_id).all()

def total_expense(db: Session, user_id: int):
    return db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id
    ).scalar() or 0

def category_total(db: Session, user_id: int):
    return db.query(
        Expense.category,
        func.sum(Expense.amount)
    ).filter(
        Expense.user_id == user_id
    ).group_by(Expense.category).all()

def category_breakdown(db: Session, user_id: int):
    return db.query(
        Expense.category,
        func.sum(Expense.amount)
    ).filter(
        Expense.user_id == user_id
    ).group_by(
        Expense.category
    ).all()