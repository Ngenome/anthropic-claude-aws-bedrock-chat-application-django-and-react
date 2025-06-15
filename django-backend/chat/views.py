from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import StreamingHttpResponse
from rest_framework import generics, permissions
from .models import Chat, MessagePair, Message, SavedSystemPrompt, Project, ProjectKnowledge, MessageContent, UserMemory, MemoryTag
from .serializers import ChatSerializer, MessageSerializer,SystemPromptSerializer, ProjectSerializer, ProjectKnowledgeSerializer, UserMemorySerializer, UserMemoryListSerializer, MemoryTagSerializer
import os
import json
import boto3
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.decorators import action
from .utils.token_counter import count_tokens,get_token_usage_stats
from .services.chat_service import ChatService
from .utils.file_validators import validate_image_size, validate_document_size, validate_mime_type
from django.core.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.utils import timezone
from django.db import models
from .services.memory_service import MemoryExtractionService


# Initialize Bedrock client
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-west-2",
    aws_access_key_id=os.getenv("AWS_BEDROCK_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_BEDROCK_SECRET_ACCESS_KEY")
)   
CLAUDE_35_SONNET_V1_0 = "anthropic.claude-3-5-sonnet-20240620-v1:0"
CLAUDE_35_SONNET_V2 = "anthropic.claude-3-5-sonnet-20241022-v2:0"
CLAUDE_35_HAIKU_V1_0 = "anthropic.claude-3-5-haiku-20241022-v1:0"



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def claude_chat_view(request):
    chat_service = ChatService()
    
    if not request.data.get('message') and not request.FILES:
        return Response(
            {'error': 'Either message or files must be provided'}, 
            status=400
        )

    try:
        chat_id = request.data.get('chat_id')
        message_text = request.data.get('message', '')
        project_id = request.data.get('project_id')
        files = request.FILES.getlist('files', [])
        
        # Create or get chat
        chat = chat_service.create_or_get_chat(request.user, chat_id, message_text, project_id)
        
        # Create message pair and user message
        message_pair = MessagePair.objects.create(chat=chat)
        user_message = chat_service.create_new_message(
            message_pair=message_pair,
            role="user",
            text=message_text,
            files=files
        )

        # Send initial message data including file contents
        def stream_response(response):
            # Send user message data
            user_message_data = {
                'type': 'message',
                'message': {
                    'id': str(user_message.id),
                    'role': 'user',
                    'contents': [{
                        'id': str(content.id),
                        'content_type': content.content_type,
                        'text_content': content.text_content,
                        'file_content': request.build_absolute_uri(content.file_content.url) if content.file_content else None,
                        'mime_type': content.mime_type,
                        'created_at': content.created_at.isoformat(),
                        'edited_at': content.edited_at.isoformat() if content.edited_at else None
                    } for content in user_message.contents.all()],
                    'created_at': user_message.created_at.isoformat(),
                    'message_pair': str(message_pair.id)
                }
            }
            yield json.dumps(user_message_data) + '\n'

            # Create initial assistant message with empty text content
            assistant_message = chat_service.create_new_message(
                message_pair=message_pair,
                role="assistant",
                text=""  # Initialize with empty text
            )
            
            # Create initial text content for assistant message
            assistant_content = MessageContent.objects.create(
                message=assistant_message,
                content_type='text',
                text_content=''
            )
            
            # Send initial assistant message data
            assistant_init_data = {
                'type': 'message',
                'message': {
                    'id': str(assistant_message.id),
                    'role': 'assistant',
                    'contents': [{
                        'id': str(assistant_content.id),
                        'content_type': 'text',
                        'text_content': '',
                        'created_at': assistant_content.created_at.isoformat()
                    }],
                    'created_at': assistant_message.created_at.isoformat(),
                    'message_pair': str(message_pair.id)
                }
            }
            yield json.dumps(assistant_init_data) + '\n'

            # Stream the assistant's response
            current_text = ""
            
            for chunk in response['body']:
                chunk_data = json.loads(chunk['chunk']['bytes'].decode())
                if chunk_data['type'] == 'content_block_delta':
                    content = chunk_data['delta']['text']
                    current_text += content
                    # Update the message content in the database
                    assistant_content.text_content = current_text
                    assistant_content.save()
                    
                    yield json.dumps({
                        'type': 'content',
                        'message_id': str(assistant_message.id),
                        'content': content
                    }) + '\n'

            # Send chat ID at the end
            yield json.dumps({
                'type': 'chat_id',
                'content': str(chat.id)
            }) + '\n'
            
            # Extract memories from this conversation asynchronously
            try:
                memory_service = MemoryExtractionService()
                # Extract memories from the current message pair
                extracted_memories = memory_service.extract_memories_from_chat(chat, message_pair)
                if extracted_memories:
                    print(f"Extracted {len(extracted_memories)} memories from chat {chat.id}")
            except Exception as e:
                print(f"Error extracting memories: {e}")

        # Prepare messages for Claude
        messages = chat_service.prepare_message_history(chat, message_text)
        body = chat_service.create_chat_request_body(messages, chat)
        response = chat_service.invoke_model(body)

        return StreamingHttpResponse(
            stream_response(response),
            content_type='text/event-stream'
        )

    except Exception as e:
        raise e

