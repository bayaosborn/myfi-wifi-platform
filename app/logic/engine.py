"""
Logic Engine - With Memory System
Handles call, message, email, add_contact, edit_contact commands
"""

from groq import Groq
import os
import json

from app.backend.supabase_client import supabase
from app.logic.helpers import get_current_date, get_current_time
from app.logic.security.abuse import is_safe, get_abuse_rules
from app.logic.memory.memory_manager import MemoryManager
from app.logic.contacts.disambiguation import get_disambiguation_examples

from app.logic.contacts.examples import get_contact_examples  # ← NEW


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
        
        print(f"✅ Logic engine initialized for user {user_id[:8]}... with memory")

    def chat(self, message: str) -> dict:
        """
        Process user message with memory context

        Args:
            message: What user typed (e.g., "Call Sarah" or "add Sarah 0712345678")

        Returns:
            {
                'response': 'Calling Sarah...',
                'hidden_commands': [...]
            }
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
            
            # ========================================
            # ✅ PROCEED NORMALLY
            # ========================================
            
            # 1. Get user's contacts as JSON
            contacts_json = self._get_contacts_json()

            # 2. Build prompt with context + memory
            system_prompt = self._build_system_prompt(
                contacts_json, 
                message,
                memory_context
            )

            # 3. Call Groq
            response = self.groq.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            ai_response = response.choices[0].message.content.strip()

            # 4. Parse JSON response
            try:
                # Remove markdown code blocks if present
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

                # ← EXPANDED VALID ACTIONS
                valid_actions = ['call', 'message', 'email', 'add_contact', 'edit_contact']
                
                if command and command.get('action') in valid_actions:
                    result['hidden_commands'].append(command)
                
                # ========================================
                # 💾 SAVE TO MEMORY
                # ========================================
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
                
                # Still save to memory (failed attempt)
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

        Returns:
            JSON array of contacts with phone AND email
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

    def _build_system_prompt(
        self, 
        contacts_json: str, 
        user_message: str,
        memory_context: str = ""
    ) -> str:
        """
        Build complete system prompt with memory context and contact examples
        
        Args:
            contacts_json: User's contacts
            user_message: Current message
            memory_context: Recent conversation + patterns
        """
        current_date = get_current_date()
        current_time = get_current_time()
        abuse_rules = get_abuse_rules()
        disambiguation_examples = get_disambiguation_examples()
    
        contact_examples = get_contact_examples()  # ← GET FULL EXAMPLES

        # Memory section
        memory_section = ""
        if memory_context:
            memory_section = f"""
{memory_context}

Use this context to understand follow-up questions and user preferences.
"""

        return f"""You are Logic, an AI for MyFi contact manager.

USER'S CONTACTS (as JSON):
{contacts_json}

{memory_section}

{disambiguation_examples}


===========================================
CRITICAL: DISAMBIGUATION ENFORCEMENT
===========================================

⚠️ YOU MUST USE PHONETIC MATCHING - DO NOT ASK FOR CLARIFICATION ON SIMILAR NAMES

When user says a name that doesn't EXACTLY match but SOUNDS SIMILAR:
- ALWAYS match to the closest contact immediately
- DO NOT ask "Did you mean...?"
- DO NOT start a conversation
- EXECUTE THE COMMAND with the closest match


EXAMPLE (FOLLOW THIS EXACTLY):
User: "Call Osborn Buyer"
Contacts: [{{"id": "abc-123", "name": "Osborn Baya", "phone": "0759335278"}}]

❌ WRONG (asking for confirmation):
{{
    "response": "Did you mean Osborn Baya?",
    "command": null
}}

✅ CORRECT (immediate execution):
{{
    "response": "Calling Osborn Baya...",
    "command": {{
        "action": "call",
        "contact_id": "abc-123",
        "contact_name": "Osborn Baya",
        "phone": "0759335278"
    }}
}}

MORE EXAMPLES OF IMMEDIATE EXECUTION:

User: "Send money to Journeys"
Contact: "Janice Wanjiru"
✅ Execute immediately: Send money to Janice Wanjiru

User: "Text Steven"
Contact: "Stephen Ochieng"
✅ Execute immediately: Text Stephen Ochieng if there is only one contact with that name

User: "Call mkubwa"
Contact: "David Mutua (Boss)"
✅ Execute immediately: Call David Mutua as "mkubwa" means boss in Swahili/Kenyan context

ONLY ASK FOR CLARIFICATION WHEN:
- Multiple contacts with EXACTLY the same first name (e.g., "John Kamau" AND "John Otieno")
- Zero phonetic matches exist
- User explicitly says "which" or "who"

DEFAULT BEHAVIOR: EXECUTE FIRST WHEN SURE, IN CASES OF PAYMENT ALWAYS CONFIRM FIRST, ASK LATER (NEVER)

I DON'T WANT YOU TO GET INTO A CONVERSATION REPEATEDLY FOR NOW BECAUSE THE USER DOES NOT SEE YOUR RESPONSES ON THE FRONTEND YET SO YOU ARE THE GUIDE.




YOUR JOB:
1. Understand what user wants to do
2. Find contacts in the JSON OR add/edit contacts
3. Use memory context for follow-ups (e.g., "her" = last person mentioned)
4. Return a response + hidden JSON command

RESPONSE FORMAT:
{{
    "response": "Human-readable message to show user",
    "command": {{
        "action": "call|message|email|add_contact|edit_contact",
        "contact_id": "uuid-here",
        "contact_name": "Name",
        "phone": "0712345678",
        "email": "person@email.com",
        "subject": "Subject",
        "body": "Body text",
        "tag": "Work",
        "name": "New Name"
    }}
}}

{abuse_rules}

===========================================
QUICK EXAMPLES
===========================================

User: "Call Sarah"
{{
    "response": "Calling Sarah...",
    "command": {{
        "action": "call",
        "contact_id": "abc-123",
        "contact_name": "Sarah",
        "phone": "0742107097"
    }}
}}

User: "add Sarah 0712345678"
{{
    "response": "Adding Sarah...",
    "command": {{
        "action": "add_contact",
        "name": "Sarah",
        "phone": "0712345678"
    }}
}}

User: "change Sarah's phone to 0798765432"
{{
    "response": "Updating Sarah's phone...",
    "command": {{
        "action": "edit_contact",
        "contact_id": "abc-123",
        "contact_name": "Sarah",
        "phone": "0798765432"
    }}
}}

===========================================
DETAILED EXAMPLES & RULES
===========================================

{contact_examples}

===========================================
CRITICAL RULES
===========================================

- ALWAYS respond in valid JSON
- If contact not found, set command to null and tell user
- ONLY use contacts from the JSON above
- NEVER use phone numbers or emails not in the JSON (except when adding new contact)
- Keep response short (1 sentence)
- Be direct: just execute, don't ask for confirmation
- Use memory context to resolve "her", "him", "them", etc.
- For add_contact: Need at least phone OR email
- For edit_contact: Must have contact_id from JSON
- NEVER delete contacts - this action is NOT allowed

CURRENT CONTEXT:
- Today is: {current_date}
- Time: {current_time}

User message: {user_message}
"""


def get_logic_engine(user_id: str):
    """Factory function to create Logic engine"""
    return LogicEngine(user_id)