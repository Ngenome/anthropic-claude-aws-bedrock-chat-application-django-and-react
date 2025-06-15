import json
import boto3
import os
from typing import List, Dict, Optional
from django.utils import timezone
from ..models import UserMemory, MemoryTag, Chat, MessagePair
from ..utils.token_counter import count_tokens


class MemoryExtractionService:
    """Service for extracting and managing user memories from conversations"""
    
    def __init__(self):
        self.bedrock_runtime = boto3.client(
            service_name="bedrock-runtime",
            region_name="us-west-2",
            aws_access_key_id=os.getenv("AWS_BEDROCK_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_BEDROCK_SECRET_ACCESS_KEY")
        )
        self.haiku_model = "anthropic.claude-3-5-haiku-20241022-v1:0"
    
    def extract_memories_from_chat(self, chat: Chat, message_pair: MessagePair = None) -> List[UserMemory]:
        """
        Extract memories from a complete chat or specific message pair
        """
        # Get conversation text
        conversation_text = self._get_conversation_text(chat, message_pair)
        
        if not conversation_text.strip():
            return []
        
        # Extract memories using Claude Haiku
        extracted_data = self._extract_with_claude(conversation_text)
        
        if not extracted_data:
            return []
        
        # Save memories to database
        memories = []
        for memory_data in extracted_data:
            memory = self._create_memory(
                user=chat.user,
                chat=chat,
                message_pair=message_pair,
                memory_data=memory_data
            )
            if memory:
                memories.append(memory)
        
        return memories
    
    def _get_conversation_text(self, chat: Chat, message_pair: MessagePair = None) -> str:
        """Extract text content from conversation"""
        conversation_parts = []
        
        if message_pair:
            # Extract from specific message pair
            pairs = [message_pair]
        else:
            # Extract from entire chat (last 10 message pairs to avoid token limits)
            pairs = chat.message_pairs.order_by('-created_at')[:10]
        
        for pair in reversed(list(pairs)):
            for message in pair.messages.all():
                role_prefix = "User: " if message.role == "user" else "Assistant: "
                
                # Get text content from all message contents
                text_contents = []
                for content in message.contents.filter(content_type='text'):
                    if content.text_content:
                        text_contents.append(content.text_content)
                
                if text_contents:
                    conversation_parts.append(f"{role_prefix}{' '.join(text_contents)}")
        
        return "\n\n".join(conversation_parts)
    
    def _extract_with_claude(self, conversation_text: str) -> List[Dict]:
        """Use Claude Haiku to extract user information"""
        
        system_prompt = """You are a memory extraction AI. Your job is to analyze conversations and extract meaningful information about the user that could be useful for future interactions.

Extract information like:
- Personal details (name, location, profession, etc.)
- Preferences and interests
- Goals and aspirations
- Work/professional information
- Relationships and family
- Lifestyle and habits
- Technical skills and knowledge
- Important context about their life

For each piece of information you extract, provide:
1. A clear, concise summary (2-3 sentences max)
2. The raw content that supports this information
3. A confidence score (0.0 to 1.0)
4. A category from: personal, preferences, work, goals, relationships, lifestyle, technical, other
5. Relevant tags (single words that describe the content)

Only extract information that is explicitly mentioned or clearly implied. Don't make assumptions.

Return your response as a JSON array of objects with this structure:
{
  "summary": "Clear summary of the information",
  "raw_content": "The actual text that contains this information", 
  "confidence_score": 0.85,
  "category": "personal",
  "tags": ["programming", "python", "ai"]
}

If no meaningful user information is found, return an empty array."""

        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "temperature": 0.1,
                "system": system_prompt,
                "messages": [
                    {
                        "role": "user",
                        "content": f"Please analyze this conversation and extract user information:\n\n{conversation_text}"
                    }
                ]
            })
            
            response = self.bedrock_runtime.invoke_model(
                body=body,
                modelId=self.haiku_model,
                contentType="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            
            # Parse the JSON response
            try:
                extracted_data = json.loads(content)
                if isinstance(extracted_data, list):
                    return extracted_data
                else:
                    return []
            except json.JSONDecodeError:
                print(f"Failed to parse Claude response as JSON: {content}")
                return []
                
        except Exception as e:
            print(f"Error extracting memories with Claude: {e}")
            return []
    
    def _create_memory(self, user, chat: Chat, message_pair: MessagePair, memory_data: Dict) -> Optional[UserMemory]:
        """Create a UserMemory object from extracted data"""
        try:
            # Validate required fields
            if not memory_data.get('summary') or not memory_data.get('raw_content'):
                return None
            
            # Check for duplicate memories
            existing_memory = UserMemory.objects.filter(
                user=user,
                summary=memory_data['summary'][:200],  # Check first 200 chars
                category=memory_data.get('category', 'other')
            ).first()
            
            if existing_memory:
                # Update existing memory if confidence is higher
                new_confidence = float(memory_data.get('confidence_score', 0.8))
                if new_confidence > existing_memory.confidence_score:
                    existing_memory.confidence_score = new_confidence
                    existing_memory.raw_content = memory_data['raw_content']
                    existing_memory.updated_at = timezone.now()
                    existing_memory.save()
                return existing_memory
            
            # Create new memory
            memory = UserMemory.objects.create(
                user=user,
                chat=chat,
                source_message_pair=message_pair,
                summary=memory_data['summary'],
                raw_content=memory_data['raw_content'],
                confidence_score=float(memory_data.get('confidence_score', 0.8)),
                category=memory_data.get('category', 'other')
            )
            
            # Add tags
            tags = memory_data.get('tags', [])
            if tags:
                self._add_tags_to_memory(memory, tags)
            
            return memory
            
        except Exception as e:
            print(f"Error creating memory: {e}")
            return None
    
    def _add_tags_to_memory(self, memory: UserMemory, tag_names: List[str]):
        """Add tags to a memory, creating tags if they don't exist"""
        for tag_name in tag_names:
            if isinstance(tag_name, str) and tag_name.strip():
                tag_name = tag_name.strip().lower()[:50]  # Normalize and limit length
                tag, created = MemoryTag.objects.get_or_create(
                    name=tag_name,
                    defaults={'color': '#3B82F6'}
                )
                memory.tags.add(tag)
    
    def get_relevant_memories(self, user, category: str = None, limit: int = 10) -> List[UserMemory]:
        """Get relevant memories for a user, optionally filtered by category"""
        queryset = UserMemory.objects.filter(
            user=user,
            is_active=True
        ).order_by('-last_referenced', '-created_at')
        
        if category:
            queryset = queryset.filter(category=category)
        
        return list(queryset[:limit])
    
    def mark_memories_as_referenced(self, memories: List[UserMemory]):
        """Mark memories as recently referenced"""
        memory_ids = [memory.id for memory in memories]
        UserMemory.objects.filter(id__in=memory_ids).update(
            last_referenced=timezone.now()
        )

    def get_relevant_memories_for_context(self, user, current_message: str, limit: int = 5) -> List[UserMemory]:
        """
        Get memories relevant to the current conversation context
        Uses keyword matching and relevance scoring
        """
        if not current_message.strip():
            return self.get_relevant_memories(user, limit=limit)
        
        # Get all active memories for the user
        all_memories = UserMemory.objects.filter(
            user=user,
            is_active=True,
            confidence_score__gte=0.5  # Only include high-confidence memories
        ).prefetch_related('tags')
        
        # Score memories based on relevance to current message
        scored_memories = []
        message_lower = current_message.lower()
        message_words = set(message_lower.split())
        
        for memory in all_memories:
            score = 0
            
            # Check for keyword matches in summary
            summary_words = set(memory.summary.lower().split())
            keyword_matches = len(message_words.intersection(summary_words))
            score += keyword_matches * 2
            
            # Check for tag matches
            memory_tags = {tag.name.lower() for tag in memory.tags.all()}
            tag_matches = len(message_words.intersection(memory_tags))
            score += tag_matches * 3
            
            # Check for partial matches in summary and raw content
            for word in message_words:
                if len(word) > 3:  # Only check meaningful words
                    if word in memory.summary.lower():
                        score += 1
                    if word in memory.raw_content.lower():
                        score += 0.5
            
            # Boost recently referenced memories
            if memory.last_referenced:
                days_since_referenced = (timezone.now() - memory.last_referenced).days
                if days_since_referenced < 7:
                    score += 2
                elif days_since_referenced < 30:
                    score += 1
            
            # Include confidence score
            score += memory.confidence_score
            
            if score > 0:
                scored_memories.append((memory, score))
        
        # Sort by score and return top memories
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        relevant_memories = [memory for memory, score in scored_memories[:limit]]
        
        # Mark these memories as referenced
        if relevant_memories:
            self.mark_memories_as_referenced(relevant_memories)
        
        return relevant_memories

    def format_memories_for_context(self, memories: List[UserMemory]) -> str:
        """
        Format memories for inclusion in chat context
        """
        if not memories:
            return ""
        
        formatted_memories = []
        for memory in memories:
            tags_str = ", ".join([tag.name for tag in memory.tags.all()[:3]])  # Limit to 3 tags
            memory_text = f"- {memory.summary}"
            if tags_str:
                memory_text += f" (Tags: {tags_str})"
            formatted_memories.append(memory_text)
        
        return f"""<user_context>
Based on our previous conversations, here's what I know about you:

{chr(10).join(formatted_memories)}
</user_context>""" 