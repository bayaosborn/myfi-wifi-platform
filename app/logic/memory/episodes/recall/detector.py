"""
Is Recall Query - Detects when user asks about past episodes
"""


class RecallQueryDetector:
    def __init__(self):
        self.recall_keywords = [
            'who did i call',
            'who did i email',
            'who did i text',
            'who did i message',
            'did i call',
            'did i email',
            'did i text',
            'did i message',
            'when did i call',
            'when did i email',
            'what did i',
            'last time i called',
            'last time i emailed',
            'yesterday',
            'last week',
            'this morning',
            'this afternoon',
            'this evening',
            'today',
            'recent calls',
            'recent emails',
            'call history',
            'email history'
        ]

    def is_recall_query(self, message: str) -> bool:
        """
        Detect if user is asking about past episodes

        Args:
            message: User's message

        Returns:
            True if it's a recall query
        """
        if not message:
            return False

        message_lower = message.lower()

        return any(keyword in message_lower for keyword in self.recall_keywords)