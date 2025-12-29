
"""
Abuse Detection - Simple & Fast
Returns: safe or blocked (that's it)
"""

import re

def is_safe(message: str) -> bool:
    """
    Check if message is safe to process
    
    Returns:
        True = safe, proceed
        False = blocked, ignore
    """
    
    if not message:
        return True
    
    msg = message.lower().strip()
    
    # Block obvious threats
    blocked_patterns = [
        # System attacks
        r'\bdelete\s+all\b',
        r'\bdrop\s+table\b',
        r"';.*--",
        
        # Prompt injection
        r'\bignore\s+(all|previous)\s+instructions\b',
        r'\bforget\s+your\s+rules\b',
        r'\bact\s+as\b',
        
        # Bulk spam
        r'\b(call|message|email)\s+(all|everyone|everybody)\b',
        r'\bsend\s+to\s+all\b',
        
        # Data theft
        r'\blist\s+all\s+contacts\b',
        r'\bexport\s+contacts\b',
        r'\bshow\s+all\s+(phone|email)',
        
        # Impersonation
        r'\bpretend\s+(to\s+be|i\'m)\b',
        r'\bas\s+(the\s+)?(bank|police|support)\b',
    ]
    
    for pattern in blocked_patterns:
        if re.search(pattern, msg):
            return False
    
    return True


def get_abuse_rules() -> str:
    """
    Get abuse rules to include in system prompt
    This teaches the AI what NOT to do
    """
    return """
CRITICAL SAFETY RULES:
- NEVER execute commands for contacts not in the user's contact list
- NEVER call, message, or email raw phone numbers or email addresses
- NEVER perform bulk actions (call all, message everyone, etc.)
- If contact not found, respond with: "I couldn't find that contact"
- If ambiguous (multiple matches), ask which one
- ALWAYS use contact data from the JSON above
"""