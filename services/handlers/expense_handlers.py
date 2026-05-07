import json
from datetime import datetime

from fastapi import Response
from models.user import User
from schemas.expense import ExpenseResponse
from sqlalchemy.orm import Session

from services import expense_service
from services.query_cache import invalidate_user_cache, make_cache_key, read_cache


def create_clarification_response(items, item_type="expense"):
    return {
        "status": "clarification_needed",
        "message": f"I found multiple {item_type}s. Please specify which one.",
        "options": [ExpenseResponse.model_validate(item).model_dump(mode="json") for item in items],
    }


def handle_add(db: Session, current_user: User, parsed: dict):
    expense_payload = parsed.copy()

    if expense_payload.get("date") is None:
        expense_payload["date"] = datetime.now()

    db_expense = expense_service.add_expense(db, current_user.id, expense_payload)
    invalidate_user_cache(current_user.id)
    return ExpenseResponse.model_validate(db_expense)


def handle_list(db: Session, current_user: User, parsed: dict):
    cache_key = make_cache_key(current_user.id, "list", parsed)
    return read_cache.get_or_set(
        cache_key,
        lambda: [ExpenseResponse.model_validate(expense) for expense in expense_service.list_expenses(db, current_user.id)],
    )


def handle_update(db: Session, current_user: User, parsed: dict):
    expense_id = parsed.get("id")
    title = parsed.get("title")

    if expense_id:
        expense = expense_service.get_expense_by_id(db, current_user.id, expense_id)
        if not expense:
            return {"error": "Expense not found"}
    elif title:
        expenses = expense_service.get_expenses_by_title(db, current_user.id, title)
        if not expenses:
            return {"error": "Expense not found"}
        if len(expenses) > 1:
            return create_clarification_response(expenses)
        expense = expenses[0]
    else:
        return {"error": "Expense ID or title is required for an update."}

    update_data = {k: v for k, v in parsed.items() if k in ["title", "amount", "category", "description"]}
    updated_expense = expense_service.update_expense(db, expense, update_data)
    invalidate_user_cache(current_user.id)
    return {"message": "Expense updated successfully", "expense": ExpenseResponse.model_validate(updated_expense)}


def handle_delete(db: Session, current_user: User, parsed: dict):
    expense_id = parsed.get("id")
    title = parsed.get("title")

    if expense_id:
        expense = expense_service.get_expense_by_id(db, current_user.id, expense_id)
        if not expense:
            return {"error": "Expense not found"}
    elif title:
        expenses = expense_service.get_expenses_by_title(db, current_user.id, title)
        if not expenses:
            return {"error": "Expense not found"}
        if len(expenses) > 1:
            return create_clarification_response(expenses)
        expense = expenses[0]
    else:
        return {"error": "Expense ID or title is required for deletion."}

    expense_service.delete_expense(db, expense)
    invalidate_user_cache(current_user.id)
    return {"message": f"Expense '{expense.title}' deleted successfully."}


def handle_filter(db: Session, current_user: User, parsed: dict):
    cache_key = make_cache_key(current_user.id, "filter", parsed)
    return read_cache.get_or_set(
        cache_key,
        lambda: expense_service.filter_expenses(db, current_user.id, parsed),
    )


def handle_total(db: Session, current_user: User, parsed: dict):
    cache_key = make_cache_key(current_user.id, "total", parsed)

    def build_response():
        total = expense_service.total_expense(db, current_user.id)
        response_data = {"total_expenses": str(total)}
        return Response(content=json.dumps(response_data), media_type="application/json")

    return read_cache.get_or_set(cache_key, build_response)
