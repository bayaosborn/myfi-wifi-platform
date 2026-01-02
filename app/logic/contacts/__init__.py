"""
Logic Contacts Module
Handles contact operations for Logic AI
"""

from app.logic.contacts.routes import logic_contacts_bp
from app.logic.contacts.operations import add_contact, edit_contact
from app.logic.contacts.examples import get_contact_examples

__all__ = [
    'logic_contacts_bp',
    'add_contact',
    'edit_contact',
    'get_contact_examples'
]