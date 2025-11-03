# routes/admin_tools.py - MIGRATED TO SUPABASE

from flask import Blueprint, render_template, jsonify, request, session
from supabase import create_client
from app.utils.decorators import admin_required
from werkzeug.security import generate_password_hash
from datetime import datetime
import random
import os
from dotenv import load_dotenv

load_dotenv()

admin_tools_bp = Blueprint('admin_tools', __name__, url_prefix='/admin/tools')

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# ============================================
# RENDER PAGES
# ============================================

@admin_tools_bp.route('/database')
@admin_required
def database_tools():
    """Database diagnostic tools page"""
    return render_template('admin/tools/database.html')


@admin_tools_bp.route('/realtime')
@admin_required
def realtime_monitor():
    """Real-time activity monitor"""
    return render_template('admin/tools/realtime.html')


@admin_tools_bp.route('/terminal')
@admin_required
def admin_terminal():
    """Admin terminal"""
    return render_template('admin/tools/terminal.html')


# ============================================
# API ENDPOINTS
# ============================================

@admin_tools_bp.route('/api/test-connection')
@admin_required
def test_connection():
    """Test Supabase connection"""
    try:
        # Test query
        result = supabase.table('user').select('id').limit(1).execute()
        
        return jsonify({
            "status": "connected",
            "database_type": "Supabase (PostgreSQL)",
            "url": os.getenv('SUPABASE_URL'),
            "test_query": "success"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }), 500


@admin_tools_bp.route('/api/list-tables')
@admin_required
def list_tables():
    """List all tables with row counts"""
    try:
        tables = ['user', 'group', 'member', 'payment', 'wifi_credential']
        table_info = []
        
        for table in tables:
            try:
                result = supabase.table(table).select('*', count='exact').execute()
                row_count = result.count if hasattr(result, 'count') else len(result.data)
                
                table_info.append({
                    "name": table,
                    "rows": row_count
                })
            except Exception as e:
                table_info.append({
                    "name": table,
                    "rows": "Error",
                    "error": str(e)
                })
        
        return jsonify({
            "status": "success",
            "table_count": len(tables),
            "tables": table_info
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@admin_tools_bp.route('/api/create-test-user', methods=['POST'])
@admin_required
def create_test_user():
    """Create a test user"""
    try:
        test_username = f"test_{random.randint(1000, 9999)}"
        test_password = "password123"
        
        new_user = {
            'username': test_username,
            'password': generate_password_hash(test_password),
            'wallet_balance': 0,
            'wallet_status': 'not_paid',
            'role': 'user',
            'created_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.table('user').insert(new_user).execute()
        
        if result.data:
            user = result.data[0]
            return jsonify({
                "status": "success",
                "user": {
                    "id": user['id'],
                    "username": user['username'],
                    "password": test_password,
                    "created_at": user['created_at']
                }
            })
        else:
            return jsonify({"status": "error", "error": "Failed to create user"}), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@admin_tools_bp.route('/api/system-stats')
@admin_required
def system_stats():
    """Get comprehensive system statistics"""
    try:
        # Get counts from Supabase
        users = supabase.table('user').select('*', count='exact').execute()
        groups = supabase.table('group').select('*', count='exact').execute()
        members = supabase.table('member').select('*', count='exact').execute()
        payments = supabase.table('payment').select('*').execute()
        
        pending_payments = [p for p in payments.data if not p.get('verified')]
        verified_payments = [p for p in payments.data if p.get('verified')]
        
        active_groups = [g for g in groups.data if g.get('status') == 'active']
        pending_groups = [g for g in groups.data if g.get('status') == 'pending']
        expired_groups = [g for g in groups.data if g.get('status') == 'expired']
        
        stats = {
            "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            "database": {
                "users": len(users.data),
                "groups": len(groups.data),
                "members": len(members.data),
                "payments": len(payments.data),
                "pending_payments": len(pending_payments),
                "verified_payments": len(verified_payments)
            },
            "groups": {
                "active": len(active_groups),
                "pending": len(pending_groups),
                "expired": len(expired_groups)
            },
            "revenue": {
                "total": sum(float(p.get('amount', 0)) for p in verified_payments),
                "pending": sum(float(p.get('amount', 0)) for p in pending_payments)
            }
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@admin_tools_bp.route('/api/recent-activity')
@admin_required
def recent_activity():
    """Get recent system activity"""
    try:
        # Recent users (last 10)
        users_result = supabase.table('user').select('*').order('created_at', desc=True).limit(10).execute()
        
        # Recent groups
        groups_result = supabase.table('group').select('*').order('created_at', desc=True).limit(10).execute()
        
        # Recent payments
        payments_result = supabase.table('payment').select('*').order('created_at', desc=True).limit(10).execute()
        
        return jsonify({
            "users": [{
                "id": u['id'],
                "username": u['username'],
                "created_at": u['created_at']
            } for u in users_result.data],
            "groups": [{
                "id": g['id'],
                "name": g['name'],
                "code": g.get('group_code'),
                "status": g.get('status'),
                "created_at": g['created_at']
            } for g in groups_result.data],
            "payments": [{
                "id": p['id'],
                "amount": p.get('amount'),
                "verified": p.get('verified'),
                "member_name": p.get('member_name', 'Unknown'),
                "created_at": p['created_at']
            } for p in payments_result.data]
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@admin_tools_bp.route('/api/execute-sql', methods=['POST'])
@admin_required
def execute_sql():
    """Execute custom SQL query via Supabase RPC"""
    return jsonify({
        "status": "not_supported",
        "message": "Direct SQL execution not available in Supabase REST API. Use Supabase Dashboard SQL Editor instead."
    }), 501