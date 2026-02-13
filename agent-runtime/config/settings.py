from pydantic_settings import BaseSettings, SettingsConfigDict


class RuntimeSettings(BaseSettings):
    LIVEKIT_URL: str
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str
    PLATFORM_API_URL: str = "http://localhost:8000"
    LOG_LEVEL: str = "INFO"
    WORKER_NUM_IDLE_PROCESSES: int = 3

    # STT (Deepgram)
    DEEPGRAM_API_KEY: str
    DEEPGRAM_BASE_URL: str = "https://api.deepgram.com"
    STT_MODEL: str = "nova-3"

    # LLM (OpenAI)
    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4.1-mini"

    # TTS (Cartesia)
    CARTESIA_API_KEY: str
    CARTESIA_BASE_URL: str = "https://api.cartesia.ai"
    TTS_MODEL: str = "sonic"
    TTS_VOICE_ID: str

    # Agent Defaults
    DEFAULT_AGENT_INSTRUCTIONS: str = (
        "You are a helpful voice assistant. Be concise and friendly."
    )
    DEFAULT_AGENT_GREETING: str = "Greet the user warmly and offer your assistance."

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = RuntimeSettings()
