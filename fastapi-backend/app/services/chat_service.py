import logging
import uuid
from typing import List, Optional, Dict, Any, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, desc
import base64
import asyncio

from app.models.chat import Chat, MessagePair, Message, MessageContent, Project, ProjectKnowledge
from app.models.user import User
from app.schemas.chat import ChatCreate, ChatMessageRequest, ChatStreamChunk
from app.utils.aws_client import bedrock_client, s3_client
from app.core.config import settings

logger = logging.getLogger(__name__)

class ChatService:
    """Service for handling AI chat conversations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_chat(self, user_id: uuid.UUID, chat_data: ChatCreate) -> Chat:
        """Create a new chat."""
        try:
            # Verify project exists if provided
            if chat_data.project_id:
                project_query = select(Project).where(
                    Project.id == chat_data.project_id,
                    Project.user_id == user_id
                )
                project = await self.db.scalar(project_query)
                if not project:
                    raise ValueError("Project not found")
            
            chat = Chat(
                user_id=user_id,
                project_id=chat_data.project_id,
                title=chat_data.title,
                system_prompt=chat_data.system_prompt
            )
            
            self.db.add(chat)
            await self.db.commit()
            await self.db.refresh(chat)
            
            logger.info(f"Created chat {chat.id} for user {user_id}")
            return chat
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating chat: {e}")
            raise
    
    async def get_chat(self, chat_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Chat]:
        """Get a chat with full details."""
        query = select(Chat).options(
            selectinload(Chat.message_pairs).selectinload(MessagePair.messages).selectinload(Message.contents),
            selectinload(Chat.project).selectinload(Project.knowledge_items)
        ).where(
            Chat.id == chat_id,
            Chat.user_id == user_id
        )
        
        return await self.db.scalar(query)
    
    async def get_user_chats(
        self, 
        user_id: uuid.UUID, 
        project_id: Optional[uuid.UUID] = None,
        include_archived: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Chat]:
        """Get user's chats with optional filtering."""
        query = select(Chat).where(Chat.user_id == user_id)
        
        if project_id:
            query = query.where(Chat.project_id == project_id)
        
        if not include_archived:
            query = query.where(Chat.is_archived == False)
        
        query = query.order_by(desc(Chat.created_at)).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def generate_chat_title(self, messages: List[Dict[str, Any]]) -> str:
        """Generate a title for the chat based on the first few messages."""
        try:
            # Get first user message for title generation
            user_messages = [msg for msg in messages if msg.get('role') == 'user']
            if not user_messages:
                return "New Chat"
            
            first_message = user_messages[0].get('content', [])
            if not first_message:
                return "New Chat"
            
            # Extract text content
            text_content = ""
            for content in first_message:
                if content.get('type') == 'text':
                    text_content += content.get('text', '')
            
            if not text_content:
                return "New Chat"
            
            # Use Claude Haiku for quick title generation
            title_messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Generate a short, descriptive title (max 50 characters) for a conversation that starts with: {text_content[:200]}. ONLY RETURN THE TITLE, NO OTHER TEXT. NO EXTRA TEXT."
                        }
                    ]
                }
            ]
            
            title = await bedrock_client.generate_single_response(
                messages=title_messages,
                model='claude-3.5-haiku',
                max_tokens=50,
                temperature=0.1
            )
            
            # Clean up the title
            title = title.strip().strip('"').strip("'")
            if len(title) > 50:
                title = title[:47] + "..."
            
            return title or "New Chat"
            
        except Exception as e:
            logger.warning(f"Failed to generate chat title: {e}")
            return "New Chat"
    
    async def get_project_context(self, project_id: uuid.UUID) -> str:
        """Get project knowledge as context string."""
        try:
            query = select(ProjectKnowledge).where(
                ProjectKnowledge.project_id == project_id,
                ProjectKnowledge.include_in_chat == True
            ).order_by(ProjectKnowledge.created_at)
            
            result = await self.db.execute(query)
            knowledge_items = result.scalars().all()
            
            if not knowledge_items:
                return ""
            
            context_parts = []
            for item in knowledge_items:
                context_parts.append(f"# {item.title}\n{item.content}")
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error getting project context: {e}")
            return ""
    
    async def prepare_messages_for_claude(
        self, 
        chat: Chat, 
        new_message_content: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Prepare message history for Claude API."""
        messages = []
        
        # Add existing message pairs
        for pair in chat.message_pairs:
            for message in pair.messages:
                if message.hidden:
                    continue
                
                # Convert message contents to Claude format
                content_blocks = []
                for content in message.contents:
                    if content.content_type == 'text' and content.text_content:
                        content_blocks.append({
                            'type': 'text',
                            'text': content.text_content
                        })
                    elif content.content_type == 'image' and content.file_path:
                        # For images, we would need to get the base64 content
                        # This is a simplified version - in production you'd fetch from S3
                        content_blocks.append({
                            'type': 'text',
                            'text': f"[Image: {content.file_path}]"
                        })
                    elif content.content_type == 'document' and content.file_path:
                        content_blocks.append({
                            'type': 'text',
                            'text': f"[Document: {content.file_path}]"
                        })
                
                if content_blocks:
                    messages.append({
                        'role': message.role,
                        'content': content_blocks
                    })
        
        # Add the new message
        messages.append({
            'role': 'user',
            'content': new_message_content
        })
        
        return messages
    
    async def get_system_prompt(self, chat: Chat) -> str:
        """Get the complete system prompt including project context."""
        base_prompt = chat.system_prompt or settings.DEFAULT_SYSTEM_PROMPT
        
        # Add project context if available
        if chat.project_id:
            project_context = await self.get_project_context(chat.project_id)
            if project_context:
                base_prompt += f"\n\n## Project Knowledge\n{project_context}"
        
        return base_prompt
    
    async def stream_chat_response(
        self,
        chat_id: uuid.UUID,
        user_id: uuid.UUID,
        message_request: ChatMessageRequest
    ) -> AsyncGenerator[ChatStreamChunk, None]:
        """Stream chat response from Claude."""
        try:
            # Get the chat
            chat = await self.get_chat(chat_id, user_id)
            if not chat:
                yield ChatStreamChunk(type="error", error="Chat not found")
                return
            
            # Create message pair
            message_pair = MessagePair(chat_id=chat_id)
            self.db.add(message_pair)
            await self.db.flush()  # Get the ID without committing
            
            # Create user message
            user_message = Message(
                message_pair_id=message_pair.id,
                role="user"
            )
            self.db.add(user_message)
            await self.db.flush()
            
            # Add message content
            message_content = MessageContent(
                message_id=user_message.id,
                content_type="text",
                text_content=message_request.message
            )
            self.db.add(message_content)
            
            # Prepare messages for Claude
            new_content = [{"type": "text", "text": message_request.message}]
            
            # TODO: Handle file uploads in message_request.files
            
            messages = await self.prepare_messages_for_claude(chat, new_content)
            
            # Get system prompt
            system_prompt = message_request.system_prompt_override or await self.get_system_prompt(chat)
            
            # Generate title if this is the first message
            if not chat.message_pairs:
                new_title = await self.generate_chat_title(messages)
                chat.title = new_title
            
            # Create assistant message
            assistant_message = Message(
                message_pair_id=message_pair.id,
                role="assistant"
            )
            self.db.add(assistant_message)
            await self.db.flush()
            
            # Stream response from Claude
            response_text = ""
            
            yield ChatStreamChunk(type="start", message_pair_id=message_pair.id)
            
            # Real AWS Bedrock streaming
            async for chunk in bedrock_client.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                stream=True
            ):
                response_text += chunk
                yield ChatStreamChunk(type="text", content=chunk)
            
            # Save assistant response
            assistant_content = MessageContent(
                message_id=assistant_message.id,
                content_type="text",
                text_content=response_text
            )
            self.db.add(assistant_content)
            
            # TODO: Count tokens and update token_count fields
            
            await self.db.commit()
            
            yield ChatStreamChunk(type="done", message_pair_id=message_pair.id)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in stream_chat_response: {e}")
            yield ChatStreamChunk(type="error", error=str(e))
    
    async def delete_chat(self, chat_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a chat."""
        try:
            query = select(Chat).where(
                Chat.id == chat_id,
                Chat.user_id == user_id
            )
            chat = await self.db.scalar(query)
            
            if not chat:
                return False
            
            await self.db.delete(chat)
            await self.db.commit()
            
            logger.info(f"Deleted chat {chat_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting chat: {e}")
            return False
    
    async def archive_chat(self, chat_id: uuid.UUID, user_id: uuid.UUID, archived: bool = True) -> bool:
        """Archive or unarchive a chat."""
        try:
            query = select(Chat).where(
                Chat.id == chat_id,
                Chat.user_id == user_id
            )
            chat = await self.db.scalar(query)
            
            if not chat:
                return False
            
            chat.is_archived = archived
            await self.db.commit()
            
            logger.info(f"{'Archived' if archived else 'Unarchived'} chat {chat_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error archiving chat: {e}")
            return False 