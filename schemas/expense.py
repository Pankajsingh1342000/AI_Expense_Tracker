from pydantic import BaseModel, ConfigDict, field_serializer
from datetime import datetime
from typing import Optional
from decimal import Decimal

class ExpenseBase(BaseModel):
    title: str
    amount: Decimal
    category: str
    description: Optional[str] = None
    date: Optional[datetime] = None

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[Decimal] = None
    category: Optional[str] = None
    description: Optional[str] = None

class ExpenseResponse(ExpenseBase):
    id: int
    date: datetime
    user_id: int

    @field_serializer('amount')
    def serialize_amount(self, value: Decimal) -> str:
        """Custom serializer to convert Decimal amount to a string with two decimal places."""

        return str(value.quantize(Decimal('0.01')))

    model_config = ConfigDict(
        from_attributes=True,
    )