from typing import List, Dict, Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    """
    Request model for the chat stream endpoint.
    """
    user_id: str
    thread_id: str
    messages: List[Dict[str, str]]
