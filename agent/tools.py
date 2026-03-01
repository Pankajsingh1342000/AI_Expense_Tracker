from db.database import SessionLocal
from db.models import Expense

def add_expense(description: str, amount: float, category: str):
    db = SessionLocal()
    expense = Expense(
        description = description,
        amount = amount,
        category = category
    )
    db.add(expense)
    db.commit()
    db.close()
    return "Expense added successfully."

def get_total_expense():
    db = SessionLocal()
    expenses = db.query(Expense).all()
    total = sum(e.amount for e in expenses)
    db.close()
    return f"Total expense is ₹{total}"