from typing import AsyncGenerator, Dict, List, Any
from loguru import logger
from app.agents.orchestrator import router_agent


class ChatService:
    def __init__(self):
        self.agent = router_agent

    async def stream_response(
        self, 
        user_id: str, 
        thread_id: str, 
        messages: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """
        Streams responses from the router agent using 'updates' mode for granular events.
        """
        config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}
        
        try:
            logger.info(f"Starting chat stream for thread {thread_id}")
            async for chunk in self.agent.astream(
                {"messages": messages}, 
                config=config,
                stream_mode="updates"
            ):
                for node_name, node_update in chunk.items():
                    logger.debug(f"Node '{node_name}' update: {node_update}")
                    
                    if isinstance(node_update, dict) and "messages" in node_update:
                        new_messages = node_update["messages"]
                        if not isinstance(new_messages, list):
                            new_messages = [new_messages]
                            
                        for msg in new_messages:
                            # 1. Handle Tool Calls
                            if hasattr(msg, "tool_calls") and msg.tool_calls:
                                for tc in msg.tool_calls:
                                    tool_name = tc.get("name", "tool")
                                    args = tc.get("args", {})
                                    yield f"event: tool_start\ndata: Calling {tool_name} with {args}\n\n"
                            
                            # 2. Handle Content (Text)
                            content = getattr(msg, "content", "")
                            # Normalize list content (e.g. Anthropic)
                            if isinstance(content, list):
                                content = " ".join([
                                    block.get("text", "") 
                                    for block in content 
                                    if isinstance(block, dict) and block.get("type") == "text"
                                ])
                            
                            if content:
                                # Categorize based on message type
                                if getattr(msg, "type", "") == "tool":
                                    yield f"event: tool_result\ndata: {content}\n\n"
                                else:
                                    # Regular AI message (Thinking or Answer)
                                    yield f"event: message\ndata: {content}\n\n"

        except Exception as e:
            logger.error(f"Error during streaming: {e}")
            yield f"event: error\ndata: {str(e)}\n\n"
            raise e

chat_service = ChatService()
