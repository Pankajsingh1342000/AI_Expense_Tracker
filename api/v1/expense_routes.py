import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ai.context import build_financial_context, invalidate_context_cache
from ai.parse import (
    AIProcessingError,
    _rule_based_parse,
    generate_reply,
    parse_user_command,
)
from api.deps import check_rate_limit, get_current_user, get_db
from models.user import User
from schemas.ai import AIQuery
from services.action_handlers import ACTION_HANDLERS
from services.conversation_memory import conversation_memory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/expenses")

# Actions that modify data — context cache must be invalidated after these
_WRITE_ACTIONS = {"add", "update", "delete", "set_budget", "update_budget", "delete_budget"}

# Actions where the parse-time reply is always accurate (read-only, no side-effects)
# For these we skip the 2nd AI call entirely.
_REPLY_FROM_PARSE = {
    "chat", "list", "total", "filter", "category",
    "monthly_summary", "daily_spending", "top_category",
    "spending_trend", "insights", "budget_overview",
    "budget_status", "budget_warning",
}


@router.post("/agent")
async def agentic_expense_handler(
    user_input: AIQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: bool = Depends(check_rate_limit),
):
    """
    Natural language expense assistant — understands intent, executes actions,
    and responds conversationally with full memory of the conversation.

    Optimisation tiers (least → most expensive):
      Tier 0: Rule-based parse    → 0 AI calls
      Tier 1: Parse reply reuse   → 1 AI call  (read-only + clean writes)
      Tier 2: generate_reply call → 2 AI calls (duplicates / errors only)
    """
    user_id = current_user.id

    # ── Tier 0: try rule-based parse first (free) ────────────────────────────
    parsed_command = _rule_based_parse(user_input.query)
    used_rule_based = parsed_command is not None

    if not used_rule_based:
        # ── Tier 1/2: fall through to AI ────────────────────────────────────
        financial_context = build_financial_context(db, user_id)
        history = conversation_memory.get(user_id)

        try:
            parsed_command = await parse_user_command(
                user_input.query,
                financial_context=financial_context,
                history=history,
            )
        except AIProcessingError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
    else:
        financial_context = ""  # not needed for rule-based path
        history = None

    action = parsed_command.get("action")
    parse_reply = parsed_command.get("reply")  # may be None for rule-based

    # ── Pure chat — use parse reply, no handler needed ───────────────────────
    if action == "chat":
        ai_reply = parse_reply or "I'm here to help with your finances!"
        _save_turn(user_id, user_input.query, ai_reply, parsed_command)
        return {"reply": ai_reply}

    # ── Dispatch to handler ──────────────────────────────────────────────────
    handler = ACTION_HANDLERS.get(action)
    if not handler:
        if parse_reply:
            _save_turn(user_id, user_input.query, parse_reply, parsed_command)
            return {"reply": parse_reply}
        raise HTTPException(status_code=400, detail=f"Unknown action: '{action}'")

    try:
        result = handler(db=db, current_user=current_user, parsed=parsed_command)

        # Serialize
        if hasattr(result, "model_dump"):
            result_dict = result.model_dump(mode="json")
        elif isinstance(result, list):
            result_dict = {
                "items": [r.model_dump(mode="json") if hasattr(r, "model_dump") else r for r in result]
            }
        elif isinstance(result, dict):
            result_dict = result
        else:
            result_dict = {"result": str(result)}

        is_clarification = result_dict.get("status") == "clarification_needed"
        has_error = "error" in result_dict

        # ── Decide which reply tier to use ───────────────────────────────────
        if not used_rule_based and not is_clarification and not has_error:
            # Tier 1: AI already generated an accurate reply during parse —
            # reuse it, no second call needed.
            ai_reply = parse_reply or _default_reply(action)
        else:
            # Tier 2: we need a post-result reply because either:
            #   a) rule-based parse was used (no AI reply was generated)
            #   b) result was clarification_needed (parse reply would be wrong)
            #   c) handler returned an error
            if not financial_context:
                financial_context = build_financial_context(db, user_id)
            if history is None:
                history = conversation_memory.get(user_id)
            ai_reply = await generate_reply(user_input.query, result_dict, financial_context, history)

        # ── Invalidate context cache after writes ─────────────────────────────
        if action in _WRITE_ACTIONS and not is_clarification and not has_error:
            invalidate_context_cache(user_id)

        # ── Save to conversation memory ───────────────────────────────────────
        _save_turn(user_id, user_input.query, ai_reply, result_dict)

        if isinstance(result, dict):
            return {**result_dict, "reply": ai_reply}
        return {"data": result_dict, "reply": ai_reply}

    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unhandled error while processing action '%s'", action)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing your request.",
        ) from exc


def _default_reply(action: str) -> str:
    """Fallback reply for rule-based-parsed commands that have no AI reply."""
    return {
        "add": "Expense added successfully.",
        "update": "Expense updated.",
        "delete": "Expense deleted.",
        "list": "Here are your expenses.",
        "total": "Here is your total.",
        "set_budget": "Budget set.",
        "update_budget": "Budget updated.",
        "delete_budget": "Budget deleted.",
    }.get(action, "Done!")


def _save_turn(user_id: int, user_message: str, ai_reply: str, result: dict) -> None:
    """Save a user+assistant turn to conversation memory."""
    conversation_memory.add(user_id, "user", user_message)
    assistant_content = ai_reply
    if result.get("status") == "clarification_needed":
        options_summary = json.dumps(result.get("options", []), default=str)
        assistant_content = (
            f"{ai_reply}\n[System: clarification pending, options: {options_summary}]"
        )
    conversation_memory.add(user_id, "assistant", assistant_content)
