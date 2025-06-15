#!/usr/bin/env python
"""
Test script to verify memory integration in chat
"""
import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aiassistant.settings')
django.setup()

from django.contrib.auth import get_user_model
from chat.models import Chat, UserMemory, MemoryTag
from chat.services.chat_service import ChatService
from chat.services.memory_service import MemoryExtractionService

User = get_user_model()

def test_memory_integration():
    print("Testing memory integration...")
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    
    # Create a test chat first (required for UserMemory)
    chat = Chat.objects.create(
        user=user,
        title="Test Chat",
        system_prompt=""
    )
    
    # Create some test memories
    memory_service = MemoryExtractionService()
    
    # Create a test memory
    memory1 = UserMemory.objects.create(
        user=user,
        chat=chat,  # Now we include the chat reference
        summary="User is a Python developer working on AI projects",
        raw_content="I'm a Python developer and I've been working on AI and machine learning projects for the past 3 years.",
        confidence_score=0.9,
        category="work",
        is_active=True
    )
    
    # Add tags
    tag1, _ = MemoryTag.objects.get_or_create(name="python", defaults={'color': '#3776ab'})
    tag2, _ = MemoryTag.objects.get_or_create(name="ai", defaults={'color': '#ff6b6b'})
    memory1.tags.add(tag1, tag2)
    
    memory2 = UserMemory.objects.create(
        user=user,
        chat=chat,  # Now we include the chat reference
        summary="User prefers clean, well-documented code",
        raw_content="I always prefer clean, well-documented code that follows best practices.",
        confidence_score=0.8,
        category="preferences",
        is_active=True
    )
    
    tag3, _ = MemoryTag.objects.get_or_create(name="coding", defaults={'color': '#4ecdc4'})
    memory2.tags.add(tag3)
    
    print(f"Created {UserMemory.objects.filter(user=user).count()} test memories")
    
    # Test memory retrieval
    test_message = "Can you help me write a Python function?"
    relevant_memories = memory_service.get_relevant_memories_for_context(
        user=user,
        current_message=test_message,
        limit=5
    )
    
    print(f"Found {len(relevant_memories)} relevant memories for message: '{test_message}'")
    for memory in relevant_memories:
        print(f"  - {memory.summary} (confidence: {memory.confidence_score})")
    
    # Test chat service integration
    chat_service = ChatService()
    messages = chat_service.prepare_message_history(chat, test_message)
    
    print(f"\nPrepared {len(messages)} messages for Claude")
    for i, msg in enumerate(messages):
        content_text = ""
        if isinstance(msg.get('content'), list) and len(msg['content']) > 0:
            content_text = msg['content'][0].get('text', '')[:100] + "..."
        print(f"  {i+1}. {msg['role']}: {content_text}")
    
    # Test memory formatting
    memory_context = memory_service.format_memories_for_context(relevant_memories)
    print(f"\nFormatted memory context:\n{memory_context[:200]}...")
    
    print("\n✅ Memory integration test completed successfully!")

if __name__ == "__main__":
    test_memory_integration() 