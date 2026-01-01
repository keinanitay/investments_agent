from pydantic import BaseModel, Field, EmailStr, BeforeValidator
from datetime import datetime
from typing import Optional, List, Annotated, Dict, Any

PyObjectId = Annotated[str, BeforeValidator(str)]

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    risk_level: str = "Medium"
    theme: str = "dark"

class UserUpdate(BaseModel):
    risk_level: Optional[str] = None
    theme: Optional[str] = None

class UserInDB(UserCreate):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    created_at: datetime
    password: str = Field(exclude=True) 


class ChatMessage(BaseModel):
    role: str
    metadata: Optional[Dict[str, Any]] = None
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatSession(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: str
    title: str
    messages: List[ChatMessage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True