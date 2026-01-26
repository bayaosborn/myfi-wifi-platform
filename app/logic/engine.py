"""
Logic Engine - With Memory System + Episodic Memory
Handles call, message, email, add_contact, edit_contact commands
"""

from groq import Groq
import os
import json

from app.backend.supabase_client import supabase

#SECURITY
from app.logic.core.security.abuse import is_safe, get_abuse_rules


#MEMORY
from app.logic.memory.memory_manager import MemoryManager
from app.logic.memory.episodes import EpisodicWriter, EpisodicReader, RecallQueryDetector

#PROMPTS
from app.logic.prompts.system_prompt import build_system_prompt


class LogicEngine:
    def __init__(self, user_id: str):
        """
        Initialize Logic for a user

        Args:
            user_id: User's UUID (from session)
        """
        self.user_id = user_id
        self.groq = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.model = 'llama-3.3-70b-versatile'
        
        # Initialize memory
        self.memory = MemoryManager(user_id)
        
        # 🆕 Initialize episodic writer
        self.episodic_writer = EpisodicWriter(user_id)
        
        # 🆕 Initialize episodic reader
        self.episodic_reader = EpisodicReader(user_id)

        #Initialize recall query detector
        self.recall_detector = RecallQueryDetector()
        
        print(f"✅ Logic engine initialized for user {user_id[:8]}... with memory + episodes")

    def chat(self, message: str) -> dict:
        """
        Process user message with memory context
        """
        try:
            # ========================================
            # 🛡️ QUICK ABUSE CHECK
            # ========================================
            if not is_safe(message):
                return {
                    'response': '',
                    'hidden_commands': []
                }
            
            # ========================================
            # 🧠 GET MEMORY CONTEXT
            # ========================================
            memory_context = self.memory.get_context(message)
            
            # 🆕 CHECK IF THIS IS A RECALL QUERY
            # ========================================
            if self.recall_detector.is_recall_query(message):
                episodic_context = self.episodic_reader.get_context_for_recall(message)
                
                if episodic_context and "No matching episodes" not in episodic_context:
                    if memory_context:
                        memory_context += "\n\n" + episodic_context
                    else:
                        memory_context = episodic_context
                    
                    print(f"✅ Added episodic context for recall query")
            
            # ========================================
            # ✅ PROCEED NORMALLY
            # ========================================
            
            contacts_json = self._get_contacts_json()

            
            system_prompt = build_system_prompt(contacts_json, message, memory_context)

            response = self.groq.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            ai_response = response.choices[0].message.content.strip()

            try:
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
                
                metadata = {
                    'action_type': command.get('action') if command else None,
                    'contact_id': command.get('contact_id') if command else None,
                    'contact_name': command.get('contact_name') if command else None,
                    'success': bool(command)
                }
                
                self.memory.save_exchange(
                    user_message=message,
                    logic_response=user_message,
                    metadata=metadata
                )

                return result

            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                print(f"AI response was: {ai_response}")
                
                self.memory.save_exchange(
                    user_message=message,
                    logic_response=ai_response,
                    metadata={'success': False, 'error': 'json_parse_error'}
                )
                
                return {
                    'response': ai_response,
                    'hidden_commands': []
                }

        except Exception as e:
            print(f"❌ Logic error: {e}")
            import traceback
            traceback.print_exc()

            return {
                'response': "Something went wrong. Please try again.",
                'hidden_commands': []
            }

    def _get_contacts_json(self) -> str:
        """
        Get user's contacts as JSON including email addresses
        """
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
        """
        Write episode to episodic memory after command execution
        """
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
            import traceback
            traceback.print_exc()

    


def get_logic_engine(user_id: str):
    """Factory function to create Logic engine"""
    return LogicEngine(user_id)