from pydantic import BaseModel
from datetime import datetime

class ExpenseCreate(BaseModel):
    title: str
    amount: float
    category: str

class ExpenseResponse(BaseModel):
    id: int
    title: str
    amount: float
    category: str
    created_at: datetime

    class Config:
        from_attributes = True