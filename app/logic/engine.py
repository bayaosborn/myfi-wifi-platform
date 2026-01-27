"""
Logic Engine - REFACTORED
Handles intent routing with clean separation of concerns

ARCHITECTURE:
- Intent Classification (LLM)
- Route to Skills (Python)
- Format Response (LLM)
- Write Memory (Storage)
"""

from groq import Groq
import os
import json

from app.backend.supabase_client import supabase

# SECURITY
from app.logic.core.security.abuse import is_safe

# INTENT CLASSIFICATION
from app.logic.core.intent import IntentClassifier

# MEMORY
from app.logic.memory.memory_manager import MemoryManager
from app.logic.memory.episodes import EpisodicWriter, EpisodicReader, RecallQueryDetector

# PROMPTS
from app.logic.prompts.system_prompt import (
    build_contact_action_prompt,
    build_merchant_response_prompt,
    build_order_confirmation_prompt
)

# MERCHANT SKILLS
from app.logic.skills.directory.merchant.discovery import MerchantDiscovery
from app.logic.skills.directory.merchant.manager import get_merchant_products
from app.logic.skills.directory.merchant.writer import MerchantDiscoveryWriter
from app.logic.skills.directory.merchant.reader import MerchantDiscoveryReader
from app.logic.skills.directory.merchant.ordering import OrderManager


