from fastapi import APIRouter, HTTPException, Body, Depends, Request
import asyncio
import time
import logging
from db.database import get_database
from db import repository
from app.models.schemas import ChatMessage, ChatSession
from app.routers.auth import get_current_user
from app.services.response_generator import generate_response, generate_chat_title
from typing import List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

class MessageInput(BaseModel):
    content: str
    session_id: Optional[str] = None # If None, we create a new chat

class RenameInput(BaseModel):
    title: str

@router.post("/message")
async def send_message(
    request: Request,
    payload: MessageInput, 
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    handles sending a message to the bot.
    if session_id is provided, it continues the chat.
    if session_id is none, it creates a new chat session.
    """
    user_id = current_user["_id"]
    
    # determine session id
    session_id = payload.session_id
    is_new_chat = False
    
    # create user message object
    user_msg = ChatMessage(role="user", content=payload.content)

    if session_id:
        # try to append to existing chat
        success = await repository.append_message_to_chat(db, session_id, user_id, user_msg.model_dump())
        if not success:
            is_new_chat = True
    else:
        is_new_chat = True

    # Initialize title variable
    dynamic_title = None
    temp_title = "New Chat"
    
    # handle new chat creation if needed
    if is_new_chat:
        # Use a temporary title initially - will be updated after AI response
        new_session = ChatSession(
            user_id=user_id,
            title=temp_title,
            messages=[user_msg]
        )
        
        session_id = await repository.create_chat_session(db, new_session.model_dump(by_alias=True, exclude=["id"]))

    # ----------------------------
    # Generate AI response based on context
    try:
        start_ts = time.time()
        
        # Get chat history for context (excluding the just-added user message)
        chat_session = await repository.get_chat_session(db, session_id, user_id)
        chat_history = []
        if chat_session and "messages" in chat_session:
            # Get all messages except the last one (which is the current user message we just added)
            chat_history = chat_session["messages"][:-1]
        
        # Generate AI response using the response generator service
        # The response generator will query MongoDB directly for the user's risk level
        ai_response_text, ai_metadata = await generate_response(
            user_message=payload.content,
            chat_history=chat_history,
            db=db,
            user_id=user_id
        )
        
        # Check if client disconnected (stop generating pressed)
        if await request.is_disconnected():
            # Rollback: Remove the user message so it doesn't appear in history
            if is_new_chat:
                await repository.delete_chat_session(db, session_id)
            else:
                await repository.remove_last_message(db, session_id)
            return

        # Create AI message object
        ai_msg = ChatMessage(
            role="assistant", 
            content=ai_response_text,
            metadata=ai_metadata
        )

        # Save AI response to database
        await repository.append_ai_message(db, session_id, ai_msg.model_dump())
        
        # Generate and update chat title for new chats based on first user message
        if is_new_chat:
            try:
                generated_title = await generate_chat_title(payload.content)
                # Update the title in MongoDB
                await repository.rename_chat_session(db, session_id, generated_title)
                dynamic_title = generated_title
            except Exception as e:
                # If title generation fails, keep the temporary title
                logger.error(f"Failed to generate chat title: {str(e)}")
                dynamic_title = temp_title

    except asyncio.CancelledError:
        raise

    return {
        "session_id": session_id, # frontend must save this for the next message
        "title": dynamic_title if is_new_chat else None,
        "user_msg": user_msg, 
        "ai_msg": ai_msg
    }

@router.get("/history/all", response_model=List[ChatSession])
async def get_user_chats(current_user: dict = Depends(get_current_user), db = Depends(get_database)):
    """
    returns a list of all chat sessions for the sidebar.
    only returns metadata (title, id), not the full message history.
    """
    chats = await repository.get_user_chats_metadata(db, current_user["_id"])
    
    # manually map _id to id for pydantic
    for chat in chats:
        chat["id"] = str(chat["_id"])
        
    return chats

@router.get("/history/{session_id}", response_model=ChatSession)
async def get_chat_history(session_id: str, current_user: dict = Depends(get_current_user), db = Depends(get_database)):
    """retrieves the full history of a specific chat session."""
    chat = await repository.get_chat_session(db, session_id, current_user["_id"])
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    # map _id to id
    chat["id"] = str(chat["_id"])
    return chat

@router.delete("/history/{session_id}")
async def delete_chat(session_id: str, current_user: dict = Depends(get_current_user), db = Depends(get_database)):
    """deletes a specific chat session."""
    success = await repository.delete_chat_session(db, session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    return {"status": "deleted", "id": session_id}

@router.put("/history/{session_id}")
async def rename_chat(session_id: str, payload: RenameInput, current_user: dict = Depends(get_current_user), db = Depends(get_database)):
    """renames a chat session."""
    success = await repository.rename_chat_session(db, session_id, payload.title)
    
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    return {"status": "updated", "title": payload.title}
