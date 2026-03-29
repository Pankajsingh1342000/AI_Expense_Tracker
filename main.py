import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.v1 import auth_routes, expense_routes
from core.config import settings
from db.base import Base
from db.database import engine
from models import budget, expense, user

logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Starting AI Expense Tracker API in %s mode", settings.environment)
    yield


app = FastAPI(
    title="AI Expense Tracker API",
    description="An API for managing personal finances with AI-assisted command parsing.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(expense_routes.router, prefix="/api/v1", tags=["AI Agent"])


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the AI Expense Tracker API"}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "environment": settings.environment}
