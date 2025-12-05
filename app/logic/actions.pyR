"""
Actions Logic Can Trigger on Frontend
(Even without full MLO integration)
"""

class LogicActions:
    """
    Actions Logic can invoke on MyFi frontend
    """
    
    @staticmethod
    def change_contact_tag_color(contact_id: int, new_color: str) -> dict:
        """
        Future: Change tag color for a contact
        Returns action payload for frontend
        """
        return {
            'action': 'change_tag_color',
            'contact_id': contact_id,
            'color': new_color,
            'instruction': f"Update contact {contact_id} tag color to {new_color}"
        }
    
    @staticmethod
    def navigate_to_contact(contact_id: int) -> dict:
        """
        Navigate frontend to specific contact
        """
        return {
            'action': 'navigate_to_contact',
            'contact_id': contact_id,
            'instruction': f"Show contact {contact_id} on main card"
        }
    
    @staticmethod
    def open_call_interface(phone_number: str) -> dict:
        """
        Trigger call interface (future)
        """
        return {
            'action': 'initiate_call',
            'phone': phone_number,
            'instruction': f"Open call to {phone_number}"
        }
    
    @staticmethod
    def copy_to_clipboard(text: str) -> dict:
        """
        Copy text to clipboard (for M-Pesa numbers, etc.)
        """
        return {
            'action': 'copy_to_clipboard',
            'text': text,
            'instruction': f"Copied: {text}"
        }
    
    @staticmethod
    def show_recommendation(contacts: list) -> dict:
        """
        Highlight recommended contacts on frontend
        """
        return {
            'action': 'show_recommendations',
            'contacts': contacts,
            'instruction': "Displaying recommended contacts"
        }