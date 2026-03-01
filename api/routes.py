from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from db.database import SessionLocal
from db.models import Expense
from agent.expense_agent import parse_user_command

router = APIRouter()

class ExpenseInput(BaseModel):
    title: str
    amount: float
    category: str

@router.post("/add")
def add_expense(expense: ExpenseInput):
    db = SessionLocal()
    new_expense = Expense(title=expense.title, amount=expense.amount, category=expense.category)
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return {"message": "Expense added", "expense": {
        "id": new_expense.id,
        "title": new_expense.title,
        "amount": new_expense.amount,
        "category": new_expense.category
    }}

@router.get("/list")
def list_expenses():
    db = SessionLocal()
    expenses = db.query(Expense).all()
    return [{"id": e.id, "title": e.title, "amount": e.amount, "category": e.category} for e in expenses]

@router.post("/ai")
def handle_ai_command(command: str):
    result = parse_user_command(command)
    db = SessionLocal()
    if "error" in result:
        raise HTTPException(status_code=400, detail="Could not parse command")

    action = result.get("action")
    if action == "add":
        new_expense = Expense(
            title=result.get("title", "Unknown"),
            amount=result.get("amount", 0),
            category=result.get("category", "Other")
        )
        db.add(new_expense)
        db.commit()
        db.refresh(new_expense)
        return {"message": "Expense added via AI", "expense": {
            "id": new_expense.id,
            "title": new_expense.title,
            "amount": new_expense.amount,
            "category": new_expense.category
        }}
    elif action == "get":
        expenses = db.query(Expense).all()
        return {"expenses": [{"title": e.title, "amount": e.amount, "category": e.category} for e in expenses]}
    else:
        raise HTTPException(status_code=400, detail="Unknown action")