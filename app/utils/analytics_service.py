# utils/analytics_service.py - MIGRATED TO SUPABASE

from datetime import datetime, timedelta
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

class AnalyticsService:
    """MYFI Analytics - Business Intelligence (Supabase)"""
    
    def __init__(self):
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
    
    def get_dashboard_stats(self):
        """Get main dashboard statistics"""
        try:
            # Get counts
            users = self.supabase.table('user').select('*', count='exact').execute()
            groups = self.supabase.table('group').select('*', count='exact').execute()
            payments = self.supabase.table('payment').select('*').execute()
            
            total_users = len(users.data)
            total_groups = len(groups.data)
            
            # Filter active/expired groups
            active_groups = [g for g in groups.data if g.get('status') == 'active']
            expired_groups = [g for g in groups.data if g.get('status') == 'expired']
            
            # Calculate revenue
            verified_payments = [p for p in payments.data if p.get('verified')]
            total_revenue = sum(float(p.get('amount', 0)) for p in verified_payments)
            
            pending_payments = [p for p in payments.data if not p.get('verified') and not p.get('rejected')]
            
            return {
                "total_users": total_users,
                "total_groups": total_groups,
                "active_groups": len(active_groups),
                "expired_groups": len(expired_groups),
                "total_revenue": total_revenue,
                "pending_payments": len(pending_payments)
            }
        except Exception as e:
            print(f"❌ Analytics error: {e}")
            return {
                "total_users": 0,
                "total_groups": 0,
                "active_groups": 0,
                "expired_groups": 0,
                "total_revenue": 0,
                "pending_payments": 0
            }
    
    def get_revenue_trend(self, days=30):
        """Get daily revenue for last N days"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get verified payments
            payments = self.supabase.table('payment').select('*').eq('verified', True).execute()
            
            # Group by date
            revenue_by_date = {}
            for payment in payments.data:
                created_at = datetime.fromisoformat(payment['created_at'].replace('Z', '+00:00'))
                if created_at >= start_date:
                    date_key = created_at.strftime('%Y-%m-%d')
                    revenue_by_date[date_key] = revenue_by_date.get(date_key, 0) + float(payment.get('amount', 0))
            
            return revenue_by_date
        except Exception as e:
            print(f"❌ Revenue trend error: {e}")
            return {}
    
    def get_group_formation_rate(self):
        """Groups created per day"""
        try:
            groups = self.supabase.table('group').select('*').execute()
            
            groups_by_date = {}
            for group in groups.data:
                created_at = datetime.fromisoformat(group['created_at'].replace('Z', '+00:00'))
                date_key = created_at.strftime('%Y-%m-%d')
                groups_by_date[date_key] = groups_by_date.get(date_key, 0) + 1
            
            return groups_by_date
        except Exception as e:
            print(f"❌ Group formation error: {e}")
            return {}
    
    def get_user_retention(self):
        """Users with active groups vs total users"""
        try:
            users = self.supabase.table('user').select('*').execute()
            
            total_users = len(users.data)
            active_users = len([u for u in users.data if u.get('member_id')])
            
            return {
                "total": total_users,
                "active": active_users,
                "retention_rate": (active_users / total_users * 100) if total_users > 0 else 0
            }
        except Exception as e:
            print(f"❌ User retention error: {e}")
            return {"total": 0, "active": 0, "retention_rate": 0}
    
    def get_popular_group_sizes(self):
        """Distribution of group sizes"""
        try:
            groups = self.supabase.table('group').select('*, member(*)').execute()
            
            size_distribution = {1: 0, 2: 0, 3: 0, 4: 0}
            for group in groups.data:
                size = len(group.get('member', []))
                if size in size_distribution:
                    size_distribution[size] += 1
            
            return size_distribution
        except Exception as e:
            print(f"❌ Group sizes error: {e}")
            return {1: 0, 2: 0, 3: 0, 4: 0}
    
    def get_churn_analysis(self):
        """Users who left groups or expired"""
        try:
            now = datetime.utcnow()
            
            groups = self.supabase.table('group').select('*, member(*)').eq('status', 'expired').execute()
            
            churned_users = sum(len(g.get('member', [])) for g in groups.data)
            
            return {
                "expired_groups": len(groups.data),
                "churned_users": churned_users
            }
        except Exception as e:
            print(f"❌ Churn analysis error: {e}")
            return {"expired_groups": 0, "churned_users": 0}
