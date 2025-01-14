from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import StreamingHttpResponse
from rest_framework import generics, permissions
from .models import Chat, MessagePair, Message, SavedSystemPrompt, Project, ProjectKnowledge
from .serializers import ChatSerializer, MessageSerializer,SystemPromptSerializer, ProjectSerializer, ProjectKnowledgeSerializer
import os
import json
import boto3
from .file_handlers import handle_file_upload, get_file_contents, delete_attachment
from .models import Attachment
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.decorators import action
from .utils.token_counter import count_tokens,get_token_usage_stats
from .services.chat_service import ChatService

# Initialize Bedrock client
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-west-2",
    aws_access_key_id=os.getenv("AWS_BEDROCK_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_BEDROCK_SECRET_ACCESS_KEY")
)   
CLAUDE_35_SONNET_V1_0 = "anthropic.claude-3-5-sonnet-20240620-v1:0"
CLAUDE_35_SONNET_V2 = "anthropic.claude-3-5-sonnet-20241022-v2:0"


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def claude_chat_view(request):
    print("request", "I got a request")
    chat_service = ChatService()

    # Validate required fields
    if not request.data.get('message') and not request.FILES:
        print("error, no message or files")
        return Response(
            {'error': 'Either message or files must be provided'}, 
            status=400
        )

    try:
        # Extract request data
        chat_id = request.data.get('chat_id')
        message_text = request.data.get('message', '')
        project_id = request.data.get('project_id')
        files = request.FILES.getlist('files', [])
        system_prompt = request.data.get('system_prompt', '')
        
        # Create or get existing chat
        chat = chat_service.create_or_get_chat(request.user, chat_id, message_text, project_id)
        
        # Create message pair
        message_pair = MessagePair.objects.create(chat=chat)
        
        # Create user message with files
        for file in files:
            message_type = 'image' if file.content_type.startswith('image/') else 'file'
            message = Message.objects.create(
                message_pair=message_pair,
                role="user",
                type=message_type,
                text=message_text if message_type == 'text' else None,
                image=file if message_type == 'image' else None,
                file=file if message_type == 'file' else None,
                file_type=file.content_type
            )
        
        # Create text message if there's text content
        if message_text and not files:
            Message.objects.create(
                message_pair=message_pair,
                role="user",
                type='text',
                text=message_text
            )

        # Prepare message history with context
        messages = chat_service.prepare_message_history(chat, message_text, files)
        
        # Create request body and invoke model
        body = chat_service.create_chat_request_body(messages, chat)
        
        assistant_response_text = []
        print("body", body)
        def stream_response(response):
            for chunk in response['body']:
                chunk_data = json.loads(chunk['chunk']['bytes'].decode())
                if chunk_data['type'] == 'content_block_delta':
                    content = chunk_data['delta']['text']
                    print(content)
                    assistant_response_text.append(content)
                    yield json.dumps({'type': 'text', 'content': content}) + '\n'
            print("assistant_response_text", assistant_response_text)
            # Save complete response
            complete_response = ''.join(assistant_response_text)
            print("complete_response", complete_response)
            Message.objects.create(
                message_pair=message_pair,
                role="assistant",
                text=complete_response,
                type='text'
            )
            yield json.dumps({'type': 'chat_id', 'content': str(chat.id)}) + '\n'

        response = chat_service.invoke_model(body)
        print("response", response)

        return StreamingHttpResponse(stream_response(response), content_type='text/event-stream')

    except Chat.DoesNotExist:
        return Response(
            {'error': 'Chat not found'}, 
            status=404
        )
    except ValueError as e:
        return Response(
            {'error': str(e)}, 
            status=400
        )
    except Exception as e:
        print(f"Error in claude_chat_view: {str(e)}")
        return Response(
            {'error': f'An unexpected error occurred: {str(e)}'}, 
            status=500
        )

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
        return Response({
            'system_prompt': chat.system_prompt,
            'messages': [{
                'id': message['id'],
                'message_pair': message['message_pair'],
                'chat': chat.id,
                'hidden': message['hidden'],
                'edited_at': message['edited_at'],
                'original_text': message['original_text'],
                'role': message['role'],
                'type': message['type'],
                'content': message['text'] if message['type'] == 'text' else message['image'],
            } for message in serializer.data]
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
                'role' : message.role,
                'type' : message.type,
                'text' : message.text if message.type == 'text' else None,
                'image':  message.image if message.type == 'image' else None,
                'created_at' : message.created_at
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
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_file(request, chat_id):
    file = request.FILES.get('file')
    if not file:
        return Response({'error': 'No file provided'}, status=400)
    
    success = handle_file_upload(file, chat_id)
    if success:
        return Response({'message': 'File uploaded successfully'})
    else:
        return Response({'error': 'File upload failed'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_attachments(request, chat_id):
    attachments = Attachment.objects.filter(chat_id=chat_id)
    data = [{
        'id': attachment.id,
        'name': attachment.original_name,
        'url': attachment.file.url
    } for attachment in attachments]
    return Response(data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_attachment_view(request, attachment_id):
    success = delete_attachment(attachment_id)
    if success:
        return Response({'message': 'Attachment deleted successfully'})
    else:
        return Response({'error': 'Failed to delete attachment'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_file_content(request, attachment_id):
    try:
        attachment = Attachment.objects.get(id=attachment_id)
        content = get_file_contents(attachment.file.path)
        return Response({'content': content})
    except Attachment.DoesNotExist:
        return Response({'error': 'Attachment not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)

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
        message_pair = MessagePair.objects.get(id=pair_id)
        message_pair.delete()
        return Response({'status': 'success'})
    except MessagePair.DoesNotExist:
        return Response({'error': 'Message pair not found'}, status=404)