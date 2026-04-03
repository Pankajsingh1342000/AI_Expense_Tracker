from models.user import User
from sqlalchemy.orm import Session

from services import budget_service
from services.query_cache import invalidate_user_cache, make_cache_key, read_cache


def handle_set_budget(db: Session, current_user: User, parsed: dict):
    budget = budget_service.set_or_update_budget(db, current_user.id, parsed["category"], parsed["amount"])
    invalidate_user_cache(current_user.id)
    return {"message": f"Budget for '{budget.category}' set to {budget.monthly_limit}."}


def handle_budget_status(db: Session, current_user: User, parsed: dict):
    category = parsed.get("category")
    if not category:
        return {"error": "Category is required to check budget status."}

    cache_key = make_cache_key(current_user.id, "budget_status", parsed)

    def build_response():
        budget = budget_service.get_budget(db, current_user.id, category)
        if not budget:
            return {"message": f"No budget set for '{category}'."}

        spent = budget_service.get_monthly_spent_for_category(db, current_user.id, category)
        return {
            "category": category,
            "budget": budget.monthly_limit,
            "spent": spent,
            "remaining": budget.monthly_limit - spent,
        }

    return read_cache.get_or_set(cache_key, build_response)


def handle_delete_budget(db: Session, current_user: User, parsed: dict):
    category = parsed.get("category")
    if not category:
        return {"error": "Category required to delete budget."}

    budget = budget_service.get_budget(db, current_user.id, category)
    if not budget:
        return {"message": f"No budget found for '{category}'."}

    budget_service.delete_budget(db, budget)
    invalidate_user_cache(current_user.id)
    return {"message": f"Budget for '{category}' deleted."}


def handle_budget_overview(db: Session, current_user: User, parsed: dict):
    cache_key = make_cache_key(current_user.id, "budget_overview", parsed)

    def build_response():
        budgets = budget_service.get_all_budgets(db, current_user.id)
        if not budgets:
            return {"message": "No budgets have been set."}

        overview = []
        for budget in budgets:
            spent = budget_service.get_monthly_spent_for_category(db, current_user.id, budget.category)
            overview.append(
                {
                    "category": budget.category,
                    "budget": budget.monthly_limit,
                    "spent": spent,
                    "remaining": budget.monthly_limit - spent,
                }
            )
        return {"budgets": overview}

    return read_cache.get_or_set(cache_key, build_response)


def handle_budget_warning(db: Session, current_user: User, parsed: dict):
    cache_key = make_cache_key(current_user.id, "budget_warning", parsed)
    return read_cache.get_or_set(
        cache_key,
        lambda: {"warnings": budget_service.get_budget_warnings(db, current_user.id)},
    )