class LogicEngine:
    """
    Clean orchestrator for Logic system
    
    Responsibilities:
    1. Classify intent
    2. Route to appropriate handler
    3. Coordinate skills
    4. Format responses
    5. Write memory
    """
    
    def __init__(self, user_id: str):
        """
        Initialize Logic for a user
        
        Args:
            user_id: User's UUID (from session)
        """
        self.user_id = user_id
        self.groq = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.model = 'llama-3.3-70b-versatile'
        
        # Initialize intent classifier
        self.intent_classifier = IntentClassifier()
        
        # Initialize memory
        self.memory = MemoryManager(user_id)
        
        # Initialize episodic memory
        self.episodic_writer = EpisodicWriter(user_id)
        self.episodic_reader = EpisodicReader(user_id)
        self.recall_detector = RecallQueryDetector(user_id)
        
        # Initialize merchant skills
        self.merchant_discovery = MerchantDiscovery(user_id)
        self.merchant_writer = MerchantDiscoveryWriter(user_id)
        self.merchant_reader = MerchantDiscoveryReader(user_id)
        self.order_manager = OrderManager(user_id)
        
        print(f"✅ Logic engine initialized for user {user_id[:8]}... (refactored)")
    
    def chat(self, message: str) -> dict:
        """
        Process user message with intent-based routing
        
        Args:
            message: User's message
        
        Returns:
            {
                'response': 'User-facing message',
                'hidden_commands': [],
                'metadata': {}
            }
        """
        try:
            # ========================================
            # 🛡️ ABUSE CHECK
            # ========================================
            if not is_safe(message):
                return {
                    'response': '',
                    'hidden_commands': []
                }
            
            # ========================================
            # 🧠 CLASSIFY INTENT
            # ========================================
            intent_result = self.intent_classifier.classify(message)
            intent = intent_result['intent']
            entities = intent_result.get('entities', {})
            
            print(f"🎯 Intent: {intent}")
            
            # ========================================
            # 🔀 ROUTE TO HANDLER
            # ========================================
            if intent == 'contact_action':
                return self._handle_contact_action(message, entities)
            
            elif intent == 'contact_management':
                return self._handle_contact_management(message, entities)
            
            elif intent == 'merchant_search':
                return self._handle_merchant_search(message, entities)
            
            elif intent == 'product_browse':
                return self._handle_product_browse(message, entities)
            
            elif intent == 'order_request':
                return self._handle_order_request(message, entities)
            
            elif intent == 'order_inquiry':
                return self._handle_order_inquiry(message, entities)
            
            elif intent == 'recall_query':
                return self._handle_recall_query(message, entities)
            
            else:  # general_chat
                return self._handle_general_chat(message)
        
        except Exception as e:
            print(f"❌ Logic error: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'response': "Something went wrong. Please try again.",
                'hidden_commands': []
            }
    
    # ========================================
    # CONTACT HANDLERS
    # ========================================
    
    def _handle_contact_action(self, message: str, entities: dict) -> dict:
        """
        Handle call/message/email actions
        
        Uses existing contact action logic
        """
        try:
            contacts_json = self._get_contacts_json()
            memory_context = self.memory.get_context(message)
            
            prompt = build_contact_action_prompt(
                contacts_json=contacts_json,
                user_message=message,
                memory_context=memory_context
            )
            
            response = self.groq.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Parse JSON response
            if '```' in ai_response:
                if '```json' in ai_response:
                    ai_response = ai_response.split('```json')[1].split('```')[0]
                else:
                    ai_response = ai_response.split('```')[1].split('```')[0]
                ai_response = ai_response.strip()
            
            parsed = json.loads(ai_response)
            
            user_message = parsed.get('response', 'Done.')
            command = parsed.get('command')
            
            result = {
                'response': user_message,
                'hidden_commands': []
            }
            
            valid_actions = ['call', 'message', 'email', 'add_contact', 'edit_contact']
            
            if command and command.get('action') in valid_actions:
                result['hidden_commands'].append(command)
                self._write_episode(command)
            
            # Save to memory
            metadata = {
                'intent': 'contact_action',
                'action_type': command.get('action') if command else None,
                'contact_id': command.get('contact_id') if command else None
            }
            
            self.memory.save_exchange(
                user_message=message,
                logic_response=user_message,
                metadata=metadata
            )
            
            return result
        
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            return {
                'response': ai_response,
                'hidden_commands': []
            }
    
    def _handle_contact_management(self, message: str, entities: dict) -> dict:
        """Handle add/edit contact"""
        # Use same logic as contact_action for now
        return self._handle_contact_action(message, entities)
    
    # ========================================
    # MERCHANT HANDLERS (NEW - FIXED)
    # ========================================
    
    def _handle_merchant_search(self, message: str, entities: dict) -> dict:
        """
        Handle merchant/product search
        
        CORRECT FLOW:
        1. Python executes search (not LLM)
        2. Get real merchant data
        3. Create discovery file
        4. LLM formats response
        """
        try:
            print(f"🛒 Merchant search: {message}")
            
            # STEP 1: PYTHON EXECUTES SEARCH
            merchants = self.merchant_discovery.search(
                query=message,
                tags=entities.get('tags'),
                location=entities.get('location')
            )
            
            if not merchants:
                # No merchants found - suggest alternatives
                return {
                    'response': "I couldn't find any merchants matching that search. Could you try describing what you need differently? For example, instead of brand names, try 'cleaning supplies' or 'gas cylinders'.",
                    'hidden_commands': [],
                    'metadata': {'intent': 'merchant_search', 'results': 0}
                }
            
            print(f"✅ Found {len(merchants)} merchants")
            
            # STEP 2: GET PRODUCTS FOR TOP MERCHANTS
            enriched_merchants = []
            for merchant in merchants[:3]:  # Top 3 results
                products = get_merchant_products(merchant['id'])
                enriched_merchants.append({
                    'merchant': merchant,
                    'products': products
                })
            
            # STEP 3: CREATE DISCOVERY FILE (now we have real data)
            if enriched_merchants:
                top_merchant = enriched_merchants[0]
                filename = self.merchant_writer.write_merchant(
                    merchant_id=top_merchant['merchant']['id'],
                    merchant_name=top_merchant['merchant']['business_name'],
                    merchant_description=top_merchant['merchant'].get('description', ''),
                    products=top_merchant['products']
                )
                
                if filename:
                    print(f"✅ Discovery file created: {filename}")
            
            # STEP 4: LLM FORMATS RESPONSE
            merchants_json = json.dumps(enriched_merchants, indent=2)
            memory_context = self.memory.get_context(message)
            
            prompt = build_merchant_response_prompt(
                user_message=message,
                merchants_data=merchants_json,
                memory_context=memory_context
            )
            
            response = self.groq.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": prompt}],
                temperature=0.5,
                max_tokens=600
            )
            
            logic_response = response.choices[0].message.content.strip()
            
            # Save to memory
            self.memory.save_exchange(
                user_message=message,
                logic_response=logic_response,
                metadata={
                    'intent': 'merchant_search',
                    'merchants_found': len(enriched_merchants),
                    'top_merchant': top_merchant['merchant']['business_name']
                }
            )
            
            return {
                'response': logic_response,
                'hidden_commands': [],
                'metadata': {
                    'merchants_found': len(enriched_merchants)
                }
            }
        
        except Exception as e:
            print(f"❌ Merchant search error: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'response': "I had trouble searching for merchants. Please try again.",
                'hidden_commands': []
            }
    
    def _handle_product_browse(self, message: str, entities: dict) -> dict:
        """
        Handle browsing specific merchant's products
        
        Example: "What does Mbauda sell?"
        """
        try:
            merchant_name = entities.get('merchant')
            
            if not merchant_name:
                return {
                    'response': "Which merchant would you like to browse?",
                    'hidden_commands': []
                }
            
            # Try to read existing discovery file
            discovery_content = self.merchant_reader.read_merchant_by_name(merchant_name)
            
            if discovery_content:
                # We have existing discovery
                memory_context = self.memory.get_context(message)
                
                prompt = build_merchant_response_prompt(
                    user_message=message,
                    merchants_data=discovery_content,
                    memory_context=memory_context
                )
                
                response = self.groq.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": prompt}],
                    temperature=0.5,
                    max_tokens=600
                )
                
                return {
                    'response': response.choices[0].message.content.strip(),
                    'hidden_commands': []
                }
            else:
                # No discovery file, search for merchant
                return self._handle_merchant_search(message, entities)
        
        except Exception as e:
            print(f"❌ Product browse error: {e}")
            return {
                'response': "I had trouble browsing that merchant. Please try again.",
                'hidden_commands': []
            }
    
    def _handle_order_request(self, message: str, entities: dict) -> dict:
        """
        Handle order requests
        
        TODO: Implement multi-step confirmation in Phase 3
        For now, return placeholder
        """
        return {
            'response': "Order handling will be implemented in Phase 3. For now, please browse products and I'll help you order soon!",
            'hidden_commands': [],
            'metadata': {'intent': 'order_request', 'status': 'not_implemented'}
        }
    
    def _handle_order_inquiry(self, message: str, entities: dict) -> dict:
        """Handle order status inquiries"""
        # TODO: Implement in Phase 3
        return {
            'response': "Order tracking will be available soon. Please contact the merchant directly for now.",
            'hidden_commands': []
        }
    
    # ========================================
    # RECALL HANDLER
    # ========================================
    
    def _handle_recall_query(self, message: str, entities: dict) -> dict:
        """
        Handle recall queries
        
        Examples:
        - "You showed me boots" → Read merchant-discovery
        - "I ordered from Mbauda" → Read episodic memory
        """
        try:
            # Determine if this is discovery recall or action recall
            if self._is_discovery_recall(message):
                # Read merchant discovery files
                discovery_content = self.merchant_reader.read_latest_merchant()
                
                if discovery_content:
                    memory_context = self.memory.get_context(message)
                    
                    prompt = f"""User is recalling a past merchant discovery.

DISCOVERY CONTENT:
{discovery_content}

MEMORY CONTEXT:
{memory_context}

USER MESSAGE: {message}

Respond naturally about what was shown to the user before."""
                    
                    response = self.groq.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "system", "content": prompt}],
                        temperature=0.5,
                        max_tokens=400
                    )
                    
                    return {
                        'response': response.choices[0].message.content.strip(),
                        'hidden_commands': []
                    }
                else:
                    return {
                        'response': "I don't have any recent merchant discoveries to recall. What would you like to find?",
                        'hidden_commands': []
                    }
            else:
                # Read episodic memory (actions taken)
                episodic_context = self.episodic_reader.get_context_for_recall(message)
                
                if episodic_context and "No matching episodes" not in episodic_context:
                    memory_context = self.memory.get_context(message)
                    
                    prompt = f"""User is recalling a past action.

EPISODIC MEMORY:
{episodic_context}

MEMORY CONTEXT:
{memory_context}

USER MESSAGE: {message}

Respond naturally about what actions were taken."""
                    
                    response = self.groq.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "system", "content": prompt}],
                        temperature=0.5,
                        max_tokens=400
                    )
                    
                    return {
                        'response': response.choices[0].message.content.strip(),
                        'hidden_commands': []
                    }
                else:
                    return {
                        'response': "I don't recall that action. Could you be more specific?",
                        'hidden_commands': []
                    }
        
        except Exception as e:
            print(f"❌ Recall query error: {e}")
            return {
                'response': "I had trouble recalling that. Could you rephrase?",
                'hidden_commands': []
            }
    
    def _is_discovery_recall(self, message: str) -> bool:
        """
        Check if recall is about discovery (browsing) or action (ordering)
        
        Discovery: "you showed me", "you told me about"
        Action: "I ordered", "I bought", "I called"
        """
        message_lower = message.lower()
        
        discovery_keywords = [
            'you showed', 'you told me', 'you mentioned',
            'you said', 'you recommended'
        ]
        
        return any(keyword in message_lower for keyword in discovery_keywords)
    
    # ========================================
    # GENERAL CHAT
    # ========================================
    
    def _handle_general_chat(self, message: str) -> dict:
        """Handle general conversation"""
        memory_context = self.memory.get_context(message)
        
        prompt = f"""You are Logic, a helpful AI assistant.

MEMORY CONTEXT:
{memory_context}

USER MESSAGE: {message}

Respond naturally and helpfully. Keep it brief."""
        
        response = self.groq.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        
        logic_response = response.choices[0].message.content.strip()
        
        self.memory.save_exchange(
            user_message=message,
            logic_response=logic_response,
            metadata={'intent': 'general_chat'}
        )
        
        return {
            'response': logic_response,
            'hidden_commands': []
        }
    
    # ========================================
    # HELPER METHODS
    # ========================================
    
    def _get_contacts_json(self) -> str:
        """Get user's contacts as JSON"""
        try:
            contacts = supabase.select(
                'contacts',
                filters={'user_id': self.user_id}
            )
            
            if not contacts:
                return "[]"
            
            simple_contacts = []
            for c in contacts:
                simple_contacts.append({
                    'id': c['id'],
                    'name': c['name'],
                    'phone': c.get('phone', ''),
                    'email': c.get('email', ''),
                    'tag': c.get('tag', 'General')
                })
            
            return json.dumps(simple_contacts, indent=2)
        
        except Exception as e:
            print(f"Error getting contacts: {e}")
            return "[]"
    
    def _write_episode(self, command: dict):
        """Write episode to episodic memory after command execution"""
        try:
            action_type = command.get('action')
            
            intent_map = {
                'call': 'call',
                'message': 'sms',
                'email': 'email',
                'add_contact': 'add-contact',
                'edit_contact': 'edit-contact'
            }
            
            intent = intent_map.get(action_type, action_type)
            
            target = command.get('contact_name')
            target_phone = command.get('phone')
            target_email = command.get('email')
            
            action_desc = f"{intent.replace('-', '_')}_executed"
            outcome = "command_sent"
            
            metadata = {}
            
            if action_type == 'call':
                metadata['call_type'] = 'outbound'
                metadata['contact_id'] = command.get('contact_id')
            
            elif action_type == 'message':
                metadata['message_preview'] = command.get('body', '')[:50] if command.get('body') else 'SMS sent'
                metadata['contact_id'] = command.get('contact_id')
            
            elif action_type == 'email':
                metadata['subject'] = command.get('subject', 'No subject')
                metadata['body_preview'] = command.get('body', '')[:50] if command.get('body') else ''
                metadata['contact_id'] = command.get('contact_id')
            
            elif action_type == 'add_contact':
                metadata['new_contact_name'] = command.get('name')
                metadata['tag'] = command.get('tag', 'General')
            
            elif action_type == 'edit_contact':
                metadata['contact_id'] = command.get('contact_id')
                metadata['updated_fields'] = []
                if 'phone' in command:
                    metadata['updated_fields'].append('phone')
                if 'email' in command:
                    metadata['updated_fields'].append('email')
                if 'name' in command:
                    metadata['updated_fields'].append('name')
                metadata['updated_fields'] = ', '.join(metadata['updated_fields']) if metadata['updated_fields'] else 'unknown'
            
            self.episodic_writer.write_episode(
                intent=intent,
                action=action_desc,
                outcome=outcome,
                target=target,
                target_phone=target_phone,
                target_email=target_email,
                metadata=metadata
            )
            
            print(f"✅ Episode written for {intent}: {target or 'N/A'}")
        
        except Exception as e:
            print(f"⚠️ Failed to write episode: {e}")


def get_logic_engine(user_id: str):
    """Factory function to create Logic engine"""
    return LogicEngine(user_id)