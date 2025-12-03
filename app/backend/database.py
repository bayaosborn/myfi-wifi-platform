import sqlite3
from datetime import datetime
import os

DATABASE_NAME = 'myfi.db'

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    return conn

def init_db():
    """Initialize database with contacts table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create contacts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            tag TEXT DEFAULT 'General',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_contacted TIMESTAMP,
            contact_frequency INTEGER DEFAULT 0,
            preferred_time TEXT
        )
    ''')
    
    # Create indexes for faster queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tag ON contacts(tag)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_name ON contacts(name)')
    
    conn.commit()
    conn.close()
    print("✓ Database initialized successfully")

# CRUD Operations

def create_contact(name, phone='', email='', tag='General', notes=''):
    """Insert a new contact into the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO contacts (name, phone, email, tag, notes)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, phone, email, tag, notes))
    
    contact_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return contact_id

def get_all_contacts(page=1, per_page=13):
    """Get all contacts with pagination"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    offset = (page - 1) * per_page
    
    cursor.execute('''
        SELECT * FROM contacts 
        ORDER BY name ASC
        LIMIT ? OFFSET ?
    ''', (per_page, offset))
    
    contacts = cursor.fetchall()
    
    # Get total count
    cursor.execute('SELECT COUNT(*) as count FROM contacts')
    total = cursor.fetchone()['count']
    
    conn.close()
    
    # Convert to list of dicts
    contacts_list = [dict(contact) for contact in contacts]
    
    return {
        'contacts': contacts_list,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    }

def get_contact_by_id(contact_id):
    """Get a single contact by ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM contacts WHERE id = ?', (contact_id,))
    contact = cursor.fetchone()
    
    conn.close()
    
    return dict(contact) if contact else None

def update_contact(contact_id, **kwargs):
    """Update contact fields"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build dynamic update query
    fields = []
    values = []
    
    for key, value in kwargs.items():
        if key in ['name', 'phone', 'email', 'tag', 'notes']:
            fields.append(f"{key} = ?")
            values.append(value)
    
    if not fields:
        return False
    
    # Add updated timestamp
    fields.append("updated_at = ?")
    values.append(datetime.now())
    values.append(contact_id)
    
    query = f"UPDATE contacts SET {', '.join(fields)} WHERE id = ?"
    
    cursor.execute(query, values)
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    
    return success

def delete_contact(contact_id):
    """Delete a contact"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM contacts WHERE id = ?', (contact_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    
    return success

def delete_all_contacts():
    """Delete all contacts safely and reset the database with explicit confirmation flag"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM contacts')
    deleted_count = cursor.rowcount

    
    conn.commit()
    conn.close()

    return {"success": True, "deleted": deleted_count}



def search_contacts(query):
    """Search contacts by name, phone, or email"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    search_term = f"%{query}%"
    cursor.execute('''
        SELECT * FROM contacts 
        WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
        ORDER BY name ASC
    ''', (search_term, search_term, search_term))
    
    contacts = cursor.fetchall()
    conn.close()
    
    return [dict(contact) for contact in contacts]

def get_contacts_by_tag(tag):
    """Get all contacts with a specific tag"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM contacts WHERE tag = ? ORDER BY name ASC', (tag,))
    contacts = cursor.fetchall()
    conn.close()
    
    return [dict(contact) for contact in contacts]

def bulk_insert_contacts(contacts_list):
    """Insert multiple contacts at once (for file uploads)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    inserted = 0
    for contact in contacts_list:
        try:
            cursor.execute('''
                INSERT INTO contacts (name, phone, email, tag, notes)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                contact.get('name', ''),
                contact.get('phone', ''),
                contact.get('email', ''),
                contact.get('tag', 'General'),
                contact.get('notes', '')
            ))
            inserted += 1
        except Exception as e:
            print(f"Error inserting contact: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    return inserted

# Initialize database when module is imported
if __name__ != '__main__':
    init_db()