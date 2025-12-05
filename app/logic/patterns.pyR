"""
Pattern Learning - How Logic gets smarter
"""

class PatternLearner:
    """
    Analyzes user behavior and learns patterns
    """
    
    def __init__(self):
        self.db = 'logic_memory.db'
    
    def learn_from_conversation(self, user_message: str, logic_response: str):
        """Extract patterns from conversation"""
        
        # 1. Detect mentions of contacts
        mentioned_contacts = self._extract_contact_mentions(user_message)
        
        # 2. Detect time patterns
        time_mentions = self._extract_time_patterns(user_message)
        
        # 3. Detect preferences
        preferences = self._extract_preferences(user_message, logic_response)
        
        # 4. Save patterns
        self._save_patterns(mentioned_contacts, time_mentions, preferences)
    
    def _extract_contact_mentions(self, message: str) -> list:
        """Find which contacts user is asking about"""
        # Connect to contacts DB
        conn = sqlite3.connect('myfi.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, name FROM contacts')
        contacts = cursor.fetchall()
        conn.close()
        
        mentioned = []
        message_lower = message.lower()
        
        for contact_id, name in contacts:
            if name.lower() in message_lower:
                mentioned.append(contact_id)
        
        return mentioned
    
    def _extract_time_patterns(self, message: str) -> dict:
        """Detect when user typically uses Logic"""
        now = datetime.now()
        
        return {
            'hour': now.hour,
            'day_of_week': now.strftime('%A'),
            'part_of_day': self._get_part_of_day(now.hour)
        }
    
    def _get_part_of_day(self, hour: int) -> str:
        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 21:
            return 'evening'
        else:
            return 'night'
    
    def _extract_preferences(self, user_msg: str, logic_response: str) -> dict:
        """Learn user preferences from interactions"""
        prefs = {}
        
        # Language style
        if any(word in user_msg.lower() for word in ['bro', 'maze', 'sawa']):
            prefs['language_style'] = 'casual_kenyan'
        
        # Response length preference
        if len(logic_response.split()) < 50:
            prefs['response_length'] = 'concise'
        
        return prefs
    
    def _save_patterns(self, contacts, times, prefs):
        """Save learned patterns to database"""
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        
        # Save time pattern
        if times:
            cursor.execute('''
                INSERT OR REPLACE INTO user_patterns
                (pattern_type, pattern_data, confidence, occurrences)
                VALUES ('usage_time', ?, 0.7, 1)
                ON CONFLICT(pattern_type) DO UPDATE SET
                    occurrences = occurrences + 1,
                    confidence = MIN(confidence + 0.05, 1.0),
                    last_updated = CURRENT_TIMESTAMP
            ''', (json.dumps(times),))
        
        # Save preferences
        for key, value in prefs.items():
            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences
                (preference_key, preference_value, confidence, learned_from)
                VALUES (?, ?, 0.6, 'conversation')
            ''', (key, value))
        
        conn.commit()
        conn.close()