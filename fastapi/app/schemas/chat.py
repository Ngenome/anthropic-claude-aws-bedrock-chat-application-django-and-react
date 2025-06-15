from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Union, Any, Dict
from datetime import datetime
import uuid

# Base schemas for message content
class MessageContentBase(BaseModel):
    content_type: str = Field(..., description="Type of content: text, image, document")
    text_content: Optional[str] = Field(None, description="Text content if type is text")
    
class MessageContentCreate(MessageContentBase):
    pass

class MessageContentResponse(MessageContentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    message_id: uuid.UUID
    file_path: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime
    edited_at: Optional[datetime] = None

# Message schemas
class MessageBase(BaseModel):
    role: str = Field(..., description="Message role: user or assistant")
    hidden: bool = Field(default=False)

class MessageCreate(MessageBase):
    contents: List[MessageContentCreate] = Field(..., description="Message content blocks")

class MessageResponse(MessageBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    message_pair_id: uuid.UUID
    token_count: int = 0
    is_archived: bool = False
    created_at: datetime
    contents: List[MessageContentResponse] = []

# Message pair schemas
class MessagePairResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    chat_id: uuid.UUID
    created_at: datetime
    messages: List[MessageResponse] = []

# Chat schemas
class ChatBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    system_prompt: Optional[str] = Field(None, description="Custom system prompt for this chat")

class ChatCreate(ChatBase):
    project_id: Optional[uuid.UUID] = Field(None, description="Associated project for context")

class ChatUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    system_prompt: Optional[str] = None
    project_id: Optional[uuid.UUID] = None
    is_archived: Optional[bool] = None

class ChatResponse(ChatBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    project_id: Optional[uuid.UUID] = None
    is_archived: bool = False
    created_at: datetime
    
class ChatDetailResponse(ChatResponse):
    message_pairs: List[MessagePairResponse] = []
    total_tokens: int = 0

# Chat interaction schemas
class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message text")
    files: Optional[List[str]] = Field(None, description="List of uploaded file IDs")
    system_prompt_override: Optional[str] = Field(None, description="Override system prompt for this message")

class ChatStreamChunk(BaseModel):
    type: str = Field(..., description="Type of chunk: text, error, done")
    content: Optional[str] = Field(None, description="Text content for text chunks")
    message_pair_id: Optional[uuid.UUID] = Field(None, description="Message pair ID when available")
    error: Optional[str] = Field(None, description="Error message if type is error")

# Project knowledge schemas
class ProjectKnowledgeBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    include_in_chat: bool = Field(default=True)

class ProjectKnowledgeCreate(ProjectKnowledgeBase):
    pass

class ProjectKnowledgeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    include_in_chat: Optional[bool] = None

class ProjectKnowledgeResponse(ProjectKnowledgeBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    project_id: uuid.UUID
    token_count: int = 0
    created_at: datetime
    updated_at: datetime

# Project schemas
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    instructions: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    instructions: Optional[str] = None
    is_archived: Optional[bool] = None

class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime

class ProjectDetailResponse(ProjectResponse):
    knowledge_items: List[ProjectKnowledgeResponse] = []
    chats: List[ChatResponse] = []
    total_knowledge_tokens: int = 0

# Saved system prompt schemas
class SavedSystemPromptBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    prompt: str = Field(..., min_length=1)

class SavedSystemPromptCreate(SavedSystemPromptBase):
    pass

class SavedSystemPromptUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    prompt: Optional[str] = Field(None, min_length=1)

class SavedSystemPromptResponse(SavedSystemPromptBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

# File upload schemas
class FileUploadResponse(BaseModel):
    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type")
    size: int = Field(..., description="File size in bytes")
    url: Optional[str] = Field(None, description="Public URL if applicable")

# Token usage schemas
class TokenUsageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    chat_id: uuid.UUID
    tokens_used: int
    created_at: datetime

class ChatTokenStats(BaseModel):
    total_tokens: int = Field(..., description="Total tokens used in chat")
    message_tokens: int = Field(..., description="Tokens from messages")
    project_tokens: int = Field(..., description="Tokens from project knowledge")
    
# Error schemas
class ChatError(BaseModel):
    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details") 