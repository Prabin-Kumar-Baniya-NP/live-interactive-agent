import json

from livekit import agents, rtc
from livekit.plugins import silero

from agents.base_agent import BaseAgent
from config.settings import settings
from core.context import SessionContext
from core.logging import get_logger, setup_logging
from core.session import create_agent_session, create_room_options

logger = get_logger("agent_runtime")


async def prewarm(proc: agents.JobProcess):
    """
    Preloads heavy models and modules to reduce cold-start latency.
    """
    logger.info("Agent process prewarming...")

    proc.userdata["vad"] = silero.VAD.load(force_download=False)
    logger.info("Silero VAD loaded")

    # Pre-import other plugins implicitly done at top level,
    # but we can force initialize things if needed.
    # For now, VAD loading is the heaviest local op.
    logger.info("Prewarm complete")


async def entrypoint(ctx: agents.JobContext):
    logger.info(f"Job received for room: {ctx.room.name}")

    # Connect to the room
    await ctx.connect()

    # Task 12.6: Event Handlers
    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        logger.info(
            f"Participant connected: {participant.identity} to room {ctx.room.name}"
        )

    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        logger.info(
            f"Participant disconnected: {participant.identity} "
            f"from room {ctx.room.name}"
        )

    @ctx.room.on("track_published")
    def on_track_published(
        publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant
    ):
        logger.info(
            f"Track published: {publication.source} by "
            f"{participant.identity} in room {ctx.room.name}"
        )

    @ctx.room.on("track_unpublished")
    def on_track_unpublished(
        publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant
    ):
        logger.info(
            f"Track unpublished: {publication.source} by "
            f"{participant.identity} in room {ctx.room.name}"
        )

    logger.info(f"Connected to room: {ctx.room.name}")

    # Task 14.4: Parse metadata and create SessionContext
    metadata = {}
    if ctx.room.remote_participants:
        # Try to get metadata from the first participant
        first_p = list(ctx.room.remote_participants.values())[0]
        if first_p.metadata:
            try:
                metadata = json.loads(first_p.metadata)
            except Exception:
                logger.warning(
                    f"Failed to parse metadata for participant {first_p.identity}"
                )

    session_ctx = SessionContext(
        user_id=metadata.get("user_id"),
        session_template_id=metadata.get("session_template_id"),
    )

    # Task 13.8: Create and start AgentSession (userdata passed to constructor)
    session = create_agent_session(settings, userdata=session_ctx)

    # Task 14.6: Register error handlers
    from core.error_handler import register_error_handlers

    register_error_handlers(session)

    # Create BaseAgent
    agent = BaseAgent(
        instructions=settings.DEFAULT_AGENT_INSTRUCTIONS,
        greeting=settings.DEFAULT_AGENT_GREETING,
    )

    # Start the session (greeting is handled by BaseAgent.on_enter)
    await session.start(
        agent=agent,
        room=ctx.room,
        room_options=create_room_options(),
    )


if __name__ == "__main__":
    setup_logging(settings.LOG_LEVEL)

    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
            ws_url=settings.LIVEKIT_URL,
            num_idle_processes=settings.WORKER_NUM_IDLE_PROCESSES,
        )
    )
