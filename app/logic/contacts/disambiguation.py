"""
Disambiguation Module for Logic Engine

Purpose:
- Provide examples of how to resolve ambiguous voice input
- Handle phonetic similarities, voice transcription errors, and context-based resolution
- Pure example-driven approach - Logic learns patterns, not rules

Categories:
1. Phonetic Confusion (similar sounding names)
2. Partial Names (incomplete information)
3. Context-Based Resolution (using conversation history)
4. Entity Type Confusion (person vs organization)
5. Language/Accent Variations (Kenyan English, Swahili influences)
6. Ambiguity Handling (when multiple matches exist)
7. Special Cases (edge scenarios)
"""

# ========================================
# CORE DISAMBIGUATION EXAMPLES
# ========================================

PHONETIC_CONFUSION_EXAMPLES = """
-------------------------------------------
PHONETIC CONFUSION (Sound-Alike Names)
-------------------------------------------

User: "Call Osborn Buyer"
Contacts: ["Osborn Baya", "Oscar Mwangi"]
Match: Osborn Baya
Reason: "Buyer" sounds like "Baya"

User: "Send money to Journeys"
Contacts: ["Janice Wanjiru", "James Kamau"]
Match: Janice Wanjiru
Reason: "Journeys" → "Janice" (phonetic similarity)

User: "Message Steven"
Contacts: ["Stephen Ochieng", "Stephanie Akinyi"]
Match: Stephen Ochieng
Reason: "Steven" = "Stephen" (common variant)

User: "Call Catherine"
Contacts: ["Kathleen Njeri", "Catherine Muthoni", "Kathryn Wambui"]
Match: Catherine Muthoni
Reason: Exact match preferred over variants

User: "Pay Brian"
Contacts: ["Bryan Kipchoge", "Ryan Kimani"]
Match: Bryan Kipchoge
Reason: "Brian" = "Bryan" (same pronunciation)

User: "Text Carol"
Contacts: ["Karol Mwangi", "Carol Achieng", "Carl Otieno"]
Match: Carol Achieng
Reason: Prefer standard spelling

User: "Call Christopher"
Contacts: ["Kristopher Otieno", "Christopher Mwangi"]
Match: Christopher Mwangi
Reason: Exact spelling match preferred

User: "Message Cynthia"
Contacts: ["Synthia Wanjiru", "Cynthia Akinyi"]
Match: Cynthia Akinyi
Reason: Standard spelling preferred
"""

PARTIAL_NAME_EXAMPLES = """
-------------------------------------------
PARTIAL NAMES (Incomplete Information)
-------------------------------------------

User: "Call Sarah"
Contacts: ["Sarah Wanjiku", "Sarah Akinyi", "Samuel Kariuki"]
Match: Ask for clarification - "Which Sarah? Sarah Wanjiku or Sarah Akinyi?"

User: "Message John about the meeting"
Contacts: ["John Kamau", "Johnny Omondi", "Johnston Mwaura"]
Match: John Kamau (if recently contacted) OR ask for clarification

User: "Send money to Mom"
Contacts: ["Mary Wanjiru (Mom)", "Margaret Achieng"]
Match: Mary Wanjiru
Reason: Tag/relationship label match

User: "Call boss"
Contacts: ["David Mutua (Boss)", "Daniel Kiplagat"]
Match: David Mutua
Reason: Tag/relationship match

User: "Text the plumber"
Contacts: ["Peter Otieno (Plumber)", "Paul Mwangi"]
Match: Peter Otieno
Reason: Tag/occupation match

User: "Pay landlord"
Contacts: ["Joseph Karanja (Landlord)", "Joshua Maina"]
Match: Joseph Karanja
Reason: Role-based tag

User: "Call doctor"
Contacts: ["Dr. Mwangi (Doctor)", "Dr. Achieng (Doctor)"]
Match: Ask - "Which doctor? Dr. Mwangi or Dr. Achieng?"

User: "Message my sister"
Contacts: ["Anne Wanjiru (Sister)", "Alice Njeri (Sister)"]
Match: Ask - "Which sister? Anne or Alice?"
"""

