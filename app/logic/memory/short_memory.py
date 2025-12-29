"""
Short-Term Memory
Stores recent conversation exchanges (last 30 minutes)

Storage: In-memory Python dict (simple, fast)
Alternative: Redis (for production scale)
"""

from datetime import datetime, timedelta
from typing import List, Dict

class ShortMemory:
    """
    In-memory storage of recent exchanges
    
    Each user has their own memory that expires after 30 min
    """
    
    # Class-level storage (shared across instances)
    _memory: Dict[str, List[Dict]] = {}
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        
        # Initialize user's memory if doesn't exist
        if user_id not in self._memory:
            self._memory[user_id] = []
    
    def add_exchange(self, user_message: str, logic_response: str):
        """
        Add a conversation exchange
        
        Args:
            user_message: What user said
            logic_response: What Logic responded
        """
        
        exchange = {
            'user': user_message,
            'logic': logic_response,
            'timestamp': datetime.now()
        }
        
        self._memory[self.user_id].append(exchange)
        
        # Clean old exchanges (older than 30 min)
        self._cleanup_old_exchanges()
        
        # Keep only last 10 exchanges max
        if len(self._memory[self.user_id]) > 10:
            self._memory[self.user_id] = self._memory[self.user_id][-10:]
    
    def get_recent_exchanges(self, limit: int = 5) -> List[Dict]:
        """
        Get recent conversation exchanges
        
        Args:
            limit: Max number of exchanges to return
            
        Returns:
            List of recent exchanges (newest last)
        """
        
        self._cleanup_old_exchanges()
        
        exchanges = self._memory.get(self.user_id, [])
        return exchanges[-limit:] if exchanges else []
    
    def _cleanup_old_exchanges(self):
        """Remove exchanges older than 30 minutes"""
        
        if self.user_id not in self._memory:
            return
        
        cutoff_time = datetime.now() - timedelta(minutes=30)
        
        self._memory[self.user_id] = [
            ex for ex in self._memory[self.user_id]
            if ex['timestamp'] > cutoff_time
        ]
    
    def clear(self):
        """Clear all memory for this user"""
        if self.user_id in self._memory:
            self._memory[self.user_id] = []