from services.handlers import expense_handlers, budget_handlers, analytics_handlers

# The Dispatcher Dictionary
ACTION_HANDLERS = {
    "add": expense_handlers.handle_add,
    "list": expense_handlers.handle_list,
    "update": expense_handlers.handle_update,
    "delete": expense_handlers.handle_delete,
    "filter": expense_handlers.handle_filter,
    "total": expense_handlers.handle_total,
    "category": analytics_handlers.handle_category_total,
    "set_budget": budget_handlers.handle_set_budget,
    "update_budget": budget_handlers.handle_set_budget, # Same as set_budget
    "delete_budget": budget_handlers.handle_delete_budget,
    "budget_status": budget_handlers.handle_budget_status,
    "budget_overview": budget_handlers.handle_budget_overview,
    "budget_warning": budget_handlers.handle_budget_warning,
    "insights": analytics_handlers.handle_insights,
    "monthly_summary": analytics_handlers.handle_monthly_summary,
    "daily_spending": analytics_handlers.handle_daily_spending,
    "top_category": analytics_handlers.handle_top_category,
    "spending_trend": analytics_handlers.handle_spending_trend,
}