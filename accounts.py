from flask import Blueprint, jsonify, request
from models import db, Group, Member, Payment

accounts_bp = Blueprint('accounts', __name__)

def init_accounts(app, db_instance):
    app.register_blueprint(accounts_bp)

@accounts_bp.route('/accounts', methods=['GET'])
def list_accounts():
    """List all groups."""
    groups = Group.query.all()
    return jsonify([{
        "id": g.id, 
        "name": g.name, 
        "code": g.group_code,
        "balance": g.current_balance,
        "target": g.target_amount
    } for g in groups])

@accounts_bp.route('/accounts/add', methods=['POST'])
def add_account():
    """Create new group."""
    data = request.get_json()
    new_group = Group(
        name=data['name'],
        group_code=data['code'],
        target_amount=data.get('target_amount', 400)
    )
    db.session.add(new_group)
    db.session.commit()
    return jsonify({"message": "Group created successfully"}), 201
