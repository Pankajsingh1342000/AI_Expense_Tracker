from sqlalchemy.orm import Session
from models.user import User
from services import analytics_service, ai_insight_service, budget_service

def handle_category_total(db: Session, current_user: User, parsed: dict):
    category = parsed.get("category")
    if category:
        total = budget_service.get_monthly_spent_for_category(db, current_user.id, category)
        return {"category": category, "total_spent": total}
    # If no category specified, return breakdown
    breakdown = analytics_service.get_category_breakdown(db, current_user.id)
    return [{"category": c, "total": a} for c, a in breakdown]

def handle_insights(db: Session, current_user: User, parsed: dict):
    breakdown = analytics_service.get_category_breakdown(db, current_user.id)
    if not breakdown: return {"message": "Not enough data for insights. Add some expenses first."}
    
    summary = "\n".join(f"- {category}: {amount:.2f}" for category, amount in breakdown)
    insight = ai_insight_service.generate_insight_from_summary(summary)
    return {"insight": insight}

def handle_monthly_summary(db: Session, current_user: User, parsed: dict):
    return analytics_service.get_monthly_summary(db, current_user.id)

def handle_daily_spending(db: Session, current_user: User, parsed: dict):
    return analytics_service.get_daily_spending(db, current_user.id)

def handle_top_category(db: Session, current_user: User, parsed: dict):
    return analytics_service.get_top_spending_category(db, current_user.id)

def handle_spending_trend(db: Session, current_user: User, parsed: dict):
    return analytics_service.get_spending_trend(db, current_user.id)
