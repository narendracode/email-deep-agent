from __future__ import annotations

import anthropic
from common.config import get_settings

_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    """Return a shared AsyncAnthropic client (lazy singleton)."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


async def complete(prompt: str, max_tokens: int = 4096) -> str:
    """Send a prompt to Claude Opus 4.8 with adaptive thinking and return the text response.

    Args:
        prompt: The user prompt to send.
        max_tokens: Maximum tokens for the response.

    Returns:
        The assistant's text response.
    """
    client = get_client()
    async with client.messages.stream(
        model="claude-opus-4-8",
        max_tokens=max_tokens,
        thinking={"type": "adaptive"},
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        message = await stream.get_final_message()

    return "".join(
        block.text
        for block in message.content
        if block.type == "text"
    )
