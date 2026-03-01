from fastapi import APIRouter
from api.schemas import QueryRequest
from agent.expense_agent import process_query

router = APIRouter()

@router.post("/ask")
def ask_agent(request: QueryRequest):
    resposne = process_query(request.query)
    return {"response": resposne}