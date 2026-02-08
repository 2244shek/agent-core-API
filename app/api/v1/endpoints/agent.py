from fastapi import APIRouter, Body, Depends
from fastapi.responses import StreamingResponse
from app.services.agent import agent_app
from langchain_core.messages import HumanMessage
import json
import asyncio
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import ChatSession, ChatMessage
from langchain_core.messages import AIMessage

router = APIRouter()

@router.post("/chat/{session_id}")
async def chat_with_agent(
    session_id: str,
    message: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    # 1. Fetch or Create Session
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not chat_session:
        chat_session = ChatSession(id=session_id)
        db.add(chat_session)
        db.commit()

    # 2. Load History for LangGraph
    history = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    past_messages = [
        HumanMessage(content=m.content) if m.role == "human" else AIMessage(content=m.content)
        for m in history
    ]

    async def event_generator():
        # Track the final AI content to save it at the end
        final_ai_content = ""
        current_input = {"messages": past_messages + [HumanMessage(content=message)]}

        async for event in agent_app.astream(current_input, stream_mode="values"):
            last_message = event["messages"][-1]

            # CASE A: Agent is calling a tool (Web Search), notify the frontend
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                yield f"data: {json.dumps({'type': 'tool', 'content': 'Searching the web...'})}\n\n"
            
            # CASE B: Agent is providing a text response(it's a final answer, yield the text)
            elif isinstance(last_message, AIMessage) and last_message.content:
                final_ai_content = last_message.content
                yield f"data: {json.dumps({'type': 'text', 'content': last_message.content})}\n\n"
            
        # 3. PERSISTENCE: Save the turn to the Database
        # Save Human Message
        db.add(ChatMessage(session_id=session_id, role="human", content=message))
        # Save AI Message (only if we got content)
        if final_ai_content:
            db.add(ChatMessage(session_id=session_id, role="ai", content=final_ai_content))
        
        db.commit()

    return StreamingResponse(event_generator(), media_type="text/event-stream")