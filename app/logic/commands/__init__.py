"""
Command Executor System
Handles all command execution with extensible architecture

Future commands:
- Contact commands (call, message, edit, etc.)
- MLO commands (ride, food, gas, etc.)
- Business commands (pay, invoice, etc.)
"""

import sqlite3
from typing import Dict, Any, Callable, List
import json

class CommandExecutor:
    """
    Central command execution system
    
    Design principles:
    - Extensible: Easy to add new commands
    - Type-safe: Commands have defined schemas
    - Auditable: All commands are logged
    - Reversible: Support for undo where possible
    """
    
    def __init__(self, logic_engine=None):
        self.logic_engine = logic_engine
        self.db_path = 'myfi.db'
        
        # Command registry
        self.commands: Dict[str, Callable] = {}
        
        # Register all commands
        self._register_commands()
        
        print("✓ Command executor initialized")
    
    def _register_commands(self):
        """Register all available commands"""
        
        # ===== CONTACT COMMANDS =====
        self.register('contact:view', self.cmd_view_contact)
        self.register('contact:call', self.cmd_call_contact)
        self.register('contact:message', self.cmd_message_contact)
        self.register('contact:email', self.cmd_email_contact)
        self.register('contact:edit', self.cmd_edit_contact)
        self.register('contact:note', self.cmd_add_note)
        self.register('contact:tag', self.cmd_change_tag)
        self.register('contact:delete', self.cmd_delete_contact)
        self.register('contact:merge', self.cmd_merge_contacts)
        self.register('contact:export', self.cmd_export_contacts)
        
        # ===== SEARCH COMMANDS =====
        self.register('search:contacts', self.cmd_search_contacts)
        self.register('search:tag', self.cmd_search_by_tag)
        self.register('search:recent', self.cmd_recent_contacts)
        
        # ===== LOGIC COMMANDS =====
        self.register('logic:suggest', self.cmd_get_suggestions)
        self.register('logic:analyze', self.cmd_analyze_contact)
        self.register('logic:remind', self.cmd_set_reminder)
        
        # ===== MLO COMMANDS (Placeholders for Phase 3) =====
        self.register('mlo:ride:request', self.cmd_mlo_placeholder)
        self.register('mlo:food:order', self.cmd_mlo_placeholder)
        self.register('mlo:gas:find', self.cmd_mlo_placeholder)
        
        # ===== BUSINESS COMMANDS (Placeholders for Future) =====
        self.register('business:pay', self.cmd_business_placeholder)
        self.register('business:invoice', self.cmd_business_placeholder)
    
    def register(self, command: str, handler: Callable):
        """Register a command handler"""
        self.commands[command] = handler
        print(f"  ↳ Registered: {command}")
    
    def execute(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a command
        
        Args:
            command: Command string (e.g., 'contact:call')
            params: Command parameters
            
        Returns:
            Result dictionary with success status and data
        """
        try:
            # Check if command exists
            if command not in self.commands:
                return {
                    'success': False,
                    'error': f'Unknown command: {command}',
                    'available_commands': list(self.commands.keys())
                }
            
            # Execute command
            handler = self.commands[command]
            result = handler(params)
            
            # Log execution
            self._log_command(command, params, result)
            
            return {
                'success': True,
                'command': command,
                'result': result
            }
            
        except Exception as e:
            error_msg = f"Command execution failed: {str(e)}"
            print(f"❌ {error_msg}")
            
            return {
                'success': False,
                'error': error_msg,
                'command': command
            }
    
    # ========================================
    # CONTACT COMMANDS
    # ========================================
    
    def cmd_view_contact(self, params: Dict) -> Dict:
        """Show contact details"""
        contact_id = params.get('id') or params.get('contactId')
        
        if not contact_id:
            return {'error': 'Contact ID required'}
        
        contact = self._get_contact(contact_id)
        
        if not contact:
            return {'error': 'Contact not found'}
        
        return {
            'action': 'show_contact',
            'contact': contact
        }
    
    def cmd_call_contact(self, params: Dict) -> Dict:
        """Initiate call to contact"""
        contact_id = params.get('id') or params.get('contactId')
        
        if not contact_id:
            return {'error': 'Contact ID required'}
        
        contact = self._get_contact(contact_id)
        
        if not contact:
            return {'error': 'Contact not found'}
        
        # Log interaction
        self._log_interaction(contact_id, 'call')
        
        return {
            'action': 'call',
            'phone': contact['phone'],
            'name': contact['name']
        }
    
    def cmd_message_contact(self, params: Dict) -> Dict:
        """Open messaging with contact"""
        contact_id = params.get('id') or params.get('contactId')
        
        if not contact_id:
            return {'error': 'Contact ID required'}
        
        contact = self._get_contact(contact_id)
        
        if not contact:
            return {'error': 'Contact not found'}
        
        # Log interaction
        self._log_interaction(contact_id, 'message')
        
        return {
            'action': 'message',
            'phone': contact['phone'],
            'name': contact['name']
        }
    
    def cmd_email_contact(self, params: Dict) -> Dict:
        """Open email to contact"""
        contact_id = params.get('id') or params.get('contactId')
        
        contact = self._get_contact(contact_id)
        
        if not contact:
            return {'error': 'Contact not found'}
        
        if not contact.get('email'):
            return {'error': 'Contact has no email'}
        
        return {
            'action': 'email',
            'email': contact['email'],
            'name': contact['name']
        }
    
    def cmd_edit_contact(self, params: Dict) -> Dict:
        """Edit contact field"""
        contact_id = params.get('id')
        field = params.get('field')
        value = params.get('value')
        
        if not all([contact_id, field, value]):
            return {'error': 'ID, field, and value required'}
        
        # Validate field
        allowed_fields = ['name', 'phone', 'email', 'tag', 'notes']
        if field not in allowed_fields:
            return {'error': f'Invalid field. Allowed: {allowed_fields}'}
        
        # Update database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            f'UPDATE contacts SET {field} = ? WHERE id = ?',
            (value, contact_id)
        )
        
        conn.commit()
        conn.close()
        
        return {
            'action': 'contact_updated',
            'contactId': contact_id,
            'field': field,
            'value': value
        }
    
    def cmd_add_note(self, params: Dict) -> Dict:
        """Add note to contact"""
        contact_id = params.get('id')
        note = params.get('note')
        
        if not all([contact_id, note]):
            return {'error': 'ID and note required'}
        
        # Get existing notes
        contact = self._get_contact(contact_id)
        existing_notes = contact.get('notes', '') or ''
        
        # Append new note with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        new_note = f"\n[{timestamp}] {note}"
        updated_notes = existing_notes + new_note
        
        # Update database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE contacts SET notes = ? WHERE id = ?',
            (updated_notes, contact_id)
        )
        
        conn.commit()
        conn.close()
        
        return {
            'action': 'note_added',
            'contactId': contact_id
        }
    
    def cmd_change_tag(self, params: Dict) -> Dict:
        """Change contact tag"""
        contact_id = params.get('id')
        tag = params.get('tag')
        
        if not all([contact_id, tag]):
            return {'error': 'ID and tag required'}
        
        return self.cmd_edit_contact({
            'id': contact_id,
            'field': 'tag',
            'value': tag
        })
    
    def cmd_delete_contact(self, params: Dict) -> Dict:
        """Delete a contact"""
        contact_id = params.get('id')
        
        if not contact_id:
            return {'error': 'Contact ID required'}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM contacts WHERE id = ?', (contact_id,))
        
        conn.commit()
        conn.close()
        
        return {
            'action': 'contact_deleted',
            'contactId': contact_id
        }
    
    def cmd_merge_contacts(self, params: Dict) -> Dict:
        """Merge two contacts"""
        id1 = params.get('id1')
        id2 = params.get('id2')
        
        if not all([id1, id2]):
            return {'error': 'Two contact IDs required'}
        
        # TODO: Implement merge logic
        return {
            'action': 'merge',
            'status': 'pending_implementation'
        }
    
    def cmd_export_contacts(self, params: Dict) -> Dict:
        """Export contacts by tag"""
        tag = params.get('tag', 'all')
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if tag == 'all':
            cursor.execute('SELECT * FROM contacts')
        else:
            cursor.execute('SELECT * FROM contacts WHERE tag = ?', (tag,))
        
        contacts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            'action': 'export',
            'contacts': contacts,
            'count': len(contacts)
        }
    
    # ========================================
    # SEARCH COMMANDS
    # ========================================
    
    def cmd_search_contacts(self, params: Dict) -> Dict:
        """Search contacts"""
        query = params.get('query', '')
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            '''SELECT * FROM contacts 
               WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?''',
            (f'%{query}%', f'%{query}%', f'%{query}%')
        )
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            'action': 'search_results',
            'results': results,
            'count': len(results)
        }
    
    def cmd_search_by_tag(self, params: Dict) -> Dict:
        """Search by tag"""
        tag = params.get('tag')
        
        if not tag:
            return {'error': 'Tag required'}
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM contacts WHERE tag = ?', (tag,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            'action': 'search_results',
            'results': results,
            'count': len(results),
            'tag': tag
        }
    
    def cmd_recent_contacts(self, params: Dict) -> Dict:
        """Get recently interacted contacts"""
        limit = params.get('limit', 10)
        
        # TODO: Query interactions table when implemented
        return {
            'action': 'recent_contacts',
            'status': 'pending_implementation'
        }
    
    # ========================================
    # LOGIC COMMANDS
    # ========================================
    
    def cmd_get_suggestions(self, params: Dict) -> Dict:
        """Get Logic suggestions"""
        if not self.logic_engine:
            return {'error': 'Logic engine not available'}
        
        response = self.logic_engine.chat(
            "Give me 3 suggestions for who to reach out to today."
        )
        
        return {
            'action': 'suggestions',
            'suggestions': response
        }
    
    def cmd_analyze_contact(self, params: Dict) -> Dict:
        """Analyze relationship with contact"""
        contact_id = params.get('id')
        
        if not contact_id:
            return {'error': 'Contact ID required'}
        
        contact = self._get_contact(contact_id)
        
        if not contact:
            return {'error': 'Contact not found'}
        
        if not self.logic_engine:
            return {'error': 'Logic engine not available'}
        
        prompt = f"Analyze my relationship with {contact['name']} (ID: {contact_id})"
        response = self.logic_engine.chat(prompt)
        
        return {
            'action': 'analysis',
            'analysis': response
        }
    
    def cmd_set_reminder(self, params: Dict) -> Dict:
        """Set reminder to contact someone"""
        contact_id = params.get('id')
        days = params.get('days', 7)
        
        # TODO: Implement reminder system
        return {
            'action': 'reminder_set',
            'status': 'pending_implementation'
        }
    
    # ========================================
    # PLACEHOLDER COMMANDS (Future)
    # ========================================
    
    def cmd_mlo_placeholder(self, params: Dict) -> Dict:
        """Placeholder for MLO commands"""
        return {
            'action': 'mlo_pending',
            'message': 'MLO commands coming in Phase 3'
        }
    
    def cmd_business_placeholder(self, params: Dict) -> Dict:
        """Placeholder for business commands"""
        return {
            'action': 'business_pending',
            'message': 'Business commands coming soon'
        }
    
    # ========================================
    # HELPER METHODS
    # ========================================
    
    def _get_contact(self, contact_id: int) -> Dict:
        """Get contact by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM contacts WHERE id = ?', (contact_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        return dict(row) if row else None
    
    def _log_interaction(self, contact_id: int, interaction_type: str):
        """Log contact interaction"""
        # TODO: Implement interactions table
        print(f"📝 Logged {interaction_type} with contact {contact_id}")
    
    def _log_command(self, command: str, params: Dict, result: Dict):
        """Log command execution"""
        # TODO: Implement command audit log
        print(f"✓ Executed: {command}")