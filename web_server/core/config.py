import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "FastAPI Forklift Game Backend Engine."
    SECRET_KEY: str = os.getenv("SECRET_KEY", "kjnsdjknsdjknsjkdnfjknsdfjknsdfjkn")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 1000

    # Environment: "development" | "production" (defaults to "development")
    ENV: str = os.getenv("ENV", os.getenv("ENVIRONMENT", "development")).strip().lower()

    @property
    def IS_DEV(self) -> bool:
        return self.ENV in ["dev", "development", "local", "test"]

    @property
    def IS_PROD(self) -> bool:
        return not self.IS_DEV

    # PostgreSQL Configuration
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "admin")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "ofbl")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    NO_FEED_IMAGE_PATH: str = os.getenv("NO_FEED_IMAGE_PATH", r"./static/images/no_feed.jpg")

    AI_SERVER_URL: str = os.getenv("AI_SERVER_URL", "http://localhost:8005/")
    LOT_DETAILS_PATH: str = os.getenv("LOT_DETAILS_PATH", r"./lots_details")

    # SQLite fallback (for local dev without PostgreSQL)
    USE_SQLITE: bool = os.getenv("USE_SQLITE", "false").strip().lower() in ["true", "1", "yes"]
    SQLITE_PATH: str = os.getenv("SQLITE_PATH", "./badmal_dev.db")

    @property
    def DATABASE_URL(self):
        if self.USE_SQLITE:
            return f"sqlite:///{self.SQLITE_PATH}"
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()