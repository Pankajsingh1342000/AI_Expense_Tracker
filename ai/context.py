import time
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from models.budget import Budget
from models.expense import Expense
from services import analytics_service, budget_service
from sqlalchemy.orm import Session

# Per-user context cache: user_id -> (context_string, built_at_unix_ts)
_context_cache: Dict[int, Tuple[str, float]] = {}
_CACHE_TTL_SECONDS = 30


def invalidate_context_cache(user_id: int) -> None:
    """Call this after any write operation so the next request gets fresh data."""
    _context_cache.pop(user_id, None)


def build_financial_context(db: Session, user_id: int) -> str:
    """
    Build a live financial context string to inject into the AI system prompt.
    Results are cached per-user for 30 seconds to reduce DB load on rapid
    back-to-back messages.
    """
    cached = _context_cache.get(user_id)
    if cached:
        context_str, built_at = cached
        if time.time() - built_at < _CACHE_TTL_SECONDS:
            return context_str

    context_str = _build(db, user_id)
    _context_cache[user_id] = (context_str, time.time())
    return context_str


def _build(db: Session, user_id: int) -> str:
    today = datetime.now()

    # Recent expenses (last 15)
    recent_expenses = (
        db.query(Expense)
        .filter(Expense.user_id == user_id)
        .order_by(Expense.date.desc())
        .limit(15)
        .all()
    )

    # Monthly summary
    monthly = analytics_service.get_monthly_summary(db, user_id)

    # All budgets with usage
    budgets = budget_service.get_all_budgets(db, user_id)
    budget_lines = []
    for b in budgets:
        spent = budget_service.get_monthly_spent_for_category(db, user_id, b.category)
        pct = round((float(spent) / float(b.monthly_limit)) * 100, 1) if b.monthly_limit else 0
        budget_lines.append(
            f"  - {b.category.title()}: Rs. {float(spent):,.0f} spent"
            f" / Rs. {float(b.monthly_limit):,.0f} limit ({pct}% used)"
        )

    # Today's spending
    daily = analytics_service.get_daily_spending(db, user_id)

    lines = [
        f"Today's date: {today.strftime('%d %B %Y')}",
        "",
        "=== USER'S LIVE FINANCIAL DATA ===",
        "",
        f"Today's spending: Rs. {float(daily.get('total_spent', 0)):,.0f}",
        "",
        f"This month's total: Rs. {float(monthly.get('month_total', 0)):,.0f}",
    ]

    if monthly.get("categories"):
        lines.append("This month by category:")
        for cat in monthly["categories"]:
            lines.append(f"  - {cat['category'].title()}: Rs. {float(cat['amount']):,.0f}")

    lines.append("")
    if budget_lines:
        lines.append("Budget status (this month):")
        lines.extend(budget_lines)
    else:
        lines.append("No budgets set yet.")

    lines.append("")
    if recent_expenses:
        lines.append("Recent expenses (latest first):")
        for e in recent_expenses:
            lines.append(
                f"  - [{e.id}] {e.title.title()} | Rs. {float(e.amount):,.0f}"
                f" | {e.category} | {e.date.strftime('%d %b')}"
            )
    else:
        lines.append("No expenses recorded yet.")

    lines.append("=================================")
    return "\n".join(lines)
