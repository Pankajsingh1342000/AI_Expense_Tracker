from fastapi import FastAPI
from db.database import init_db
from api.routes import router as expense_router

app = FastAPI()
init_db()

app.include_router(expense_router, prefix="/expense")