"""
Intent Classifier
app/logic/core/intent.py

Uses lightweight LLM to classify user intent
Replaces brittle keyword matching
"""

from groq import Groq
import os
import json
from typing import Dict, Optional


class IntentClassifier:
    """
    Classifies user intent using LLM
    
    Intent types:
    - contact_action: call/message/email
    - contact_management: add/edit contact
    - merchant_search: find products/services
    - product_browse: view specific merchant catalog
    - order_request: purchase something
    - order_inquiry: check order status
    - recall_query: "what did I...", "you showed me..."
    - general_chat: everything else
    """
    
    INTENTS = [
        'contact_action',       # "call John", "text Sarah"
        'contact_management',   # "add contact", "update John's email"
        'merchant_search',      # "I want boots", "find gas"
        'product_browse',       # "what does Mbauda sell"
        'order_request',        # "order 6kg gas", "buy boots"
        'order_inquiry',        # "where's my order", "check order status"
        'recall_query',         # "you showed me...", "I ordered..."
        'general_chat'          # "hello", "how are you"
    ]
    
    def __init__(self):
        """Initialize classifier"""
        self.groq = Groq(api_key=os.getenv('GROQ_API_KEY'))
        # Use smallest, fastest model for classification
        self.model = 'llama-3.1-8b-instant'
    
    def classify(self, message: str) -> Dict:
        """
        Classify user intent
        
        Args:
            message: User's message
        
        Returns:
            {
                'intent': 'merchant_search',
                'confidence': 0.95,
                'entities': {
                    'product': 'boots',
                    'merchant': None,
                    'contact_name': None,
                    'quantity': None
                },
                'reasoning': 'User is looking for a product'
            }
        """
        try:
            prompt = self._build_prompt(message)
            
            response = self.groq.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt}
                ],
                temperature=0.1,  # Low temp for consistency
                max_tokens=200
            )
            
            result = response.choices[0].message.content.strip()
            
            # Parse JSON response
            if '```json' in result:
                result = result.split('```json')[1].split('```')[0].strip()
            elif '```' in result:
                result = result.split('```')[1].split('```')[0].strip()
            
            parsed = json.loads(result)
            
            # Validate intent
            if parsed.get('intent') not in self.INTENTS:
                print(f"⚠️ Invalid intent: {parsed.get('intent')}, defaulting to general_chat")
                parsed['intent'] = 'general_chat'
            
            print(f"✅ Intent classified: {parsed['intent']} (confidence: {parsed.get('confidence', 'N/A')})")
            
            return parsed
        
        except Exception as e:
            print(f"❌ Intent classification error: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to general_chat
            return {
                'intent': 'general_chat',
                'confidence': 0.5,
                'entities': {},
                'reasoning': 'Classification failed, defaulting to general chat'
            }
    
    def _build_prompt(self, message: str) -> str:
        """
        Build classification prompt
        
        Args:
            message: User's message
        
        Returns:
            System prompt for classification
        """
        return f"""You are an intent classifier for a contact manager + merchant discovery system.

TASK: Classify the user's intent and extract entities.

INTENT TYPES:

1. **contact_action** - User wants to call, text, or email someone
   Examples: "call John", "text Sarah", "email Mike"
   
2. **contact_management** - User wants to add/edit contacts
   Examples: "add contact", "update John's phone", "save this number"
   
3. **merchant_search** - User wants to find products/services
   Examples: "I want boots", "find gas", "where can I buy soap"
   
4. **product_browse** - User wants to see what a specific merchant sells
   Examples: "what does Mbauda sell", "show me Viva Ronaldo's products"
   
5. **order_request** - User wants to purchase something
   Examples: "order 6kg gas", "buy CR7 boots", "I'll take 2 soaps"
   
6. **order_inquiry** - User asking about order status
   Examples: "where's my order", "did my gas arrive", "check my order status"
   
7. **recall_query** - User referencing past conversation
   Examples: "you showed me boots", "I ordered from Mbauda", "what did I buy last week"
   
8. **general_chat** - General conversation
   Examples: "hello", "thanks", "how are you"

RESPONSE FORMAT: Return ONLY valid JSON.

{{
    "intent": "merchant_search",
    "confidence": 0.95,
    "entities": {{
        "product": "boots",
        "merchant": null,
        "contact_name": null,
        "quantity": null,
        "action_type": null
    }},
    "reasoning": "User is looking for a product to purchase"
}}

CRITICAL RULES:

1. **Disambiguate "want":**
   - "I want to call John" → contact_action (NOT merchant_search)
   - "I want boots" → merchant_search
   - "I want to order gas" → order_request

2. **Contact vs Merchant:**
   - If message mentions calling/texting/emailing → contact_action
   - If message asks about products → merchant_search

3. **Search vs Order:**
   - "find boots" → merchant_search (discovery)
   - "order boots" → order_request (purchase)
   - "buy boots" → order_request (purchase)

4. **Entity Extraction:**
   - Extract product names: "boots", "gas", "soap"
   - Extract merchant names: "Mbauda", "Viva Ronaldo"
   - Extract contact names: "John", "Sarah"
   - Extract quantities: "2", "6kg"

5. **Swahili/Sheng Support:**
   - "nataka viatu" → merchant_search (viatu = shoes)
   - "nipigie John" → contact_action (pigia = call)
   - "kununua sabuni" → order_request (kununua = buy, sabuni = soap)

USER MESSAGE: {message}

RESPOND WITH JSON ONLY."""
    
    def is_merchant_related(self, intent: str) -> bool:
        """
        Check if intent is merchant-related
        
        Args:
            intent: Classified intent
        
        Returns:
            True if merchant-related
        """
        merchant_intents = [
            'merchant_search',
            'product_browse',
            'order_request',
            'order_inquiry'
        ]
        
        return intent in merchant_intents
    
    def is_contact_related(self, intent: str) -> bool:
        """
        Check if intent is contact-related
        
        Args:
            intent: Classified intent
        
        Returns:
            True if contact-related
        """
        contact_intents = [
            'contact_action',
            'contact_management'
        ]
        
        return intent in contact_intents
    
    def needs_confirmation(self, intent: str) -> bool:
        """
        Check if intent needs user confirmation before execution
        
        Args:
            intent: Classified intent
        
        Returns:
            True if needs confirmation
        """
        # Orders should be confirmed before execution
        return intent == 'order_request'


def get_intent_classifier():
    """Factory function to create intent classifier"""
    return IntentClassifier()