"""
Logic Engine with Memory & Learning
"""

from groq import Groq
import os
from .prompts import SYSTEM_PROMPT
from .memory import init_logic_db
from .cache import LogicCache
from .patterns import PatternLearner
from .conversations import ConversationManager

class LogicEngine:
    def __init__(self):
        # Initialize memory systems
        init_logic_db()
        
        self.groq = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.model = 'llama-3.3-70b-versatile'
        
        # Memory components
        self.cache = LogicCache()
        self.learner = PatternLearner()
        self.conversation = ConversationManager()
        
        # Direct database access
        self.contacts_db = 'myfi.db'
        self.logic_db = 'logic_memory.db'
        
        print("✓ Logic initialized with memory")
    
    def chat(self, message: str) -> str:
        """
        Enhanced chat with memory, caching, and learning
        """
        # 1. Get conversation context
        recent_history = self.conversation.get_recent_context(limit=5)
        learned_context = self.conversation.extract_important_context()
        
        # 2. Build context summary for cache
        context_summary = f"{len(recent_history)} exchanges"
        
        # 3. Check cache first
        if self.cache.should_cache(message):
            cached = self.cache.get_cached_response(message, context_summary)
            if cached:
                return cached
        
        # 4. Get current contacts from database directly
        contacts_summary = self._get_contacts_from_db()
        
        # 5. Build messages
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": f"CONTACTS:\n{contacts_summary}"},
            {"role": "system", "content": f"LEARNED CONTEXT:\n{learned_context}"}
        ]
        
        # Add recent history
        for exchange in recent_history:
            messages.append({"role": "user", "content": exchange['user_message']})
            messages.append({"role": "assistant", "content": exchange['logic_response']})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # 6. Call API
        try:
            response = self.groq.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            logic_response = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            # 7. Save to conversation history
            self.conversation.save_exchange(message, logic_response, tokens_used)
            
            # 8. Learn from this exchange
            self.learner.learn_from_conversation(message, logic_response)
            
            # 9. Cache if appropriate
            if self.cache.should_cache(message):
                self.cache.cache_response(message, context_summary, logic_response)
            
            return logic_response
        
        except Exception as e:
            print(f"Error: {e}")
            return "I'm having trouble right now. Please try again.\n\n/Created by Osborn Baya"
    
    def _get_contacts_from_db(self) -> str:
        """Read contacts directly from MyFi database"""
        import sqlite3
        
        conn = sqlite3.connect(self.contacts_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, name, phone, email, tag FROM contacts LIMIT 100')
        contacts = cursor.fetchall()
        conn.close()
        
        if not contacts:
            return "No contacts in database."
        
        summary = f"📊 {len(contacts)} contacts in database:\n\n"
        for contact in contacts:
            summary += f"- {contact['name']} ({contact['tag']}) | {contact['phone']}\n"
        
        return summary







