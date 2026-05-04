from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

HBC_CHOICES = ['Nazareth', 'Judea', 'Jerusalem', 'Vicars Care']
DEPARTMENT_CHOICES = ['KAMA', 'Mothers Union', 'KAYO', 'Choir', 'ACWF', 'ACMF']
GIVING_TYPE_CHOICES = [
    'Tithe', 'Thanksgiving', 'Development', 'Baptism',
    'Confirmation', 'KAMA Enrollment', 'MU Enrollment', 'KAYO Enrollment',
    'Registration'
]
ROLE_CHOICES = ['Admin', 'Vicar', 'Vice Chairman', 'Treasurer', 'Secretary', 'HBC Leader', 'Member', 'Peoples Warden', 'Vicars Warden']
PAYMENT_METHODS = ['Cash', 'M-Pesa', 'Account']

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(30), nullable=False)
    hbc_leader_for = db.Column(db.String(30), nullable=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=True)
    member = db.relationship('Member', backref='user', uselist=False)
    must_change_password = db.Column(db.Boolean, default=True)

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    unique_member_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    spouse_name = db.Column(db.String(100), nullable=True)
    spouse_contact = db.Column(db.String(20), nullable=True)
    hbc = db.Column(db.String(30), nullable=False)
    department = db.Column(db.String(30), nullable=False)
    photo_filename = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    children = db.relationship('Child', backref='parent', lazy=True, cascade='all, delete-orphan')
    givings = db.relationship('Giving', backref='member', lazy=True)
    payments = db.relationship('Payment', backref='member', lazy=True)

    @property
    def number_of_children(self):
        return len(self.children)

class Child(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)

class Giving(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    giving_type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='pending')

class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class PendingMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(20), nullable=False)
    spouse_name = db.Column(db.String(100), nullable=True)
    spouse_contact = db.Column(db.String(20), nullable=True)
    hbc = db.Column(db.String(30), nullable=False)
    department = db.Column(db.String(30), nullable=False)
    children_data = db.Column(db.Text, nullable=True)
    photo_filename = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='pending')
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.String(200), nullable=True)
    username = db.Column(db.String(80), nullable=True)
    temp_password = db.Column(db.String(100), nullable=True)
    total_fee = db.Column(db.Float, default=0.0)
    mpesa_code = db.Column(db.String(100), nullable=True)
    payment_status = db.Column(db.String(20), default='pending')
    payment_id = db.Column(db.Integer, db.ForeignKey('payment.id'), nullable=True)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(20), nullable=False)
    transaction_code = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='completed')
    recorded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    receipt_no = db.Column(db.String(50), unique=True, nullable=True)
    notes = db.Column(db.String(200), nullable=True)
