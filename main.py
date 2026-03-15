from fastapi import FastAPI
from db.database import engine
from db.base import Base
from api.v1 import auth_routes, expense_routes
from models import user, expense, budget

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Expense Tracker API",
    description="An agentic API for managing personal finances.",
    version="1.0.0"
)

app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(expense_routes.router, prefix="/api/v1", tags=["AI Agent"])

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the AI Expense Tracker API"}