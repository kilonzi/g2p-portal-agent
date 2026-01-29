from typing import AsyncGenerator, Dict, List, Any
from loguru import logger
from app.agents.orchestrator import router_agent
from app.agents.model import get_model
import json
import uuid


class ChatService:
    def __init__(self):
        self.agent = router_agent
    
    async def _generate_thread_metadata(self, user_query: str, ai_response: str) -> Dict[str, str]:
        """Generate a concise title and summary for a new thread."""
        model = get_model()
        prompt = f"""Based on this conversation, generate a concise title (3-8 words) and a one-sentence summary.

User: {user_query}
Assistant: {ai_response[:500]}...

Return ONLY a JSON object with "title" and "summary" keys. No markdown, no explanation.
Example: {{"title": "LDLR Gene Analysis", "summary": "Discussion about the LDLR gene and its role in familial hypercholesterolemia."}}"""
        
        try:
            response = await model.ainvoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            content = content.strip().strip('```json').strip('```').strip()
            metadata = json.loads(content)
            return metadata
        except Exception as e:
            logger.error(f"Failed to generate thread metadata: {e}")
            fallback_title = " ".join(user_query.split()[:6])
            return {"title": fallback_title, "summary": user_query[:100]}

    async def stream_response(
        self, 
        user_id: str, 
        thread_id: str, 
        messages: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """
        Streams responses using simplified 4-event model:
        - thinking: AI reasoning/decisions
        - action: Tool/specialist execution
        - content: Final message
        - meta: Control signals
        """
        from app.services.stream_events import (
            emit_stream_start, emit_thinking, emit_action,
            emit_content, emit_meta,
            get_tool_info, get_subagent_info, format_args_summary
        )
        
        config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}
        context_logger = logger.bind(user_id=user_id, thread_id=thread_id)
        
        # Generate stream ID
        stream_id = f"str_{uuid.uuid4().hex[:12]}"
        
        # Load User Preferences
        user_prefs_text = ""
        try:
            import os
            pref_path = f"./.memory/users/{user_id}/preferences.json"
            if os.path.exists(pref_path):
                with open(pref_path, "r") as f:
                    prefs = json.load(f)
                    
                if prefs:
                    user_prefs_text = "\n\n### 👤 My Preferences:\n"
                    for cat, data in prefs.items():
                        user_prefs_text += f"- **{cat.title().replace('_', ' ')}**: {data.get('text', '')}\n"
                    user_prefs_text += "\n"
                    context_logger.info(f"Loaded user preferences for {user_id}")
        except Exception as e:
            context_logger.warning(f"Could not load user preferences: {e}")
        
        # Inject context (Global is already in System Prompt, User Prefs go here)
        if user_prefs_text and messages and messages[0].get("role") == "user":
            messages[0]["content"] = user_prefs_text + messages[0]["content"]
        
        is_first_exchange = len([m for m in messages if m.get("role") == "user"]) == 1
        user_first_message = messages[0].get("content", "") if is_first_exchange else ""
        collected_content = ""  # Collect all content, send ONCE at end
        
        # Track active actions
        active_actions = {}
        
        try:
            context_logger.info(f"Starting stream {stream_id} for thread {thread_id}")
            
            # 1. Send stream manifest
            yield emit_stream_start(stream_id, estimated_duration_ms=5000)
            
            # 2. Stream updates
            async for chunk in self.agent.astream(
                {"messages": messages}, 
                config=config,
                stream_mode="updates"
            ):
                for node_name, node_data in chunk.items():
                    context_logger.debug(f"Node '{node_name}' update")
                    
                    if isinstance(node_data, dict) and "messages" in node_data:
                        new_messages = node_data["messages"]
                        if not isinstance(new_messages, list):
                            new_messages = [new_messages]
                        
                        for msg in new_messages:
                            # === TOOL CALLS ===
                            if hasattr(msg, "tool_calls") and msg.tool_calls:
                                for tc in msg.tool_calls:
                                    tool_name = tc.get("name", "unknown_tool")
                                    action_id = tc.get("id", f"act_{len(active_actions)}")
                                    args = tc.get("args", {})
                                    
                                    tool_info = get_tool_info(tool_name)
                                    
                                    # Track action
                                    active_actions[action_id] = {
                                        "name": tool_name,
                                        "args": args
                                    }
                                    
                                    # Special: subagent delegation
                                    if tool_name == "task":
                                        subagent_type = args.get("subagent_type", "unknown")
                                        task_desc = args.get("description", "")
                                        subagent_info = get_subagent_info(subagent_type)
                                        
                                        # Emit thinking (decision)
                                        yield emit_thinking(
                                            thinking_type="decision",
                                            summary=f"Delegating to {subagent_info['title']}",
                                            details={
                                                "question": "Which specialist?",
                                                "chosen": subagent_type,
                                                "reasoning": f"Query requires {subagent_type} expertise",
                                                "confidence": 0.9
                                            },
                                            visibility="advanced"
                                        )
                                        
                                        # Emit action (delegation)
                                        yield emit_action(
                                            action_type="delegation",
                                            display_title=subagent_info['title'],
                                            status="running",
                                            action_id=action_id,
                                            display_summary=task_desc,
                                            visibility="standard",
                                            raw_data={"subagent_type": subagent_type, "task": task_desc}
                                        )
                                    else:
                                        # Regular tool
                                        args_summary = format_args_summary(args)
                                        
                                        yield emit_action(
                                            action_type="tool",
                                            display_title=tool_info['title'],
                                            status="running",
                                            action_id=action_id,
                                            display_summary=args_summary or tool_info['description'],
                                            visibility="standard",
                                            raw_data={"tool": tool_name, "args": args}
                                        )
                                    
                                    context_logger.info(f"🔧 ACTION START: {tool_info['title']}")
                            
                            # === TOOL RESULTS ===
                            if getattr(msg, "type", "") == "tool":
                                content = getattr(msg, "content", "")
                                tool_call_id = getattr(msg, "tool_call_id", None)
                                
                                if tool_call_id and tool_call_id in active_actions:
                                    action_info = active_actions[tool_call_id]
                                    tool_name = action_info["name"]
                                    tool_info = get_tool_info(tool_name)
                                    
                                    # Emit action completion
                                    yield emit_action(
                                        action_type="tool" if tool_name != "task" else "delegation",
                                        display_title=tool_info['title'],
                                        status="success",
                                        action_id=tool_call_id,
                                        display_summary=content[:100] if content else "Completed",
                                        visibility="standard"
                                    )
                                    
                                    context_logger.info(f"✅ ACTION COMPLETE: {tool_info['title']}")
                                
                                # Collect content (don't stream yet)
                                if content:
                                    if is_first_exchange:
                                        collected_content += content + "\n\n"
                            
                            # === AI MESSAGES ===
                            else:
                                content = getattr(msg, "content", "")
                                if isinstance(content, list):
                                    content = " ".join([
                                        block.get("text", "") 
                                        for block in content 
                                        if isinstance(block, dict) and block.get("type") == "text"
                                    ])
                                
                                if content:
                                    if is_first_exchange:
                                        collected_content += content
                                    context_logger.debug(f"💬 CONTENT: {len(content)} chars")
            
            # 3. Send FINAL content (only once)
            if collected_content:
                yield emit_content(
                    text=collected_content.strip(),
                    is_final=True,
                    source="agent",
                    visibility="minimal"
                )
            
            # 4. Generate thread metadata if first exchange
            if is_first_exchange and collected_content:
                context_logger.info("Generating thread metadata")
                metadata = await self._generate_thread_metadata(user_first_message, collected_content)
                yield emit_meta("title", {"title": metadata.get("title"), "summary": metadata.get("summary")})
            
            # 5. Send end signal
            yield emit_meta("end", {"stream_id": stream_id})
        
        except Exception as e:
            context_logger.error(f"Error during streaming: {e}")
            yield emit_meta("error", {"error": str(e), "stream_id": stream_id})
            raise e


chat_service = ChatService()
