from models import db, Group
from datetime import datetime

class WiFiService:
    """WiFi and group management service"""
    
    @staticmethod
    def check_expired_groups():
        """Check and expire groups that have passed their week_end date"""
        try:
            now = datetime.utcnow()
            expired_groups = Group.query.filter(
                Group.week_end <= now,
                Group.status != 'expired'
            ).all()
            
            for group in expired_groups:
                group.status = 'expired'
                group.password_revealed = False
            
            if expired_groups:
                db.session.commit()
                print(f"✅ Expired {len(expired_groups)} groups")
            
            return len(expired_groups)
        except Exception as e:
            print(f"❌ Error checking expired groups: {e}")
            db.session.rollback()
            return 0
    
    @staticmethod
    def activate_group_if_ready(group):
        """Activate group if payment target is reached"""
        if group.current_balance >= group.target_amount:
            if not group.password_revealed:
                group.password_revealed = True
                group.status = 'active'
                db.session.commit()
                return True
        return False