from fastapi import FastAPI
from api.routes import router
from db.database import engine
from db.models import Base

app = FastAPI()

Base.metadata.create_all(bind = engine)
app.include_router(router)


@app.get("/")
def home():
    return {"message": "Expense AI Agent Running"}