from fastapi import FastAPI
from api.routes import router as api_router
from db.database import init_db

app = FastAPI(title="AI Expense Tracker")

init_db()

app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "AI Expense Tracker API is running"}