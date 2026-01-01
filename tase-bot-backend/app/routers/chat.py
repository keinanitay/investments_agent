from fastapi import APIRouter, HTTPException, Body, Depends, Request
import asyncio
import time
from app.db.database import get_database
from app.db import repository
from app.models.schemas import ChatMessage, ChatSession
from app.routers.auth import get_current_user
from typing import List, Optional
from pydantic import BaseModel

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

    # handle new chat creation if needed
    if is_new_chat:
        # get user details for the title
        username = current_user.get("username", "user")
        
        # calculate next chat number for the title
        current_count = await repository.count_user_chats(db, user_id)
        next_number = current_count + 1
        
        # generate title: usr_{username}_chat_{number}
        dynamic_title = f"usr_{username}_chat_{next_number}"
        
        new_session = ChatSession(
            user_id=user_id,
            title=dynamic_title,
            messages=[user_msg]
        )
        
        session_id = await repository.create_chat_session(db, new_session.model_dump(by_alias=True, exclude=["id"]))

    # ----------------------------
    # simulated ai logic - REPLACE WITH LLM GENERATED RESPONSES:
    # this is where the actual ai response generation should be plugged in
    try:
        start_ts = time.time()
        await asyncio.sleep(2.5) # simulate processing delay
        
        # check if client disconnected (stop generating pressed)
        if await request.is_disconnected():
            return

        # construct simulated rich response with markdown
        ai_response_text = (
            "Here is the **Bank Leumi** analysis:\n\n"  # Double \n for new paragraph
            "* Trend: **Positive**\n"
            "* Risk: _Medium_\n\n"                      # Double \n before link
            "[Click here for TASE page](https://www.tase.co.il)"
        )
        
        # add metadata for charts and sources
        ai_metadata = {
            "type": "chart",
            "chart_data": [
                {"name": "Jan", "value": 100},
                {"name": "Feb", "value": 120},
                {"name": "Mar", "value": 110},
                {"name": "Apr", "value": 140}
            ],
            "sources": [{"name": "TASE API"}, {"name": "Bizportal"}],
            "execution_time": time.time() - start_ts
        }

        ai_msg = ChatMessage(
            role="assistant", 
            content=ai_response_text,
            metadata=ai_metadata
        )
        # ----------------------------------

        # save ai response to database
        await repository.append_ai_message(db, session_id, ai_msg.model_dump())

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
