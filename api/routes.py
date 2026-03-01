from fastapi import APIRouter
from agent.expense_agent import handle_user_command
from api.schemas import AskRequest

router = APIRouter()

@router.post("/ask")
def ask_expense(request: AskRequest):
    result = handle_user_command(request.command)
    return {"result": result}