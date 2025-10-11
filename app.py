from flask import Flask, render_template, jsonify, request
import qrcode
import io
import base64
from models import db, Group, Member, Payment, WiFiCredential
from accounts import init_accounts
import random
import string


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///myfi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
init_accounts(app, db)

# Create tables on startup
with app.app_context():
    db.create_all()
    print("✅ Database tables created")

# Network credentials
SSID = "poaA7rgIU"
PASSWORD = "b8K!p2Zr#V7m"
SECURITY = "WPA"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    wifi_string = f"WIFI:T:{SECURITY};S:{SSID};P:{PASSWORD};;"
    img = qrcode.make(wifi_string)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return render_template('index.html', qr_image=qr_b64, ssid=SSID)

@app.route('/test-db')
def test_db():
    test_group = Group(
        name="Test Group",
        group_code="TEST123",
        target_amount=400
    )
    db.session.add(test_group)
    db.session.commit()
    
    groups = Group.query.all()
    return jsonify({
        "status": "success",
        "groups_count": len(groups),
        "groups": [{"id": g.id, "name": g.name, "code": g.group_code} for g in groups]
    })

@app.route('/groups/join')
def join_group_page():
    return render_template('join_group.html')

@app.route('/api/create-group', methods=['POST'])
def create_group():
    data = request.get_json()
    
    target = 400
    
    new_group = Group(
        name=data['group_name'],
        group_code=data['group_code'],
        target_amount=target
    )
    db.session.add(new_group)
    db.session.commit()
    
    member = Member(
        name=data['member_name'],
        phone=data['phone'],
        group_id=new_group.id
    )
    db.session.add(member)
    db.session.commit()
    
    return jsonify({
        "message": "Group created successfully!",
        "group_code": new_group.group_code,
        "group_id": new_group.id
    })

@app.route('/api/join-group', methods=['POST'])
def join_group():
    data = request.get_json()
    
    group = Group.query.filter_by(group_code=data['group_code']).first()
    if not group:
        return jsonify({"message": "Group not found!"}), 404
    
    member = Member(
        name=data['member_name'],
        phone=data['phone'],
        group_id=group.id
    )
    db.session.add(member)
    db.session.commit()
    
    return jsonify({
        "message": f"Joined {group.name} successfully!",
        "group_id": group.id
    })

@app.route('/groups')
def groups_page():
    all_groups = Group.query.all()
    return render_template('groups.html', groups=all_groups)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
