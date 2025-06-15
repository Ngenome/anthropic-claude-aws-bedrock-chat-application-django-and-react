# chat/urls.py
from django.urls import path, include
from .views import (
    ChatViewSet, ProjectViewSet, ProjectKnowledgeViewSet,
    ChatListView, ChatMessagesListView, ChatDetailView, claude_chat_view,
    update_chat_system_prompt, SavedSystemPromptListCreateView,
    SavedSystemPromptRetrieveUpdateDestroyView,
    ProjectChatsView, get_chat_token_usage, edit_message, toggle_message_pair,
    delete_message_pair, validate_file_view, UserMemoryViewSet, MemoryTagViewSet,
    extract_memories_from_chat, memory_stats, get_user_context
)
from rest_framework.routers import DefaultRouter

# Set up the router
router = DefaultRouter()
router.register(r'chats', ChatViewSet, basename='chat')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'knowledge', ProjectKnowledgeViewSet, basename='knowledge')
router.register(r'memories', UserMemoryViewSet, basename='memory')
router.register(r'memory-tags', MemoryTagViewSet, basename='memory-tag')

urlpatterns = [
    # Include router URLs first
    path('', include(router.urls)),
    
    # Chat related URLs
    path('chat/', claude_chat_view, name='chat'),
    path('chats/<str:pk>/', ChatDetailView.as_view(), name='chat-detail'),
    path('chats/<str:chat_id>/messages/', ChatMessagesListView.as_view(), name='chat-messages'),
    path('messages/<str:message_id>/edit/', edit_message, name='edit-message'),
    path('message-pairs/<str:pair_id>/toggle/', toggle_message_pair, name='toggle-message-pair'),
    path('message-pairs/<str:pair_id>/delete/', delete_message_pair, name='delete-message-pair'),
    
    # System prompts
    path('saved-system-prompts/', SavedSystemPromptListCreateView.as_view()),
    path('saved-system-prompts/<str:pk>/', SavedSystemPromptRetrieveUpdateDestroyView.as_view()),
    
    # Project chats
    path('projects/<str:pk>/chats/', ProjectChatsView.as_view(), name='project-chats'),
    
    # Token usage
    path('chats/<str:chat_id>/tokens/', get_chat_token_usage, name='chat-tokens'),
    
    # Memory related URLs
    path('chats/<str:chat_id>/extract-memories/', extract_memories_from_chat, name='extract-memories'),
    path('memory/stats/', memory_stats, name='memory-stats'),
    path('memory/context/', get_user_context, name='user-context'),

    # File validation
    path('validate-file/', validate_file_view, name='validate-file'),
]
