from models.user import User
from sqlalchemy.orm import Session

from services import ai_insight_service, analytics_service, budget_service
from services.query_cache import make_cache_key, read_cache


def handle_category_total(db: Session, current_user: User, parsed: dict):
    cache_key = make_cache_key(current_user.id, "category", parsed)

    def build_response():
        category = parsed.get("category")
        if category:
            total = budget_service.get_monthly_spent_for_category(db, current_user.id, category)
            return {"category": category, "total_spent": total}

        breakdown = analytics_service.get_category_breakdown(db, current_user.id)
        return [{"category": c, "total": a} for c, a in breakdown]

    return read_cache.get_or_set(cache_key, build_response)


def handle_insights(db: Session, current_user: User, parsed: dict):
    cache_key = make_cache_key(current_user.id, "insights", parsed)

    def build_response():
        breakdown = analytics_service.get_category_breakdown(db, current_user.id)
        if not breakdown:
            return {"message": "Not enough data for insights. Add some expenses first."}

        summary = "\n".join(f"- {category}: {amount:.2f}" for category, amount in breakdown)
        insight = ai_insight_service.generate_insight_from_summary(summary)
        return {"insight": insight}

    return read_cache.get_or_set(cache_key, build_response)


def handle_monthly_summary(db: Session, current_user: User, parsed: dict):
    cache_key = make_cache_key(current_user.id, "monthly_summary", parsed)
    return read_cache.get_or_set(cache_key, lambda: analytics_service.get_monthly_summary(db, current_user.id))


def handle_daily_spending(db: Session, current_user: User, parsed: dict):
    cache_key = make_cache_key(current_user.id, "daily_spending", parsed)
    return read_cache.get_or_set(cache_key, lambda: analytics_service.get_daily_spending(db, current_user.id))


def handle_top_category(db: Session, current_user: User, parsed: dict):
    cache_key = make_cache_key(current_user.id, "top_category", parsed)
    return read_cache.get_or_set(cache_key, lambda: analytics_service.get_top_spending_category(db, current_user.id))


def handle_spending_trend(db: Session, current_user: User, parsed: dict):
    cache_key = make_cache_key(current_user.id, "spending_trend", parsed)
    return read_cache.get_or_set(cache_key, lambda: analytics_service.get_spending_trend(db, current_user.id))
