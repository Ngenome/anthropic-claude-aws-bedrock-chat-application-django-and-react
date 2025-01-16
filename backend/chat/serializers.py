# serializers.py
from rest_framework import serializers
from .models import Chat, Message, MessagePair, SavedSystemPrompt, Project, ProjectKnowledge, MessageContent

class MessageContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageContent
        fields = ['id', 'content_type', 'text_content', 'file_content', 'mime_type', 'edited_at', 'created_at']

class MessageSerializer(serializers.ModelSerializer):
    contents = MessageContentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'message_pair', 'role', 'contents', 'hidden', 'created_at', 'is_archived', 'token_count']

class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ['id', 'title', 'created_at', 'system_prompt', 'project', 'user']

class SystemPromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedSystemPrompt
        fields = '__all__'
        read_only_fields = ['user']

class MessagePairSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = MessagePair
        fields = '__all__'

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'instructions', 'created_at', 'updated_at', 'total_knowledge_tokens']
        read_only_fields = ['created_at', 'updated_at']

class ProjectKnowledgeSerializer(serializers.ModelSerializer):
    token_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ProjectKnowledge
        fields = ['id', 'project', 'content', 'title', 'include_in_chat', 
                 'token_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'token_count']

    def validate(self, data):
        from .utils.token_counter import count_tokens
        
        content = data.get('content', '')
        project = data.get('project')
        
        # Count tokens for new content
        token_count = count_tokens(content)
        
        # Validate against project limits
        is_valid, error_message = project.validate_knowledge_tokens(token_count)
        if not is_valid:
            raise serializers.ValidationError(error_message)
            
        return data