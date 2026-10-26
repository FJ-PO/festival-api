import pytest
from sqlalchemy import select

from app.core.config import settings
from app.core.security import decode_access_token
from app.models import User, UserRole
from app.services.github import GithubProfile


@pytest.fixture(autouse=True)
def github_off(monkeypatch):
    """Parte siempre sin credenciales, para no depender de las que haya en el `.env` local."""
    monkeypatch.setattr(settings, "github_client_id", "")
    monkeypatch.setattr(settings, "github_client_secret", "")


@pytest.fixture()
def github_enabled(monkeypatch):
    """Activa el login con GitHub con credenciales de prueba (no se llega a usar la red real)."""
    monkeypatch.setattr(settings, "github_client_id", "test-client-id")
    monkeypatch.setattr(settings, "github_client_secret", "test-client-secret")


@pytest.fixture()
def fake_github(monkeypatch):
    """Sustituye la llamada a GitHub por un perfil fijo, para no salir a la red en los tests."""
    def _use(github_id: int, email: str, full_name: str = "Octo Cat"):
        def fake_fetch_profile(code, redirect_uri):
            return GithubProfile(github_id=github_id, email=email.lower(), full_name=full_name)

        monkeypatch.setattr("app.services.github.fetch_profile", fake_fetch_profile)

    return _use


def test_providers_reports_github_state(client, github_enabled):
    assert client.get("/api/v1/auth/providers").json() == {"github": True}


def test_providers_github_off_by_default(client):
    assert client.get("/api/v1/auth/providers").json() == {"github": False}


def test_authorize_url_includes_client_id_and_state(client, github_enabled):
    r = client.get(
        "/api/v1/auth/github/authorize",
        params={"redirect_uri": "http://localhost:5173/oauth/github/callback", "state": "un-estado-aleatorio"},
    )
    assert r.status_code == 200, r.text
    url = r.json()["url"]
    assert url.startswith("https://github.com/login/oauth/authorize?")
    assert "client_id=test-client-id" in url
    assert "state=un-estado-aleatorio" in url


def test_authorize_404_when_disabled(client):
    r = client.get(
        "/api/v1/auth/github/authorize",
        params={"redirect_uri": "http://localhost:5173/oauth/github/callback", "state": "un-estado-aleatorio"},
    )
    assert r.status_code == 404


def test_github_login_creates_new_customer(client, db, github_enabled, fake_github):
    fake_github(github_id=4242, email="nuevo@github.com", full_name="Nuevo Usuario")
    r = client.post(
        "/api/v1/auth/github",
        json={"code": "abc", "redirect_uri": "http://localhost:5173/oauth/github/callback"},
    )
    assert r.status_code == 200, r.text
    assert "set-cookie" not in r.headers
    body = r.json()
    assert body["user"]["email"] == "nuevo@github.com"
    assert body["user"]["role"] == "customer"
    assert decode_access_token(body["access_token"])["role"] == "customer"
    user = db.scalar(select(User).where(User.github_id == 4242))
    assert user is not None and user.hashed_password == ""


def test_github_login_links_existing_email_account(client, db, make_user, github_enabled, fake_github):
    existing = make_user(UserRole.CUSTOMER, email="cliente@github.com")
    fake_github(github_id=777, email="cliente@github.com")
    r = client.post(
        "/api/v1/auth/github",
        json={"code": "abc", "redirect_uri": "http://localhost:5173/oauth/github/callback"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["user"]["id"] == existing.id
    db.refresh(existing)
    assert existing.github_id == 777


def test_github_login_reuses_linked_account(client, github_enabled, fake_github):
    fake_github(github_id=999, email="repite@github.com")
    first = client.post(
        "/api/v1/auth/github",
        json={"code": "abc", "redirect_uri": "http://localhost:5173/oauth/github/callback"},
    )
    second = client.post(
        "/api/v1/auth/github",
        json={"code": "def", "redirect_uri": "http://localhost:5173/oauth/github/callback"},
    )
    assert first.json()["user"]["id"] == second.json()["user"]["id"]


def test_github_account_cannot_login_with_password(client, github_enabled, fake_github):
    fake_github(github_id=111, email="solo-github@github.com")
    client.post(
        "/api/v1/auth/github",
        json={"code": "abc", "redirect_uri": "http://localhost:5173/oauth/github/callback"},
    )
    # Sin contraseña local: el login por formulario debe fallar
    r = client.post("/api/v1/auth/login", data={"username": "solo-github@github.com", "password": "loquesea"})
    assert r.status_code == 401
