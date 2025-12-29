"""
Memory Manager
Orchestrates short-term and long-term memory for Logic

Design:
- Short-term: Last 5 exchanges (fast)
- Long-term: Patterns from history (smart)
- Minimal tokens: Only send what's needed
"""

from app.logic.memory.short_memory import ShortMemory
from app.logic.memory.long_memory import LongMemory

class MemoryManager:
    """
    Central memory coordinator
    
    Usage:
        memory = MemoryManager(user_id)
        context = memory.get_context(current_message)
        memory.save_exchange(user_msg, logic_response)
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.short_memory = ShortMemory(user_id)
        self.long_memory = LongMemory(user_id)
    
    def get_context(self, current_message: str) -> str:
        """
        Get relevant context for Logic
        
        Returns compact string for AI prompt (~200 tokens)
        """
        
        # 1. Get recent exchanges (short-term)
        recent = self.short_memory.get_recent_exchanges(limit=3)
        
        # 2. Get relevant patterns (long-term)
        patterns = self.long_memory.get_relevant_patterns(current_message)
        
        # 3. Build compact context string
        context_parts = []
        
        # Recent conversation
        if recent:
            context_parts.append("RECENT CONVERSATION:")
            for exchange in recent[-3:]:  # Last 3 only
                context_parts.append(f"  User: {exchange['user']}")
                context_parts.append(f"  You: {exchange['logic']}")
        
        # Learned patterns
        if patterns:
            context_parts.append("\nLEARNED PATTERNS:")
            for pattern in patterns[:3]:  # Top 3 only
                context_parts.append(f"  - {pattern}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def save_exchange(
        self, 
        user_message: str, 
        logic_response: str,
        metadata: dict = None
    ):
        """
        Save conversation exchange to both memories
        
        Args:
            user_message: What user said
            logic_response: What Logic responded
            metadata: Additional context (action type, contact, etc.)
        """
        
        # Save to short-term (fast, temporary)
        self.short_memory.add_exchange(user_message, logic_response)
        
        # Save to long-term (persistent database)
        self.long_memory.save_conversation(
            user_message=user_message,
            logic_response=logic_response,
            metadata=metadata
        )