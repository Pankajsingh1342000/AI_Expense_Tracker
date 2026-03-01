import datetime

from sqlalchemy import Column, DateTime, Integer, String, Float
from db.database import Base

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.timezone.utc)