import asyncio
from typing import AsyncGenerator
from litestar import get, post
from litestar.response import Stream
from loguru import logger

from app.api.schemas import ChatRequest
from app.services.chat import chat_service


@get("/status")
async def check_status() -> dict[str, str]:
    """
    Health check endpoint.
    """
    return {"status": "ok"}

from litestar.response import Stream

@post("/chat/stream")
async def chat_stream(data: ChatRequest) -> Stream:
    """
    Streams the chat response from the multi-agent system using SSE.
    """
    logger.info(f"Received chat request for user_id={data.user_id}, thread_id={data.thread_id}")

    return Stream(
        chat_service.stream_response(
            user_id=data.user_id,
            thread_id=data.thread_id,
            messages=data.messages
        ),
        media_type="text/event-stream"
    )
