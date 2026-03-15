from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class AIQuery(BaseModel):
    query: str

class AIResponse(BaseModel):
    action: str
    id: Optional[int] = None
    title: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    model_config = ConfigDict(
        from_attributes=True
    )