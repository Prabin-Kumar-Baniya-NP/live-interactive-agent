from typing import List, Union

from pydantic import validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Live Interactive Agent"
    API_V1_PREFIX: str = "/api/v1"

    # Feature Flags / Environment
    DEBUG: bool = False

    # Database
    DATABASE_URL: str
    REDIS_URL: str

    # LiveKit
    LIVEKIT_URL: str
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str

    # Security
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra fields in .env
    )


settings = Settings()
