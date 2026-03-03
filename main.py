# from fastapi import FastAPI
# from api.routes import router as api_router
# from db.database import init_db

# app = FastAPI(title="AI Expense Tracker")

# init_db()

# app.include_router(api_router, prefix="/api")

# @app.get("/")
# def root():
#     return {"message": "AI Expense Tracker API is running"}

from fastapi import FastAPI
from db.database import engine
from db.base import Base
from api import auth, expenses

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router)
app.include_router(expenses.router)