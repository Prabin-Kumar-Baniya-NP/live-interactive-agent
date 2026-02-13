import logging
import traceback
from typing import Any

from livekit.agents import AgentSession


def register_error_handlers(session: AgentSession) -> None:
    """Register error handlers on the AgentSession."""
    logger = logging.getLogger("core.error_handler")

    # Note: 'agent_speech_interrupted' payload might vary based on SDK version
    # but typically provides info about what was being spoken
    @session.on("agent_speech_interrupted")
    def on_agent_speech_interrupted(msg: Any, interrupted_by_user: bool):
        logger.info(
            f"Agent speech interrupted. Message: {msg}, By User: {interrupted_by_user}"
        )

    @session.on("error")
    def on_error(error: Exception):
        handle_pipeline_error(error, "AgentSession", logger)


def handle_pipeline_error(
    error: Exception, component: str, logger: logging.Logger
) -> None:
    """Log and classify pipeline errors."""
    error_type = type(error).__name__
    error_msg = str(error)

    # Basic classification logic for transient vs permanent errors
    is_transient = any(
        keyword in error_msg.lower()
        for keyword in [
            "timeout",
            "network",
            "rate limit",
            "503",
            "504",
            "connection reset",
        ]
    )

    severity = "WARNING" if is_transient else "ERROR"

    log_msg = f"Pipeline Error in {component}: [{error_type}] {error_msg}"

    if severity == "WARNING":
        logger.warning(log_msg)
    else:
        # Include traceback for permanent errors
        logger.error(log_msg)
        logger.error(traceback.format_exc())
