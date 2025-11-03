# utils/wifi_service.py - MIGRATED TO SUPABASE

from datetime import datetime
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

class WiFiService:
    """WiFi and group management service (Supabase)"""
    
    def __init__(self):
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
    
    def check_expired_groups(self):
        """Check and expire groups that have passed their week_end date"""
        try:
            now = datetime.utcnow()
            
            # Get all active groups
            groups = self.supabase.table('group').select('*').neq('status', 'expired').execute()
            
            expired_count = 0
            for group in groups.data:
                week_end = datetime.fromisoformat(group['week_end'].replace('Z', '+00:00'))
                
                if week_end <= now:
                    # Expire this group
                    self.supabase.table('group').update({
                        'status': 'expired',
                        'password_revealed': False
                    }).eq('id', group['id']).execute()
                    
                    expired_count += 1
            
            if expired_count > 0:
                print(f"✅ Expired {expired_count} groups")
            
            return expired_count
        except Exception as e:
            print(f"❌ Error checking expired groups: {e}")
            return 0
    
    def activate_group_if_ready(self, group_id):
        """Activate group if payment target is reached"""
        try:
            # Get group
            result = self.supabase.table('group').select('*').eq('id', group_id).execute()
            
            if not result.data:
                return False
            
            group = result.data[0]
            current_balance = float(group.get('current_balance', 0))
            target_amount = float(group.get('target_amount', 0))
            
            if current_balance >= target_amount:
                if not group.get('password_revealed'):
                    self.supabase.table('group').update({
                        'password_revealed': True,
                        'status': 'active'
                    }).eq('id', group_id).execute()
                    
                    print(f"✅ Activated group {group_id}")
                    return True
            
            return False
        except Exception as e:
            print(f"❌ Error activating group: {e}")
            return False
