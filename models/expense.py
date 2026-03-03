from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from db.base import Base

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    amount = Column(Float)
    category = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))