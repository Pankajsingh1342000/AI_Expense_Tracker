import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ai.parse import AIProcessingError, parse_user_command
from api.deps import check_rate_limit, get_current_user, get_db
from models.user import User
from schemas.ai import AIQuery
from services.action_handlers import ACTION_HANDLERS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/expenses")


@router.post("/agent")
async def agentic_expense_handler(
    user_input: AIQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _rate_limit: bool = Depends(check_rate_limit),
):
    """
    Parse a natural language expense command and dispatch it to the matching domain handler.
    """
    try:
        parsed_command = await parse_user_command(user_input.query)
    except AIProcessingError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    action = parsed_command.get("action")
    handler = ACTION_HANDLERS.get(action)

    if not handler:
        raise HTTPException(status_code=400, detail=f"Unknown or unsupported action: '{action}'")

    try:
        return handler(db=db, current_user=current_user, parsed=parsed_command)
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
