from bson import ObjectId
from typing import List, Optional, Dict, Any
from pymongo.database import Database

async def get_user_by_email(db: Database, email: str) -> Optional[Dict]:
    """retrieves a user document by email."""
    return await db["users"].find_one({"email": email})

async def get_user_by_id(db: Database, user_id: str) -> Optional[Dict]:
    """retrieves a user document by their unique id."""
    if not ObjectId.is_valid(user_id):
        return None
    return await db["users"].find_one({"_id": ObjectId(user_id)})

async def create_user(db: Database, user_data: Dict) -> str:
    """inserts a new user into the database and returns the id."""
    result = await db["users"].insert_one(user_data)
    return str(result.inserted_id)

async def update_user(db: Database, user_id: str, update_data: Dict) -> bool:
    """updates specific fields of a user document."""
    if not ObjectId.is_valid(user_id):
        return False
    result = await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    return result.matched_count > 0

async def delete_user(db: Database, user_id: str) -> bool:
    """deletes a user and all their associated chat sessions."""
    if not ObjectId.is_valid(user_id):
        return False
    # delete chats first
    await db["chats"].delete_many({"user_id": user_id})
    # delete user
    result = await db["users"].delete_one({"_id": ObjectId(user_id)})
    return result.deleted_count > 0

async def append_message_to_chat(db: Database, session_id: str, user_id: str, message: Dict) -> bool:
    """
    appends a message to an existing chat.
    returns true if chat was found and updated, false otherwise.
    """
    if not ObjectId.is_valid(session_id):
        return False
    
    result = await db["chats"].update_one(
        {"_id": ObjectId(session_id), "user_id": user_id},
        {"$push": {"messages": message}}
    )
    return result.matched_count > 0

async def append_ai_message(db: Database, session_id: str, message: Dict) -> bool:
    """appends an ai response to the chat history."""
    if not ObjectId.is_valid(session_id):
        return False
    result = await db["chats"].update_one(
        {"_id": ObjectId(session_id)},
        {"$push": {"messages": message}}
    )
    return result.matched_count > 0

async def count_user_chats(db: Database, user_id: str) -> int:
    """returns the total number of chats for a specific user."""
    return await db["chats"].count_documents({"user_id": user_id})

async def create_chat_session(db: Database, chat_data: Dict) -> str:
    """creates a new chat session and returns its id."""
    result = await db["chats"].insert_one(chat_data)
    return str(result.inserted_id)

async def get_user_chats_metadata(db: Database, user_id: str, limit: int = 100) -> List[Dict]:
    """retrieves metadata (no messages) for user chats, sorted by date."""
    cursor = db["chats"].find(
        {"user_id": user_id},
        {"messages": 0} # projection: exclude messages array
    ).sort("created_at", -1)
    
    return await cursor.to_list(length=limit)

async def get_chat_session(db: Database, session_id: str, user_id: str) -> Optional[Dict]:
    """retrieves a full chat session including messages."""
    if not ObjectId.is_valid(session_id):
        return None
    return await db["chats"].find_one({"_id": ObjectId(session_id), "user_id": user_id})

async def delete_chat_session(db: Database, session_id: str) -> bool:
    """deletes a specific chat session."""
    if not ObjectId.is_valid(session_id):
        return False
    result = await db["chats"].delete_one({"_id": ObjectId(session_id)})
    return result.deleted_count > 0

async def rename_chat_session(db: Database, session_id: str, new_title: str) -> bool:
    """updates the title of a chat session."""
    if not ObjectId.is_valid(session_id):
        return False
    result = await db["chats"].update_one(
        {"_id": ObjectId(session_id)},
        {"$set": {"title": new_title}}
    )
    return result.matched_count > 0

async def remove_last_message(db: Database, session_id: str) -> bool:
    """removes the last message from a chat session (used for rollback)."""
    if not ObjectId.is_valid(session_id):
        return False
    result = await db["chats"].update_one(
        {"_id": ObjectId(session_id)},
        {"$pop": {"messages": 1}}
    )
    return result.matched_count > 0