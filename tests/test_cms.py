import io

import pytest

from app.models import UserRole

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@pytest.fixture()
def admin_headers(client):
    r = client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_site_settings_defaults_and_update(client, admin_headers, make_user, login):
    r = client.get("/api/v1/site")
    assert r.status_code == 200
    settings = r.json()
    assert settings["site_name"]

    settings.update(hero_title="Nuevo titular", accent_color="#00ccaa")
    settings["social"]["instagram"] = "https://instagram.com/festivales"
    settings.pop("updated_at")
    r = client.put("/api/v1/site", json=settings, headers=admin_headers)
    assert r.status_code == 200, r.text
    assert client.get("/api/v1/site").json()["hero_title"] == "Nuevo titular"

    make_user(UserRole.CUSTOMER)
    assert client.put("/api/v1/site", json=settings, headers=login("customer@example.com")).status_code == 403
    assert client.put("/api/v1/site", json=settings).status_code == 401


def test_page_lifecycle(client, admin_headers):
    r = client.post(
        "/api/v1/pages",
        json={"title": "Preguntas frecuentes", "content": "## ¿Puedo entrar con comida?\nNo.", "show_in_menu": True},
        headers=admin_headers,
    )
    assert r.status_code == 201, r.text
    page = r.json()
    assert page["slug"] == "preguntas-frecuentes"
    assert page["status"] == "draft"

    # Un borrador no es público, pero el admin puede previsualizarlo
    assert client.get("/api/v1/pages/slug/preguntas-frecuentes").status_code == 404
    assert client.get("/api/v1/pages/slug/preguntas-frecuentes", headers=admin_headers).status_code == 200
    assert client.get("/api/v1/pages?menu=true").json()["total"] == 0

    r = client.patch(f"/api/v1/pages/{page['id']}", json={"status": "published"}, headers=admin_headers)
    assert r.json()["published_at"] is not None
    assert client.get("/api/v1/pages/slug/preguntas-frecuentes").status_code == 200
    assert client.get("/api/v1/pages?menu=true").json()["total"] == 1

    # Slug duplicado -> se numera
    r = client.post("/api/v1/pages", json={"title": "Preguntas frecuentes"}, headers=admin_headers)
    assert r.json()["slug"] == "preguntas-frecuentes-2"

    assert client.delete(f"/api/v1/pages/{page['id']}", headers=admin_headers).status_code == 204
    assert client.get("/api/v1/pages/manage", headers=admin_headers).json()["total"] == 1


def test_posts_public_list(client, admin_headers):
    client.post("/api/v1/posts", json={"title": "Primeros nombres", "status": "published"}, headers=admin_headers)
    client.post("/api/v1/posts", json={"title": "Borrador interno"}, headers=admin_headers)
    titles = [p["title"] for p in client.get("/api/v1/posts").json()["items"]]
    assert titles == ["Primeros nombres"]


def test_media_upload_validates_content(client, admin_headers, tmp_path):
    r = client.post("/api/v1/media", files={"file": ("cartel.png", io.BytesIO(PNG), "image/png")},
                    data={"alt": "Cartel"}, headers=admin_headers)
    assert r.status_code == 201, r.text
    media = r.json()
    assert media["url"].startswith("/uploads/") and media["url"].endswith(".png")
    assert (tmp_path / "uploads" / media["filename"]).exists()

    # Un HTML disfrazado de imagen se rechaza
    fake = io.BytesIO(b"<script>alert(1)</script>")
    r = client.post("/api/v1/media", files={"file": ("x.png", fake, "image/png")}, headers=admin_headers)
    assert r.status_code == 415

    assert client.get("/api/v1/media", headers=admin_headers).json()["total"] == 1
    assert client.delete(f"/api/v1/media/{media['id']}", headers=admin_headers).status_code == 204
    assert not (tmp_path / "uploads" / media["filename"]).exists()


def test_dashboard(client, admin_headers, make_user, login):
    r = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["sales_last_30_days"]) == 30
    assert body["users_by_role"]["admin"] >= 1
    make_user(UserRole.CUSTOMER)
    assert client.get("/api/v1/admin/dashboard", headers=login("customer@example.com")).status_code == 403


def test_newsletter(client, admin_headers):
    r = client.post("/api/v1/newsletter", json={"email": "Fan@Example.com", "name": "Fan"})
    assert r.status_code == 201
    assert client.post("/api/v1/newsletter", json={"email": "fan@example.com"}).status_code == 200
    assert client.post("/api/v1/newsletter", json={"email": "no-es-email"}).status_code == 422
    assert client.get("/api/v1/newsletter").status_code == 401
    subs = client.get("/api/v1/newsletter", headers=admin_headers).json()
    assert subs["total"] == 1 and subs["items"][0]["email"] == "fan@example.com"
