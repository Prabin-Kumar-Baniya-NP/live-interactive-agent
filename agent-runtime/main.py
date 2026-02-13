import asyncio

from livekit import agents, rtc

from config.settings import settings
from core.logging import get_logger, setup_logging

logger = get_logger("agent_runtime")


async def prewarm(proc: agents.JobProcess):
    logger.info("Agent process prewarming...")
    # Pre-import heavy modules here for faster job startup


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

    # Task 12.7: Graceful Shutdown
    shutdown_event = asyncio.Event()

    @ctx.room.on("disconnected")
    def on_disconnected(event=None):
        logger.info(f"Room disconnected: {ctx.room.name}, cleaning up...")
        shutdown_event.set()

    logger.info(f"Connected to room: {ctx.room.name}")

    # TODO: Epic 13 - Initialize AgentSession and start pipeline

    # Wait for the room to disconnect
    await shutdown_event.wait()


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