CONTEXT_RESOLUTION_EXAMPLES = """
-------------------------------------------
CONTEXT-BASED RESOLUTION
-------------------------------------------

Conversation history:
User: "Call Sarah Wanjiku"
Logic: "Calling Sarah Wanjiku..."
[2 minutes later]
User: "Send her 500 shillings"
Match: Sarah Wanjiku
Reason: "Her" refers to last person mentioned

Conversation history:
User: "Message John Kamau about dinner"
Logic: "Message sent to John Kamau"
User: "Call him back"
Match: John Kamau
Reason: "Him" refers to last male contact mentioned

Conversation history:
User: "I need to pay the mechanic"
Logic: "Who is the mechanic?"
User: "James"
Match: James Omondi (tagged as Mechanic)
Reason: Context + first name + tag

Conversation history:
User: "Send 1000 to my brother"
Logic: "Sent KES 1000 to Brian Odhiambo"
User: "Send them another 500"
Match: Brian Odhiambo
Reason: "Them" (singular they) refers to last person

Conversation history:
User: "Call the landlord about rent"
Logic: "Calling Joseph Karanja..."
User: "Text them I'll pay tomorrow"
Match: Joseph Karanja
Reason: Continuing same conversation

Pattern: Recent conversation context (last 5 minutes)
- "her/him/them" → last mentioned person
- "again/back" → repeat last action with same contact
- Follow-up without name → use previous contact
- Pronoun resolution based on gender/context
"""

ENTITY_TYPE_EXAMPLES = """
-------------------------------------------
ENTITY TYPE CONFUSION (Person vs Organization)
-------------------------------------------

User: "Pay Circle"
Contacts: ["SACCO", "Circle K Store"]
Match: SACCO
Reason: "Circle" likely voice error for "SACCO"

User: "Pay SAKO"
Contacts: ["SACCO", "Sako Traders Ltd"]
Match: SACCO
Reason: Phonetic match + financial context

User: "Send money to the Sacco"
Contacts: ["SACCO", "Samuel Achieng Called 'Sacco'"]
Match: SACCO (organization)
Reason: "the Sacco" indicates organization, not nickname

User: "Pay KRA"
Contacts: ["Kenya Revenue Authority", "Kara Wanjiru"]
Match: Kenya Revenue Authority
Reason: Common abbreviation for organization

User: "Send to Safaricom"
Contacts: ["Safaricom Ltd (Airtime)", "Sam Safaricom"]
Match: Safaricom Ltd
Reason: Well-known organization name

User: "Pay NHIF"
Contacts: ["National Hospital Insurance Fund", "Nihir Patel"]
Match: National Hospital Insurance Fund
Reason: Common government acronym

User: "Send money to KPLC"
Contacts: ["Kenya Power & Lighting", "Kelly PLCorp"]
Match: Kenya Power & Lighting
Reason: Utility company context

User: "Pay equity"
Contacts: ["Equity Bank", "Eric Equity"]
Match: Equity Bank
Reason: Financial institution context
"""

KENYAN_CONTEXT_EXAMPLES = """
-------------------------------------------
KENYAN CONTEXT & LANGUAGE VARIATIONS
-------------------------------------------

User: "Call daktari"
Contacts: ["Dr. Mwangi (Doctor)", "David Tari"]
Match: Dr. Mwangi
Reason: "Daktari" = Swahili for doctor

User: "Text my bro"
Contacts: ["Brian Odhiambo (Brother)", "Robert Kimani (Bro)"]
Match: Brian Odhiambo
Reason: Family relationship tag

User: "Pay landlord"
Contacts: ["Joseph Karanja (Landlord)", "Lawrence Ndungu"]
Match: Joseph Karanja
Reason: Role-based tag

User: "Send airtime to mtoto wa Kamau"
Contacts: ["Peter Kamau Jr", "Kamau Electronics"]
Match: Peter Kamau Jr
Reason: "Mtoto wa" = child of (Swahili)

User: "Message shosh"
Contacts: ["Grandma Mary", "Sharon Otieno"]
Match: Grandma Mary
Reason: "Shosh" = Grandmother (Sheng)

User: "Call mkubwa"
Contacts: ["David Mutua (Boss)", "Michael Kubwa"]
Match: David Mutua
Reason: "Mkubwa" = boss/elder (Swahili)

User: "Text mzee"
Contacts: ["Dad John Kariuki", "Moses Zeenat"]
Match: Dad John Kariuki
Reason: "Mzee" = elder/father (Swahili)

User: "Call mama"
Contacts: ["Mom Mary Wanjiru", "Maria Martinez"]
Match: Mom Mary Wanjiru
Reason: "Mama" = mother (Swahili)

User: "Send to rafiki"
Contacts: ["Peter Otieno (Friend)", "Rafael Ikiara"]
Match: Peter Otieno
Reason: "Rafiki" = friend (Swahili)

User: "Pay kaka"
Contacts: ["Brother Daniel Omondi", "Kaka Stores"]
Match: Brother Daniel Omondi
Reason: "Kaka" = brother (Swahili)

User: "Message dada"
Contacts: ["Sister Anne Njeri", "Dada Textiles"]
Match: Sister Anne Njeri
Reason: "Dada" = sister (Swahili)
"""

