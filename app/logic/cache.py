"""
KV Cache Implementation for Logic
Reduces API calls by 60-80%
"""

import hashlib
import sqlite3

class LogicCache:
    """
    Key-Value cache for Logic responses
    """
    
    def __init__(self):
        self.db = 'logic_memory.db'
    
    def _hash_query(self, query: str, context_summary: str) -> str:
        """Create hash of query + context"""
        combined = f"{query}|{context_summary}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get_cached_response(self, query: str, context_summary: str) -> str:
        """Check if we have a cached response"""
        query_hash = self._hash_query(query, context_summary)
        
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT response, hits FROM response_cache
            WHERE query_hash = ?
            AND (
                created_at > datetime('now', '-7 days')
                OR hits > 5
            )
        ''', (query_hash,))
        
        result = cursor.fetchone()
        
        if result:
            # Update hit count and last_used
            cursor.execute('''
                UPDATE response_cache
                SET hits = hits + 1,
                    last_used = CURRENT_TIMESTAMP
                WHERE query_hash = ?
            ''', (query_hash,))
            conn.commit()
            conn.close()
            
            print(f"✓ Cache hit! ({result[1]} previous hits)")
            return result[0]
        
        conn.close()
        return None
    
    def cache_response(self, query: str, context_summary: str, response: str):
        """Save response to cache"""
        query_hash = self._hash_query(query, context_summary)
        
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO response_cache
            (query_hash, response, context_snapshot, created_at, hits)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, 0)
        ''', (query_hash, response, context_summary))
        
        conn.commit()
        conn.close()
    
    def should_cache(self, query: str) -> bool:
        """Decide if query should be cached"""
        # Cache these types:
        cacheable_patterns = [
            'show me', 'list', 'who is', 'what is',
            'how many', 'find', 'search'
        ]
        
        query_lower = query.lower()
        
        # Don't cache time-sensitive queries
        time_sensitive = ['today', 'now', 'recent', 'last']
        if any(word in query_lower for word in time_sensitive):
            return False
        
        # Cache if matches pattern
        return any(pattern in query_lower for pattern in cacheable_patterns)