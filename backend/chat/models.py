from django.db import models
from django.core.exceptions import ValidationError
from .utils.file_validators import validate_image_size, validate_document_size, validate_mime_type
import uuid
import base64

class MessageContent(models.Model):
    CONTENT_TYPES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('document', 'Document')    
    )
    
    message = models.ForeignKey('Message', related_name='contents', on_delete=models.CASCADE)
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES)
    text_content = models.TextField(null=True, blank=True)
    file_content = models.FileField(
        upload_to='chat_contents/%Y/%m/%d/',
        null=True, blank=True,
        validators=[validate_mime_type]
    )
    edited_at = models.DateTimeField(auto_now=True, null=True)
    mime_type = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def clean(self):
        if self.content_type == 'text' and not self.text_content:
            raise ValidationError('Text content is required for text type')
        
        if self.content_type in ['image', 'document'] and not self.file_content:
            raise ValidationError('File content is required for image/document type')
        
        if self.content_type == 'image':
            validate_image_size(self.file_content)
        
        if self.content_type == 'document':
            validate_document_size(self.file_content)
        
        # Validate content limits per message
        content_count = MessageContent.objects.filter(
            message=self.message,
            content_type=self.content_type
        ).count()
        
        if self.content_type == 'image' and content_count >= 20:
            raise ValidationError('Maximum 20 images per message')
        
        if self.content_type == 'document' and content_count >= 5:
            raise ValidationError('Maximum 5 documents per message')

    def save(self, *args, **kwargs):
        if self.file_content:
            self.mime_type = validate_mime_type(self.file_content)
        super().save(*args, **kwargs)

class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message_pair = models.ForeignKey('MessagePair', on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=(("user", "user"), ("assistant", "assistant")))
    hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)
    token_count = models.IntegerField(default=0)

    def get_content(self) -> list:
        """
        Get message content in Claude API format
        Returns a list of content blocks
        """
        content_blocks = []
        
        for content_item in self.contents.all():
            if content_item.content_type == 'text':
                content_blocks.append({
                    'type': 'text',
                    'text': content_item.text_content
                })
            elif content_item.content_type in ['image', 'document']:
                try:
                    # Read file content as base64
                    file_content = content_item.file_content
                    if not file_content:
                        continue
                        
                    # Get the file content as bytes
                    file_bytes = file_content.read()
                    
                    # Encode as base64
                    base64_content = base64.b64encode(file_bytes).decode('utf-8')
                    
                    if content_item.content_type == 'image':
                        content_blocks.append({
                            'type': 'image',
                            'source': {
                                'type': 'base64',
                                'media_type': content_item.mime_type,
                                'data': base64_content
                            }
                        })
                    else:  # document
                        content_blocks.append({
                            'type': 'text',
                            'text': f"[Document: {content_item.file_content.name}]\n"
                        })
                        
                except Exception as e:
                    print(f"Error processing file content: {e}")
                    continue
                finally:
                    # Reset file pointer if it's a file
                    if file_content:
                        file_content.seek(0)
        
        return content_blocks

    def __str__(self):
        return f"{self.role} message in {self.message_pair}"

class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    instructions = models.TextField(blank=True, null=True)
    user = models.ForeignKey('appauth.AppUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']

    @property
    def total_knowledge_tokens(self):
        """Get total tokens used by all included knowledge items"""
        return self.knowledge_items.filter(
            include_in_chat=True
        ).aggregate(
            total=models.Sum('token_count')
        )['total'] or 0

    def validate_knowledge_tokens(self, new_token_count=0):
        """
        Validate if adding new_token_count would exceed the limit
        Returns (bool, str) - (is_valid, error_message)
        """
        current_total = self.total_knowledge_tokens
        new_total = current_total + new_token_count
        max_tokens = 160000  # 80% of context window

        if new_total > max_tokens:
            return False, f"Adding this would exceed the token limit. Current: {current_total}, New: {new_token_count}, Max: {max_tokens}"
        return True, ""

class ProjectKnowledge(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='knowledge_items')
    content = models.TextField()
    title = models.CharField(max_length=200)
    include_in_chat = models.BooleanField(default=True)
    token_count = models.IntegerField(default=0)  # Store token count for quick access
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.project.name}"

    class Meta:
        ordering = ['-created_at']

# Modify the Chat model to include project
class Chat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('appauth.AppUser', on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='chats')
    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    system_prompt = models.TextField(blank=True, null=True)
    is_archived = models.BooleanField(default=False)
    def __str__(self):
        return self.title

    @property
    def total_tokens(self):
        """Get total tokens used in this chat including project knowledge"""
        message_tokens = sum(
            message.token_count 
            for pair in self.message_pairs.all()
            for message in pair.messages.all()
        )
        project_tokens = self.project.total_knowledge_tokens if self.project else 0
        return message_tokens + project_tokens

class MessagePair(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='message_pairs')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message Pair for {self.chat.title} at {self.created_at}"


class SavedSystemPrompt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('appauth.AppUser', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    prompt = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class TokenUsage(models.Model):
    user = models.ForeignKey('appauth.AppUser', on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    tokens_used = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.tokens_used} tokens on {self.created_at}"
    



