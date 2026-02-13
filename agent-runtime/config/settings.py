from pydantic_settings import BaseSettings, SettingsConfigDict


class RuntimeSettings(BaseSettings):
    LIVEKIT_URL: str
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str
    PLATFORM_API_URL: str = "http://localhost:8000"
    LOG_LEVEL: str = "INFO"
    WORKER_NUM_IDLE_PROCESSES: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = RuntimeSettings()
