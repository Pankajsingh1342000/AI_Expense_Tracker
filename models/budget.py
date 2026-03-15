from sqlalchemy import Column, Integer, Float, String, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from db.base import Base

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    category = Column(String, nullable=False)
    monthly_limit = Column(Numeric(10, 2), nullable=False)

    user = relationship("User", back_populates="budgets")