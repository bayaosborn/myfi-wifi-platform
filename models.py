from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

db = SQLAlchemy()

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    group_code = db.Column(db.String(10), unique=True, nullable=False)
    target_amount = db.Column(db.Float, default=0.0)
    current_balance = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)
    password_revealed = db.Column(db.Boolean, default=False)
    week_start = db.Column(db.DateTime, default=datetime.utcnow)
    week_end = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))
    status = db.Column(db.String(20), default='pending')  # pending/active/expired
    
    members = db.relationship('Member', backref='group', lazy=True)
    payments = db.relationship('Payment', backref='group', lazy=True)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(15))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    amount_contributed = db.Column(db.Float, default=0.0)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    mpesa_code = db.Column(db.String(20))
    verified = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    member = db.relationship('Member', backref='payments')

class WiFiCredential(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ssid = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    valid_from = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    member = db.relationship('Member', backref='user', uselist=False)