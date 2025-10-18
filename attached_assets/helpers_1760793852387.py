# utils/helpers.py

import random
import string
from datetime import datetime, timedelta

def generate_group_code(length=6):
    """
    Generate a random group code
    
    Args:
        length (int): Length of code (default 6)
    
    Returns:
        str: Random uppercase alphanumeric code (e.g., 'A3X9K2')
    """
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def format_currency(amount):
    """
    Format amount as currency
    
    Args:
        amount (float): Amount to format
    
    Returns:
        str: Formatted currency (e.g., '350 KSH')
    """
    return f"{int(amount)} KSH"


def calculate_time_remaining(end_date):
    """
    Calculate time remaining until expiration
    
    Args:
        end_date (datetime): Expiration date
    
    Returns:
        dict: Days, hours, minutes remaining
    """
    now = datetime.utcnow()
    if end_date <= now:
        return {"days": 0, "hours": 0, "minutes": 0, "expired": True}
    
    delta = end_date - now
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    
    return {
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "expired": False
    }


def validate_phone(phone):
    """
    Validate Kenyan phone number
    
    Args:
        phone (str): Phone number to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    # Remove spaces and special characters
    phone = ''.join(filter(str.isdigit, phone))
    
    # Kenyan numbers: 10 digits starting with 07 or 01
    # Or 12 digits starting with 254
    if len(phone) == 10 and phone.startswith(('07', '01')):
        return True
    if len(phone) == 12 and phone.startswith('254'):
        return True
    
    return False


def format_phone(phone):
    """
    Format phone to standard Kenyan format
    
    Args:
        phone (str): Phone number
    
    Returns:
        str: Formatted phone (e.g., '0712345678' or '254712345678')
    """
    phone = ''.join(filter(str.isdigit, phone))
    
    # Convert to 254 format if starts with 0
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    
    return phone


def sanitize_input(text, max_length=100):
    """
    Sanitize user input
    
    Args:
        text (str): Input text
        max_length (int): Maximum allowed length
    
    Returns:
        str: Sanitized text
    """
    if not text:
        return ""
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Limit length
    text = text[:max_length]
    
    return text


def get_week_dates():
    """
    Get start and end dates for current week
    
    Returns:
        tuple: (week_start, week_end) datetime objects
    """
    now = datetime.utcnow()
    week_start = now
    week_end = now + timedelta(days=7)
    
    return week_start, week_end


def is_valid_mpesa_code(code):
    """
    Validate M-Pesa transaction code format
    
    Args:
        code (str): M-Pesa code
    
    Returns:
        bool: True if valid format
    """
    if not code:
        return False
    
    # M-Pesa codes are typically 10 characters alphanumeric
    code = code.strip().upper()
    
    if len(code) < 8 or len(code) > 15:
        return False
    
    # Must contain letters and numbers
    has_letter = any(c.isalpha() for c in code)
    has_digit = any(c.isdigit() for c in code)
    
    return has_letter and has_digit


def calculate_group_progress(current_balance, target_amount):
    """
    Calculate group payment progress
    
    Args:
        current_balance (float): Current group balance
        target_amount (float): Target amount
    
    Returns:
        dict: Progress info
    """
    percentage = (current_balance / target_amount * 100) if target_amount > 0 else 0
    remaining = max(0, target_amount - current_balance)
    is_complete = current_balance >= target_amount
    
    return {
        "percentage": round(percentage, 1),
        "remaining": remaining,
        "is_complete": is_complete,
        "current": current_balance,
        "target": target_amount
    }


def get_user_display_name(user):
    """
    Get display name for user
    
    Args:
        user (User): User object
    
    Returns:
        str: Display name
    """
    if not user:
        return "Unknown"
    
    return user.username or f"User {user.id}"