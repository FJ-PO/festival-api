"""Cliente mínimo del OAuth2 de GitHub (Authorization Code).

Aislado del router para poder sustituirlo en los tests sin salir a la red. El `client_secret`
solo se usa aquí, en el servidor: nunca se expone al navegador.
"""

from dataclasses import dataclass

import httpx
from fastapi import HTTPException, status

from app.core.config import settings


@dataclass
class GithubProfile:
    github_id: int
    email: str
    full_name: str


def build_authorize_url(redirect_uri: str, state: str) -> str:
    """URL de GitHub a la que se envía al usuario para que autorice la aplicación."""
    params = httpx.QueryParams(
        {
            "client_id": settings.github_client_id,
            "redirect_uri": redirect_uri,
            "scope": "read:user user:email",
            "state": state,
            "allow_signup": "true",
        }
    )
    return f"{settings.github_authorize_url}?{params}"


def _exchange_code(code: str, redirect_uri: str) -> str:
    """Canjea el `code` por un token de acceso de GitHub (usa el client_secret)."""
    resp = httpx.post(
        settings.github_token_url,
        headers={"Accept": "application/json"},
        data={
            "client_id": settings.github_client_id,
            "client_secret": settings.github_client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        },
        timeout=10,
    )
    data = resp.json() if resp.is_success else {}
    token = data.get("access_token")
    if not token:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "GitHub rechazó el código de autorización")
    return token


def _get(client: httpx.Client, path: str):
    resp = client.get(f"{settings.github_api_url}{path}", timeout=10)
    if not resp.is_success:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "No se pudo obtener el perfil de GitHub")
    return resp.json()


def fetch_profile(code: str, redirect_uri: str) -> GithubProfile:
    """Canjea el código y devuelve el perfil (id, email verificado y nombre) del usuario de GitHub."""
    token = _exchange_code(code, redirect_uri)
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    with httpx.Client(headers=headers) as client:
        user = _get(client, "/user")
        email = user.get("email")
        if not email:
            # El email puede ser privado: se busca el primario verificado entre los del usuario.
            emails = _get(client, "/user/emails")
            email = next(
                (e["email"] for e in emails if e.get("primary") and e.get("verified")),
                next((e["email"] for e in emails if e.get("verified")), None),
            )

    github_id = user.get("id")
    if github_id is None or not email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Tu cuenta de GitHub no tiene un email verificado")
    return GithubProfile(
        github_id=int(github_id),
        email=str(email).lower(),
        full_name=user.get("name") or user.get("login") or "Usuario de GitHub",
    )
