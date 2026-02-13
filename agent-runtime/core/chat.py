import logging

from livekit.agents import llm


def create_initial_chat_ctx(system_prompt: str) -> llm.ChatContext:
    """Create a new ChatContext with an initial system prompt."""
    chat_ctx = llm.ChatContext()
    chat_ctx.add_message(role="system", content=system_prompt)
    return chat_ctx


def log_chat_ctx_summary(chat_ctx: llm.ChatContext, logger: logging.Logger) -> None:
    """Log a summary of the current chat context."""
    if not chat_ctx:
        logger.warning("Attempted to log summary of empty ChatContext")
        return

    messages = chat_ctx.messages()
    message_count = len(messages)

    # Estimate token count roughly by characters / 4
    total_chars = 0
    for msg in messages:
        for part in msg.content or []:
            total_chars += len(str(part))
    approx_tokens = total_chars // 4

    roles = [msg.role for msg in messages]
    role_counts = {}
    for role in roles:
        role_counts[role] = role_counts.get(role, 0) + 1

    logger.info(
        f"ChatContext Summary: {message_count} messages, "
        f"Roles: {role_counts}, "
        f"Approx Tokens: {approx_tokens}"
    )


def get_chat_ctx_message_count(chat_ctx: llm.ChatContext) -> int:
    """Return the total number of messages in the chat context."""
    if not chat_ctx:
        return 0
    return len(chat_ctx.messages())
