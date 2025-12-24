"""
Logic Helper Functions
Reusable utility functions for Logic engine
"""

from datetime import datetime, timedelta

def get_current_date() -> str:
    """
    Get current date in readable format
    
    Returns:
        String like "Friday, December 20, 2024"
    """
    return datetime.now().strftime('%A, %B %d, %Y')

def get_current_time() -> str:
    """
    Get current time in 12-hour format
    
    Returns:
        String like "02:30 PM"
    """
    return datetime.now().strftime('%I:%M %p')

def get_tomorrow_date() -> str:
    """
    Get tomorrow's date
    
    Returns:
        String like "Saturday, December 21, 2024"
    """
    tomorrow = datetime.now() + timedelta(days=1)
    return tomorrow.strftime('%A, %B %d, %Y')

def get_day_of_week(days_ahead: int = 0) -> str:
    """
    Get day of week for X days from now
    
    Args:
        days_ahead: Number of days from today (0 = today)
        
    Returns:
        Day name like "Monday"
    """
    target_date = datetime.now() + timedelta(days=days_ahead)
    return target_date.strftime('%A')