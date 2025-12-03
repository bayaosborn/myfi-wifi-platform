"""
Examples of patterns Logic learns
"""

PATTERN_TYPES = {
    # 1. COMMUNICATION PATTERNS
    'call_frequency': {
        'contact_id': 5,
        'frequency': 'weekly',
        'preferred_day': 'Friday',
        'preferred_time': '18:00-20:00'
    },
    
    # 2. NEGLECT PATTERNS
    'neglected_contact': {
        'contact_id': 12,
        'last_interaction': '2025-10-15',
        'days_since': 45,
        'relationship': 'family'
    },
    
    # 3. TAG PREFERENCES
    'tag_usage': {
        'most_used': 'friends',
        'least_used': 'work',
        'missing_tags': 5
    },
    
    # 4. SEARCH PATTERNS
    'search_behavior': {
        'most_searched': 'family',
        'search_frequency': 'daily',
        'typical_time': 'evening'
    },
    
    # 5. USER HABITS
    'usage_times': {
        'peak_hours': ['08:00-09:00', '18:00-20:00'],
        'typical_days': ['Monday', 'Friday'],
        'session_length': '5-10 minutes'
    },
    
    # 6. CONTACT GROUPING
    'social_clusters': {
        'family_circle': [1, 2, 3, 4],
        'close_friends': [5, 6, 7],
        'work_colleagues': [8, 9, 10]
    },
    
    # 7. LANGUAGE PREFERENCES
    'communication_style': {
        'formality': 'casual',
        'tone': 'friendly',
        'emoji_usage': 'moderate',
        'slang': ['bro', 'maze', 'sawa']
    }
}