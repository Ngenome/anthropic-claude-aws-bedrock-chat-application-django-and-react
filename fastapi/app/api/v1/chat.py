from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import uuid
import json

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.chat import Chat
from app.schemas.chat import (
    ChatCreate, ChatResponse, ChatDetailResponse, ChatUpdate,
    ChatMessageRequest, ChatStreamChunk, ProjectCreate, ProjectResponse,
    ProjectDetailResponse, ProjectKnowledgeCreate, ProjectKnowledgeResponse,
    SavedSystemPromptCreate, SavedSystemPromptResponse
)
from app.services.chat_service import ChatService

router = APIRouter()

# ===============================
# Chat Management Endpoints
# ===============================

@router.post("/chats", response_model=ChatResponse)
async def create_chat(
    chat_data: ChatCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat."""
    chat_service = ChatService(db)
    try:
        chat = await chat_service.create_chat(current_user.id, chat_data)
        return chat
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create chat")

@router.get("/chats", response_model=List[ChatResponse])
async def get_chats(
    project_id: Optional[uuid.UUID] = None,
    include_archived: bool = False,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's chats with optional filtering."""
    chat_service = ChatService(db)
    chats = await chat_service.get_user_chats(
        current_user.id, project_id, include_archived, limit, offset
    )
    return chats

@router.get("/chats/{chat_id}", response_model=ChatDetailResponse)
async def get_chat(
    chat_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific chat with full details."""
    chat_service = ChatService(db)
    chat = await chat_service.get_chat(chat_id, current_user.id)
    
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    
    return chat

@router.put("/chats/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: uuid.UUID,
    chat_update: ChatUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a chat."""
    chat_service = ChatService(db)
    chat = await chat_service.get_chat(chat_id, current_user.id)
    
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    
    # Update fields
    update_data = chat_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(chat, field, value)
    
    await db.commit()
    await db.refresh(chat)
    
    return chat

@router.delete("/chats/{chat_id}")
async def delete_chat(
    chat_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat."""
    chat_service = ChatService(db)
    success = await chat_service.delete_chat(chat_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    
    return {"message": "Chat deleted successfully"}

@router.post("/chats/{chat_id}/archive")
async def archive_chat(
    chat_id: uuid.UUID,
    archived: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Archive or unarchive a chat."""
    chat_service = ChatService(db)
    success = await chat_service.archive_chat(chat_id, current_user.id, archived)
    
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    
    action = "archived" if archived else "unarchived"
    return {"message": f"Chat {action} successfully"}

# ===============================
# Chat Interaction Endpoints
# ===============================

@router.post("/chats/{chat_id}/messages")
async def send_message(
    chat_id: uuid.UUID,
    message_request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a message to a chat and get streaming response."""
    chat_service = ChatService(db)
    
    async def generate_response():
        """Generator function for streaming response."""
        async for chunk in chat_service.stream_chat_response(
            chat_id, current_user.id, message_request
        ):
            # Convert chunk to JSON and add newline for SSE format
            yield f"data: {chunk.model_dump_json()}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

# ===============================
# Project Management Endpoints
# ===============================

@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new project."""
    from app.models.chat import Project
    
    project = Project(
        user_id=current_user.id,
        name=project_data.name,
        description=project_data.description,
        instructions=project_data.instructions
    )
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    return project

@router.get("/projects", response_model=List[ProjectResponse])
async def get_projects(
    include_archived: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's projects."""
    from sqlalchemy import select
    from app.models.chat import Project
    
    query = select(Project).where(Project.user_id == current_user.id)
    
    if not include_archived:
        query = query.where(Project.is_archived == False)
    
    query = query.order_by(Project.created_at.desc())
    
    result = await db.execute(query)
    projects = result.scalars().all()
    
    return projects

@router.get("/projects/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific project with details."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.chat import Project
    
    query = select(Project).options(
        selectinload(Project.knowledge_items),
        selectinload(Project.chats)
    ).where(
        Project.id == project_id,
        Project.user_id == current_user.id
    )
    
    project = await db.scalar(query)
    
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    return project

@router.post("/projects/{project_id}/knowledge", response_model=ProjectKnowledgeResponse)
async def add_project_knowledge(
    project_id: uuid.UUID,
    knowledge_data: ProjectKnowledgeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add knowledge to a project."""
    from sqlalchemy import select
    from app.models.chat import Project, ProjectKnowledge
    
    # Verify project ownership
    project_query = select(Project).where(
        Project.id == project_id,
        Project.user_id == current_user.id
    )
    project = await db.scalar(project_query)
    
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # TODO: Calculate token count for the content
    knowledge = ProjectKnowledge(
        project_id=project_id,
        title=knowledge_data.title,
        content=knowledge_data.content,
        include_in_chat=knowledge_data.include_in_chat,
        token_count=0  # TODO: Implement token counting
    )
    
    db.add(knowledge)
    await db.commit()
    await db.refresh(knowledge)
    
    return knowledge

# ===============================
# System Prompts Endpoints
# ===============================

@router.post("/system-prompts", response_model=SavedSystemPromptResponse)
async def create_system_prompt(
    prompt_data: SavedSystemPromptCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Save a system prompt."""
    from app.models.chat import SavedSystemPrompt
    
    prompt = SavedSystemPrompt(
        user_id=current_user.id,
        title=prompt_data.title,
        prompt=prompt_data.prompt
    )
    
    db.add(prompt)
    await db.commit()
    await db.refresh(prompt)
    
    return prompt

@router.get("/system-prompts", response_model=List[SavedSystemPromptResponse])
async def get_system_prompts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's saved system prompts."""
    from sqlalchemy import select
    from app.models.chat import SavedSystemPrompt
    
    query = select(SavedSystemPrompt).where(
        SavedSystemPrompt.user_id == current_user.id
    ).order_by(SavedSystemPrompt.created_at.desc())
    
    result = await db.execute(query)
    prompts = result.scalars().all()
    
    return prompts

# ===============================
# Utility Endpoints
# ===============================

@router.get("/chats/{chat_id}/export")
async def export_chat(
    chat_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export chat conversation as JSON."""
    chat_service = ChatService(db)
    chat = await chat_service.get_chat(chat_id, current_user.id)
    
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    
    # Build export data
    export_data = {
        "chat_id": str(chat.id),
        "title": chat.title,
        "created_at": chat.created_at.isoformat(),
        "project": {
            "id": str(chat.project.id) if chat.project else None,
            "name": chat.project.name if chat.project else None
        },
        "messages": []
    }
    
    for pair in chat.message_pairs:
        for message in pair.messages:
            if not message.hidden:
                message_data = {
                    "role": message.role,
                    "created_at": message.created_at.isoformat(),
                    "contents": []
                }
                
                for content in message.contents:
                    content_data = {
                        "type": content.content_type,
                        "text": content.text_content,
                        "file_path": content.file_path,
                        "mime_type": content.mime_type
                    }
                    message_data["contents"].append(content_data)
                
                export_data["messages"].append(message_data)
    
    return export_data 