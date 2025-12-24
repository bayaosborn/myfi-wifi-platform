"""
Logic Engine - Ultra Simplified
Handles call, message, email commands
"""

from groq import Groq
import os
from app.backend.supabase_client import supabase
from app.logic.helpers import get_current_date, get_current_time  # ← IMPORT
import json

class LogicEngine:
    def __init__(self, user_id, access_token):
        """
        Initialize Logic for a user
        
        Args:
            user_id: User's UUID
            access_token: Supabase token
        """
        self.user_id = user_id
        self.access_token = access_token
        self.groq = Groq(api_key=os.getenv('GROQ_API_KEY'))
        self.model = 'llama-3.3-70b-versatile'
    
    def chat(self, message: str) -> dict:
        """
        Process user message
        
        Args:
            message: What user typed (e.g., "Call Sarah")
            
        Returns:
            {
                'response': 'Calling Sarah...',
                'hidden_commands': [...]
            }
        """
        try:
            # 1. Get user's contacts as JSON (for AI to parse)
            contacts_json = self._get_contacts_json()
            
            # 2. Build prompt with context
            system_prompt = self._build_system_prompt(contacts_json, message)
            
            # 3. Call Groq
            response = self.groq.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt}
                ],
                temperature=0.3,
                max_tokens=500  # ← Increased for email drafts
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # 4. Parse JSON response
            try:
                # Remove markdown code blocks if present
                if '```' in ai_response:
                    # Extract JSON from code block
                    if '```json' in ai_response:
                        ai_response = ai_response.split('```json')[1].split('```')[0]
                    else:
                        ai_response = ai_response.split('```')[1].split('```')[0]
                    ai_response = ai_response.strip()
                
                parsed = json.loads(ai_response)
                
                user_message = parsed.get('response', 'Done.')
                command = parsed.get('command')
                
                # 5. Build response
                result = {
                    'response': user_message,
                    'hidden_commands': []
                }
                
                # Add command to hidden array if exists
                if command and command.get('action') in ['call', 'message', 'email']:
                    result['hidden_commands'].append(command)
                
                return result
                
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                print(f"AI response was: {ai_response}")
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
                filters={'user_id': self.user_id},
                access_token=self.access_token
            )
            
            if not contacts:
                return "[]"
            
            # Build JSON with phone AND email
            simple_contacts = []
            for c in contacts:
                simple_contacts.append({
                    'id': c['id'],
                    'name': c['name'],
                    'phone': c.get('phone', ''),
                    'email': c.get('email', ''),  # ← ADDED EMAIL
                    'tag': c.get('tag', 'General')
                })
            
            return json.dumps(simple_contacts, indent=2)
            
        except Exception as e:
            print(f"Error getting contacts: {e}")
            return "[]"
    
    def _build_system_prompt(self, contacts_json: str, user_message: str) -> str:
        """
        Build complete system prompt with all examples
        
        Args:
            contacts_json: User's contacts as JSON
            user_message: What user typed
            
        Returns:
            Complete prompt string
        """
        
        # Get current date/time using helpers
        current_date = get_current_date()
        current_time = get_current_time()
        
        return f"""You are Logic, an AI for MyFi contact manager.

USER'S CONTACTS (as JSON):
{contacts_json}

YOUR JOB:
1. Understand what user wants to do
2. Find the contact in the JSON above
3. Return a response + hidden JSON command

RESPONSE FORMAT:
{{
    "response": "Human-readable message to show user",
    "command": {{
        "action": "call|message|email",
        "contact_id": "uuid-here",
        "contact_name": "Name",
        "phone": "0712345678",
        "email": "person@email.com",
        "subject": "Subject",
        "body": "Body text"
    }}
}}

EXAMPLES:

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

User: "Message Sarah"
{{
    "response": "Messaging Sarah...",
    "command": {{
        "action": "message",
        "contact_id": "abc-123",
        "contact_name": "Sarah",
        "phone": "0742107097"
    }}
}}

User: "Email Sarah"
{{
    "response": "Opening email to Sarah...",
    "command": {{
        "action": "email",
        "contact_id": "abc-123",
        "contact_name": "Sarah",
        "email": "sarah@email.com",
        "subject": "",
        "body": ""
    }}
}}

User: "Email my lecturer telling him I'm sick and will be unable to attend his morning class tomorrow"
{{
    "response": "Drafting email to lecturer...",
    "command": {{
        "action": "email",
        "contact_id": "xyz-789",
        "contact_name": "Dr. Smith",
        "email": "smith@university.edu",
        "subject": "Unable to Attend Morning Class Tomorrow",
        "body": "Dear Dr. Smith,\\n\\nI hope this email finds you well. I am writing to inform you that I am currently unwell and will unfortunately be unable to attend your morning class tomorrow.\\n\\nI apologize for any inconvenience this may cause and will catch up on any missed material as soon as possible.\\n\\nThank you for your understanding.\\n\\nBest regards"
    }}
}}

DRAFTING RULES FOR EMAIL:
- If user gives context → draft a FULL email
- Use tone based on contact tag:
  * Work/Lecturer → Formal ("Dear Dr. Smith", "Best regards")
  * Family → Casual ("Hi Mom", "Love")
  * Friends → Friendly ("Hey Sarah!", "Cheers")
- If user just says "Email X" → leave subject and body empty
- Keep emails concise (2-3 paragraphs max)

RULES:
- ALWAYS respond in valid JSON
- If contact not found, set command to null
- Use phone/email from contacts JSON
- Keep response short (1 sentence)

CURRENT CONTEXT:
- Today is: {current_date}
- Time: {current_time}
- When user says "tomorrow", include actual date

User message: {user_message}
"""


def get_logic_engine(user_id: str, access_token: str):
    """Factory function to create Logic engine"""
    return LogicEngine(user_id, access_token)