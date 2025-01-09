import os
from functools import lru_cache
from transformers import GPT2TokenizerFast

tokenizer = GPT2TokenizerFast.from_pretrained("Xenova/claude-tokenizer")

def count_tokens(text: str) -> int:
    return len(tokenizer.encode(text))

def validate_token_count(text: str, max_tokens: int = 160000) -> bool:  # 80% of 200k
    """Returns True if token count is within limit"""
    token_count = count_tokens(text)
    return token_count <= max_tokens

def get_token_usage_stats(chat):
    """Get detailed token usage stats for a chat"""
    message_tokens = sum(
        message.token_count 
        for pair in chat.message_pairs.all()
        for message in pair.messages.all()
    )
    
    project_tokens = chat.project.total_knowledge_tokens if chat.project else 0
    total_tokens = message_tokens + project_tokens
    
    return {
        'message_tokens': message_tokens,
        'project_tokens': project_tokens,
        'total_tokens': total_tokens,
        'max_tokens': 200000,
        'usage_percentage': (total_tokens / 200000) * 100
    } 