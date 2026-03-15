import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from api.deps import get_db
from db.base import Base

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

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    del app.dependency_overrides[get_db]

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