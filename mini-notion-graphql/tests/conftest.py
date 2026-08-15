import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base
from app import main as main_module
from app.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def _fresh_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def _patch_session(monkeypatch):
    # Point the app's session factory at our in-memory SQLite engine for the test run.
    monkeypatch.setattr(main_module, "SessionLocal", TestingSessionLocal)
    yield


@pytest.fixture
def client():
    return TestClient(app)


def gql(client, query, variables=None, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = client.post("/graphql", json={"query": query, "variables": variables or {}}, headers=headers)
    return resp.json()


@pytest.fixture
def register_user(client):
    def _register(email="user@example.com", name="Test User", password="password123"):
        result = gql(
            client,
            """
            mutation Register($email: String!, $name: String!, $password: String!) {
              register(email: $email, name: $name, password: $password) {
                token
                user { id email name }
              }
            }
            """,
            {"email": email, "name": name, "password": password},
        )
        return result["data"]["register"]

    return _register
