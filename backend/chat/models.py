from django.db import models
from django.core.exceptions import ValidationError

class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    instructions = models.TextField(blank=True, null=True)
    user = models.ForeignKey('appauth.AppUser', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
    uuid = models.CharField(max_length=100)
    user = models.ForeignKey('appauth.AppUser', on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='chats')
    title = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)
    system_prompt = models.TextField(blank=True, null=True)

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
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='message_pairs')
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message Pair for {self.chat.title} at {self.date}"

class Message(models.Model):
    message_pair = models.ForeignKey(MessagePair, on_delete=models.CASCADE, related_name='messages',default=1)
    ROLE_CHOICES = (
        ("user", "user"),
        ("assistant", "assistant"),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    TYPE_CHOICES = (
        ("text", "text"),
        ("image", "image"),
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="text")
    image = models.ImageField(upload_to='chat/images/', null=True, blank=True)
    text = models.TextField()
    token_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.role} message in {self.message_pair}"

    def save(self, *args, **kwargs):
        if not self.token_count:
            from .utils.token_counter import count_tokens
            self.token_count = count_tokens(self.text)
        super().save(*args, **kwargs)

class SavedSystemPrompt(models.Model):
    user = models.ForeignKey('appauth.AppUser', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    prompt = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Attachment(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='chat_attachments/')
    original_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_name

class TokenUsage(models.Model):
    user = models.ForeignKey('appauth.AppUser', on_delete=models.CASCADE)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    tokens_used = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.email} - {self.tokens_used} tokens on {self.date}"