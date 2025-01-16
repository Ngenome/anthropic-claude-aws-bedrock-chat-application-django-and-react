from django.core.management.base import BaseCommand
from chat.models import Chat, Project, ProjectKnowledge, Message, MessagePair, MessageContent
import json
from django.core.files.base import ContentFile
import base64
from django.utils.timezone import make_aware
from datetime import datetime
import os

class Command(BaseCommand):
    help = 'Import chat data from JSON format'

    def handle(self, *args, **options):
        # Load the JSON data
        with open('chat_data_export.json', 'r') as f:
            data = json.load(f)

        # Import Projects
        for project_data in data['projects']:
            project = Project(
                id=project_data['id'],
                name=project_data['name'],
                description=project_data['description'],
                instructions=project_data['instructions'],
                user_id=project_data['user_id'],
                created_at=make_aware(datetime.fromisoformat(project_data['created_at'])),
                updated_at=make_aware(datetime.fromisoformat(project_data['updated_at'])),
                is_archived=project_data['is_archived']
            )
            project.save()

        # Import ProjectKnowledge
        for knowledge_data in data['project_knowledge']:
            knowledge = ProjectKnowledge(
                project_id=knowledge_data['project_id'],
                content=knowledge_data['content'],
                title=knowledge_data['title'],
                include_in_chat=knowledge_data['include_in_chat'],
                token_count=knowledge_data['token_count'],
                created_at=make_aware(datetime.fromisoformat(knowledge_data['created_at'])),
                updated_at=make_aware(datetime.fromisoformat(knowledge_data['updated_at']))
            )
            knowledge.save()

        # Import Chats
        for chat_data in data['chats']:
            chat = Chat(
                id=chat_data['id'],
                user_id=chat_data['user_id'],
                project_id=chat_data['project_id'],
                title=chat_data['title'],
                created_at=make_aware(datetime.fromisoformat(chat_data['created_at'])),
                system_prompt=chat_data['system_prompt'],
                is_archived=chat_data['is_archived']
            )
            chat.save()

        # Import MessagePairs
        for pair_data in data['message_pairs']:
            pair = MessagePair(
                id=pair_data['id'],
                chat_id=pair_data['chat_id'],
                created_at=make_aware(datetime.fromisoformat(pair_data['created_at']))
            )
            pair.save()

        # Import Messages
        for message_data in data['messages']:
            message = Message(
                id=message_data['id'],
                message_pair_id=message_data['message_pair_id'],
                role=message_data['role'],
                hidden=message_data['hidden'],
                created_at=make_aware(datetime.fromisoformat(message_data['created_at'])),
                is_archived=message_data['is_archived'],
                token_count=message_data['token_count']
            )
            message.save()

        # Import MessageContents
        for content_data in data['message_contents']:
            content = MessageContent(
                message_id=content_data['message_id'],
                content_type=content_data['content_type'],
                text_content=content_data['text_content'],
                mime_type=content_data['mime_type'],
                created_at=make_aware(datetime.fromisoformat(content_data['created_at']))
            )

            # Handle file content if present
            if content_data.get('file_content_base64'):
                file_data = base64.b64decode(content_data['file_content_base64'])
                file_name = content_data['file_name']
                content.file_content.save(
                    file_name,
                    ContentFile(file_data),
                    save=False
                )

            content.save()

        self.stdout.write(self.style.SUCCESS('Successfully imported all data')) 