AMBIGUITY_HANDLING_EXAMPLES = """
-------------------------------------------
HANDLING TRUE AMBIGUITY
-------------------------------------------

User: "Call Mike"
Contacts: ["Michael Wanjiru", "Mike Omondi", "Mikaela Achieng"]
Logic Response: "I found 2 Mikes: Michael Wanjiru and Mike Omondi. Which one?"
User: "The first one"
Match: Michael Wanjiru

User: "Send 1000 to James"
Contacts: ["James Kamau (Work)", "James Otieno (Friend)", "James Kipchoge (Cousin)"]
Logic Response: "Which James? Work, Friend, or Cousin?"
User: "Work"
Match: James Kamau

User: "Pay Jane"
Contacts: ["Jane Wanjiku (Last contacted 2 days ago)", "Jane Akinyi (Last contacted 2 months ago)"]
Match: Jane Wanjiku
Reason: Prefer recently contacted when truly ambiguous

User: "Call the electrician"
Contacts: ["No contacts tagged as electrician"]
Logic Response: "I don't have an electrician in your contacts. Would you like to add one?"

User: "Text Mary"
Contacts: ["Mary Wanjiru (Mom)", "Mary Akinyi (Work)", "Mary Njoki (Friend)"]
Logic Response: "Which Mary? Mom, Work, or Friend?"

User: "Send money to David"
Contacts: ["David Mutua", "David Otieno", "David Kimani"]
No tags or recent context
Logic Response: "I found 3 Davids. Can you be more specific?"

DISAMBIGUATION PRIORITY:
1. Exact name match → Use immediately
2. Single phonetic match → Use with confidence message
3. Tag/relationship match → Prefer over name-only match
4. Recent contact match → Use when multiple matches
5. Multiple matches → Ask for clarification
6. No matches → Suggest adding contact
7. Context-based resolution → Use recent conversation
"""

SPECIAL_CASES_EXAMPLES = """
-------------------------------------------
SPECIAL CASES & EDGE HANDLING
-------------------------------------------

User: "Call myself"
Action: Invalid - cannot call own number
Logic Response: "I can't call your own number. Did you mean someone else?"

User: "Send 500 to unknown number 0712345678"
Action: Send to raw phone number (not in contacts)
Logic Response: "Sending KES 500 to 0712345678. This number isn't in your contacts."

User: "Text everyone about the meeting"
Contacts: ["Group: Work Team", "All contacts"]
Logic Response: "Send to Work Team group or all contacts? (Warning: This will message [N] people)"

User: "Call the last person who called me"
Action: Query call logs for most recent incoming call
Match: Based on call history, not contacts

User: "Delete contact James"
Action: FORBIDDEN - Logic never deletes contacts
Logic Response: "I can't delete contacts. You can do this in Settings."

User: "Who is this?"
Context: During active call or after missed call
Logic Response: "That's [Contact Name] ([Phone Number]). Last contacted [Time]."

User: "Add new contact"
Action: Collect name and phone/email
Logic Response: "What's their name?"
User: "Sarah Mwangi"
Logic Response: "What's Sarah's phone number or email?"

User: "Block this number"
Action: Not allowed - suggest manual blocking
Logic Response: "I can't block numbers. You can block them in your phone's call settings."

User: "Call emergency"
Action: Recognize special case
Logic Response: "Calling 999 (emergency services)..." 
Alternative: "Do you mean emergency services (999) or a contact named Emergency?"

User: "Send money to +254712345678"
Action: Accept international format
Match: Format phone number, send payment
Logic Response: "Sending to +254712345678..."
"""

