# Create: routes/cron.py
from flask import Blueprint
from supabase import create_client
from datetime import datetime
import os

cron_bp = Blueprint('cron', __name__)

@cron_bp.route('/cron/expire-groups', methods=['GET', 'POST'])
def expire_groups():
    """Mark expired groups as expired"""
    try:
        supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
        
        now = datetime.utcnow().isoformat()
        
        # Find active groups that have passed week_end
        result = supabase.table('group').select('*').eq('status', 'active').lt('week_end', now).execute()
        
        expired_count = 0
        for group in result.data:
            supabase.table('group').update({'status': 'expired'}).eq('id', group['id']).execute()
            expired_count += 1
        
        print(f"✅ Expired {expired_count} groups")
        return {"success": True, "expired": expired_count}
    except Exception as e:
        print(f"Error expiring groups: {e}")
        return {"success": False, "error": str(e)}