from livekit.plugins import cartesia, deepgram, openai, silero
from livekit.plugins.turn_detector import multilingual

from config.settings import settings


def create_stt(
    api_key: str = settings.DEEPGRAM_API_KEY,
    base_url: str = settings.DEEPGRAM_BASE_URL,
    model: str = settings.STT_MODEL,
) -> deepgram.STT:
    """
    Creates a configured instance of Deepgram STT plugin.

    Args:
        api_key: Deepgram API key.
        base_url: Deepgram API base URL (e.g., https://api.deepgram.com).
        model: Deepgram STT model.

    Returns:
        Configured deepgram.STT instance.
    """
    # If base_url does not end with /v1/listen,
    # we should probably let deepgram SDK handle it
    # or append it if we know the SDK requires the full path.
    # The default in deepgram.STT is 'https://api.deepgram.com/v1/listen'.
    # If the user provides 'https://api.deepgram.com', we might need to fix it.
    # However, standard practice with Deepgram SDK is that it might handle base URL.
    # But inspecting the signature, it defaults to the full URL.
    # So if we override it, we must provide the full URL.

    if base_url and not base_url.endswith("/v1/listen"):
        # Helper to construct the full URL if only base is provided
        base_url = f"{base_url.rstrip('/')}/v1/listen"

    return deepgram.STT(
        model=model,
        api_key=api_key,
        base_url=base_url,
    )


def create_tts(
    api_key: str = settings.CARTESIA_API_KEY,
    base_url: str = settings.CARTESIA_BASE_URL,
    model: str = settings.TTS_MODEL,
    voice_id: str = settings.TTS_VOICE_ID,
) -> cartesia.TTS:
    """
    Creates a configured instance of Cartesia TTS plugin.

    Args:
        api_key: Cartesia API key.
        base_url: Cartesia API base URL.
        model: Cartesia TTS model.
        voice_id: Cartesia voice ID.

    Returns:
        Configured cartesia.TTS instance.
    """
    return cartesia.TTS(
        model=model,
        api_key=api_key,
        voice=voice_id,
        base_url=base_url,
    )


def create_llm(
    api_key: str = settings.OPENAI_API_KEY,
    base_url: str = settings.OPENAI_BASE_URL,
    model: str = settings.LLM_MODEL,
) -> openai.LLM:
    """
    Creates a configured instance of OpenAI LLM plugin.

    Args:
        api_key: OpenAI API key.
        base_url: OpenAI API base URL.
        model: OpenAI LLM model.

    Returns:
        Configured openai.LLM instance.
    """
    return openai.LLM(
        model=model,
        api_key=api_key,
        base_url=base_url,
    )


def create_vad() -> silero.VAD:
    """
    Creates a loaded Silero VAD instance.
    """
    return silero.VAD.load()


def create_turn_detector() -> multilingual.MultilingualModel:
    """
    Creates a configured LiveKit multilingual turn detector.
    """
    return multilingual.MultilingualModel()
