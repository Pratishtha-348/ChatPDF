from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Optional[str] = "user"  # Default to user

class AdminCreate(BaseModel):
    email: EmailStr
    password: str
    admin_key: str  # Secret key to create admin

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str  # Include role in token response

class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str

    class Config:
        from_attributes_mode = True

class IngestRequest(BaseModel):
    title: Optional[str] = None
    text: str

class IngestResponse(BaseModel):
    doc_id: str
    title: Optional[str] = None

class QueryRequest(BaseModel):
    query: str
    top_k: int = 8

class Source(BaseModel):
    doc_id: str
    score: float
    chunk: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]

class ConversationMessage(BaseModel):
    role: str
    content: str

class ConversationHistory(BaseModel):
    messages: List[ConversationMessage]

class DocumentInfo(BaseModel):
    id: str
    title: Optional[str]
    uploaded_by: str
    created_at: datetime
    
    class Config:
        from_attributes_mode = True