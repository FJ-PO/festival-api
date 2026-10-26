from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Festival Tickets API"
    api_prefix: str = "/api/v1"

    secret_key: str = "change-me-in-production-please-use-env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    database_url: str = "sqlite:///./festival.db"

    # Minutos que un pedido pendiente mantiene reservadas las entradas
    order_expiration_minutes: int = 15

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"]

    # Administrador que se crea al arrancar si no existe
    admin_username: str = "admin"
    admin_password: str = "admin123"
    admin_email: str = "admin@laspalomasfestival.es"

    # Carpeta donde se guardan los archivos subidos desde el panel (biblioteca de medios)
    upload_dir: str = "uploads"

    # Inicio de sesión con GitHub (OAuth2). Vacío = desactivado (no se muestra el botón).
    # El client_id es público; el client_secret NUNCA sale del backend.
    github_client_id: str = ""
    github_client_secret: str = ""
    github_authorize_url: str = "https://github.com/login/oauth/authorize"
    github_token_url: str = "https://github.com/login/oauth/access_token"
    github_api_url: str = "https://api.github.com"

    @property
    def github_enabled(self) -> bool:
        return bool(self.github_client_id and self.github_client_secret)


settings = Settings()
