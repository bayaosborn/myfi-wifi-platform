from flask import Blueprint, request, jsonify, session, render_template
from datetime import datetime
import json
from pywebpush import webpush, WebPushException
import os
from supabase import create_client

notifications_bp = Blueprint('notifications', __name__)

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY')
VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY')
VAPID_CLAIM_EMAIL = os.getenv('VAPID_CLAIM_EMAIL')

# ============ NOTIFICATION SETTINGS PAGE ============

@notifications_bp.route('/notifications-setup')
def notifications_setup():
    """
    Page shown after location capture to set up notifications
    """
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
    
    return render_template(
        'notifications/setup.html',
        vapid_public_key=VAPID_PUBLIC_KEY
    )

# ============ SUBSCRIPTION MANAGEMENT ============

@notifications_bp.route('/api/notifications/subscribe', methods=['POST'])
def subscribe():
    """
    Save push subscription from browser
    """
    try:
        user_id = session.get('user_id')
        device_id = session.get('device_id')
        
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
        
        subscription_data = request.get_json()
        
        # Extract subscription details
        endpoint = subscription_data.get('endpoint')
        keys = subscription_data.get('keys', {})
        p256dh = keys.get('p256dh')
        auth = keys.get('auth')
        
        if not all([endpoint, p256dh, auth]):
            return jsonify({'error': 'Invalid subscription data'}), 400
        
        # Check if subscription already exists
        existing = supabase.table('push_subscriptions')\
            .select('id')\
            .eq('endpoint', endpoint)\
            .execute()
        
        if existing.data:
            # Update existing
            supabase.table('push_subscriptions').update({
                'last_used_at': datetime.utcnow().isoformat(),
                'is_active': True
            }).eq('endpoint', endpoint).execute()
        else:
            # Create new subscription
            subscription_record = {
                'user_id': user_id,
                'device_id': device_id,
                'endpoint': endpoint,
                'p256dh_key': p256dh,
                'auth_key': auth,
                'user_agent': request.headers.get('User-Agent'),
                'is_active': True
            }
            
            supabase.table('push_subscriptions').insert(subscription_record).execute()
        
        # Create default notification preferences if don't exist
        prefs_check = supabase.table('notification_preferences')\
            .select('id')\
            .eq('user_id', user_id)\
            .execute()
        
        if not prefs_check.data:
            prefs = {
                'user_id': user_id,
                'weather_enabled': True,
                'service_enabled': True,
                'promo_enabled': True,
                'social_enabled': False,
                'system_enabled': True,
                'quiet_hours_enabled': False,
                'location_radius_km': 5
            }
            supabase.table('notification_preferences').insert(prefs).execute()
        
        # Send welcome notification
        send_notification_to_user(
            user_id=user_id,
            title="🎉 Notifications Enabled!",
            message="You'll now get weather alerts, service updates, and more.",
            category='system',
            priority='low'
        )
        
        return jsonify({
            'success': True,
            'message': 'Notifications enabled successfully'
        }), 200
        
    except Exception as e:
        print(f"Error subscribing: {e}")
        return jsonify({'error': str(e)}), 500

# ============ SENDING NOTIFICATIONS ============







