"""
Single Continuous Chat Implementation
"""

class ConversationManager:
    """
    Manages the ONE continuous conversation with Logic
    """
    
    def __init__(self):
        self.db = 'logic_memory.db'
        self.max_history = 20  # Keep last 20 exchanges in memory
    
    def get_recent_context(self, limit=10) -> list:
        """Get recent conversation for context"""
        conn = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_message, logic_response, timestamp
            FROM conversations
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        history = cursor.fetchall()
        conn.close()
        
        # Reverse to chronological order
        return list(reversed([dict(row) for row in history]))
    
    def save_exchange(self, user_msg: str, logic_response: str, tokens: int):
        """Save conversation exchange"""
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversations
            (user_message, logic_response, tokens_used)
            VALUES (?, ?, ?)
        ''', (user_msg, logic_response, tokens))
        
        conn.commit()
        conn.close()
    
    def get_conversation_summary(self) -> str:
        """Get summary of entire conversation history"""
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) as total,
                   SUM(tokens_used) as total_tokens,
                   MIN(timestamp) as first_interaction,
                   MAX(timestamp) as last_interaction
            FROM conversations
        ''')
        
        stats = cursor.fetchone()
        conn.close()
        
        return f"""
Conversation History:
- Total exchanges: {stats[0]}
- Tokens used: {stats[1]}
- First chat: {stats[2]}
- Last chat: {stats[3]}
        """
    
    def extract_important_context(self) -> str:
        """
        Analyze conversation and extract what matters
        This becomes Logic's "memory"
        """
        recent = self.get_recent_context(limit=50)
        
        # Extract key information
        contacts_mentioned = set()
        topics_discussed = set()
        user_questions = []
        
        for exchange in recent:
            # Simple extraction (you can make this smarter)
            msg = exchange['user_message'].lower()
            
            # Track topics
            if 'family' in msg:
                topics_discussed.add('family')
            if 'work' in msg:
                topics_discussed.add('work')
            if 'call' in msg:
                user_questions.append('calling_contacts')
        
        context = f"""
LEARNED CONTEXT:
- Frequently mentioned: {', '.join(contacts_mentioned) if contacts_mentioned else 'N/A'}
- Topics of interest: {', '.join(topics_discussed) if topics_discussed else 'general contacts'}
- Common actions: {', '.join(set(user_questions)) if user_questions else 'browsing contacts'}
        """
        
        return context