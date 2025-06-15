from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, Float, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

# Association table for UserMemory and MemoryTag many-to-many relationship
memory_tags_association = Table(
    'memory_tags_association',
    Base.metadata,
    Column('memory_id', UUID(as_uuid=True), ForeignKey('user_memories.id')),
    Column('tag_id', UUID(as_uuid=True), ForeignKey('memory_tags.id'))
)

class MessageContent(Base):
    __tablename__ = "message_contents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False)
    content_type = Column(String(10), nullable=False)  # text, image, document
    text_content = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)  # S3 path for uploaded files
    mime_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    edited_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    message = relationship("Message", back_populates="contents")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_pair_id = Column(UUID(as_uuid=True), ForeignKey("message_pairs.id"), nullable=False)
    role = Column(String(10), nullable=False)  # user, assistant
    hidden = Column(Boolean, default=False)
    token_count = Column(Integer, default=0)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    message_pair = relationship("MessagePair", back_populates="messages")
    contents = relationship("MessageContent", back_populates="message", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="projects")
    knowledge_items = relationship("ProjectKnowledge", back_populates="project", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="project")

class ProjectKnowledge(Base):
    __tablename__ = "project_knowledge"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    include_in_chat = Column(Boolean, default=True)
    token_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="knowledge_items")

class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    title = Column(String(100), nullable=False)
    system_prompt = Column(Text, nullable=True)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chats")
    project = relationship("Project", back_populates="chats")
    message_pairs = relationship("MessagePair", back_populates="chat", cascade="all, delete-orphan")
    extracted_memories = relationship("UserMemory", back_populates="chat")
    token_usage = relationship("TokenUsage", back_populates="chat")

class MessagePair(Base):
    __tablename__ = "message_pairs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    chat = relationship("Chat", back_populates="message_pairs")
    messages = relationship("Message", back_populates="message_pair", cascade="all, delete-orphan")
    source_memories = relationship("UserMemory", back_populates="source_message_pair")

class SavedSystemPrompt(Base):
    __tablename__ = "saved_system_prompts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(100), nullable=False)
    prompt = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="saved_prompts")

class TokenUsage(Base):
    __tablename__ = "token_usage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id"), nullable=False)
    tokens_used = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="token_usage")
    chat = relationship("Chat", back_populates="token_usage")

class MemoryTag(Base):
    __tablename__ = "memory_tags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)
    color = Column(String(7), default="#3B82F6")  # Hex color for UI
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    memories = relationship("UserMemory", secondary=memory_tags_association, back_populates="tags")

class UserMemory(Base):
    __tablename__ = "user_memories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("chats.id"), nullable=False)
    source_message_pair_id = Column(UUID(as_uuid=True), ForeignKey("message_pairs.id"), nullable=True)
    
    # Core memory data
    summary = Column(Text, nullable=False)
    raw_content = Column(Text, nullable=False)
    confidence_score = Column(Float, default=0.8)
    
    # Memory categorization
    category = Column(String(50), default='other')  # personal, preferences, work, goals, etc.
    
    # Metadata
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_referenced = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="memories")
    chat = relationship("Chat", back_populates="extracted_memories")
    source_message_pair = relationship("MessagePair", back_populates="source_memories")
    tags = relationship("MemoryTag", secondary=memory_tags_association, back_populates="memories") 