class ChatMessagesListView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        chat_id = self.kwargs['chat_id']
        message_pairs = MessagePair.objects.filter(chat_id=chat_id).order_by('created_at')
        messages = []
        for pair in message_pairs:
            messages.extend(pair.messages.all())
        return messages

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        chat = Chat.objects.get(id=self.kwargs['chat_id'])
        
        messages = []
        for message in serializer.data:
            message_contents = []
            for content in message['contents']:
                message_contents.append({
                    'id': content['id'],
                    'content_type': content['content_type'],
                    'text_content': content['text_content'],
                    'file_content': content['file_content'],
                    'mime_type': content['mime_type'],
                    'edited_at': content['edited_at'],
                    'created_at': content['created_at']
                })

            messages.append({
                'id': message['id'],
                'role': message['role'],
                'contents': message_contents,
                'created_at': message['created_at'],
                'message_pair': message['message_pair'],
                'hidden': message['hidden']
            })

        return Response({
            'system_prompt': chat.system_prompt,
            'messages': messages
        })

    def perform_create(self, serializer):
        chat_id = self.kwargs['chat_id']
        chat = Chat.objects.get(id=chat_id)
        message_pair = MessagePair.objects.create(chat=chat)
        serializer.save(message_pair=message_pair)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def chat_list_view(request):
    if request.method == 'GET':
        chats = Chat.objects.filter(user=request.user).order_by('-created_at')
        return Response([{'id': chat.id, 'title': chat.title} for chat in chats])
    elif request.method == 'POST':
        title = request.data.get('title', 'New Chat')
        chat = Chat.objects.create(user=request.user, title=title)
        return Response({'id': chat.id, 'title': chat.title})
    
class ChatDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Chat.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        data['system_prompt'] = instance.system_prompt
        return Response(data)

class ChatListView(generics.ListCreateAPIView):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Chat.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def chat_list_view(request):
    if request.method == 'GET':
        chats = Chat.objects.filter(user=request.user).order_by('-created_at')
        return Response([{'id': chat.id, 'title': chat.title} for chat in chats])
    elif request.method == 'POST':
        title = request.data.get('title', 'New Chat')
        chat = Chat.objects.create(user=request.user, title=title)
        return Response({'id': chat.id, 'title': chat.title})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_messages_view(request, chat_id):
    try:
        chat = Chat.objects.get(id=chat_id, user=request.user)
    except Chat.DoesNotExist:
        return Response({'error': 'Chat not found'}, status=404)

    message_pairs = MessagePair.objects.filter(chat=chat).order_by('created_at')
    messages = []
    for pair in message_pairs:
        for message in pair.messages.all():
            messages.append({
                'id': message.id,
                'role': message.role,
                'contents': [{
                    'id': content.id,
                    'content_type': content.content_type,
                    'text_content': content.text_content,
                    'file_content': content.file_content.url if content.file_content else None,
                    'mime_type': content.mime_type,
                    'edited_at': content.edited_at,
                    'created_at': content.created_at
                } for content in message.contents.all()],
                'created_at': message.created_at,
                'message_pair': message.message_pair.id,
                'hidden': message.hidden
            })
    return Response(messages)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_chat_system_prompt(request, chat_id):
    try:
        chat = Chat.objects.get(id=chat_id, user=request.user)
        chat.system_prompt = request.data.get('system_prompt', '')
        chat.save()
        return Response({'status': 'success'})
    except Chat.DoesNotExist:
        return Response({'error': 'Chat not found'}, status=404)

