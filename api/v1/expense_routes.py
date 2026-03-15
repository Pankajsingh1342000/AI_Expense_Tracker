from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ai.parse import parse_user_command
from api.deps import get_db, get_current_user # You might need to create api/deps.py if it's not global
from schemas.ai import AIQuery
from models.user import User
from services.action_handlers import ACTION_HANDLERS

router = APIRouter(prefix="/expenses")

@router.post("/agent")
def agentic_expense_handler(
    user_input: AIQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fully agentic endpoint. The AI parses natural language and this dispatcher
    routes the command to the appropriate handler.
    """
    parsed_command = parse_user_command(user_input.query)
    action = parsed_command.get("action")

    handler = ACTION_HANDLERS.get(action)

    if not handler:
        raise HTTPException(status_code=400, detail=f"Unknown or unsupported action: '{action}'")

    try:
        result = handler(db=db, current_user=current_user, parsed=parsed_command)
        return result
    except Exception as e:
        # Log the real error for debugging
        print(f"ERROR handling action '{action}': {e}")
        # Return a generic error to the user
        raise HTTPException(status_code=500, detail="An internal error occurred while processing your request.")