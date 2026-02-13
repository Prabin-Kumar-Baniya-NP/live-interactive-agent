from typing import Optional

from livekit import agents
from livekit.agents import llm

from core.logging import get_logger

logger = get_logger("agents.base_agent")


class BaseAgent(agents.Agent):
    def __init__(
        self,
        *,
        instructions: str,
        greeting: Optional[str] = None,
        chat_ctx: Optional[llm.ChatContext] = None,
    ):
        super().__init__(instructions=instructions, chat_ctx=chat_ctx)
        self._greeting = greeting

    @property
    def greeting(self) -> Optional[str]:
        return self._greeting

    async def on_enter(self) -> None:
        """Called when the agent takes control of the session."""
        logger.info(f"Agent {self} entered session")
        if self._greeting:
            logger.info(f"Generating greeting: {self._greeting}")
            await self.session.generate_reply(instructions=self._greeting)

    async def on_user_turn_completed(
        self, turn_ctx: llm.ChatContext, new_message: llm.ChatMessage
    ) -> None:
        """Called after the user finishes speaking."""
        try:
            # content is a list of parts (strings, images, etc.)
            content_parts = new_message.content or []
            content_text = " ".join(str(p) for p in content_parts)
            logger.info(
                f"User turn completed (transcript length: {len(content_text)}, "
                f"total messages: {len(turn_ctx.messages())})"
            )
        except Exception as e:
            logger.error(f"Error logging user turn: {e}")
