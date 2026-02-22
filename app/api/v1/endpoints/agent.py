from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.services.agent import agent_app
from langchain_core.messages import HumanMessage
import json
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import ChatSession, ChatMessage
from langchain_core.messages import AIMessage
from pydantic import BaseModel


def _make_session_title(message: str, max_len: int = 60) -> str:
    """Derive a human-readable session title from the user's first message."""
    text = message.strip()
    if len(text) <= max_len:
        return text
    # Cut at last space before limit so we don't break mid-word
    truncated = text[:max_len].rsplit(" ", 1)[0]
    return truncated + "…"

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: str

@router.get("/sessions")
async def get_all_sessions(db: Session = Depends(get_db)):
    """
    Fetches all unique chat sessions from the database.
    """
    sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()
    return [
        {"id": s.id, "title": s.title or f"Chat {s.id[:8]}", "updated_at": s.updated_at} 
        for s in sessions
    ]

@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    """
    Returns all messages for a specific session to populate the frontend UI.
    """
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    return [
        {"role": m.role, "content": m.content, "created_at": m.created_at} 
        for m in messages
    ]


class RenameRequest(BaseModel):
    title: str


@router.patch("/sessions/{session_id}")
async def rename_session(session_id: str, body: RenameRequest, db: Session = Depends(get_db)):
    """
    Renames a chat session by updating its title.
    """
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
    chat_session.title = body.title.strip() or chat_session.title
    chat_session.updated_at = datetime.utcnow()
    db.commit()
    return {"id": chat_session.id, "title": chat_session.title}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    """
    Deletes a chat session and all its messages (cascade handled by relationship).
    """
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(chat_session)
    db.commit()
    return {"deleted": session_id}


@router.post("/chat")
async def chat_with_agent(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    session_id = request.session_id
    message = request.message
    
    # 1. Fetch or Create Session
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    is_new_session = chat_session is None
    if is_new_session:
        title = _make_session_title(message)
        chat_session = ChatSession(id=session_id, title=title)
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
        # Refresh session timestamp so sidebar stays sorted by latest activity
        chat_session.updated_at = datetime.utcnow()
        db.commit()

    return StreamingResponse(event_generator(), media_type="text/event-stream")