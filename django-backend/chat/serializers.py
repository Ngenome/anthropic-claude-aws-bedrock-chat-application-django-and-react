# serializers.py
from rest_framework import serializers
from .models import Chat, Message, MessagePair, SavedSystemPrompt, Project, ProjectKnowledge, MessageContent, UserMemory, MemoryTag

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

class MemoryTagSerializer(serializers.ModelSerializer):
    memory_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MemoryTag
        fields = ['id', 'name', 'color', 'created_at', 'memory_count']
        read_only_fields = ['created_at']
    
    def get_memory_count(self, obj):
        """Return the number of active memories with this tag"""
        return obj.memories.filter(is_active=True).count()

class UserMemorySerializer(serializers.ModelSerializer):
    tags = MemoryTagSerializer(many=True, read_only=True)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of tag IDs to associate with this memory"
    )
    
    class Meta:
        model = UserMemory
        fields = [
            'id', 'summary', 'raw_content', 'confidence_score', 'category',
            'tags', 'tag_ids', 'is_verified', 'is_active', 'source_message_pair',
            'created_at', 'updated_at', 'last_referenced'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_referenced']
    
    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        memory = UserMemory.objects.create(**validated_data)
        
        if tag_ids:
            tags = MemoryTag.objects.filter(id__in=tag_ids)
            memory.tags.set(tags)
        
        return memory
    
    def update(self, instance, validated_data):
        tag_ids = validated_data.pop('tag_ids', None)
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update tags if provided
        if tag_ids is not None:
            tags = MemoryTag.objects.filter(id__in=tag_ids)
            instance.tags.set(tags)
        
        return instance

class UserMemoryListSerializer(serializers.ModelSerializer):
    """Simplified serializer for memory lists"""
    tags = MemoryTagSerializer(many=True, read_only=True)
    tag_count = serializers.SerializerMethodField()
    
    class Meta:
        model = UserMemory
        fields = [
            'id', 'summary', 'category', 'confidence_score', 'is_verified', 
            'is_active', 'tags', 'tag_count', 'created_at', 'last_referenced'
        ]
    
    def get_tag_count(self, obj):
        return obj.tags.count()