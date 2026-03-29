from sqlalchemy.orm import Session
from sqlalchemy import func
from models.expense import Expense
from schemas.expense import ExpenseUpdate
from typing import List, Dict, Any
from decimal import Decimal

def add_expense(db: Session, user_id: int, expense_data: dict) -> Expense:
    """
    Adds an expense with intelligent categorization fallback.
    """
    TITLE_TO_CATEGORY_MAP = {
        "rapido": "transport", "uber": "transport", "ola": "transport",
        "metro": "transport", "zomato": "food", "swiggy": "food",
        "coffee": "beverages", "starbucks": "beverages",
        "blinkit": "groceries", "zepto": "groceries",
        "groceries": "food", "pizza": "food", "dinner": "food", "lunch": "food"
    }

    CATEGORY_NORMALIZATION_MAP = {
        "groceries": "food",
        "beverage": "beverages",
        "drinks": "beverages",
        "transportation": "transport",
    }
    
    title = expense_data.get("title")
    if not title:
        raise ValueError("Expense title is required")

    category = expense_data.get("category")

    # 1. Normalize provided category
    if category:
        category = CATEGORY_NORMALIZATION_MAP.get(category.lower(), category.lower())
    
    # 2. If no category or LLM gave "misc", try title-based lookup
    if not category or category == "misc":
        category = TITLE_TO_CATEGORY_MAP.get(title.lower(), "misc")

    expense_data["category"] = category
    
    if expense_data.get('amount') is not None:
        amount = Decimal(str(expense_data['amount']))
        if amount <= 0:
            raise ValueError("Amount must be positive")
        expense_data['amount'] = amount

    allowed_keys = {"title", "amount", "category", "description", "date"}
    
    filtered_data = {
        key: expense_data[key] 
        for key in allowed_keys 
        if key in expense_data and expense_data[key] is not None
    }
    
    if 'category' not in filtered_data:
        filtered_data['category'] = 'misc'

    db_expense = Expense(**filtered_data, user_id=user_id)
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

def list_expenses(db: Session, user_id: int) -> List[Expense]:
    return db.query(Expense).filter(Expense.user_id == user_id).order_by(Expense.date.desc()).all()

def total_expense(db: Session, user_id: int) -> Decimal:
    total = db.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id
    ).scalar() or 0
    return total if total is not None else Decimal('0.00')

def get_expenses_by_title(db: Session, user_id: int, title: str) -> List[Expense]:
    return db.query(Expense).filter(
        Expense.user_id == user_id,
        func.lower(Expense.title).contains(title.lower())
    ).all()

def get_expense_by_id(db: Session, user_id: int, expense_id: int) -> Expense:
    return db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == user_id).first()

def delete_expense(db: Session, expense: Expense) -> None:
    db.delete(expense)
    db.commit()

def update_expense(db: Session, expense: Expense, update_data: Dict[str, Any]) -> Expense:
    if 'amount' in update_data and update_data['amount'] is not None:
        update_data['amount'] = Decimal(str(update_data['amount']))
    for key, value in update_data.items():
        if value is not None:
            setattr(expense, key, value)
    db.commit()
    db.refresh(expense)
    return expense

def filter_expenses(db: Session, user_id: int, filters: dict) -> List[Expense]:
    query = db.query(Expense).filter(Expense.user_id == user_id)
    if filters.get("category"):
        query = query.filter(func.lower(Expense.category) == filters["category"].lower())
    if filters.get("min_amount"):
        query = query.filter(Expense.amount >= filters["min_amount"])
    if filters.get("max_amount"):
        query = query.filter(Expense.amount <= filters["max_amount"])
    return query.order_by(Expense.date.desc()).all()