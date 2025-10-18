from models import Group, User, Payment, Member
from datetime import datetime, timedelta
from sqlalchemy import func

class AnalyticsService:
    """Pamoja Analytics - Business Intelligence"""
    
    @staticmethod
    def get_dashboard_stats():
        """Get main dashboard statistics"""
        total_users = User.query.count()
        total_groups = Group.query.count()
        active_groups = Group.query.filter_by(status='active').count()
        expired_groups = Group.query.filter_by(status='expired').count()
        
        verified_payments = Payment.query.filter_by(verified=True).all()
        total_revenue = sum(p.amount for p in verified_payments)
        
        pending_payments = Payment.query.filter_by(verified=False).count()
        
        return {
            "total_users": total_users,
            "total_groups": total_groups,
            "active_groups": active_groups,
            "expired_groups": expired_groups,
            "total_revenue": total_revenue,
            "pending_payments": pending_payments
        }

    @staticmethod
    def get_revenue_trend(days=30):
        """Get daily revenue for last N days"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        payments = Payment.query.filter(
            Payment.verified == True,
            Payment.created_at >= start_date
        ).all()
        
        # Group by date
        revenue_by_date = {}
        for payment in payments:
            date_key = payment.created_at.strftime('%Y-%m-%d')
            revenue_by_date[date_key] = revenue_by_date.get(date_key, 0) + payment.amount
        
        return revenue_by_date
    
    @staticmethod
    def get_group_formation_rate():
        """Groups created per day"""
        groups = Group.query.all()
        
        groups_by_date = {}
        for group in groups:
            date_key = group.created_at.strftime('%Y-%m-%d')
            groups_by_date[date_key] = groups_by_date.get(date_key, 0) + 1
        
        return groups_by_date
    
    @staticmethod
    def get_user_retention():
        """Users with active groups vs total users"""
        total_users = User.query.count()
        active_users = User.query.filter(User.member_id.isnot(None)).count()
        
        return {
            "total": total_users,
            "active": active_users,
            "retention_rate": (active_users / total_users * 100) if total_users > 0 else 0
        }
    
    @staticmethod
    def get_popular_group_sizes():
        """Distribution of group sizes"""
        groups = Group.query.all()
        
        size_distribution = {1: 0, 2: 0, 3: 0, 4: 0}
        for group in groups:
            size = len(group.members)
            if size in size_distribution:
                size_distribution[size] += 1
        
        return size_distribution
    
    @staticmethod
    def get_churn_analysis():
        """Users who left groups or expired"""
        now = datetime.utcnow()
        
        expired_groups = Group.query.filter(
            Group.status == 'expired',
            Group.week_end <= now
        ).all()
        
        churned_users = sum(len(g.members) for g in expired_groups)
        
        return {
            "expired_groups": len(expired_groups),
            "churned_users": churned_users
        }