class SavedSystemPromptListCreateView(generics.ListCreateAPIView):
    serializer_class = SystemPromptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedSystemPrompt.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SavedSystemPromptRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):    
    serializer_class = SystemPromptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedSystemPrompt.objects.filter(user=self.request.user)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_saved_system_prompt(request, prompt_id):
    try:
        prompt = SavedSystemPrompt.objects.get(id=prompt_id, user=request.user)
        prompt.title = request.data.get('title', prompt.title)
        prompt.prompt = request.data.get('prompt', prompt.prompt)
        prompt.save()
        return Response({'status': 'success'})
    except SavedSystemPrompt.DoesNotExist:
        return Response({'error': 'Saved system prompt not found'}, status=404)
    

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Chat.objects.filter(user=self.request.user)
        search = self.request.query_params.get('search', None)
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(message_pairs__messages__contents__text_content__icontains=search)
            ).distinct()
            
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        chat = self.get_object()
        chat.is_archived = True
        chat.save()
        return Response({'status': 'chat archived'})

    @action(detail=True, methods=['post'])
    def unarchive(self, request, pk=None):
        chat = self.get_object()
        chat.is_archived = False
        chat.save()
        return Response({'status': 'chat unarchived'})

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Project.objects.filter(user=self.request.user)
        search = self.request.query_params.get('search', None)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
            
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'])
    def knowledge(self, request, pk=None):
        project = self.get_object()
        knowledge_items = project.knowledge_items.all()
        serializer = ProjectKnowledgeSerializer(knowledge_items, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def chats(self, request, pk=None):
        project = self.get_object()
        chats = Chat.objects.filter(project=project).order_by('-created_at')
        serializer = ChatSerializer(chats, many=True)
        return Response(serializer.data)

class ProjectKnowledgeViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectKnowledgeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ProjectKnowledge.objects.filter(project__user=self.request.user)

    def perform_create(self, serializer):
        from .utils.token_counter import count_tokens
        content = self.request.data.get('content', '')
        token_count = count_tokens(content)
        serializer.save(token_count=token_count)

    @action(detail=True, methods=['patch'])
    def toggle(self, request, pk=None):
        knowledge = self.get_object()
        knowledge.include_in_chat = not knowledge.include_in_chat
        knowledge.save()
        return Response({'include_in_chat': knowledge.include_in_chat})

# Modify the existing chat_view to include project knowledge
def get_project_knowledge(chat):
    if not chat.project:
        return ""
    
    knowledge_items = chat.project.knowledge_items.filter(include_in_chat=True)
    if not knowledge_items:
        return ""
        
    knowledge_text = "\n\n".join([
        f"### {item.title} ###\n{item.content}"
        for item in knowledge_items
    ])
    
    return f"\nProject Knowledge:\n{knowledge_text}\n"

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_token_usage(request, chat_id):
    try:
        chat = Chat.objects.get(id=chat_id, user=request.user)
        stats = get_token_usage_stats(chat)
        return Response(stats)
    except Chat.DoesNotExist:
        return Response({'error': 'Chat not found'}, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_project_token_usage(request, project_id):
    try:
        project = Project.objects.get(id=project_id, user=request.user)
        total_tokens = project.total_knowledge_tokens
        return Response({
            'total_tokens': total_tokens,
            'max_tokens': 160000,
            'usage_percentage': (total_tokens / 160000) * 100
        })
    except Project.DoesNotExist:
        return Response({'error': 'Project not found'}, status=404)

class ProjectChatsView(generics.ListAPIView):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        return Chat.objects.filter(
            user=self.request.user,
            project_id=project_id
        ).order_by('-created_at')

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def edit_message(request, message_id):
    try:
        message = Message.objects.get(id=message_id)
        
        # Store original text if this is the first edit
        if not message.original_text:
            message.original_text = message.text
            
        message.text = request.data.get('text', message.text)
        message.token_count = count_tokens(message.text)
        message.save()
        
        # If this is a user message, remove the associated assistant message
        if message.role == 'user':
            message_pair = message.message_pair
            message_pair.messages.filter(role='assistant').delete()
            
        return Response({'status': 'success'})
    except Message.DoesNotExist:
        return Response({'error': 'Message not found'}, status=404)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def toggle_message_pair(request, pair_id):
    try:
        message_pair = MessagePair.objects.get(id=pair_id)
        messages = message_pair.messages.all()
        hidden = request.data.get('hidden', True)
        
        for message in messages:
            message.hidden = hidden
            message.save()
            
        return Response({'status': 'success'})
    except MessagePair.DoesNotExist:
        return Response({'error': 'Message pair not found'}, status=404)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_message_pair(request, pair_id):
    try:
        message_pair = MessagePair.objects.get(id=pair_id, chat__user=request.user)
        message_pair.delete()
        return Response({'message': 'Message pair deleted successfully'})
    except MessagePair.DoesNotExist:
        return Response({'error': 'Message pair not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=400)


# Memory Management Views

class MemoryPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserMemoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user memories"""
    permission_classes = [IsAuthenticated]
    pagination_class = MemoryPagination
    
    def get_queryset(self):
        queryset = UserMemory.objects.filter(user=self.request.user)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by tags
        tag_names = self.request.query_params.getlist('tags')
        if tag_names:
            queryset = queryset.filter(tags__name__in=tag_names).distinct()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Search in summary and raw content
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(summary__icontains=search) | Q(raw_content__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return UserMemoryListSerializer
        return UserMemorySerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Mark a memory as verified by the user"""
        memory = self.get_object()
        memory.is_verified = True
        memory.save()
        return Response({'message': 'Memory verified successfully'})
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle the active status of a memory"""
        memory = self.get_object()
        memory.is_active = not memory.is_active
        memory.save()
        status = 'activated' if memory.is_active else 'deactivated'
        return Response({'message': f'Memory {status} successfully'})


class MemoryTagViewSet(viewsets.ModelViewSet):
    """ViewSet for managing memory tags"""
    serializer_class = MemoryTagSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Return tags that are used by the current user's memories
        return MemoryTag.objects.filter(
            memories__user=self.request.user
        ).distinct().order_by('name')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def extract_memories_from_chat(request, chat_id):
    """Manually trigger memory extraction for a specific chat"""
    try:
        chat = Chat.objects.get(id=chat_id, user=request.user)
        
        memory_service = MemoryExtractionService()
        memories = memory_service.extract_memories_from_chat(chat)
        
        serializer = UserMemoryListSerializer(memories, many=True)
        
        return Response({
            'message': f'Extracted {len(memories)} memories from chat',
            'memories': serializer.data
        })
        
    except Chat.DoesNotExist:
        return Response({'error': 'Chat not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def memory_stats(request):
    """Get memory statistics for the user"""
    user = request.user
    
    total_memories = UserMemory.objects.filter(user=user).count()
    active_memories = UserMemory.objects.filter(user=user, is_active=True).count()
    verified_memories = UserMemory.objects.filter(user=user, is_verified=True).count()
    
    # Category breakdown
    category_stats = UserMemory.objects.filter(user=user, is_active=True).values('category').annotate(
        count=models.Count('id')
    ).order_by('-count')
    
    # Recent memories (last 7 days)
    from datetime import timedelta
    recent_cutoff = timezone.now() - timedelta(days=7)
    recent_memories = UserMemory.objects.filter(
        user=user, 
        created_at__gte=recent_cutoff
    ).count()
    
    return Response({
        'total_memories': total_memories,
        'active_memories': active_memories,
        'verified_memories': verified_memories,
        'recent_memories': recent_memories,
        'category_breakdown': list(category_stats),
        'verification_rate': round((verified_memories / total_memories * 100) if total_memories > 0 else 0, 1)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_context(request):
    """Get relevant user memories for context in conversations"""
    user = request.user
    category = request.query_params.get('category')
    limit = int(request.query_params.get('limit', 10))
    
    memory_service = MemoryExtractionService()
    memories = memory_service.get_relevant_memories(user, category, limit)
    
    # Mark as referenced
    if memories:
        memory_service.mark_memories_as_referenced(memories)
    
    serializer = UserMemoryListSerializer(memories, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_file_view(request):
    file = request.FILES.get('file')
    if not file:
        return Response({'error': 'No file provided'}, status=400)
    
    try:
        mime_type = validate_mime_type(file)
        
        if mime_type.startswith('image/'):
            validate_image_size(file)
        else:
            validate_document_size(file)
            
        return Response({
            'valid': True,
            'mime_type': mime_type
        })
    except ValidationError as e:
        return Response({
            'valid': False,
            'error': str(e)
        }, status=400)