def send_notification_to_user(user_id, title, message, category='system', priority='medium', action_url=None, icon_url=None):
    """
    Send notification - just save to DB, polling handles the rest
    """
    try:
        notification_record = {
            'user_id': user_id,
            'title': title,
            'message': message,
            'category': category,
            'priority': priority,
            'action_url': action_url,
            'icon_url': icon_url,
            'is_read': False,
            'created_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('notifications').insert(notification_record).execute()
        print(f"✅ Notification saved for user {user_id}")
        
        # Polling will pick this up within 5 seconds!
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving notification: {e}")
        return False



# Add this to notifications.py

@notifications_bp.route('/api/whoami')
def whoami():
    """Return current user ID"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    
    return jsonify({'user_id': user_id})


# ============ NOTIFICATIONS CENTER ============

@notifications_bp.route('/notifications')
def notifications_center():
    """
    Page showing all user notifications
    """
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
    
    return render_template('notifications/center.html')

@notifications_bp.route('/api/notifications', methods=['GET'])
def get_notifications():
    """
    Fetch user's notifications (for notifications center)
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
        
        # Get notifications (latest 50)
        notifications = supabase.table('notifications')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .limit(50)\
            .execute()
        
        return jsonify({
            'success': True,
            'notifications': notifications.data
        }), 200
        
    except Exception as e:
        print(f"Error fetching notifications: {e}")
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/api/notifications/<int:notification_id>/read', methods=['PATCH'])
def mark_read(notification_id):
    """
    Mark notification as read
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
        
        supabase.table('notifications').update({
            'is_read': True,
            'read_at': datetime.utcnow().isoformat()
        }).eq('id', notification_id).eq('user_id', user_id).execute()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ PREFERENCES ============

@notifications_bp.route('/notifications/settings')
def notification_settings():
    """
    Page for managing notification preferences
    """
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('auth.login'))
    
    # Get current preferences
    prefs = supabase.table('notification_preferences')\
        .select('*')\
        .eq('user_id', user_id)\
        .single()\
        .execute()
    
    return render_template(
        'notifications/settings.html',
        preferences=prefs.data if prefs.data else {}
    )

@notifications_bp.route('/api/notifications/preferences', methods=['PATCH'])
def update_preferences():
    """
    Update notification preferences
    """
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Unauthorized'}), 401
        
        data = request.get_json()
        
        # Update preferences
        supabase.table('notification_preferences').update({
            **data,
            'updated_at': datetime.utcnow().isoformat()
        }).eq('user_id', user_id).execute()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@notifications_bp.route('/test-notification')
def test_notification():
    """
    Send yourself a test notification
    """
    user_id = session.get('user_id')
    if not user_id:
        return "Not logged in", 401
    
    try:
        send_notification_to_user(
            user_id=user_id,
            title="🎉 Welcome to Myfi!",
            message="Notifications are working! You'll get important updates here.",
            category='system',
            priority='low'
        )
        return "Test notification sent! Check your browser."
    except Exception as e:
        return f"Error: {str(e)}", 500



@notifications_bp.route('/debug-subscription')
def debug_subscription():
    """Check subscription status"""
    user_id = session.get('user_id')
    if not user_id:
        return "Not logged in", 401
    
    try:
        # Get subscriptions
        subs = supabase.table('push_subscriptions')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('is_active', True)\
            .execute()
        
        html = f"<h2>Subscription Debug</h2>"
        html += f"<p>User ID: {user_id}</p>"
        html += f"<p>Active Subscriptions: {len(subs.data)}</p>"
        
        if subs.data:
            for sub in subs.data:
                html += f"<hr><p><strong>Endpoint:</strong> {sub['endpoint'][:50]}...</p>"
                html += f"<p><strong>Created:</strong> {sub.get('created_at')}</p>"
        else:
            html += "<p><strong>NO SUBSCRIPTIONS FOUND!</strong></p>"
            html += "<p>Go to /notifications-setup to enable notifications</p>"
        
        return html
    except Exception as e:
        return f"Error: {str(e)}", 500



@notifications_bp.route('/debug-notifications')
def debug_notifications():
    """See all notifications in database"""
    user_id = session.get('user_id')
    if not user_id:
        return "Not logged in", 401
    
    try:
        # Get all notifications for user
        notifs = supabase.table('notifications')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .execute()
        
        html = f"<h2>Notifications Debug</h2>"
        html += f"<p>User ID: {user_id}</p>"
        html += f"<p>Total Notifications: {len(notifs.data)}</p><hr>"
        
        if notifs.data:
            for notif in notifs.data:
                html += f"<div style='border:1px solid #ccc; padding:10px; margin:10px 0;'>"
                html += f"<strong>{notif['title']}</strong><br>"
                html += f"{notif['message']}<br>"
                html += f"<small>Category: {notif['category']} | Created: {notif.get('created_at')}</small>"
                html += f"</div>"
        else:
            html += "<p><strong>NO NOTIFICATIONS FOUND IN DATABASE!</strong></p>"
        
        return html
    except Exception as e:
        return f"Error: {str(e)}", 500




@notifications_bp.route('/api/config')
def get_config():
    """Return public config for frontend"""
    return jsonify({
        'supabase_url': os.getenv('SUPABASE_URL'),
        'supabase_anon_key': os.getenv('SUPABASE_KEY')  # This should be your ANON key, not service key
    })