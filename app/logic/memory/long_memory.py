"""
Long-Term Memory
Learns patterns from conversation history

Storage: Postgres (logic_conversations table)
"""

from app.backend.supabase_client import supabase
from datetime import datetime, timedelta
from typing import List, Dict
import json
import uuid

class LongMemory:
    """
    Persistent memory and pattern learning
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
    
    def save_conversation(
        self, 
        user_message: str, 
        logic_response: str,
        metadata: dict = None
    ):
        """
        Save conversation to database
        
        Args:
            user_message: What user said
            logic_response: What Logic responded
            metadata: Additional context (action, contact, etc.)
        """
        
        try:
            data = {
                'id': str(uuid.uuid4()),
                'user_id': self.user_id,
                'user_message': user_message,
                'logic_response': logic_response,
                'tokens_used': 0,  # Could track from Groq response
                'context': json.dumps(metadata) if metadata else None
            }
            
            result = supabase.insert('logic_conversations', data)
            
            if not result['success']:
                print(f"⚠️ Failed to save conversation: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ Error saving conversation: {e}")
    
    def get_relevant_patterns(self, current_message: str) -> List[str]:
        """
        Extract relevant patterns from history
        
        Phase 1: Simple keyword matching
        Phase 2: Vector similarity (later)
        
        Returns:
            List of relevant pattern strings
        """
        
        patterns = []
        
        # Get recent history (last 30 days)
        history = self._get_recent_history(days=30)
        
        if not history:
            return patterns
        
        # Extract patterns
        action_patterns = self._extract_action_patterns(history)
        contact_patterns = self._extract_contact_patterns(history, current_message)
        
        patterns.extend(action_patterns)
        patterns.extend(contact_patterns)
        
        return patterns[:3]  # Top 3 only
    
    def _get_recent_history(self, days: int = 30) -> List[Dict]:
        """Get conversations from last N days"""
        
        try:
            conversations = supabase.select(
                'logic_conversations',
                filters={'user_id': self.user_id}
            )
            
            # Filter by date
            cutoff = datetime.now() - timedelta(days=days)
            recent = [
                c for c in conversations
                if datetime.fromisoformat(c['created_at'].replace('Z', '+00:00')) > cutoff
            ]
            
            return recent
            
        except Exception as e:
            print(f"Error getting history: {e}")
            return []
    
    def _extract_action_patterns(self, history: List[Dict]) -> List[str]:
        """
        Learn action patterns
        
        Example: "You often call Sarah on weekday mornings"
        """
        
        patterns = []
        
        # Count actions per contact
        action_counts = {}
        
        for conv in history:
            try:
                context = json.loads(conv.get('context') or '{}')
                action = context.get('action_type')
                contact = context.get('contact_name')
                
                if action and contact:
                    key = f"{action}:{contact}"
                    action_counts[key] = action_counts.get(key, 0) + 1
            except:
                continue
        
        # Find frequent patterns (3+ occurrences)
        for key, count in action_counts.items():
            if count >= 3:
                action, contact = key.split(':')
                patterns.append(f"You often {action} {contact}")
        
        return patterns
    
    def _extract_contact_patterns(
        self, 
        history: List[Dict], 
        current_message: str
    ) -> List[str]:
        """
        Learn contact-specific patterns
        
        Example: "When you say 'Sarah', you usually mean Sarah Johnson"
        """
        
        patterns = []
        
        # Extract contact mentions from current message
        msg_lower = current_message.lower()
        
        # Find contacts mentioned in history
        mentioned_contacts = {}
        
        for conv in history:
            try:
                context = json.loads(conv.get('context') or '{}')
                contact_name = context.get('contact_name')
                
                if contact_name and contact_name.lower() in msg_lower:
                    mentioned_contacts[contact_name] = mentioned_contacts.get(contact_name, 0) + 1
            except:
                continue
        
        # Find most frequently used contact for ambiguous names
        if mentioned_contacts:
            most_frequent = max(mentioned_contacts.items(), key=lambda x: x[1])
            if most_frequent[1] >= 2:
                patterns.append(f"You usually mean {most_frequent[0]}")
        
        return patterns
    
    def get_disambiguation_preference(self, ambiguous_name: str) -> str:
        """
        Get user's preferred contact when name is ambiguous
        
        Args:
            ambiguous_name: Name like "Sarah"
            
        Returns:
            Full contact name user typically means, or None
        """
        
        history = self._get_recent_history(days=90)
        
        # Count which "Sarah" user contacted most
        contact_counts = {}
        
        for conv in history:
            try:
                context = json.loads(conv.get('context') or '{}')
                contact_name = context.get('contact_name', '')
                
                if ambiguous_name.lower() in contact_name.lower():
                    contact_counts[contact_name] = contact_counts.get(contact_name, 0) + 1
            except:
                continue
        
        if contact_counts:
            # Return most frequent
            return max(contact_counts.items(), key=lambda x: x[1])[0]
        
        return None