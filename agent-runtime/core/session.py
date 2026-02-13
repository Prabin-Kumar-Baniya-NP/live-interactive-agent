import logging
from typing import Any, Optional

from livekit.agents import AgentSession, room_io
from livekit.plugins import noise_cancellation

from config.settings import RuntimeSettings
from core.plugins import (
    create_llm,
    create_stt,
    create_tts,
    create_turn_detector,
    create_vad,
)

logger = logging.getLogger("agent-runtime")


def create_agent_session(
    settings: RuntimeSettings, userdata: Optional[Any] = None
) -> AgentSession:
    """
    Creates a configured AgentSession with all voice pipeline plugins.
    """
    logger.info("Initializing AgentSession plugins...")

    stt = create_stt()
    llm = create_llm()
    tts = create_tts()
    vad = create_vad()
    turn_detector = create_turn_detector()

    # Log configuration (safe logging, no keys)
    logger.info(f"STT Model: {settings.STT_MODEL}")
    logger.info(f"LLM Model: {settings.LLM_MODEL}")
    logger.info(f"TTS Model: {settings.TTS_MODEL}")
    logger.info("VAD: Silero VAD loaded")
    logger.info("Turn Detector: LiveKit Multilingual Model initialized")

    kwargs = dict(
        stt=stt,
        llm=llm,
        tts=tts,
        vad=vad,
        turn_detection=turn_detector,
    )

    if userdata is not None:
        kwargs["userdata"] = userdata

    session = AgentSession(**kwargs)

    return session


def create_room_options() -> room_io.RoomOptions:
    """
    Creates a configured RoomOptions instance with noise cancellation.
    """
    return room_io.RoomOptions(
        audio_input=room_io.AudioInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
        video_input=False,
    )
