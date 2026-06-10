import os
from pathlib import Path
from dotenv import load_dotenv

# Explicitly load .env from repo root, not current working directory
repo_root = Path(__file__).parent.parent
load_dotenv(repo_root / ".env")


class Settings:
    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_NAME: str = os.getenv("DB_NAME", "nfl_fantasy")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "postgres")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))

    @property
    def db_dsn(self) -> str:
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15")
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(
        os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30")
    )

    # OAuth state signing (itsdangerous)
    STATE_SECRET_KEY: str = os.getenv("STATE_SECRET_KEY", "")
    STATE_MAX_AGE_SECONDS: int = 600  # 10 minutes

    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:8001/auth/callback?provider=google"
    )

    # Microsoft (Azure AD) OAuth
    AZURE_CLIENT_ID: str = os.getenv("AZURE_CLIENT_ID", "")
    AZURE_CLIENT_SECRET: str = os.getenv("AZURE_CLIENT_SECRET", "")
    AZURE_TENANT_ID: str = os.getenv("AZURE_TENANT_ID", "common")
    AZURE_REDIRECT_URI: str = os.getenv(
        "AZURE_REDIRECT_URI",
        "http://localhost:8001/auth/callback?provider=microsoft",
    )

    # Frontend URL (used for OAuth redirect)
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # CORS — comma-separated list of allowed origins
    CORS_ORIGINS: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173"
    ).split(",")


settings = Settings()
