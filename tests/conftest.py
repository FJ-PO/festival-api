import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.security import hash_password
from app.db.session import Base, get_db
from app.main import app
from app.models import User, UserRole

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def make_user(db):
    def _make(role: UserRole, email: str | None = None) -> User:
        user = User(
            email=email or f"{role.value}@example.com",
            full_name=f"Usuario {role.value}",
            role=role,
            hashed_password=hash_password("Password123"),
        )
        db.add(user)
        db.commit()
        return user

    return _make


@pytest.fixture()
def login(client):
    def _login(email: str) -> dict:
        r = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123"})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    return _login
