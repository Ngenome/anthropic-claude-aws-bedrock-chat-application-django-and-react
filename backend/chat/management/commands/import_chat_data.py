from django.core.management.base import BaseCommand
from chat.models import Chat, Project, ProjectKnowledge, Message, MessagePair, MessageContent
import json
from django.core.files.base import ContentFile
import base64
from django.utils.timezone import make_aware, is_aware
from datetime import datetime
import os
from django.db import transaction
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Import chat data from JSON format'

    def parse_datetime(self, datetime_str):
        """Parse datetime string and ensure it's timezone aware"""
        dt = datetime.fromisoformat(datetime_str)
        return dt if is_aware(dt) else make_aware(dt)

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            # Get the first user from the database
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR("No users found in the database"))
                return

            self.stdout.write(f"Using user ID: {user.id} for all data")

            # Load the JSON data
            with open('chat_data_export.json', 'r') as f:
                data = json.load(f)

            self.stdout.write("Starting import process...")

            # Clear existing data
            # self.stdout.write("Clearing existing data...")
            # MessageContent.objects.all().delete()
            # Message.objects.all().delete()
            # MessagePair.objects.all().delete()
            # Chat.objects.all().delete()
            # ProjectKnowledge.objects.all().delete()
            # Project.objects.all().delete()

            # Import Projects first
            self.stdout.write("Importing projects...")
            for project_data in data['projects']:
                Project.objects.create(
                    id=project_data['id'],
                    name=project_data['name'],
                    description=project_data['description'],
                    instructions=project_data['instructions'],
                    user_id=user.id,  # Use the found user
                    created_at=self.parse_datetime(project_data['created_at']),
                    updated_at=self.parse_datetime(project_data['updated_at']),
                    is_archived=project_data['is_archived']
                )

            # Import ProjectKnowledge
            self.stdout.write("Importing project knowledge...")
            for knowledge_data in data['project_knowledge']:
                ProjectKnowledge.objects.create(
                    project_id=knowledge_data['project_id'],
                    content=knowledge_data['content'],
                    title=knowledge_data['title'],
                    include_in_chat=knowledge_data['include_in_chat'],
                    token_count=knowledge_data['token_count'],
                    created_at=self.parse_datetime(knowledge_data['created_at']),
                    updated_at=self.parse_datetime(knowledge_data['updated_at'])
                )

            # Import Chats
            self.stdout.write("Importing chats...")
            for chat_data in data['chats']:
                Chat.objects.create(
                    id=chat_data['id'],
                    user_id=user.id,  # Use the found user
                    project_id=chat_data['project_id'],
                    title=chat_data['title'],
                    created_at=self.parse_datetime(chat_data['created_at']),
                    system_prompt=chat_data['system_prompt'],
                    is_archived=chat_data['is_archived']
                )

            # Import MessagePairs
            self.stdout.write("Importing message pairs...")
            for pair_data in data['message_pairs']:
                MessagePair.objects.create(
                    id=pair_data['id'],
                    chat_id=pair_data['chat_id'],
                    created_at=self.parse_datetime(pair_data['created_at'])
                )

            # Import Messages
            self.stdout.write("Importing messages...")
            for message_data in data['messages']:
                Message.objects.create(
                    id=message_data['id'],
                    message_pair_id=message_data['message_pair_id'],
                    role=message_data['role'],
                    hidden=message_data['hidden'],
                    created_at=self.parse_datetime(message_data['created_at']),
                    is_archived=message_data['is_archived'],
                    token_count=message_data['token_count']
                )

            # Import MessageContents
            self.stdout.write("Importing message contents...")
            for content_data in data['message_contents']:
                content = MessageContent(
                    message_id=content_data['message_id'],
                    content_type=content_data['content_type'],
                    text_content=content_data['text_content'],
                    mime_type=content_data['mime_type'],
                    created_at=self.parse_datetime(content_data['created_at'])
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

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Import failed: {str(e)}'))
            raise