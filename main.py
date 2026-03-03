from fastapi import FastAPI
from db.database import engine
from db.base import Base
from api import auth, expenses
from models import user, expense, budget

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router)
app.include_router(expenses.router)