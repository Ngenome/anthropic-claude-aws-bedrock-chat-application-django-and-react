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

# Initialize Bedrock client
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1",
    aws_access_key_id=os.getenv("AWS_BEDROCK_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_BEDROCK_SECRET_ACCESS_KEY")
)


def stream_response(response):
    for chunk in response['body']:
        chunk_data = json.loads(chunk['chunk']['bytes'].decode())
        # if the chunk is a message start ignore it, if it is a content block start, ignore it, if it is a content block delta, yield the text content
        if chunk_data['type'] == 'content_block_delta':
            print(chunk_data['delta']['text'])
            yield json.dumps({'type': 'text', 'content': chunk_data['delta']['text']} ) + '\n'
            

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def claude_chat_view(request):
    chat_id = request.data.get('chat_id')
    message_text = request.data.get('message')
    project_id = request.data.get('project_id')
    attachment_ids = request.data.get('attachment_ids', [])
    
    if chat_id is None or chat_id == 'new':
        try:
            title = message_text[:15] + "..."
            project = None
            if project_id:
                try:
                    project = Project.objects.get(id=project_id, user=request.user)
                except Project.DoesNotExist:
                    return Response({'error': 'Project not found'}, status=404)
            
            chat = Chat.objects.create(
                title=title, 
                user=request.user,
                project=project
            )
        except Exception as e:
            print(f"Error in claude_chat_view: {str(e)}")
            return Response({'error': str(e)}, status=500)
    else:
        try:
            chat = Chat.objects.get(id=chat_id, user=request.user)
        except Chat.DoesNotExist:
            return Response({'error': 'Chat not found'}, status=404)

    message_pair = MessagePair.objects.create(chat=chat)
    Message.objects.create(
        message_pair=message_pair,
        role="user",
        text=message_text,
        type='text'
    )

    # Get project knowledge and instructions if chat is tied to a project
    project_context = ""
    if chat.project:
        knowledge_items = chat.project.knowledge_items.filter(include_in_chat=True)
        if knowledge_items:
            knowledge_text = "\n\n".join([
                f"### {item.title} ###\n{item.content}"
                for item in knowledge_items
            ])
            project_context = f"\nProject Knowledge:\n{knowledge_text}\n"
        
        if chat.project.instructions:
            project_context = f"Project Instructions:\n{chat.project.instructions}\n\n{project_context}"

    # Add project context to the message if it exists
    if project_context:
        message_text = f"{project_context}\n\nUser Message:\n{message_text}"

    history_message_pairs = MessagePair.objects.filter(chat=chat).order_by('date')
    messages = []
    for pair in history_message_pairs:
        user_message = pair.messages.filter(role="user").first()
        assistant_message = pair.messages.filter(role="assistant").first()
        
        if user_message:
            messages.append({
                'role': 'user',
                'content': [{'type': 'text', 'text': user_message.text}]
            })
            if user_message.type == 'image':
                messages[-1]['content'].append({
                    'type': 'image',
                    'source': {
                        'type': 'base64',
                        'media_type': 'image/jpeg',
                        'data': user_message.image
                    }
                })
        
        if assistant_message:
            messages.append({
                'role': 'assistant',
                'content': [{'type': 'text', 'text': assistant_message.text}]
            })
        

    # if image:
    #     messages[-1]['content'].append({
    #         'type': 'image',
    #         'source': {
    #             'type': 'base64',
    #             'media_type': 'image/jpeg',
    #             'data': image
    #         }
    #     })
    #     Message.objects.create(
    #         message_pair=message_pair,
    #         role='user',
    #         type='image',
    #         image=image
    #     )
    file_contents = []
    for attachment_id in attachment_ids:
        try:
            attachment = Attachment.objects.get(id=attachment_id)
            content = get_file_contents(attachment.file.path)
            file_contents.append(f"File: {attachment.original_name}\n\n{content}\n\n")
        except Attachment.DoesNotExist:
            continue
    

    if file_contents:
        file_context = "Here are the contents of the attached files:\n\n" + "\n".join(file_contents)
        # to the last message (if it is a user message), append the file context
        if messages[-1]['role'] == 'user':
            messages[-1]['content'].append({
                'type': 'text',
                'text': file_context
            })

    # Get project knowledge if chat is tied to a project
    project_knowledge = get_project_knowledge(chat) if chat else ""
    
    # Modify the message construction to include project knowledge
    if project_knowledge:
        messages[-1]['content'].append({
            'type': 'text',
            'text': project_knowledge
        })

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "messages": messages
    })
    assistant_response_text = []
    def stream_response(response):
        for chunk in response['body']:
            chunk_data = json.loads(chunk['chunk']['bytes'].decode())
            if chunk_data['type'] == 'content_block_delta':
                content = chunk_data['delta']['text']
                assistant_response_text.append(content)
                yield json.dumps({'type': 'text', 'content': content}) + '\n'
                # print(chunk_data['delta']['text'])
        
        # After streaming is complete, save the assistant's response to the database
        complete_response = ''.join(assistant_response_text)
        Message.objects.create(
            message_pair=message_pair,
            role="assistant",
            text=complete_response,
            type='text'
        )
        yield json.dumps({'type': 'chat_id', 'content': str(chat.id)}) + '\n'

    try:
        response = bedrock_runtime.invoke_model_with_response_stream(
            body=body,
            modelId="anthropic.claude-3-5-sonnet-20240620-v1:0"
            
        )
        return StreamingHttpResponse(stream_response(response), content_type='text/event-stream')

    except Exception as e:
        # raise the exception
        raise e

class ChatMessagesListView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        chat_id = self.kwargs['chat_id']
        message_pairs = MessagePair.objects.filter(chat_id=chat_id).order_by('date')
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
        chats = Chat.objects.filter(user=request.user).order_by('-date')
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
        return Chat.objects.filter(user=self.request.user).order_by('-date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def chat_list_view(request):
    if request.method == 'GET':
        chats = Chat.objects.filter(user=request.user).order_by('-date')
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

    message_pairs = MessagePair.objects.filter(chat=chat).order_by('date')
    messages = []
    for pair in message_pairs:
        for message in pair.messages.all():
            messages.append({ 
                'role' : message.role,
                'type' : message.type,
                'text' : message.text if message.type == 'text' else None,
                'image':  message.image if message.type == 'image' else None,
                'date' : message.date
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
        chats = Chat.objects.filter(project=project).order_by('-date')
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
        ).order_by('-date')