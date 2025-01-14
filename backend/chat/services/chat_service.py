from typing import List, Dict, Any, Optional
import json
import boto3
import os
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from ..models import Chat, MessagePair, Message, Project, Attachment
from ..file_handlers import get_file_contents
from ..prompts.coding import get_coding_system_prompt
User = get_user_model()

class ChatService:
    CLAUDE_35_SONNET_V2 = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    def __init__(self):
        self.bedrock_runtime = boto3.client(
            service_name="bedrock-runtime",
            region_name="us-west-2",
            aws_access_key_id=os.getenv("AWS_BEDROCK_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_BEDROCK_SECRET_ACCESS_KEY")
        )

    def create_or_get_chat(self, user: AbstractUser, chat_id: str, message_text: str, project_id: Optional[str] = None) -> Chat:
        if chat_id is None or chat_id == 'new':
            return self._create_new_chat(user, message_text, project_id)
        return Chat.objects.get(id=chat_id, user=user)

    def _create_new_chat(self, user: AbstractUser, message_text: str, project_id: Optional[str]) -> Chat:
        title = message_text[:15] + "..."
        project = None
        if project_id:
            project = Project.objects.get(id=project_id, user=user)
            
        # Create chat with default coding system prompt
        chat = Chat.objects.create(
            title=title, 
            user=user, 
            project=project,
            system_prompt=""
        )
        return chat

    def get_project_context(self, chat: Chat) -> str:
        if not chat.project:
            return ""

        context_parts = []
        
        if chat.project.instructions:
            context_parts.append(f"Project Instructions:\n{chat.project.instructions}")

        knowledge_items = chat.project.knowledge_items.filter(include_in_chat=True)
        if knowledge_items:
            knowledge_text = "\n\n".join([
                f"### {item.title} ###\n{item.content}"
                for item in knowledge_items
            ])
            context_parts.append(f"Project Knowledge:\n{knowledge_text}")

        return "\n\n".join(context_parts)

    def prepare_message_history(self, chat: Chat, message_text: str, attachment_ids: List[str]) -> List[Dict[str, Any]]:
        messages = []
        
        # Add project context as a separate user message if exists
        project_context = self.get_project_context(chat)
        if project_context:
            messages.append({
                'role': 'user',
                'content': [{'type': 'text', 'text': f"<project_knowledge>\n{project_context}\n</project_knowledge>"}]
            })
        
        # Build message history
        messages.extend(self._build_message_history(chat))
        
        # Add file contents if any
        file_contents = self._get_attachment_contents(attachment_ids)
        file_context = ""
        if file_contents:
            file_context = f"<file_attachments>\n{self._format_file_contents(file_contents)}\n</file_attachments>\n\n"
        
        # Add current user message with appropriate tags
        current_message = f"{file_context}<user_query>\n{message_text}\n</user_query>"
        messages.append({
            'role': 'user',
            'content': [{'type': 'text', 'text': current_message}]
        })
        
        return messages

    def _format_file_contents(self, file_contents: List[str]) -> str:
        return "\n".join(file_contents)

    def _build_message_history(self, chat: Chat) -> List[Dict[str, Any]]:
        messages = []
        for pair in MessagePair.objects.filter(chat=chat).order_by('created_at'):
            for message in pair.messages.all():
                messages.append({
                    'role': message.role,
                    'content': message.get_content()
                })
        return messages

    def _get_attachment_contents(self, attachment_ids: List[str]) -> List[str]:
        file_contents = []
        for attachment_id in attachment_ids:
            try:
                attachment = Attachment.objects.get(id=attachment_id)
                content = get_file_contents(attachment.file.path)
                file_contents.append(f"File: {attachment.original_name}\n\n{content}\n\n")
            except Attachment.DoesNotExist:
                continue
        return file_contents

    def prepare_message_content(self, message_text: str, files: List[Any]) -> List[Dict[str, Any]]:
        """Prepare message content with text and files"""
        content = []
        
        # Handle image files
        for file in files:
            if file.content_type.startswith('image/'):
                import base64
                encoded_image = base64.b64encode(file.read()).decode('utf-8')
                content.append({
                    'type': 'image',
                    'source': {
                        'type': 'base64',
                        'media_type': file.content_type,
                        'data': encoded_image
                    }
                })
        
        # Add text content
        if message_text:
            content.append({
                'type': 'text',
                'text': message_text
            })
            
        return content

    def create_chat_request_body(self, messages: List[Dict[str, Any]], chat: Chat) -> str:
        system_prompt = get_coding_system_prompt(chat.system_prompt or "")
        
        return json.dumps({
            "system": system_prompt,
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": messages
        })

    def invoke_model(self, body: str):
        return self.bedrock_runtime.invoke_model_with_response_stream(
            body=body,
            modelId=self.CLAUDE_35_SONNET_V2
        ) 