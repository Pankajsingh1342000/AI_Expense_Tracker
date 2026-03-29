from sqlalchemy.orm import Session
from models.user import User
from services import budget_service

def handle_set_budget(db: Session, current_user: User, parsed: dict):
    budget = budget_service.set_or_update_budget(db, current_user.id, parsed["category"], parsed["amount"])
    return {"message": f"Budget for '{budget.category}' set to {budget.monthly_limit}."}

def handle_budget_status(db: Session, current_user: User, parsed: dict):
    category = parsed.get("category")
    if not category: return {"error": "Category is required to check budget status."}
    
    budget = budget_service.get_budget(db, current_user.id, category)
    if not budget: return {"message": f"No budget set for '{category}'."}
    
    spent = budget_service.get_monthly_spent_for_category(db, current_user.id, category)
    return {
        "category": category,
        "budget": budget.monthly_limit,
        "spent": spent,
        "remaining": budget.monthly_limit - spent
    }

def handle_delete_budget(db: Session, current_user: User, parsed: dict):
    category = parsed.get("category")
    if not category: return {"error": "Category required to delete budget."}
    
    budget = budget_service.get_budget(db, current_user.id, category)
    if not budget: return {"message": f"No budget found for '{category}'."}

    budget_service.delete_budget(db, budget)
    return {"message": f"Budget for '{category}' deleted."}

def handle_budget_overview(db: Session, current_user: User, parsed: dict):
    budgets = budget_service.get_all_budgets(db, current_user.id)
    if not budgets: return {"message": "No budgets have been set."}

    overview = []
    for budget in budgets:
        spent = budget_service.get_monthly_spent_for_category(db, current_user.id, budget.category)
        overview.append({
            "category": budget.category,
            "budget": budget.monthly_limit,
            "spent": spent,
            "remaining": budget.monthly_limit - spent
        })
    return {"budgets": overview}

def handle_budget_warning(db: Session, current_user: User, parsed: dict):
    warnings = budget_service.get_budget_warnings(db, current_user.id)
    return {"warnings": warnings}
