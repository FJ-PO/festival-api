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


settings = Settings()
