"""
Logic Engine - Ultra Simplified
Handles call, message, email commands
"""

from groq import Groq
import os
import json

from app.backend.supabase_client import supabase
from app.logic.helpers import get_current_date, get_current_time


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

    def _build_system_prompt(self, contacts_json: str, user_message: str) -> str:
        """
        Build complete system prompt with all examples
        """
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


def get_logic_engine(user_id: str):
    """Factory function to create Logic engine"""
    return LogicEngine(user_id)