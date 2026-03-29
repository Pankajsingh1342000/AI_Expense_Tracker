import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from api.deps import get_db, check_rate_limit
from db.base import Base
from api.v1 import expense_routes
from services.handlers import analytics_handlers

# --- Test Database Setup ---
# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Pytest Fixtures ---

@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    """
    Fixture to create and tear down the in-memory database for the test session.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """
    Fixture to provide a database session for a single test function.
    Rolls back any changes after the test.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    """
    Fixture to get a TestClient that uses the test database session.
    """
    def override_get_db():
        yield db_session

    def override_check_rate_limit():
        return True

    # Mock the AI parser to return structured data based on simple keywords for tests.
    async def mock_parse_user_command(query: str):
        query = query.lower()
        if "show my expenses" in query or "list expenses" in query:
            return {"action": "list"}
        if "show food expenses" in query:
            return {"action": "filter", "category": "food"}
        if "show expenses above 100" in query:
            return {"action": "filter", "min_amount": 100}
        if "top spending category" in query:
            return {"action": "top_category"}
        if "today spending" in query:
            return {"action": "daily_spending"}
        if "monthly summary" in query:
            return {"action": "monthly_summary"}
        if "give me insights" in query or "insights" in query:
            return {"action": "insights"}
        if "total" in query:
            return {"action": "total"}
        if "food" in query and "how much" in query:
            return {"action": "category", "category": "food"}
        if "what is my beverages budget" in query:
            return {"action": "budget_status", "category": "beverages"}
        if "what is my entertainment budget" in query:
            return {"action": "budget_status", "category": "entertainment"}
        if "any budget warning" in query or "near my budget" in query:
            return {"action": "budget_warning"}
        if "show all budgets" in query:
            return {"action": "budget_overview"}
        if "set beverages budget to 100" in query:
            return {"action": "set_budget", "category": "beverages", "amount": 100.0}
        if "set food budget 200" in query:
            return {"action": "set_budget", "category": "food", "amount": 200.0}
        if "set transport budget 300" in query:
            return {"action": "set_budget", "category": "transport", "amount": 300.0}
        if "set entertainment budget to 500" in query:
            return {"action": "set_budget", "category": "entertainment", "amount": 500.0}
        if "delete entertainment budget" in query:
            return {"action": "delete_budget", "category": "entertainment"}
        if "movie ticket 150" in query:
            return {"action": "add", "title": "movie ticket", "amount": 150.0, "category": "entertainment"}
        if "update movie ticket" in query:
            return {"action": "update", "title": "movie ticket", "amount": 160.75, "category": "entertainment"}
        if "delete expense id" in query:
            import re
            match = re.search(r"id (\d+)", query)
            return {"action": "delete", "id": int(match.group(1)) if match else None}
        if "delete lunch" in query:
            return {"action": "delete", "title": "lunch"}
        if "another lunch" in query:
            return {"action": "add", "title": "another lunch", "amount": 120.0, "category": "food"}
        if "lunch for 100" in query:
            return {"action": "add", "title": "lunch", "amount": 100.0, "category": "food"}
        if "snacks" in query:
            return {"action": "add", "title": "snacks", "amount": 50.0, "category": "food"}
        if "train" in query:
            return {"action": "add", "title": "train ticket", "amount": 200.0, "category": "transport"}
        if "dinner" in query:
            return {"action": "add", "title": "dinner", "amount": 150.0, "category": "food"}
        if "groceries for 70" in query:
            return {"action": "add", "title": "groceries", "amount": 70.0, "category": "food"}
        if "uber" in query:
            return {"action": "add", "title": "uber", "amount": 80.0, "category": "transport"}
        if "coffee" in query:
            if "10" in query:
                return {"action": "add", "title": "coffee", "amount": 10.0, "category": "beverages"}
            return {"action": "add", "title": "coffee", "amount": 50.0, "category": "beverages"}
        if "pizza" in query:
            if "25.50" in query:
                amount = 25.50
            elif "150" in query:
                amount = 150.0
            elif "120" in query:
                amount = 120.0
            else:
                amount = 100.0
            return {"action": "add", "title": "pizza", "amount": amount, "category": "food"}
        
        return {"action": "unknown"}

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[check_rate_limit] = override_check_rate_limit

    original_parse = expense_routes.parse_user_command
    original_generate_insight = analytics_handlers.ai_insight_service.generate_insight_from_summary

    expense_routes.parse_user_command = mock_parse_user_command
    analytics_handlers.ai_insight_service.generate_insight_from_summary = (
        lambda _summary: "Spending is concentrated in a few categories. Review recurring costs."
    )
    
    yield TestClient(app)
    
    expense_routes.parse_user_command = original_parse
    analytics_handlers.ai_insight_service.generate_insight_from_summary = original_generate_insight
    del app.dependency_overrides[get_db]
    del app.dependency_overrides[check_rate_limit]

@pytest.fixture(scope="function")
def auth_token(client):
    """
    Fixture to create a test user and return an authorization token.
    """
    # 1. Register a test user
    client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )

    # 2. Login to get the token
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
    )
    token_data = login_response.json()
    token = token_data["access_token"]
    
    # 3. Return the full authorization header
    return f"Bearer {token}"
