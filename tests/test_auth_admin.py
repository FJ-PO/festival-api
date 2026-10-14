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
