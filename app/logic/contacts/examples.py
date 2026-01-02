"""
Contact Operation Examples for Logic AI
Clear examples to help Logic understand how to add/edit contacts

Location: app/logic/contacts/examples.py
"""

CONTACT_EXAMPLES = """
===========================================
ADDING CONTACTS
===========================================

KEYWORDS: "add", "save", "create", "store", "put"

FORMAT:
{
    "response": "Adding [name]...",
    "command": {
        "action": "add_contact",
        "name": "Full Name",
        "phone": "0712345678",
        "email": "person@email.com",
        "tag": "Work"
    }
}

EXAMPLES:

1. Add with phone:
User: "add Sarah 0712345678"
{
    "response": "Adding Sarah...",
    "command": {
        "action": "add_contact",
        "name": "Sarah",
        "phone": "0712345678"
    }
}

2. Add with email:
User: "save John email john@email.com"
{
    "response": "Adding John...",
    "command": {
        "action": "add_contact",
        "name": "John",
        "email": "john@email.com"
    }
}


RULES ON ADDING/EDITING EMAILS

DO NOT add a . when adding an email or editing when user pauses between 2 words in an email. See an example here of what to to add:

USER: "add John Samuel and email john samuel at gmail dot com"

WRONG EMAIL: john.samuel@gmail.com

CORRECT EMAIL: johnsamuel@gmail.com

AVOID THE . between names unless user explicitly specifies it.



3. Add with tag:
User: "create contact Dr. Smith email smith@uni.edu tag Work"
{
    "response": "Adding Dr. Smith to Work...",
    "command": {
        "action": "add_contact",
        "name": "Dr. Smith",
        "email": "smith@uni.edu",
        "tag": "Work"
    }
}

4. Add with tag where user specifies nature of contact:
User: "add my new coworker John number 0742786455"
{
    "response": "Adding John to Work...",
    "command": {
        "action": "add_contact",
        "name": "John",
        "phone": "0742786455",
        "tag": "Work"
    }
}

RULES ON CONTACTS RELATIONSHIP
I'm Osborn Baya, your creator and I want to give you some rules on how to handle contacts relationship 



Contact Nature Understanding Rules for Logic

Core principle

You should only tag when confidence is high.
If confidence is low or ambiguous → default to "General".

Allowed tags (for now)

Family

Friends

Work

General (fallback)





Tagging Rules

Rule 1: Explicit relationship words → tag directly

If the user explicitly states the relationship, you must tag accordingly.

High-confidence keywords

Family: cousin, brother, sister, mum, dad, aunt, uncle, wife, husband

Friends: friend, buddy, pal

Work: coworker, colleague, manager, boss, supervisor





Rule 2: Named relationship overrides ambiguity

If a relationship word is present, you should not hesitate, even if the name is unfamiliar.




Rule 3: No relationship mentioned → General

If the user only provides a name/number without context, you must not infer.




Rule 4: Confidence gate

You must ask internally:

> “Did the user clearly tell me the nature?”



Yes → apply tag

No / unsure → General





Examples




1. Family tag (explicit relationship)

User:

> “add my cousin Kamau number 0712345678”



{
  "response": "Adding Kamau to Family...",
  "command": {
    "action": "add_contact",
    "name": "Kamau",
    "phone": "0712345678",
    "tag": "Family"
  }
}

Why:
“cousin” is a clear family indicator → high confidence.




2. Friends tag (explicit and already defined)

User:

> “add my friend Lisa”



{
  "response": "Adding Lisa to Friends...",
  "command": {
    "action": "add_contact",
    "name": "Lisa",
    "tag": "Friends"
  }
}

Why:
“friend” directly maps to the Friends tag.



3. Default to General (no nature given)

User:

> “add Brian number 0700112233”



{
  "response": "Adding Brian to contacts...",
  "command": {
    "action": "add_contact",
    "name": "Brian",
    "phone": "0700112233",
    "tag": "General"
  }
}

Why:
No relationship stated → no assumptions allowed.



Your Example (#4) — Valid & Correct ✅

Your coworker example is exactly how you should behave when confidence is high.

Key takeaway:

> You should not guess relationships — it listens.



If you want, next we can:

Add confidence scoring

Support multiple tags later

Define override rules (“actually move John to Friends”)



5. Add with phone and email:
User: "store Mom 0700123456 email mom@email.com tag Family"
{
    "response": "Adding Mom to Family...",
    "command": {
        "action": "add_contact",
        "name": "Mom",
        "phone": "0700123456",
        "email": "mom@email.com",
        "tag": "Family"
    }
}

6. Add with international number:
User: "add Maria +1 555 123 4567"
{
    "response": "Adding Maria...",
    "command": {
        "action": "add_contact",
        "name": "Maria",
        "phone": "+15551234567"
    }
}

FAILURES:

User: "add Sarah" (no phone or email)
{
    "response": "I need a phone number or email for Sarah.",
    "command": null
}

User: "add Sarah 0712345678" (Sarah already exists)
{
    "response": "Sarah already exists in your contacts.",
    "command": null
}

===========================================
EDITING CONTACTS
===========================================

KEYWORDS: "change", "update", "edit", "fix", "modify", "move"

FORMAT:
{
    "response": "Updating [name]'s [field]...",
    "command": {
        "action": "edit_contact",
        "contact_id": "uuid-from-json",
        "contact_name": "Name",
        "phone": "new-number"  // OR email, tag, name
    }
}

EXAMPLES:

1. Change phone:
User: "change Sarah's phone to 0798765432"
{
    "response": "Updating Sarah's phone...",
    "command": {
        "action": "edit_contact",
        "contact_id": "abc-123",
        "contact_name": "Sarah",
        "phone": "0798765432"
    }
}

2. Update email:
User: "update John's email to john.new@email.com"
{
    "response": "Updating John's email...",
    "command": {
        "action": "edit_contact",
        "contact_id": "xyz-789",
        "contact_name": "John",
        "email": "john.new@email.com"
    }
}

3. Change tag:
User: "move Sarah to Family"
{
    "response": "Moving Sarah to Family...",
    "command": {
        "action": "edit_contact",
        "contact_id": "abc-123",
        "contact_name": "Sarah",
        "tag": "Family"
    }
}

4. Fix name:
User: "rename John to John Smith"
{
    "response": "Renaming to John Smith...",
    "command": {
        "action": "edit_contact",
        "contact_id": "xyz-789",
        "contact_name": "John",
        "name": "John Smith"
    }
}

5. Update multiple fields:
User: "update Sarah's phone to 0798765432 and email to sarah@new.com"
{
    "response": "Updating Sarah...",
    "command": {
        "action": "edit_contact",
        "contact_id": "abc-123",
        "contact_name": "Sarah",
        "phone": "0798765432",
        "email": "sarah@new.com"
    }
}

FAILURES:

User: "change Sarah's phone" (no new number given)
{
    "response": "What should Sarah's new phone number be?",
    "command": null
}

User: "update Bob's email" (Bob not in contacts)
{
    "response": "I couldn't find Bob in your contacts.",
    "command": null
}

===========================================
IMPORTANT RULES
===========================================

1. ADDING:
   - Need at least phone OR email
   - Check if name already exists
   - Clean phone numbers (remove spaces, commas)
   - Default tag is "General" if not specified
   - Keep international format (+1, +254, etc.)

2. EDITING:
   - Must find contact in JSON by name
   - Use contact_id from the JSON
   - Only update fields user mentions
   - Be specific: "phone", "email", "tag", or "name"
   - Clean phone numbers before updating

3. RESPONSES:
   - Keep short (1 sentence)
   - Be direct, no questions unless failure
   - Say what you're doing: "Adding...", "Updating..."
   - If field specified, say it: "Updating Sarah's phone..."

4. NEVER:
   - Delete contacts
   - Use phone/email not in JSON (except when adding)
   - Ask for confirmation
   - Make up contact IDs
   - Force country codes

===========================================
COMMON PHRASES TO DETECT
===========================================

ADD CONTACT:
- "add [name] [phone/email]"
- "save [name] number [phone]"
- "create contact [name]"
- "store [name]'s [phone/email]"
- "put [name] in contacts"

EDIT PHONE:
- "change [name]'s phone to [number]"
- "update [name]'s number to [number]"
- "fix [name]'s phone it's [number]"
- "[name]'s new number is [number]"

EDIT EMAIL:
- "change [name]'s email to [email]"
- "update [name]'s email"
- "[name]'s new email is [email]"

CHANGE TAG:
- "move [name] to [tag]"
- "put [name] in [tag]"
- "change [name]'s tag to [tag]"

RENAME:
- "rename [name] to [new name]"
- "change [name]'s name to [new name]"
"""


def get_contact_examples() -> str:
    """Return contact operation examples for Logic prompt"""
    return CONTACT_EXAMPLES