CONFIDENCE_EXAMPLES = """
-------------------------------------------
CONFIDENCE-BASED RESPONSES
-------------------------------------------

HIGH CONFIDENCE (95%+):
User: "Call Sarah Wanjiku"
Contact: "Sarah Wanjiku"
Logic: "Calling Sarah Wanjiku..." (no confirmation needed)

User: "Send 1000 to Mom"
Contact: "Mary Wanjiru (Mom)"
Logic: "Sending KES 1000 to Mom..." (tag match is confident)

MEDIUM CONFIDENCE (70-95%):
User: "Call Osborn Buyer"
Contact: "Osborn Baya"
Logic: "Calling Osborn Baya..." (proceed with slight mismatch)

User: "Text Steven"
Contact: "Stephen Ochieng"
Logic: "Texting Stephen..." (common spelling variant)

LOW CONFIDENCE (40-70%):
User: "Call Stephany"
Contacts: ["Stephanie Akinyi", "Stephany Njeri"]
Logic: "Did you mean Stephanie Akinyi or Stephany Njeri?"

User: "Pay John"
Contacts: ["John Kamau", "Johnny Omondi", "Johnston Mwaura"]
Logic: "Which John? Kamau, Omondi (Johnny), or Mwaura (Johnston)?"

VERY LOW CONFIDENCE (<40%):
User: "Call Xyz"
Contacts: ["No phonetic matches"]
Logic: "I couldn't find anyone named Xyz in your contacts."

User: "Send money to Qwerty"
Contacts: ["No similar names"]
Logic: "I don't have a contact named Qwerty. Would you like to add them?"

CONFIDENCE INDICATORS:
- Exact match = proceed immediately
- Close phonetic match = proceed with name confirmation
- Multiple matches = ask for clarification
- No match = suggest adding contact
- Context available = boost confidence
- Recent interaction = boost confidence
"""

# ========================================
# COMPILATION FUNCTION
# ========================================

def get_disambiguation_examples() -> str:
    """
    Return all disambiguation examples for Logic prompt
    
    Returns:
        Formatted string with all disambiguation patterns
    """
    return f"""
===========================================
NAME & ENTITY DISAMBIGUATION (VOICE INPUT)
===========================================

NOTE:
Voice input may normalize or translate names incorrectly.
Logic should resolve to the closest known contact or entity.

{PHONETIC_CONFUSION_EXAMPLES}

{PARTIAL_NAME_EXAMPLES}

{CONTEXT_RESOLUTION_EXAMPLES}

{ENTITY_TYPE_EXAMPLES}

{KENYAN_CONTEXT_EXAMPLES}

{AMBIGUITY_HANDLING_EXAMPLES}

{SPECIAL_CASES_EXAMPLES}

{CONFIDENCE_EXAMPLES}

===========================================
SUMMARY: DISAMBIGUATION PRINCIPLES
===========================================

Logic should:
1. Prefer phonetic similarity over exact spelling
2. Use conversation context (last 5 minutes)
3. Respect tags/relationships (Mom, Boss, Doctor)
4. Recognize Kenyan/Swahili terms and context
5. Ask for clarification when truly ambiguous
6. Provide confidence-based responses
7. Never assume - confirm when unsure
8. Learn from patterns, not rigid rules
9. Prefer recently contacted when multiple matches
10. Always validate against known contacts list

Voice input is messy. Logic adapts.
"""


# ========================================
# OPTIONAL: CATEGORY-SPECIFIC ACCESS
# ========================================

def get_phonetic_examples() -> str:
    """Get only phonetic confusion examples"""
    return PHONETIC_CONFUSION_EXAMPLES


def get_context_examples() -> str:
    """Get only context-based resolution examples"""
    return CONTEXT_RESOLUTION_EXAMPLES


def get_kenyan_examples() -> str:
    """Get only Kenyan context examples"""
    return KENYAN_CONTEXT_EXAMPLES


def get_ambiguity_examples() -> str:
    """Get only ambiguity handling examples"""
    return AMBIGUITY_HANDLING_EXAMPLES


def get_confidence_examples() -> str:
    """Get only confidence-based response examples"""
    return CONFIDENCE_EXAMPLES


