"""
Logic Memory Database
Separate from user contacts - stores what Logic learns
"""

import sqlite3
from datetime import datetime
import json

LOGIC_DB = 'logic_memory.db'

def init_logic_db():
    """Initialize Logic's memory database"""
    conn = sqlite3.connect(LOGIC_DB)
    cursor = conn.cursor()
    
    # 1. CONVERSATION HISTORY
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'default',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_message TEXT NOT NULL,
            logic_response TEXT NOT NULL,
            context_used TEXT,
            tokens_used INTEGER
        )
    ''')
    
    # 2. USER PATTERNS (What Logic learns)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'default',
            pattern_type TEXT NOT NULL,
            pattern_data JSON NOT NULL,
            confidence REAL DEFAULT 0.5,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            occurrences INTEGER DEFAULT 1
        )
    ''')
    
    # 3. CACHED RESPONSES (KV Cache)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS response_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_hash TEXT UNIQUE NOT NULL,
            response TEXT NOT NULL,
            context_snapshot TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            hits INTEGER DEFAULT 0,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 4. CONTACT INSIGHTS (What Logic observes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contact_insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER NOT NULL,
            insight_type TEXT NOT NULL,
            insight_data JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contact_id) REFERENCES contacts(id)
        )
    ''')
    
    # 5. USER PREFERENCES (Learned over time)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'default',
            preference_key TEXT NOT NULL,
            preference_value TEXT NOT NULL,
            learned_from TEXT,
            confidence REAL DEFAULT 0.5,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, preference_key)
        )
    ''')
    
    # 6. IMPORTANT CONTEXT (What Logic decides to remember)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS important_context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'default',
            context_type TEXT NOT NULL,
            context_data JSON NOT NULL,
            importance_score REAL DEFAULT 0.5,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_patterns_type ON user_patterns(pattern_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_hash ON response_cache(query_hash)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_insights_contact ON contact_insights(contact_id)')
    
    conn.commit()
    conn.close()
    print("✓ Logic memory database initialized")

# Initialize on import
init_logic_db()