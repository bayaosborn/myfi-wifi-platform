"""
Phone Number Utilities for MyFi - SIMPLIFIED
"""

import re
import bcrypt

# Kenya phone pattern
KENYA_PATTERN = re.compile(
    r'^(?:254|\+254|0)?(7(?:[0-9][0-9]|0[0-8]|9[0-2])[0-9]{6})$'
)

def normalize_phone(phone):
    """
    Normalize phone to 254 format (NO plus sign)
    0759335278 -> 254759335278
    759335278 -> 254759335278
    +254759335278 -> 254759335278
    """
    if not phone:
        return None
    
    # Remove ALL non-digit characters (including +)
    phone = re.sub(r'\D', '', phone.strip())
    
    # Match pattern
    match = KENYA_PATTERN.match(phone)
    if match:
        core = match.group(1)  # Get the 9-digit number (7XXXXXXXX)
        return f'254{core}'  # NO plus sign
    
    return None

def is_valid_phone(phone):
    """Check if phone is valid"""
    return normalize_phone(phone) is not None

def hash_pin(pin):
    """Hash PIN with bcrypt"""
    if not pin or not pin.isdigit():
        raise ValueError("PIN must be digits only")
    
    if len(pin) not in [4, 6]:
        raise ValueError("PIN must be 4 or 6 digits")
    
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pin.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_pin(pin, pin_hash):
    """Verify PIN against hash"""
    if not pin or not pin_hash:
        return False
    
    try:
        return bcrypt.checkpw(pin.encode('utf-8'), pin_hash.encode('utf-8'))
    except Exception as e:
        print(f"PIN verification error: {e}")
        return False