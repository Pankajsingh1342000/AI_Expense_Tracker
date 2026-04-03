from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from models.user import User
from services import ai_insight_service, analytics_service, budget_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/category-breakdown")
def get_category_breakdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    breakdown = analytics_service.get_category_breakdown(db, current_user.id)
    return [{"category": category, "total": amount} for category, amount in breakdown]


@router.get("/category-total/{category}")
def get_category_total(
    category: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total = budget_service.get_monthly_spent_for_category(db, current_user.id, category)
    return {"category": category, "total_spent": total}


@router.get("/monthly-summary")
def get_monthly_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return analytics_service.get_monthly_summary(db, current_user.id)


@router.get("/daily-spending")
def get_daily_spending(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return analytics_service.get_daily_spending(db, current_user.id)


@router.get("/top-category")
def get_top_category(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return analytics_service.get_top_spending_category(db, current_user.id)


@router.get("/spending-trend")
def get_spending_trend(
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return analytics_service.get_spending_trend(db, current_user.id, days=days)


@router.get("/insights")
def get_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    breakdown = analytics_service.get_category_breakdown(db, current_user.id)
    if not breakdown:
        return {"message": "Not enough data for insights. Add some expenses first."}
    summary = "\n".join(f"- {category}: {amount:.2f}" for category, amount in breakdown)
    return {"insight": ai_insight_service.generate_insight_from_summary(summary)}
