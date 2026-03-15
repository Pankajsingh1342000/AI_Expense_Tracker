from pydantic import BaseModel
from typing import Optional

class BudgetBase(BaseModel):
    category: str
    monthly_limit: float

class BudgetCreate(BudgetBase):
    pass

class BudgetUpdate(BaseModel):
    monthly_limit: float

class BudgetResponse(BudgetBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class BudgetStatus(BaseModel):
    category: str
    budget: float
    spent: float
    remaining: float

class BudgetWarning(BudgetStatus):
    usage_percent: float