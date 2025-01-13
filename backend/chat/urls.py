# chat/urls.py
from django.urls import path, include
from .views import (
    ChatListView, ChatMessagesListView, ChatDetailView, claude_chat_view,
    update_chat_system_prompt, SavedSystemPromptListCreateView,
    SavedSystemPromptRetrieveUpdateDestroyView, upload_file, get_attachments,
    delete_attachment_view, get_file_content, ProjectViewSet, ProjectKnowledgeViewSet,
    ProjectChatsView, get_chat_token_usage, edit_message, toggle_message_pair,
    delete_message_pair,
)
from rest_framework.routers import DefaultRouter

# Set up the router
router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'knowledge', ProjectKnowledgeViewSet, basename='knowledge')

urlpatterns = [
    # Include router URLs first
    path('', include(router.urls)),
    
    # Chat related URLs
    path('chat-list/', ChatListView.as_view(), name='chat-list'),
    path('chats/<int:chat_id>/messages/', ChatMessagesListView.as_view(), name='chat-messages-list'),
    path('chats/<int:pk>/', ChatDetailView.as_view(), name='chat-detail'),
    path('claude/', claude_chat_view, name='claude-chat'),
    path('chats/<int:chat_id>/system-prompt/', update_chat_system_prompt),
    
    # Message management
    path('messages/<int:message_id>/edit/', edit_message, name='edit-message'),
    path('message-pairs/<int:pair_id>/', delete_message_pair, name='delete-message-pair'),
    path('message-pairs/<int:pair_id>/toggle/', toggle_message_pair, name='toggle-message-pair'),
    
    # System prompts
    path('saved-system-prompts/', SavedSystemPromptListCreateView.as_view()),
    path('saved-system-prompts/<int:pk>/', SavedSystemPromptRetrieveUpdateDestroyView.as_view()),
    
    # File attachments
    path('chats/<int:chat_id>/upload/', upload_file, name='upload-file'),
    path('chats/<int:chat_id>/attachments/', get_attachments, name='get-attachments'),
    path('attachments/<int:attachment_id>/', delete_attachment_view, name='delete-attachment'),
    path('attachments/<int:attachment_id>/content/', get_file_content, name='get-file-content'),
    
    # Project chats
    path('projects/<int:project_id>/chats/', ProjectChatsView.as_view(), name='project-chats'),
    
    # Token usage
    path('chats/<str:chat_id>/tokens/', get_chat_token_usage, name='chat-tokens'),
]
