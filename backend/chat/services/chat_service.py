from typing import List, Dict, Any, Optional
import json
import boto3
import os
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from ..models import Chat, MessagePair, Message, Project, MessageContent
from ..prompts.coding import get_coding_system_prompt
from ..utils.file_validators import validate_image_size, validate_document_size, validate_mime_type
from ..utils.token_counter import count_tokens
from botocore.exceptions import ClientError
from transformers import GPT2TokenizerFast
User = get_user_model()

class ChatService:
    CLAUDE_35_SONNET_V2 = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    CLAUDE_35_HAIKU_V1_0 = "anthropic.claude-3-5-haiku-20241022-v1:0"

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

    def _generate_chat_title(self, message_text: str, project_context: str = "") -> str:
        """
        Generate a chat title using Claude 3.5 Haiku
        Falls back to truncated message if generation fails
        """
        try:
            # Prepare context for title generation
            context = message_text
            
            # If we have project context, process it to stay within token limits
            if project_context:
                context_tokens = count_tokens(project_context)
                if context_tokens > 5000:
                    # Split into first 2k and last 2k tokens
                    tokenizer = GPT2TokenizerFast.from_pretrained("Xenova/claude-tokenizer")
                    tokens = tokenizer.encode(project_context)
                    first_part = tokenizer.decode(tokens[:2000])
                    last_part = tokenizer.decode(tokens[-2000:])
                    project_context = f"{first_part}\n...\n{last_part}"
                
                context = f"{project_context}\n\nUser Question: {message_text}"

            # Prepare the message for Claude
            messages = [{
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": f"Based on this context, generate a concise and descriptive title that is exactly 5 words or less. Respond with ONLY the title, no other text or explanation:\n\n{context}"
                }]
            }]

            # Make the API call
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 20,
                "messages": messages
            })

            response = self.bedrock_runtime.invoke_model(
                body=body,
                modelId=self.CLAUDE_35_HAIKU_V1_0
            )
            
            response_body = json.loads(response.get('body').read())
            title = response_body.get('content')[0].get('text').strip()
            
            # Validate the title
            if title and len(title.split()) <= 10:
                return title

        except (ClientError, Exception) as e:
            print(f"Error generating title: {str(e)}")

        # Fallback to truncated message
        return message_text[:15] + "..."

    def _create_new_chat(self, user: AbstractUser, message_text: str, project_id: Optional[str]) -> Chat:
        project = None
        project_context = ""
        
        if project_id:
            project = Project.objects.get(id=project_id, user=user)
            # Get project context for title generation
            context_parts = []
            if project.instructions:
                context_parts.append(f"Project Instructions:\n{project.instructions}")

            knowledge_items = project.knowledge_items.filter(include_in_chat=True)
            if knowledge_items:
                knowledge_text = "\n\n".join([
                    f"### {item.title} ###\n{item.content}"
                    for item in knowledge_items
                ])
                context_parts.append(f"Project Knowledge:\n{knowledge_text}")
            
            project_context = "\n\n".join(context_parts)

        # Generate title using Claude
        title = self._generate_chat_title(message_text, project_context)
            
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

    def prepare_message_history(self, chat: Chat) -> List[Dict[str, Any]]:
        """
        Prepare message history in Claude API format
        """
        messages = []
        
        # Add project context as a separate user message if exists
        project_context = self.get_project_context(chat)
        if project_context:
            messages.append({
                'role': 'user',
                'content': [{'type': 'text', 'text': f"<project_knowledge>\n{project_context}\n</project_knowledge>"}]
            })
        
        # Build message history
        for pair in MessagePair.objects.filter(chat=chat).order_by('created_at'):
            for message in pair.messages.all():
                messages.append({
                    'role': message.role,
                    'content': message.get_content()  # This now returns content blocks as per Claude API
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


    def prepare_message_content(self, message: Message) -> List[Dict[str, Any]]:
        """Prepare message content for Claude API"""

        return message.get_content()

    def create_chat_request_body(self, messages: List[Dict[str, Any]], chat: Chat) -> str:
        """
        Create request body for Claude API
        """
        system_prompt = get_coding_system_prompt(chat.system_prompt or "")
        
        return json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": messages,
        })

    def invoke_model(self, body: str):
        return self.bedrock_runtime.invoke_model_with_response_stream(
            body=body,
            modelId=self.CLAUDE_35_SONNET_V2
        )

    def create_new_message(self, message_pair: MessagePair, role: str, text: str = None, files: list = None) -> Message:
        """
        Create a new message with optional file attachments using MessageContent model.
        """
        # Create the base message
        message = Message.objects.create(
            message_pair=message_pair,
            role=role
        )

        # Add text content if provided
        if text:
            MessageContent.objects.create(
                message=message,
                content_type='text',
                text_content=text
            )

        # Handle file attachments if any
        if files:
            for file in files:
                # Determine content type based on mime type
                mime_type = validate_mime_type(file)
                content_type = 'image' if mime_type.startswith('image/') else 'document'
                
                MessageContent.objects.create(
                    message=message,
                    content_type=content_type,
                    file_content=file,
                    mime_type=mime_type
                )

        return message 