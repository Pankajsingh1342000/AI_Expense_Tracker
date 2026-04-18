from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional

class AIQuery(BaseModel):
    query: str

class AIResponse(BaseModel):
    action: str
    reply: Optional[str] = None
    id: Optional[int] = None
    title: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None

    @field_validator('amount')
    @classmethod
    def amount_must_be_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError('Amount must be positive')
        return v

    @field_validator('title')
    @classmethod
    def title_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            return None # Or handle as error
        return v.strip() if v else v

    model_config = ConfigDict(
        from_attributes=True
    )