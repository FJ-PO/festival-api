from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from app.core.security import decode_access_token
from app.models import UserRole


def test_bootstrap_admin_can_login_with_username(client):
    r = client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin123"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    assert body["user"]["username"] == "admin"
    assert body["user"]["role"] == "admin"
    assert decode_access_token(body["access_token"])["role"] == "admin"


def test_login_does_not_set_cookies(client):
    r = client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin123"})
    assert "set-cookie" not in r.headers
    assert not r.cookies


def test_wrong_password_rejected(client):
    r = client.post("/api/v1/auth/login", data={"username": "admin", "password": "otra-cosa"})
    assert r.status_code == 401


def test_requests_without_token_are_rejected(client):
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer no-es-un-jwt"}).status_code == 401


def test_refresh_returns_new_token_with_current_role(client, db, make_user, login):
    user = make_user(UserRole.CUSTOMER)
    headers = login(user.email)
    user.role = UserRole.ORGANIZER
    db.commit()
    r = client.post("/api/v1/auth/refresh", headers=headers)
    assert r.status_code == 200, r.text
    assert "set-cookie" not in r.headers
    body = r.json()
    assert body["expires_in"] > 0
    assert body["user"]["role"] == "organizer"
    assert decode_access_token(body["access_token"])["role"] == "organizer"
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.json()["email"] == user.email


def test_refresh_rejects_expired_or_missing_token(client, make_user):
    user = make_user(UserRole.CUSTOMER)
    past = datetime.now(timezone.utc) - timedelta(minutes=5)
    expired = jwt.encode(
        {"sub": str(user.id), "role": "customer", "iat": past - timedelta(hours=1), "exp": past},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    assert client.post("/api/v1/auth/refresh", headers={"Authorization": f"Bearer {expired}"}).status_code == 401
    assert client.post("/api/v1/auth/refresh").status_code == 401


def test_refresh_rejects_deactivated_user(client, db, make_user, login):
    user = make_user(UserRole.CUSTOMER)
    headers = login(user.email)
    user.is_active = False
    db.commit()
    assert client.post("/api/v1/auth/refresh", headers=headers).status_code == 401


def test_admin_creates_staff_user(client, make_user, login):
    make_user(UserRole.CUSTOMER)
    r = client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin123"})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    r = client.post(
        "/api/v1/users",
        json={"email": "puerta@example.com", "full_name": "Puerta Norte", "password": "Password123",
              "username": "puerta1", "role": "staff"},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    assert client.post("/api/v1/auth/login", data={"username": "puerta1", "password": "Password123"}).status_code == 200
    # Un cliente no puede crear usuarios
    r = client.post("/api/v1/users", json={"email": "x@example.com", "full_name": "X", "password": "Password123"},
                    headers=login("customer@example.com"))
    assert r.status_code == 403
