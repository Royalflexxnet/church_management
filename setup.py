import os

os.makedirs("templates", exist_ok=True)
os.makedirs("static/uploads", exist_ok=True)

files = {
    "requirements.txt": """Flask==2.2.5
Flask-SQLAlchemy==3.0.3
Flask-Login==0.6.2
Flask-WTF==1.1.1
WTForms==3.0.1
email-validator==2.0.0
werkzeug==2.2.3
reportlab==4.2.2
""",
    "config.py": '''import os

class Config:
    SECRET_KEY = 'your-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///church.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
''',
    "models.py": '''from flask_sqlalchemy import SQLAlchemy
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
''',
    "forms.py": '''from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, FloatField, DateField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, Optional, Length, EqualTo, NumberRange
from models import HBC_CHOICES, DEPARTMENT_CHOICES, GIVING_TYPE_CHOICES, ROLE_CHOICES, PAYMENT_METHODS

class MemberForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    contact = StringField('Phone Number', validators=[DataRequired()])
    spouse_name = StringField('Spouse Name')
    spouse_contact = StringField('Spouse Contact')
    hbc = SelectField('HBC', choices=[(c,c) for c in HBC_CHOICES], validators=[DataRequired()])
    department = SelectField('Department', choices=[(c,c) for c in DEPARTMENT_CHOICES], validators=[DataRequired()])

class MemberWithLoginForm(MemberForm):
    username = StringField('Username (for login)', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Temporary Password', validators=[DataRequired(), Length(min=4)])
    payment_method = SelectField('Payment Method', choices=[('', 'None')] + [(m,m) for m in PAYMENT_METHODS], validators=[Optional()])
    payment_amount = FloatField('Amount Paid (KES)', validators=[Optional(), NumberRange(min=0)])
    transaction_code = StringField('Transaction Reference', validators=[Optional()])

class SelfRegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    contact = StringField('Phone Number', validators=[DataRequired()])
    spouse_name = StringField('Spouse Name')
    spouse_contact = StringField('Spouse Contact')
    hbc = SelectField('HBC', choices=[(c,c) for c in HBC_CHOICES], validators=[DataRequired()])
    department = SelectField('Department', choices=[(c,c) for c in DEPARTMENT_CHOICES], validators=[DataRequired()])
    username = StringField('Desired Username (for login)', validators=[DataRequired(), Length(min=3, max=80)])
    mpesa_code = StringField('M-Pesa Transaction Code', validators=[DataRequired()])

class GivingForm(FlaskForm):
    giving_type = SelectField('Giving Type', choices=[(c,c) for c in GIVING_TYPE_CHOICES], validators=[DataRequired()])
    amount = FloatField('Amount (KES)', validators=[DataRequired()])
    date = DateField('Date', default=None, validators=[Optional()])
    notes = TextAreaField('Notes')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Temporary Password', validators=[DataRequired(), Length(min=4)])
    role = SelectField('Role', choices=[(c,c) for c in ROLE_CHOICES if c != 'Member'], validators=[DataRequired()])
    hbc_leader_for = SelectField('If HBC Leader, which HBC?', choices=[('', 'None')] + [(c,c) for c in HBC_CHOICES])

class NoticeForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=4)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])

class ApprovalForm(FlaskForm):
    action = SelectField('Action', choices=[('approve', 'Approve'), ('reject', 'Reject')], validators=[DataRequired()])
    rejection_reason = TextAreaField('Rejection Reason (if rejecting)')
''',
    "auth.py": '''from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from forms import LoginForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            if user.must_change_password:
                flash('You must change your password before continuing.', 'warning')
                return redirect(url_for('change_password'))
            return redirect(url_for('index'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
''',
    "app.py": '''from flask import Flask, render_template, request, redirect, url_for, flash, abort, jsonify, send_file
from flask_login import LoginManager, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from config import Config
from models import db, User, Member, Child, Giving, Notice, PendingMember, Payment, DEPARTMENT_CHOICES
from forms import MemberForm, MemberWithLoginForm, GivingForm, UserForm, NoticeForm, ChangePasswordForm, SelfRegisterForm, ApprovalForm
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO
from datetime import datetime
from sqlalchemy import func
import os, random, string, json

app = Flask(__name__)
app.config.from_object(Config)
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
db.init_app(app)
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from auth import auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')

def require_password_change(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.must_change_password:
            if request.endpoint != 'change_password':
                flash('You must change your password before continuing.', 'warning')
                return redirect(url_for('change_password'))
        return f(*args, **kwargs)
    return decorated_function

def generate_unique_member_id():
    last_member = Member.query.order_by(Member.id.desc()).first()
    if last_member and last_member.unique_member_id:
        try:
            last_num = int(last_member.unique_member_id.split('-')[1])
            next_num = last_num + 1
        except:
            next_num = 1001
    else:
        next_num = 1001
    return f"ASMM-{next_num}"

def generate_receipt_no():
    return f"RCP-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000,9999)}"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def save_photo(file, prefix='member'):
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{prefix}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filename
    return None

def role_required(*allowed_roles):
    def wrapper(f):
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in allowed_roles:
                abort(403)
            return f(*args, **kwargs)
        decorated.__name__ = f.__name__
        return decorated
    return wrapper

def calculate_registration_fee(has_spouse, children_data):
    total = 200
    if has_spouse:
        total += 200
    for child in children_data:
        age = child.get('age')
        if age:
            if 13 <= age <= 18:
                total += 100
            elif 5 <= age <= 12:
                total += 50
    return total

def get_department_statistics():
    stats = {}
    for dept in DEPARTMENT_CHOICES:
        stats[dept] = Member.query.filter_by(department=dept).count()
    sunday_school = 0
    teens = 0
    for member in Member.query.all():
        for child in member.children:
            if child.age:
                if 5 <= child.age <= 12:
                    sunday_school += 1
                elif 13 <= child.age <= 18:
                    teens += 1
    stats['Sunday School (5-12 yrs)'] = sunday_school
    stats['Teens (13-18 yrs)'] = teens
    stats['KAYO Members'] = Member.query.filter_by(department='KAYO').count()
    return stats

@app.route('/')
@login_required
@require_password_change
def index():
    notices = Notice.query.filter_by(is_active=True).order_by(Notice.date_posted.desc()).all()
    return render_template('index.html', notices=notices)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not check_password_hash(current_user.password, form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('change_password'))
        current_user.password = generate_password_hash(form.new_password.data)
        current_user.must_change_password = False
        db.session.commit()
        flash('Password changed successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('change_password.html', form=form)

# =============== SELF REGISTRATION ===============
@app.route('/self_register', methods=['GET', 'POST'])
def self_register():
    form = SelfRegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken.', 'danger')
            return render_template('self_register.html', form=form)
        child_names = request.form.getlist('child_name[]')
        child_ages = request.form.getlist('child_age[]')
        children_data = []
        for i, name in enumerate(child_names):
            if name.strip():
                age = int(child_ages[i]) if i < len(child_ages) and child_ages[i] else 0
                children_data.append({'name': name.strip(), 'age': age})
        has_spouse = bool(form.spouse_name.data and form.spouse_name.data.strip())
        total_fee = calculate_registration_fee(has_spouse, children_data)
        photo_filename = save_photo(request.files.get('photo'), 'pending')
        pending = PendingMember(
            name=form.name.data,
            contact=form.contact.data,
            spouse_name=form.spouse_name.data,
            spouse_contact=form.spouse_contact.data,
            hbc=form.hbc.data,
            department=form.department.data,
            children_data=json.dumps(children_data),
            photo_filename=photo_filename,
            username=form.username.data,
            total_fee=total_fee,
            mpesa_code=form.mpesa_code.data,
            payment_status='pending',
            status='pending'
        )
        db.session.add(pending)
        db.session.commit()
        flash(f'Registration submitted. Total fee KES {total_fee}. Treasurer will verify M-Pesa payment.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('self_register.html', form=form)

# =============== HBC LEADER APPROVALS ===============
@app.route('/pending_approvals')
@login_required
@role_required('Admin', 'HBC Leader')
@require_password_change
def pending_approvals():
    if current_user.role == 'HBC Leader':
        pendings = PendingMember.query.filter_by(hbc=current_user.hbc_leader_for, status='pending').all()
    else:
        pendings = PendingMember.query.filter_by(status='pending').all()
    return render_template('pending_approvals.html', pendings=pendings)

@app.route('/approve_pending/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'HBC Leader')
@require_password_change
def approve_pending(id):
    pending = PendingMember.query.get_or_404(id)
    if current_user.role == 'HBC Leader' and pending.hbc != current_user.hbc_leader_for:
        abort(403)
    form = ApprovalForm()
    if form.validate_on_submit():
        if form.action.data == 'approve':
            member = Member(
                name=pending.name,
                contact=pending.contact,
                spouse_name=pending.spouse_name,
                spouse_contact=pending.spouse_contact,
                hbc=pending.hbc,
                department=pending.department,
                photo_filename=pending.photo_filename
            )
            member.unique_member_id = generate_unique_member_id()
            db.session.add(member)
            db.session.flush()
            children_data = json.loads(pending.children_data) if pending.children_data else []
            for child in children_data:
                db.session.add(Child(name=child['name'], age=child.get('age'), member_id=member.id))
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            user = User(
                username=pending.username,
                password=generate_password_hash(temp_password),
                role='Member',
                member_id=member.id,
                must_change_password=True
            )
            db.session.add(user)
            pending.status = 'approved'
            pending.approved_by = current_user.id
            pending.approved_at = datetime.utcnow()
            pending.temp_password = temp_password
            db.session.commit()
            flash(f'Registration approved. Member ID: {member.unique_member_id}. Temp password: {temp_password}', 'success')
        else:
            pending.status = 'rejected'
            pending.rejection_reason = form.rejection_reason.data
            db.session.commit()
            flash('Registration rejected.', 'warning')
        return redirect(url_for('pending_approvals'))
    return render_template('approve_pending.html', form=form, pending=pending)

# =============== TREASURER PAYMENT REVIEW (registration payments) ===============
@app.route('/treasurer/payments')
@login_required
@role_required('Treasurer', 'Admin')
@require_password_change
def pending_payments():
    pendings = PendingMember.query.filter_by(payment_status='pending').all()
    return render_template('treasurer_payments.html', pendings=pendings)

@app.route('/treasurer/payment/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('Treasurer', 'Admin')
@require_password_change
def review_payment(id):
    pending = PendingMember.query.get_or_404(id)
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'approve':
            member = Member(
                name=pending.name,
                contact=pending.contact,
                spouse_name=pending.spouse_name,
                spouse_contact=pending.spouse_contact,
                hbc=pending.hbc,
                department=pending.department,
                photo_filename=pending.photo_filename
            )
            member.unique_member_id = generate_unique_member_id()
            db.session.add(member)
            db.session.flush()
            children_data = json.loads(pending.children_data) if pending.children_data else []
            for child in children_data:
                db.session.add(Child(name=child['name'], age=child.get('age'), member_id=member.id))

            payment = Payment(
                member_id=member.id,
                amount=pending.total_fee,
                method='M-Pesa',
                transaction_code=pending.mpesa_code,
                status='completed',
                recorded_by=current_user.id,
                approved_by=current_user.id,
                approved_at=datetime.utcnow(),
                receipt_no=generate_receipt_no()
            )
            db.session.add(payment)
            db.session.flush()

            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            user = User(
                username=pending.username,
                password=generate_password_hash(temp_password),
                role='Member',
                member_id=member.id,
                must_change_password=True
            )
            db.session.add(user)

            pending.status = 'approved'
            pending.payment_status = 'completed'
            pending.payment_id = payment.id
            pending.approved_by = current_user.id
            pending.approved_at = datetime.utcnow()
            pending.temp_password = temp_password
            db.session.commit()

            flash(f'Registration approved. Member ID: {member.unique_member_id}. Temp password: {temp_password}', 'success')
        else:
            pending.payment_status = 'rejected'
            pending.status = 'rejected'
            pending.rejection_reason = request.form.get('rejection_reason')
            db.session.commit()
            flash('Payment rejected.', 'warning')
        return redirect(url_for('pending_payments'))
    return render_template('review_payment.html', pending=pending)

# =============== GIVINGS APPROVAL (Treasurer) ===============
@app.route('/pending_givings')
@login_required
@role_required('Treasurer', 'Admin')
@require_password_change
def pending_givings():
    pending_givings_list = Giving.query.filter_by(status='pending').all()
    return render_template('pending_givings.html', givings=pending_givings_list)

@app.route('/approve_giving/<int:giving_id>')
@login_required
@role_required('Treasurer', 'Admin')
@require_password_change
def approve_giving(giving_id):
    giving = Giving.query.get_or_404(giving_id)
    giving.status = 'approved'
    db.session.commit()
    flash(f'Giving of KES {giving.amount} from {giving.member.name} approved.', 'success')
    return redirect(url_for('pending_givings'))

@app.route('/reject_giving/<int:giving_id>')
@login_required
@role_required('Treasurer', 'Admin')
@require_password_change
def reject_giving(giving_id):
    giving = Giving.query.get_or_404(giving_id)
    giving.status = 'rejected'
    db.session.commit()
    flash(f'Giving of KES {giving.amount} from {giving.member.name} rejected.', 'warning')
    return redirect(url_for('pending_givings'))

# =============== MEMBER MANAGEMENT ===============
@app.route('/members')
@login_required
@require_password_change
def members():
    if current_user.role == 'Member':
        return redirect(url_for('my_profile'))
    search = request.args.get('search', '')
    if current_user.role == 'HBC Leader' and current_user.hbc_leader_for:
        query = Member.query.filter_by(hbc=current_user.hbc_leader_for)
    else:
        query = Member.query
    if search:
        query = query.filter(
            (Member.name.contains(search)) |
            (Member.unique_member_id.contains(search)) |
            (Member.contact.contains(search))
        )
    member_list = query.all()
    return render_template('members.html', members=member_list, search=search)

@app.route('/member/<int:id>')
@login_required
@require_password_change
def member_detail(id):
    member = Member.query.get_or_404(id)
    if current_user.role == 'HBC Leader' and current_user.hbc_leader_for != member.hbc:
        abort(403)
    if current_user.role == 'Member' and current_user.member_id != id:
        abort(403)
    return render_template('member_detail.html', member=member)

@app.route('/member/add', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Vicar', 'Secretary', 'HBC Leader', 'Peoples Warden', 'Vicars Warden')
@require_password_change
def add_member():
    form = MemberForm()
    if form.validate_on_submit():
        member = Member(
            name=form.name.data,
            contact=form.contact.data,
            spouse_name=form.spouse_name.data,
            spouse_contact=form.spouse_contact.data,
            hbc=form.hbc.data,
            department=form.department.data
        )
        member.unique_member_id = generate_unique_member_id()
        photo_file = request.files.get('photo')
        if photo_file:
            member.photo_filename = save_photo(photo_file, 'member')
        db.session.add(member)
        db.session.flush()
        child_names = request.form.getlist('child_name')
        child_ages = request.form.getlist('child_age')
        for i, name in enumerate(child_names):
            if name.strip():
                age = int(child_ages[i]) if i < len(child_ages) and child_ages[i] else None
                db.session.add(Child(name=name.strip(), age=age, member_id=member.id))
        payment_method = request.form.get('payment_method')
        payment_amount = request.form.get('payment_amount')
        if payment_method and payment_amount and float(payment_amount) > 0:
            payment = Payment(
                member_id=member.id,
                amount=float(payment_amount),
                method=payment_method,
                transaction_code=request.form.get('transaction_code'),
                status='completed',
                recorded_by=current_user.id,
                receipt_no=generate_receipt_no()
            )
            db.session.add(payment)
        db.session.commit()
        flash('Member added.', 'success')
        return redirect(url_for('members'))
    return render_template('add_member.html', form=form)

@app.route('/member/add_with_login', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Vicar', 'Secretary', 'HBC Leader', 'Peoples Warden', 'Vicars Warden')
@require_password_change
def add_member_with_login():
    form = MemberWithLoginForm()
    if form.validate_on_submit():
        member = Member(
            name=form.name.data,
            contact=form.contact.data,
            spouse_name=form.spouse_name.data,
            spouse_contact=form.spouse_contact.data,
            hbc=form.hbc.data,
            department=form.department.data
        )
        member.unique_member_id = generate_unique_member_id()
        photo_file = request.files.get('photo')
        if photo_file:
            member.photo_filename = save_photo(photo_file, 'member')
        db.session.add(member)
        db.session.flush()
        child_names = request.form.getlist('child_name')
        child_ages = request.form.getlist('child_age')
        for i, name in enumerate(child_names):
            if name.strip():
                age = int(child_ages[i]) if i < len(child_ages) and child_ages[i] else None
                db.session.add(Child(name=name.strip(), age=age, member_id=member.id))
        user = User(
            username=form.username.data,
            password=generate_password_hash(form.password.data),
            role='Member',
            member_id=member.id,
            must_change_password=True
        )
        db.session.add(user)
        payment_method = request.form.get('payment_method')
        payment_amount = request.form.get('payment_amount')
        if payment_method and payment_amount and float(payment_amount) > 0:
            payment = Payment(
                member_id=member.id,
                amount=float(payment_amount),
                method=payment_method,
                transaction_code=request.form.get('transaction_code'),
                status='completed',
                recorded_by=current_user.id,
                receipt_no=generate_receipt_no()
            )
            db.session.add(payment)
        db.session.commit()
        flash('Member and login account created.', 'success')
        return redirect(url_for('members'))
    return render_template('add_member_with_login.html', form=form)

@app.route('/member/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Vicar', 'Secretary')
@require_password_change
def edit_member(id):
    member = Member.query.get_or_404(id)
    form = MemberForm(obj=member)
    if form.validate_on_submit():
        member.name = form.name.data
        member.contact = form.contact.data
        member.spouse_name = form.spouse_name.data
        member.spouse_contact = form.spouse_contact.data
        member.hbc = form.hbc.data
        member.department = form.department.data
        photo_file = request.files.get('photo')
        if photo_file:
            if member.photo_filename:
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], member.photo_filename)
                if os.path.exists(old_path):
                    os.remove(old_path)
            member.photo_filename = save_photo(photo_file, 'member')
        Child.query.filter_by(member_id=member.id).delete()
        child_names = request.form.getlist('child_name')
        child_ages = request.form.getlist('child_age')
        for i, name in enumerate(child_names):
            if name.strip():
                age = int(child_ages[i]) if i < len(child_ages) and child_ages[i] else None
                db.session.add(Child(name=name.strip(), age=age, member_id=member.id))
        db.session.commit()
        flash('Member updated.', 'success')
        return redirect(url_for('member_detail', id=member.id))
    existing_children = [{'name': c.name, 'age': c.age} for c in member.children]
    return render_template('edit_member.html', form=form, member=member, children=existing_children)

@app.route('/member/delete/<int:id>')
@login_required
@role_required('Admin')
@require_password_change
def delete_member(id):
    member = Member.query.get_or_404(id)
    if member.photo_filename:
        path = os.path.join(app.config['UPLOAD_FOLDER'], member.photo_filename)
        if os.path.exists(path):
            os.remove(path)
    user = User.query.filter_by(member_id=id).first()
    if user:
        db.session.delete(user)
    db.session.delete(member)
    db.session.commit()
    flash('Member deleted.', 'warning')
    return redirect(url_for('members'))

@app.route('/member_data/<int:id>')
@login_required
@require_password_change
def member_data(id):
    member = Member.query.get_or_404(id)
    if current_user.role == 'HBC Leader' and current_user.hbc_leader_for != member.hbc:
        abort(403)
    if current_user.role == 'Member' and current_user.member_id != id:
        abort(403)
    children = [{'name': c.name, 'age': c.age} for c in member.children]
    givings = [{'id': g.id, 'type': g.giving_type, 'amount': g.amount, 'date': g.date.strftime('%Y-%m-%d')} for g in member.givings if g.status == 'approved']
    return jsonify({
        'unique_member_id': member.unique_member_id,
        'name': member.name,
        'contact': member.contact,
        'spouse_name': member.spouse_name or 'None',
        'spouse_contact': member.spouse_contact or 'None',
        'hbc': member.hbc,
        'department': member.department,
        'children': children,
        'givings': givings,
        'photo': member.photo_filename
    })

# =============== MEMBERSHIP CARD ===============
@app.route('/member_card/<int:id>')
@login_required
def member_card(id):
    member = Member.query.get_or_404(id)
    if current_user.role not in ['Admin', 'Vicar', 'Secretary', 'HBC Leader', 'Peoples Warden', 'Vicars Warden']:
        if current_user.role == 'Member' and current_user.member_id != member.id:
            abort(403)
    return render_template('member_card.html', member=member)

@app.route('/member_card_pdf/<int:id>')
@login_required
def member_card_pdf(id):
    member = Member.query.get_or_404(id)
    if current_user.role not in ['Admin', 'Vicar', 'Secretary', 'HBC Leader', 'Peoples Warden', 'Vicars Warden']:
        if current_user.role == 'Member' and current_user.member_id != member.id:
            abort(403)
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, height - 70, "ACK St. Mark's Parish Malaa")
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 95, "Membership Card")
    p.line(50, height - 105, width - 50, height - 105)
    if member.photo_filename:
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], member.photo_filename)
        if os.path.exists(photo_path):
            p.drawImage(photo_path, width - 150, height - 270, width=100, height=100, preserveAspectRatio=True)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height - 150, f"Name: {member.name}")
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 180, f"Church ID: {member.unique_member_id}")
    p.drawString(50, height - 210, f"Contact: {member.contact}")
    p.drawString(50, height - 240, f"HBC: {member.hbc}")
    p.drawString(50, height - 270, f"Department: {member.department}")
    children_str = ', '.join([f"{c.name} ({c.age})" for c in member.children])
    if children_str:
        p.drawString(50, height - 300, f"Children: {children_str}")
    p.setFont("Helvetica-Oblique", 8)
    p.drawString(50, 50, "Official membership card of ACK St. Mark's Parish Malaa.")
    p.drawString(50, 35, f"Issued: {member.created_at.strftime('%d/%m/%Y')}")
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"membership_card_{member.unique_member_id}.pdf", mimetype='application/pdf')

# =============== GIVINGS (admin view, member view only approved) ===============
@app.route('/givings')
@login_required
@require_password_change
def givings():
    if current_user.role == 'Member':
        return redirect(url_for('my_givings'))
    # HBC Leader, Peoples Warden, Vicars Warden can see all givings (but cannot see reports)
    if current_user.role in ('Treasurer', 'Admin', 'Vicar', 'HBC Leader', 'Peoples Warden', 'Vicars Warden'):
        all_givings = Giving.query.all()
    else:
        all_givings = Giving.query.filter_by(member_id=current_user.member_id).all()
    return render_template('givings.html', givings=all_givings)

@app.route('/giving/add', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Vicar', 'Treasurer', 'HBC Leader', 'Peoples Warden', 'Vicars Warden')
@require_password_change
def add_giving():
    form = GivingForm()
    members = Member.query.all()
    if request.method == 'POST':
        member_id = request.form.get('member_id')
        member = Member.query.get(member_id)
        if not member:
            flash('Invalid member', 'danger')
            return redirect(url_for('add_giving'))
        # HBC Leader can only give to his own HBC members
        if current_user.role == 'HBC Leader' and current_user.hbc_leader_for and member.hbc != current_user.hbc_leader_for:
            abort(403)
        giving = Giving(
            member_id=member.id,
            giving_type=form.giving_type.data,
            amount=form.amount.data,
            date=form.date.data or None,
            notes=form.notes.data,
            status='pending'
        )
        db.session.add(giving)
        db.session.commit()
        flash('Giving recorded and pending treasurer approval.', 'success')
        return redirect(url_for('givings'))
    return render_template('add_giving.html', form=form, members=members)

@app.route('/receipt/<int:giving_id>')
@login_required
@require_password_change
def receipt(giving_id):
    giving = Giving.query.get_or_404(giving_id)
    member = giving.member
    if giving.status != 'approved' and current_user.role not in ['Admin', 'Treasurer']:
        abort(403, "Receipt not available until giving is approved.")
    if current_user.role not in ['Admin', 'Vicar', 'Treasurer', 'HBC Leader', 'Peoples Warden', 'Vicars Warden']:
        if current_user.role == 'Member' and current_user.member_id != member.id:
            abort(403)
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "ACK St. Mark's Parish Malaa")
    p.setFont("Helvetica", 10)
    p.drawString(50, height - 70, "Official Receipt")
    p.line(50, height - 95, width - 50, height - 95)
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 130, f"Receipt No: REC-{giving.id:05d}")
    p.drawString(50, height - 160, f"Date: {giving.date.strftime('%d/%m/%Y')}")
    p.drawString(50, height - 190, f"Member: {member.name} ({member.unique_member_id})")
    p.drawString(50, height - 220, f"Type: {giving.giving_type}")
    p.drawString(50, height - 250, f"Amount: KES {giving.amount:,.2f}")
    if giving.notes:
        p.drawString(50, height - 280, f"Notes: {giving.notes}")
    p.drawString(50, 80, "Thank you for your offering.")
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"giving_receipt_{giving.id}.pdf", mimetype='application/pdf')

# =============== NOTICES ===============
@app.route('/notices')
@login_required
@require_password_change
def notices():
    all_notices = Notice.query.order_by(Notice.date_posted.desc()).all()
    return render_template('notices.html', notices=all_notices)

@app.route('/notice/add', methods=['GET', 'POST'])
@login_required
@role_required('Secretary', 'Admin', 'Vicar')
@require_password_change
def add_notice():
    form = NoticeForm()
    if form.validate_on_submit():
        notice = Notice(title=form.title.data, content=form.content.data, created_by=current_user.username)
        db.session.add(notice)
        db.session.commit()
        flash('Notice posted.', 'success')
        return redirect(url_for('notices'))
    return render_template('add_notice.html', form=form)

@app.route('/notice/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('Secretary', 'Admin', 'Vicar')
@require_password_change
def edit_notice(id):
    notice = Notice.query.get_or_404(id)
    if current_user.role not in ['Admin', 'Vicar'] and notice.created_by != current_user.username:
        abort(403)
    form = NoticeForm(obj=notice)
    if form.validate_on_submit():
        notice.title = form.title.data
        notice.content = form.content.data
        db.session.commit()
        flash('Notice updated.', 'success')
        return redirect(url_for('notices'))
    return render_template('edit_notice.html', form=form, notice=notice)

@app.route('/notice/delete/<int:id>')
@login_required
@role_required('Secretary', 'Admin', 'Vicar')
@require_password_change
def delete_notice(id):
    notice = Notice.query.get_or_404(id)
    if current_user.role not in ['Admin', 'Vicar'] and notice.created_by != current_user.username:
        abort(403)
    db.session.delete(notice)
    db.session.commit()
    flash('Notice deleted.', 'warning')
    return redirect(url_for('notices'))

# =============== REPORTS (only Admin, Vicar, Treasurer) ===============
@app.route('/dept_report')
@login_required
@role_required('Admin', 'Vicar', 'Vice Chairman')
@require_password_change
def dept_report():
    stats = get_department_statistics()
    return render_template('dept_report.html', stats=stats)

@app.route('/reports')
@login_required
@role_required('Admin', 'Vicar', 'Treasurer')
@require_password_change
def reports():
    total_by_type = db.session.query(Giving.giving_type, func.sum(Giving.amount)).filter(Giving.status == 'approved').group_by(Giving.giving_type).all()
    total_by_hbc = db.session.query(Member.hbc, func.sum(Giving.amount)).join(Giving).filter(Giving.status == 'approved').group_by(Member.hbc).all()
    return render_template('reports.html', total_by_type=total_by_type, total_by_hbc=total_by_hbc)

# =============== USER MANAGEMENT ===============
@app.route('/my_profile')
@login_required
@require_password_change
def my_profile():
    if current_user.role != 'Member' or current_user.member_id is None:
        abort(403)
    member = Member.query.get(current_user.member_id)
    payments = Payment.query.filter_by(member_id=member.id).all()
    return render_template('member_profile.html', member=member, payments=payments)

@app.route('/my_givings')
@login_required
@require_password_change
def my_givings():
    if current_user.role != 'Member' or current_user.member_id is None:
        abort(403)
    givings = Giving.query.filter_by(member_id=current_user.member_id, status='approved').all()
    return render_template('my_givings.html', givings=givings)

@app.route('/admin/users')
@login_required
@role_required('Admin')
@require_password_change
def admin_users():
    users = User.query.filter(User.role != 'Member').all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
@require_password_change
def add_user():
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            password=generate_password_hash(form.password.data),
            role=form.role.data,
            hbc_leader_for=form.hbc_leader_for.data if form.role.data == 'HBC Leader' else None,
            must_change_password=True
        )
        db.session.add(user)
        db.session.commit()
        flash('User created.', 'success')
        return redirect(url_for('admin_users'))
    return render_template('add_user.html', form=form)

@app.route('/admin/user/delete/<int:id>')
@login_required
@role_required('Admin')
@require_password_change
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Cannot delete own account.', 'danger')
        return redirect(url_for('admin_users'))
    if user.member_id:
        member = Member.query.get(user.member_id)
        if member and member.photo_filename:
            path = os.path.join(app.config['UPLOAD_FOLDER'], member.photo_filename)
            if os.path.exists(path): os.remove(path)
        if member:
            db.session.delete(member)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted.', 'success')
    return redirect(url_for('admin_users'))

# =============== PASSWORD RESET FOR MEMBERS ===============
@app.route('/reset_member_password/<int:member_id>')
@login_required
@role_required('Admin', 'Vicar', 'Secretary')
@require_password_change
def reset_member_password(member_id):
    member = Member.query.get_or_404(member_id)
    user = User.query.filter_by(member_id=member.id).first()
    if not user:
        flash('This member does not have a login account.', 'warning')
        return redirect(url_for('member_detail', id=member.id))
    new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    user.password = generate_password_hash(new_password)
    user.must_change_password = True
    db.session.commit()
    flash(f'Password for {member.name} has been reset. Temporary password: {new_password}', 'success')
    return redirect(url_for('member_detail', id=member.id))

# =============== REGISTRATION PAYMENT RECEIPT ===============
@app.route('/payment_receipt/<int:payment_id>')
@login_required
@require_password_change
def payment_receipt(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    member = payment.member
    if current_user.role not in ['Admin', 'Treasurer']:
        if current_user.role == 'Member' and current_user.member_id != member.id:
            abort(403)
        elif current_user.role not in ['Admin', 'Treasurer']:
            abort(403)
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "ACK St. Mark's Parish Malaa")
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 80, "REGISTRATION PAYMENT RECEIPT")
    p.line(50, height - 95, width - 50, height - 95)
    p.setFont("Helvetica", 11)
    p.drawString(50, height - 130, f"Receipt No: {payment.receipt_no or 'N/A'}")
    p.drawString(50, height - 155, f"Date: {payment.recorded_at.strftime('%d/%m/%Y %H:%M')}")
    p.drawString(50, height - 180, f"Member: {member.name} ({member.unique_member_id})")
    p.drawString(50, height - 205, f"Amount Paid: KES {payment.amount:,.2f}")
    p.drawString(50, height - 230, f"Payment Method: {payment.method}")
    if payment.transaction_code:
        p.drawString(50, height - 255, f"Transaction Code: {payment.transaction_code}")
    p.drawString(50, height - 280, f"Status: {payment.status.capitalize()}")
    p.setFont("Helvetica-Oblique", 8)
    p.drawString(50, 80, "This is an official receipt for registration payment.")
    p.drawString(50, 65, "Thank you for registering with ACK St. Mark's Parish Malaa.")
    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"registration_receipt_{payment.receipt_no or payment.id}.pdf", mimetype='application/pdf')

# =============== DIAGNOSTIC ROUTE ===============
@app.route('/debug_payments/<int:member_id>')
@login_required
@role_required('Admin', 'Treasurer')
def debug_payments(member_id):
    member = Member.query.get_or_404(member_id)
    payments = Payment.query.filter_by(member_id=member.id).all()
    output = f"Member: {member.name} (ID: {member.id})<br>"
    output += f"Payments found: {len(payments)}<br>"
    for p in payments:
        output += f"- Receipt: {p.receipt_no}, Amount: {p.amount}, Status: {p.status}<br>"
    return output

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password=generate_password_hash('admin123'), role='Admin', must_change_password=False)
        db.session.add(admin)
        db.session.commit()
        print("Default admin: admin / admin123")

if __name__ == '__main__':
    app.run(debug=True)
''',
}

# =============== HTML TEMPLATES (all) ===============
html_files = {
    "templates/base.html": '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ACK St. Mark's Parish Malaa CMS</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #f8f9fc; }
        .sidebar { background-color: #1e2a3e; min-height: 100vh; }
        .sidebar .nav-link { color: #cbd5e1; padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 0.25rem; }
        .sidebar .nav-link:hover, .sidebar .nav-link.active { background-color: #2d3e50; color: white; }
        .sidebar .nav-link i { margin-right: 10px; width: 20px; }
        .card { border: none; border-radius: 12px; box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075); transition: transform 0.2s; }
        .card:hover { transform: translateY(-3px); box-shadow: 0 0.5rem 1rem rgba(0,0,0,0.1); }
        .member-id-link { cursor: pointer; color: #0d6efd; text-decoration: none; font-weight: 600; }
        .member-id-link:hover { text-decoration: underline; }
        @media (max-width: 768px) { .sidebar { min-height: auto; margin-bottom: 1rem; } }
        .photo-preview { max-width: 100px; max-height: 100px; border-radius: 50%; object-fit: cover; }
        .member-card-photo { width: 120px; height: 120px; object-fit: cover; border-radius: 10px; margin-bottom: 10px; }
    </style>
</head>
<body>
<div class="container-fluid">
    <div class="row">
        <div class="col-md-3 col-lg-2 px-0 sidebar">
            <div class="py-4 px-3 text-center text-white"><h5 class="mb-0">ACK St. Mark's</h5><small>Malaa Parish</small></div>
            <nav class="nav flex-column px-2">
                {% if current_user.is_authenticated %}
                    <a class="nav-link" href="{{ url_for('change_password') }}"><i class="bi bi-key"></i> Change Password</a>
                    {% if current_user.role == 'Member' %}
                        <a class="nav-link" href="{{ url_for('my_profile') }}"><i class="bi bi-person-circle"></i> My Profile</a>
                        <a class="nav-link" href="{{ url_for('my_givings') }}"><i class="bi bi-wallet2"></i> My Givings</a>
                        <a class="nav-link" href="{{ url_for('notices') }}"><i class="bi bi-megaphone"></i> Notices</a>
                    {% else %}
                        <a class="nav-link" href="{{ url_for('members') }}"><i class="bi bi-people"></i> Members</a>
                        {% if current_user.role not in ['Secretary', 'HBC Leader'] %}
                        <a class="nav-link" href="{{ url_for('givings') }}"><i class="bi bi-cash-stack"></i> Givings</a>
                        {% endif %}
                        {% if current_user.role in ['Admin','Vicar','Treasurer'] %}
                            <a class="nav-link" href="{{ url_for('reports') }}"><i class="bi bi-bar-chart"></i> Financial Reports</a>
                        {% endif %}
                        {% if current_user.role in ['Admin','Vicar','Vice Chairman'] %}
                            <a class="nav-link" href="{{ url_for('dept_report') }}"><i class="bi bi-pie-chart"></i> Department Stats</a>
                        {% endif %}
                        <a class="nav-link" href="{{ url_for('notices') }}"><i class="bi bi-megaphone"></i> Notices</a>
                        {% if current_user.role in ['Admin', 'HBC Leader'] %}
                            <a class="nav-link" href="{{ url_for('pending_approvals') }}"><i class="bi bi-clock-history"></i> Pending Approvals</a>
                        {% endif %}
                        {% if current_user.role in ['Treasurer', 'Admin'] %}
                            <a class="nav-link" href="{{ url_for('pending_payments') }}"><i class="bi bi-currency-exchange"></i> Pending Payments</a>
                            <a class="nav-link" href="{{ url_for('pending_givings') }}"><i class="bi bi-clock-history"></i> Pending Givings</a>
                        {% endif %}
                        {% if current_user.role == 'Admin' %}
                            <a class="nav-link" href="{{ url_for('admin_users') }}"><i class="bi bi-gear"></i> Users</a>
                        {% endif %}
                    {% endif %}
                    <a class="nav-link" href="{{ url_for('auth.logout') }}"><i class="bi bi-box-arrow-right"></i> Logout</a>
                {% else %}
                    <a class="nav-link" href="{{ url_for('auth.login') }}"><i class="bi bi-key"></i> Login</a>
                    <a class="nav-link" href="{{ url_for('self_register') }}"><i class="bi bi-person-plus"></i> Self Register</a>
                {% endif %}
            </nav>
        </div>
        <div class="col-md-9 col-lg-10 ms-sm-auto px-md-4 py-3">
            <nav class="navbar navbar-light bg-white rounded-3 shadow-sm p-3 mb-4">
                <span class="navbar-brand h5"><i class="bi bi-building"></i> ACK St. Mark's Parish Malaa</span>
                <span class="text-muted">{% if current_user.is_authenticated %}{{ current_user.username }} ({{ current_user.role }}){% endif %}</span>
            </nav>
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show">{{ message }}<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>
                {% endfor %}
            {% endwith %}
            {% block content %}{% endblock %}
        </div>
    </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
{% block scripts %}{% endblock %}
</body>
</html>''',
    "templates/index.html": '''{% extends "base.html" %}
{% block content %}
<div class="row"><div class="col-12"><div class="card bg-primary text-white p-5 mb-4"><h1 class="display-4">Welcome to ACK St. Mark's Parish Malaa</h1><p class="lead">Church Management System</p><hr class="my-4 bg-white">{% if current_user.role == 'Member' %}<p>View your profile and giving records.</p><a class="btn btn-light btn-lg" href="{{ url_for('my_profile') }}">My Profile</a><a class="btn btn-outline-light btn-lg" href="{{ url_for('my_givings') }}">My Givings</a>{% else %}<p>Manage members, record givings, and view reports.</p><a class="btn btn-light btn-lg" href="{{ url_for('members') }}">View Members</a>{% if current_user.role not in ['Secretary', 'HBC Leader'] %}<a class="btn btn-outline-light btn-lg" href="{{ url_for('givings') }}">View Givings</a>{% endif %}{% if current_user.role in ['Admin','Vicar','Treasurer'] %}<a class="btn btn-success btn-lg" href="{{ url_for('reports') }}">Reports</a>{% endif %}{% endif %}</div></div></div>
<div class="row mt-4"><div class="col-12"><div class="card"><div class="card-header bg-info text-white"><h4><i class="bi bi-megaphone"></i> Latest Church Notices</h4></div><div class="card-body">{% if notices %}{% for notice in notices[:3] %}<div class="mb-3 pb-2 border-bottom"><h5>{{ notice.title }}</h5><small class="text-muted">Posted by {{ notice.created_by }} on {{ notice.date_posted.strftime('%d/%m/%Y %H:%M') }}</small><p class="mt-2">{{ notice.content }}</p></div>{% endfor %}<a href="{{ url_for('notices') }}" class="btn btn-sm btn-outline-primary">View All Notices</a>{% else %}<p>No notices yet.</p>{% endif %}</div></div></div></div>
{% endblock %}''',
    "templates/login.html": '''{% extends "base.html" %}
{% block content %}<div class="row justify-content-center"><div class="col-md-5"><div class="card shadow"><div class="card-header bg-primary text-white"><h3>Login</h3></div><div class="card-body"><form method="POST">{{ form.hidden_tag() }}{{ form.username.label }} {{ form.username(class="form-control") }}{{ form.password.label }} {{ form.password(class="form-control") }}<button type="submit" class="btn btn-primary w-100 mt-3">Login</button></form><hr><div class="text-center"><p>New member? <a href="{{ url_for('self_register') }}" class="btn btn-success">Self Register</a></p></div></div></div></div></div>{% endblock %}''',
    "templates/self_register.html": '''{% extends "base.html" %}
{% block content %}<div class="row justify-content-center"><div class="col-md-8"><div class="card"><div class="card-header bg-primary text-white"><h3>Self Registration</h3></div><div class="card-body"><form method="POST" enctype="multipart/form-data">{{ form.hidden_tag() }}<div class="row"><div class="col-md-6">{{ form.name.label }} {{ form.name(class="form-control") }}{{ form.contact.label }} {{ form.contact(class="form-control") }}{{ form.spouse_name.label }} {{ form.spouse_name(class="form-control") }}{{ form.spouse_contact.label }} {{ form.spouse_contact(class="form-control") }}</div><div class="col-md-6">{{ form.hbc.label }} {{ form.hbc(class="form-select") }}{{ form.department.label }} {{ form.department(class="form-select") }}{{ form.username.label }} {{ form.username(class="form-control") }}{{ form.mpesa_code.label }} {{ form.mpesa_code(class="form-control", placeholder="e.g., QWERTY123") }}</div></div><div class="mb-3"><label>Children (with age)</label><div id="children-fields"><div class="row mb-2"><div class="col"><input type="text" name="child_name[]" class="form-control" placeholder="Name"></div><div class="col"><input type="number" name="child_age[]" class="form-control" placeholder="Age"></div></div></div><button type="button" class="btn btn-secondary btn-sm" onclick="addChildField()">+ Add child</button></div><div class="mb-3"><label>Passport Photo</label><input type="file" name="photo" accept="image/*" class="form-control" id="photoInput"><div><video id="video" width="200" height="150" autoplay style="display:none;"></video><button type="button" id="start-camera" class="btn btn-sm btn-secondary mt-2">Use Webcam</button><button type="button" id="capture" class="btn btn-sm btn-success mt-2" style="display:none;">Capture</button><canvas id="canvas" style="display:none;"></canvas><img id="photo-preview" class="mt-2" style="max-width:150px; display:none;"></div></div><div class="alert alert-info"><strong>Fees:</strong> Adult KES 200, Spouse +200, Youth 13-18 +100, Sunday School 5-12 +50.</div><button type="submit" class="btn btn-success">Submit Registration</button> <a href="{{ url_for('auth.login') }}" class="btn btn-secondary">Back to Login</a></form></div></div></div></div>
<script>function addChildField(){let c=document.getElementById('children-fields');let d=document.createElement('div');d.className='row mb-2';d.innerHTML='<div class="col"><input type="text" name="child_name[]" class="form-control" placeholder="Name"></div><div class="col"><input type="number" name="child_age[]" class="form-control" placeholder="Age"></div>';c.appendChild(d);}
let video=document.getElementById('video'),canvas=document.getElementById('canvas'),startBtn=document.getElementById('start-camera'),captureBtn=document.getElementById('capture'),photoInput=document.getElementById('photoInput'),preview=document.getElementById('photo-preview');
startBtn.onclick=function(){navigator.mediaDevices.getUserMedia({video:true}).then(s=>{video.srcObject=s;video.style.display='block';startBtn.style.display='none';captureBtn.style.display='inline-block';}).catch(e=>alert('Camera error'))};
captureBtn.onclick=function(){canvas.width=video.videoWidth;canvas.height=video.videoHeight;canvas.getContext('2d').drawImage(video,0,0);let dataURL=canvas.toDataURL('image/png');fetch(dataURL).then(r=>r.blob()).then(b=>{let file=new File([b],"webcam.png",{type:"image/png"});let dt=new DataTransfer();dt.items.add(file);photoInput.files=dt.files;preview.src=dataURL;preview.style.display='block';});let stream=video.srcObject;stream.getTracks().forEach(t=>t.stop());video.style.display='none';captureBtn.style.display='none';};
</script>
{% endblock %}''',
    "templates/treasurer_payments.html": '''{% extends "base.html" %}
{% block content %}<h2>Pending Registration Payments</h2><div class="row">{% for p in pendings %}<div class="col-md-6 mb-4"><div class="card"><div class="card-header bg-warning">{{ p.name }} ({{ p.hbc }})</div><div class="card-body"><p><strong>Total Fee:</strong> KES {{ p.total_fee }}</p><p><strong>M-Pesa Code:</strong> {{ p.mpesa_code }}</p><p><strong>Submitted:</strong> {{ p.submitted_at.strftime('%d/%m/%Y %H:%M') }}</p><a href="{{ url_for('review_payment', id=p.id) }}" class="btn btn-primary">Review</a></div></div></div>{% else %}<div class="alert alert-info">No pending payments.</div>{% endfor %}</div>{% endblock %}''',
    "templates/review_payment.html": '''{% extends "base.html" %}
{% block content %}<div class="card"><div class="card-header bg-primary"><h3>Review Payment</h3></div><div class="card-body"><h4>{{ pending.name }}</h4>{% if pending.photo_filename %}<img src="{{ url_for('static', filename='uploads/' + pending.photo_filename) }}" style="max-width:150px; float:right;">{% endif %}<p>Contact: {{ pending.contact }}<br>Spouse: {{ pending.spouse_name or 'None' }} ({{ pending.spouse_contact or '-' }})<br>HBC: {{ pending.hbc }}<br>Department: {{ pending.department }}<br>Children: {{ pending.children_data }}</p><p><strong>Total Fee:</strong> KES {{ pending.total_fee }}<br><strong>M-Pesa Code:</strong> {{ pending.mpesa_code }}</p><form method="POST"><div class="mb-3"><label>Action</label><br><button type="submit" name="action" value="approve" class="btn btn-success">Approve & Activate</button> <button type="submit" name="action" value="reject" class="btn btn-danger" onclick="return confirm('Reject?')">Reject</button></div><div class="mb-3"><label>Rejection Reason</label><textarea name="rejection_reason" class="form-control" rows="2"></textarea></div></form></div></div>{% endblock %}''',
    "templates/pending_approvals.html": '''{% extends "base.html" %}
{% block content %}<h2>Pending Registrations (HBC Approval)</h2><div class="row">{% for p in pendings %}<div class="col-md-6 mb-4"><div class="card"><div class="card-header bg-warning">{{ p.name }} ({{ p.hbc }})</div><div class="card-body">{% if p.photo_filename %}<img src="{{ url_for('static', filename='uploads/' + p.photo_filename) }}" style="max-width:100px; float:right;">{% endif %}<p><strong>Contact:</strong> {{ p.contact }}</p><p><strong>Spouse:</strong> {{ p.spouse_name or 'None' }} ({{ p.spouse_contact or '-' }})</p><p><strong>Department:</strong> {{ p.department }}</p><p><strong>Children:</strong> {{ p.children_data or 'None' }}</p><p><strong>Username:</strong> {{ p.username }}</p><p><strong>Submitted:</strong> {{ p.submitted_at.strftime('%d/%m/%Y %H:%M') }}</p><a href="{{ url_for('approve_pending', id=p.id) }}" class="btn btn-primary">Review</a></div></div></div>{% else %}<div class="alert alert-info">No pending registrations for your HBC.</div>{% endfor %}</div>{% endblock %}''',
    "templates/approve_pending.html": '''{% extends "base.html" %}
{% block content %}<div class="card"><div class="card-header bg-primary"><h3>Approve/Reject Registration</h3></div><div class="card-body"><h4>{{ pending.name }}</h4>{% if pending.photo_filename %}<img src="{{ url_for('static', filename='uploads/' + pending.photo_filename) }}" style="max-width:150px;">{% endif %}<p><strong>Contact:</strong> {{ pending.contact }}</p><p><strong>Spouse:</strong> {{ pending.spouse_name or 'None' }} ({{ pending.spouse_contact or '-' }})</p><p><strong>HBC:</strong> {{ pending.hbc }}</p><p><strong>Department:</strong> {{ pending.department }}</p><p><strong>Children:</strong> {{ pending.children_data or 'None' }}</p><p><strong>Username:</strong> {{ pending.username }}</p><form method="POST">{{ form.hidden_tag() }}{{ form.action.label }} {{ form.action(class="form-select") }}{{ form.rejection_reason.label }} {{ form.rejection_reason(class="form-control", rows=3) }}<button type="submit" class="btn btn-success mt-3">Submit</button> <a href="{{ url_for('pending_approvals') }}" class="btn btn-secondary">Back</a></form></div></div>{% endblock %}''',
    "templates/members.html": '''{% extends "base.html" %}
{% block content %}<div class="d-flex justify-content-between"><h2>Members</h2>{% if current_user.role in ['Admin','Vicar','Secretary','HBC Leader','Peoples Warden','Vicars Warden'] %}<div><a href="{{ url_for('add_member') }}" class="btn btn-primary">+ Add (no login)</a><a href="{{ url_for('add_member_with_login') }}" class="btn btn-success ms-2">+ Add with Login</a></div>{% endif %}</div>
<div class="card mb-3"><div class="card-body"><form method="GET"><div class="input-group"><input type="text" name="search" class="form-control" placeholder="Search..." value="{{ search or '' }}"><button class="btn btn-primary">Search</button>{% if search %}<a href="{{ url_for('members') }}" class="btn btn-secondary">Clear</a>{% endif %}</div></form></div></div>
<div class="row">{% for m in members %}<div class="col-md-3 mb-3"><div class="card h-100"><div class="card-body"><h5>{{ m.name }}</h5><p><i class="bi bi-telephone"></i> {{ m.contact }}<br><i class="bi bi-building"></i> {{ m.hbc }}<br><i class="bi bi-diagram-3"></i> {{ m.department }}</p><p><strong class="member-id-link" data-member-id="{{ m.id }}" data-bs-toggle="modal" data-bs-target="#memberModal">{{ m.unique_member_id }}</strong></p><a href="{{ url_for('member_detail', id=m.id) }}" class="btn btn-sm btn-outline-primary">View</a> <a href="{{ url_for('member_card', id=m.id) }}" class="btn btn-sm btn-outline-info">Card</a>{% if current_user.role in ['Admin','Vicar','Secretary'] %}<a href="{{ url_for('edit_member', id=m.id) }}" class="btn btn-sm btn-outline-warning">Edit</a>{% endif %}{% if current_user.role == 'Admin' %}<a href="{{ url_for('delete_member', id=m.id) }}" class="btn btn-sm btn-outline-danger" onclick="return confirm('Delete?')">Del</a>{% endif %}</div></div></div>{% endfor %}</div>
<div class="modal fade" id="memberModal" tabindex="-1"><div class="modal-dialog modal-lg"><div class="modal-content"><div class="modal-header bg-primary text-white"><h5>Member Details</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div><div class="modal-body" id="modalBodyContent">Loading...</div><div class="modal-footer"><button class="btn btn-secondary" data-bs-dismiss="modal">Close</button></div></div></div></div>
<script>$(document).ready(function(){$('.member-id-link').click(function(){var mid=$(this).data('member-id');$('#modalBodyContent').html('Loading...');$.ajax({url:'/member_data/'+mid,success:function(data){var html='<p><strong>ID:</strong> '+data.unique_member_id+'</p><p><strong>Name:</strong> '+data.name+'</p><p><strong>Contact:</strong> '+data.contact+'</p><p><strong>Spouse:</strong> '+data.spouse_name+' ('+data.spouse_contact+')</p><p><strong>HBC:</strong> '+data.hbc+'</p><p><strong>Department:</strong> '+data.department+'</p><p><strong>Children:</strong> <ul>'+(data.children.length?data.children.map(c=>'<li>'+c.name+' ('+c.age+')</li>').join(''):'<li>None</li>')+'</ul></p>';if(data.photo)html='<img src="/static/uploads/'+data.photo+'" style="max-width:150px;float:right;">'+html;$('#modalBodyContent').html(html);}});});});</script>
{% endblock %}''',
    "templates/add_member.html": '''{% extends "base.html" %}
{% block content %}<div class="card"><div class="card-header bg-primary"><h3>Add Member</h3></div><div class="card-body"><form method="POST" enctype="multipart/form-data">{{ form.hidden_tag() }}
<div class="row"><div class="col-md-6">{{ form.name.label }} {{ form.name(class="form-control") }}{{ form.contact.label }} {{ form.contact(class="form-control") }}{{ form.spouse_name.label }} {{ form.spouse_name(class="form-control") }}{{ form.spouse_contact.label }} {{ form.spouse_contact(class="form-control") }}</div>
<div class="col-md-6">{{ form.hbc.label }} {{ form.hbc(class="form-select") }}{{ form.department.label }} {{ form.department(class="form-select") }}<label>Photo</label><input type="file" name="photo" class="form-control"><div><video id="video" width="200" height="150" autoplay style="display:none;"></video><button type="button" id="start-camera" class="btn btn-sm btn-secondary mt-2">Webcam</button><button type="button" id="capture" class="btn btn-sm btn-success mt-2" style="display:none;">Capture</button><canvas id="canvas" style="display:none;"></canvas><img id="photo-preview" style="max-width:150px; margin-top:5px;"></div></div></div>
<div class="mb-3"><label>Children (name & age)</label><div id="children-fields"><div class="row mb-2"><div class="col"><input type="text" name="child_name" class="form-control" placeholder="Name"></div><div class="col"><input type="number" name="child_age" class="form-control" placeholder="Age"></div></div></div><button type="button" class="btn btn-secondary btn-sm" onclick="addChildField()">+ Add child</button></div>
<div class="mb-3"><label>Payment (optional)</label><div class="row"><div class="col"><select name="payment_method" class="form-select"><option value="">None</option><option value="Cash">Cash</option><option value="M-Pesa">M-Pesa</option><option value="Account">Account</option></select></div><div class="col"><input type="number" step="0.01" name="payment_amount" class="form-control" placeholder="Amount"></div><div class="col"><input type="text" name="transaction_code" class="form-control" placeholder="Reference"></div></div></div>
<button type="submit" class="btn btn-success">Save Member</button> <a href="{{ url_for('members') }}" class="btn btn-secondary">Cancel</a>
</form></div></div>
<script>function addChildField(){let c=document.getElementById('children-fields');let d=document.createElement('div');d.className='row mb-2';d.innerHTML='<div class="col"><input type="text" name="child_name" class="form-control" placeholder="Name"></div><div class="col"><input type="number" name="child_age" class="form-control" placeholder="Age"></div>';c.appendChild(d);}
let video=document.getElementById('video'),canvas=document.getElementById('canvas'),startBtn=document.getElementById('start-camera'),captureBtn=document.getElementById('capture'),photoInput=document.querySelector('input[name="photo"]'),preview=document.getElementById('photo-preview');
startBtn.onclick=function(){navigator.mediaDevices.getUserMedia({video:true}).then(s=>{video.srcObject=s;video.style.display='block';startBtn.style.display='none';captureBtn.style.display='inline-block';}).catch(e=>alert('Camera error'))};
captureBtn.onclick=function(){canvas.width=video.videoWidth;canvas.height=video.videoHeight;canvas.getContext('2d').drawImage(video,0,0);let dataURL=canvas.toDataURL('image/png');fetch(dataURL).then(r=>r.blob()).then(b=>{let file=new File([b],"webcam.png",{type:"image/png"});let dt=new DataTransfer();dt.items.add(file);photoInput.files=dt.files;preview.src=dataURL;preview.style.display='block';});let stream=video.srcObject;stream.getTracks().forEach(t=>t.stop());video.style.display='none';captureBtn.style.display='none';};
</script>
{% endblock %}''',
    "templates/add_member_with_login.html": '''{% extends "base.html" %}
{% block content %}<div class="card"><div class="card-header bg-success"><h3>Add Member with Login</h3></div><div class="card-body"><form method="POST" enctype="multipart/form-data">{{ form.hidden_tag() }}
<div class="row"><div class="col-md-6">{{ form.name.label }} {{ form.name(class="form-control") }}{{ form.contact.label }} {{ form.contact(class="form-control") }}{{ form.spouse_name.label }} {{ form.spouse_name(class="form-control") }}{{ form.spouse_contact.label }} {{ form.spouse_contact(class="form-control") }}</div>
<div class="col-md-6">{{ form.hbc.label }} {{ form.hbc(class="form-select") }}{{ form.department.label }} {{ form.department(class="form-select") }}{{ form.username.label }} {{ form.username(class="form-control") }}{{ form.password.label }} {{ form.password(class="form-control") }}<label>Photo</label><input type="file" name="photo" class="form-control"><div><video id="video" width="200" height="150" autoplay style="display:none;"></video><button type="button" id="start-camera" class="btn btn-sm btn-secondary mt-2">Webcam</button><button type="button" id="capture" class="btn btn-sm btn-success mt-2" style="display:none;">Capture</button><canvas id="canvas" style="display:none;"></canvas><img id="photo-preview" style="max-width:150px; margin-top:5px;"></div></div></div>
<div class="mb-3"><label>Children (name & age)</label><div id="children-fields"><div class="row mb-2"><div class="col"><input type="text" name="child_name" class="form-control" placeholder="Name"></div><div class="col"><input type="number" name="child_age" class="form-control" placeholder="Age"></div></div></div><button type="button" class="btn btn-secondary btn-sm" onclick="addChildField()">+ Add child</button></div>
<div class="mb-3"><label>Payment (optional)</label><div class="row"><div class="col"><select name="payment_method" class="form-select"><option value="">None</option><option value="Cash">Cash</option><option value="M-Pesa">M-Pesa</option><option value="Account">Account</option></select></div><div class="col"><input type="number" step="0.01" name="payment_amount" class="form-control" placeholder="Amount"></div><div class="col"><input type="text" name="transaction_code" class="form-control" placeholder="Reference"></div></div></div>
<button type="submit" class="btn btn-success">Save Member & Account</button> <a href="{{ url_for('members') }}" class="btn btn-secondary">Cancel</a>
</form></div></div>
<script>function addChildField(){let c=document.getElementById('children-fields');let d=document.createElement('div');d.className='row mb-2';d.innerHTML='<div class="col"><input type="text" name="child_name" class="form-control" placeholder="Name"></div><div class="col"><input type="number" name="child_age" class="form-control" placeholder="Age"></div>';c.appendChild(d);}
let video=document.getElementById('video'),canvas=document.getElementById('canvas'),startBtn=document.getElementById('start-camera'),captureBtn=document.getElementById('capture'),photoInput=document.querySelector('input[name="photo"]'),preview=document.getElementById('photo-preview');
startBtn.onclick=function(){navigator.mediaDevices.getUserMedia({video:true}).then(s=>{video.srcObject=s;video.style.display='block';startBtn.style.display='none';captureBtn.style.display='inline-block';}).catch(e=>alert('Camera error'))};
captureBtn.onclick=function(){canvas.width=video.videoWidth;canvas.height=video.videoHeight;canvas.getContext('2d').drawImage(video,0,0);let dataURL=canvas.toDataURL('image/png');fetch(dataURL).then(r=>r.blob()).then(b=>{let file=new File([b],"webcam.png",{type:"image/png"});let dt=new DataTransfer();dt.items.add(file);photoInput.files=dt.files;preview.src=dataURL;preview.style.display='block';});let stream=video.srcObject;stream.getTracks().forEach(t=>t.stop());video.style.display='none';captureBtn.style.display='none';};
</script>
{% endblock %}''',
    "templates/member_detail.html": '''{% extends "base.html" %}
{% block content %}<div class="card"><div class="card-header bg-primary text-white"><h3>{{ member.name }}</h3></div><div class="card-body">{% if member.photo_filename %}<img src="{{ url_for('static', filename='uploads/' + member.photo_filename) }}" style="max-width:150px; float:right; border-radius:10px;">{% endif %}<p><strong>ID:</strong> {{ member.unique_member_id }}</p><p><strong>Contact:</strong> {{ member.contact }}</p><p><strong>Spouse:</strong> {{ member.spouse_name or 'None' }} ({{ member.spouse_contact or '-' }})</p><p><strong>HBC:</strong> {{ member.hbc }}</p><p><strong>Department:</strong> {{ member.department }}</p><p><strong>Children:</strong> <ul>{% for child in member.children %}<li>{{ child.name }} ({{ child.age if child.age else '?' }})</li>{% endfor %}</ul></p><h4>Givings</h4><table class="table table-sm"><thead><tr><th>Type</th><th>Amount</th><th>Date</th><th>Receipt</th></tr></thead><tbody>{% for g in member.givings if g.status == 'approved' %}<tr><td>{{ g.giving_type }}</td><td>{{ g.amount }}</td><td>{{ g.date.strftime('%Y-%m-%d') }}</td><td><a href="{{ url_for('receipt', giving_id=g.id) }}" target="_blank">PDF</a></td></tr>{% endfor %}</tbody></table><a href="{{ url_for('members') }}" class="btn btn-secondary">Back</a>{% if current_user.role in ['Admin','Vicar','Secretary'] %} <a href="{{ url_for('edit_member', id=member.id) }}" class="btn btn-warning">Edit</a> <a href="{{ url_for('reset_member_password', member_id=member.id) }}" class="btn btn-danger" onclick="return confirm('Reset password for this member?')">Reset Password</a>{% endif %}</div></div>{% endblock %}''',
    "templates/edit_member.html": '''{% extends "base.html" %}
{% block content %}<div class="card"><div class="card-header bg-warning"><h3>Edit Member</h3></div><div class="card-body"><form method="POST" enctype="multipart/form-data">{{ form.hidden_tag() }}
<div class="row"><div class="col-md-6">{{ form.name.label }} {{ form.name(class="form-control") }}{{ form.contact.label }} {{ form.contact(class="form-control") }}{{ form.spouse_name.label }} {{ form.spouse_name(class="form-control") }}{{ form.spouse_contact.label }} {{ form.spouse_contact(class="form-control") }}</div><div class="col-md-6">{{ form.hbc.label }} {{ form.hbc(class="form-select") }}{{ form.department.label }} {{ form.department(class="form-select") }}<label>Photo</label><input type="file" name="photo" class="form-control"><div><video id="video" width="200" height="150" autoplay style="display:none;"></video><button type="button" id="start-camera" class="btn btn-sm btn-secondary mt-2">Webcam</button><button type="button" id="capture" class="btn btn-sm btn-success mt-2" style="display:none;">Capture</button><canvas id="canvas" style="display:none;"></canvas><img id="photo-preview" style="max-width:150px; margin-top:5px;"></div></div></div>
<div class="mb-3"><label>Children (name & age)</label><div id="children-fields">{% for child in children %}<div class="row mb-2"><div class="col"><input type="text" name="child_name" class="form-control" value="{{ child.name }}"></div><div class="col"><input type="number" name="child_age" class="form-control" value="{{ child.age }}"></div></div>{% endfor %}<div class="row mb-2"><div class="col"><input type="text" name="child_name" class="form-control" placeholder="New child name"></div><div class="col"><input type="number" name="child_age" class="form-control" placeholder="Age"></div></div></div><button type="button" class="btn btn-secondary btn-sm" onclick="addChildField()">+ Add another child</button></div>
<button type="submit" class="btn btn-primary">Update</button> <a href="{{ url_for('member_detail', id=member.id) }}" class="btn btn-secondary">Cancel</a>
</form></div></div>
<script>function addChildField(){let c=document.getElementById('children-fields');let d=document.createElement('div');d.className='row mb-2';d.innerHTML='<div class="col"><input type="text" name="child_name" class="form-control" placeholder="Name"></div><div class="col"><input type="number" name="child_age" class="form-control" placeholder="Age"></div>';c.appendChild(d);}
let video=document.getElementById('video'),canvas=document.getElementById('canvas'),startBtn=document.getElementById('start-camera'),captureBtn=document.getElementById('capture'),photoInput=document.querySelector('input[name="photo"]'),preview=document.getElementById('photo-preview');
startBtn.onclick=function(){navigator.mediaDevices.getUserMedia({video:true}).then(s=>{video.srcObject=s;video.style.display='block';startBtn.style.display='none';captureBtn.style.display='inline-block';}).catch(e=>alert('Camera error'))};
captureBtn.onclick=function(){canvas.width=video.videoWidth;canvas.height=video.videoHeight;canvas.getContext('2d').drawImage(video,0,0);let dataURL=canvas.toDataURL('image/png');fetch(dataURL).then(r=>r.blob()).then(b=>{let file=new File([b],"webcam.png",{type:"image/png"});let dt=new DataTransfer();dt.items.add(file);photoInput.files=dt.files;preview.src=dataURL;preview.style.display='block';});let stream=video.srcObject;stream.getTracks().forEach(t=>t.stop());video.style.display='none';captureBtn.style.display='none';};
</script>
{% endblock %}''',
    "templates/member_card.html": '''{% extends "base.html" %}
{% block content %}
<style>
    @media print {
        body * {
            visibility: hidden;
        }
        .card, .card * {
            visibility: visible;
        }
        .card {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            margin: 0;
            border: none;
            box-shadow: none;
        }
        .btn, .card-footer, .mt-3, .navbar, .sidebar, nav, .alert {
            display: none !important;
        }
    }
</style>
<div class="card mx-auto" style="max-width: 450px; border: 2px solid #0d6efd; border-radius: 15px;">
    <div class="card-header bg-primary text-white text-center">
        <h3>ACK St. Mark's Parish Malaa</h3>
        <h5>Membership Card</h5>
    </div>
    <div class="card-body text-center">
        {% if member.photo_filename %}
            <img src="{{ url_for('static', filename='uploads/' + member.photo_filename) }}" class="member-card-photo" style="width:150px; height:150px; border-radius:50%; object-fit:cover;">
        {% else %}
            <div style="width:150px; height:150px; background:#ccc; border-radius:50%; margin:0 auto; line-height:150px;">No Photo</div>
        {% endif %}
        <h4 class="mt-3">{{ member.name }}</h4>
        <p><strong>Church ID:</strong> {{ member.unique_member_id }}</p>
        <p><strong>Contact:</strong> {{ member.contact }}</p>
        <p><strong>HBC:</strong> {{ member.hbc }}</p>
        <p><strong>Department:</strong> {{ member.department }}</p>
        <p class="text-muted mt-4">Issued: {{ member.created_at.strftime('%d/%m/%Y') }}</p>
        <div class="mt-3">
            <button onclick="window.print()" class="btn btn-primary">Print Card</button>
            <a href="{{ url_for('member_card_pdf', id=member.id) }}" class="btn btn-success">Download PDF</a>
            <a href="{{ url_for('members') }}" class="btn btn-secondary">Back</a>
        </div>
    </div>
</div>
{% endblock %}''',
    "templates/givings.html": '''{% extends "base.html" %}
{% block content %}<div class="d-flex justify-content-between"><h2>Givings</h2>{% if current_user.role in ['Admin','Vicar','Treasurer','HBC Leader','Peoples Warden','Vicars Warden'] %}<a href="{{ url_for('add_giving') }}" class="btn btn-primary">Record Giving</a>{% endif %}</div><div class="card"><div class="card-body"><table class="table table-bordered"><thead><tr><th>Member</th><th>Type</th><th>Amount</th><th>Date</th><th>Status</th><th>Receipt</th></tr></thead><tbody>{% for g in givings %}<tr><td>{{ g.member.name }} ({{ g.member.unique_member_id }})</td><td>{{ g.giving_type }}</td><td>{{ g.amount }}</td><td>{{ g.date.strftime('%Y-%m-%d') }}</td><td><span class="badge bg-{% if g.status == 'approved' %}success{% elif g.status == 'rejected' %}danger{% else %}warning{% endif %}">{{ g.status }}</span></td><td>{% if g.status == 'approved' %}<a href="{{ url_for('receipt', giving_id=g.id) }}" target="_blank" class="btn btn-sm btn-outline-secondary">PDF</a>{% else %}N/A{% endif %}</td></tr>{% endfor %}</tbody></table></div></div>{% endblock %}''',
    "templates/add_giving.html": '''{% extends "base.html" %}
{% block content %}<div class="card"><div class="card-header bg-primary"><h3>Record Giving</h3></div><div class="card-body"><form method="POST">{{ form.hidden_tag() }}<div class="mb-3"><label>Member</label><select name="member_id" class="form-select" required>{% for m in members %}<option value="{{ m.id }}">{{ m.name }} ({{ m.unique_member_id }})</option>{% endfor %}</select></div>{{ form.giving_type.label }} {{ form.giving_type(class="form-select") }}{{ form.amount.label }} {{ form.amount(class="form-control") }}{{ form.date.label }} {{ form.date(class="form-control", type="date") }}{{ form.notes.label }} {{ form.notes(class="form-control") }}<button type="submit" class="btn btn-success mt-3">Save</button> <a href="{{ url_for('givings') }}" class="btn btn-secondary">Cancel</a></form></div></div>{% endblock %}''',
    "templates/pending_givings.html": '''{% extends "base.html" %}
{% block content %}<h2>Pending Givings (Awaiting Approval)</h2><div class="card"><div class="card-body">{% if givings %}<table class="table table-bordered"><thead><tr><th>Member</th><th>Type</th><th>Amount (KES)</th><th>Date</th><th>Notes</th><th>Actions</th></tr></thead><tbody>{% for g in givings %}<tr><td>{{ g.member.name }} ({{ g.member.unique_member_id }})</td><td>{{ g.giving_type }}</td><td>{{ g.amount }}</td><td>{{ g.date.strftime('%Y-%m-%d') }}</td><td>{{ g.notes or '' }}</td><td><a href="{{ url_for('approve_giving', giving_id=g.id) }}" class="btn btn-sm btn-success" onclick="return confirm('Approve this giving?')">Approve</a> <a href="{{ url_for('reject_giving', giving_id=g.id) }}" class="btn btn-sm btn-danger" onclick="return confirm('Reject this giving?')">Reject</a></td></tr>{% endfor %}</tbody></table>{% else %}<div class="alert alert-info">No pending givings.</div>{% endif %}</div></div>{% endblock %}''',
    "templates/notices.html": '''{% extends "base.html" %}
{% block content %}<div class="d-flex justify-content-between"><h2>Notices</h2>{% if current_user.role in ['Secretary','Admin','Vicar'] %}<a href="{{ url_for('add_notice') }}" class="btn btn-primary">+ New Notice</a>{% endif %}</div>{% for notice in notices %}<div class="card mb-3"><div class="card-header"><h4>{{ notice.title }}</h4><small>By {{ notice.created_by }} on {{ notice.date_posted.strftime('%d/%m/%Y') }}</small></div><div class="card-body"><p>{{ notice.content }}</p></div>{% if current_user.role in ['Secretary','Admin','Vicar'] and (current_user.role in ['Admin','Vicar'] or notice.created_by == current_user.username) %}<div class="card-footer"><a href="{{ url_for('edit_notice', id=notice.id) }}" class="btn btn-sm btn-warning">Edit</a> <a href="{{ url_for('delete_notice', id=notice.id) }}" class="btn btn-sm btn-danger" onclick="return confirm('Delete?')">Delete</a></div>{% endif %}</div>{% endfor %}{% endblock %}''',
    "templates/add_notice.html": '''{% extends "base.html" %}
{% block content %}<div class="card"><div class="card-header bg-primary"><h3>Post Notice</h3></div><div class="card-body"><form method="POST">{{ form.hidden_tag() }}{{ form.title.label }} {{ form.title(class="form-control") }}{{ form.content.label }} {{ form.content(class="form-control", rows=6) }}<button type="submit" class="btn btn-success mt-3">Post</button> <a href="{{ url_for('notices') }}" class="btn btn-secondary">Cancel</a></form></div></div>{% endblock %}''',
    "templates/edit_notice.html": '''{% extends "base.html" %}
{% block content %}<div class="card"><div class="card-header bg-warning"><h3>Edit Notice</h3></div><div class="card-body"><form method="POST">{{ form.hidden_tag() }}{{ form.title.label }} {{ form.title(class="form-control") }}{{ form.content.label }} {{ form.content(class="form-control", rows=6) }}<button type="submit" class="btn btn-primary mt-3">Update</button> <a href="{{ url_for('notices') }}" class="btn btn-secondary">Cancel</a></form></div></div>{% endblock %}''',
    "templates/dept_report.html": '''{% extends "base.html" %}
{% block content %}<h2>Department & Children Statistics</h2><div class="row"><div class="col-md-6"><div class="card"><div class="card-header">Departments</div><div class="card-body"><table class="table">{% for key, value in stats.items() if key in ['KAMA', 'Mothers Union', 'KAYO', 'Choir', 'ACWF', 'ACMF'] %}<tr><td>{{ key }}</td><td>{{ value }}</td></tr>{% endfor %}</table></div></div></div><div class="col-md-6"><div class="card"><div class="card-header">Age Groups / Youth</div><div class="card-body"><table class="table"><tr><td>Sunday School (5-12 yrs)</td><td>{{ stats['Sunday School (5-12 yrs)'] }}</td></tr><tr><td>Teens (13-18 yrs)</td><td>{{ stats['Teens (13-18 yrs)'] }}</td></tr><tr><td>KAYO Members</td><td>{{ stats['KAYO Members'] }}</td></tr></table></div></div></div></div>{% endblock %}''',
    "templates/reports.html": '''{% extends "base.html" %}
{% block content %}<h2>Financial Reports (Approved Givings)</h2><div class="row"><div class="col-md-6"><div class="card"><div class="card-header">By Giving Type</div><div class="card-body"><table class="table">{% for t,total in total_by_type %}<tr><td>{{ t }}</td><td>{{ total or 0 }}</td></tr>{% endfor %}</table></div></div></div><div class="col-md-6"><div class="card"><div class="card-header">By HBC</div><div class="card-body"><table class="table">{% for hbc,total in total_by_hbc %}<tr><td>{{ hbc }}</td><td>{{ total or 0 }}</td></tr>{% endfor %}</table></div></div></div></div>{% endblock %}''',
    "templates/admin_users.html": '''{% extends "base.html" %}
{% block content %}<div class="d-flex justify-content-between"><h2>System Users (Officials)</h2><a href="{{ url_for('add_user') }}" class="btn btn-primary">+ Add User</a></div><div class="card"><div class="card-body"><table class="table"><thead><tr><th>Username</th><th>Role</th><th>HBC Leader For</th><th>Linked Member</th><th>Action</th></tr></thead><tbody>{% for u in users %}<tr><td>{{ u.username }}</td><td>{{ u.role }}</td><td>{{ u.hbc_leader_for or '-' }}</td><td>{% if u.member_id %}{{ u.member.name }}{% else %}None{% endif %}</td><td>{% if u.id != current_user.id %}<a href="{{ url_for('delete_user', id=u.id) }}" class="btn btn-sm btn-danger" onclick="return confirm('Delete user and linked member?')">Delete</a>{% else %}(current){% endif %}</td></tr>{% endfor %}</tbody></table></div></div>{% endblock %}''',
    "templates/add_user.html": '''{% extends "base.html" %}
{% block content %}<div class="card"><div class="card-header bg-primary"><h3>Add User (Official)</h3></div><div class="card-body"><form method="POST">{{ form.hidden_tag() }}{{ form.username.label }} {{ form.username(class="form-control") }}{{ form.password.label }} {{ form.password(class="form-control") }}{{ form.role.label }} {{ form.role(class="form-select") }}{{ form.hbc_leader_for.label }} {{ form.hbc_leader_for(class="form-select") }}<button type="submit" class="btn btn-success mt-3">Create User</button> <a href="{{ url_for('admin_users') }}" class="btn btn-secondary">Cancel</a></form></div></div>{% endblock %}''',
    "templates/member_profile.html": '''{% extends "base.html" %}
{% block content %}<div class="card"><div class="card-header bg-primary text-white"><h3>My Profile</h3></div><div class="card-body">{% if member.photo_filename %}<img src="{{ url_for('static', filename='uploads/' + member.photo_filename) }}" style="max-width:150px; border-radius:50%; float:right;">{% endif %}<p><strong>Unique ID:</strong> {{ member.unique_member_id }}</p><p><strong>Name:</strong> {{ member.name }}</p><p><strong>Phone:</strong> {{ member.contact }}</p><p><strong>Spouse:</strong> {{ member.spouse_name or 'None' }} ({{ member.spouse_contact or '-' }})</p><p><strong>HBC:</strong> {{ member.hbc }}</p><p><strong>Department:</strong> {{ member.department }}</p><p><strong>Children:</strong> <ul>{% for child in member.children %}<li>{{ child.name }} (Age {{ child.age }})</li>{% endfor %}</ul></p><hr><h4>Registration Payment</h4>{% if payments %}<table class="table table-bordered"><thead><tr><th>Receipt No</th><th>Amount (KES)</th><th>Method</th><th>Date</th><th>Status</th><th>Receipt</th></tr></thead><tbody>{% for payment in payments %}<tr><td>{{ payment.receipt_no or 'N/A' }}</td><td>{{ payment.amount }}</td><td>{{ payment.method }}</td><td>{{ payment.recorded_at.strftime('%d/%m/%Y') }}</td><td>{{ payment.status.capitalize() }}</td><td><a href="{{ url_for('payment_receipt', payment_id=payment.id) }}" target="_blank" class="btn btn-sm btn-outline-secondary">PDF Receipt</a></td></tr>{% endfor %}</tbody></table>{% else %}<p class="text-muted">No registration payment recorded yet.</p>{% endif %}<a href="{{ url_for('index') }}" class="btn btn-secondary mt-3">Back</a></div></div>{% endblock %}''',
    "templates/my_givings.html": '''{% extends "base.html" %}
{% block content %}<h2>My Giving History</h2><div class="card"><div class="card-body">{% if givings %}<table class="table"><thead><tr><th>Type</th><th>Amount</th><th>Date</th><th>Receipt</th></tr></thead><tbody>{% for g in givings %}<tr><td>{{ g.giving_type }}</td><td>{{ g.amount }}</td><td>{{ g.date.strftime('%Y-%m-%d') }}</td><td><a href="{{ url_for('receipt', giving_id=g.id) }}" target="_blank">PDF</a></td></tr>{% endfor %}</tbody></table>{% else %}<p>No approved givings yet.</p>{% endif %}<a href="{{ url_for('index') }}" class="btn btn-secondary">Back</a></div></div>{% endblock %}''',
    "templates/change_password.html": '''{% extends "base.html" %}
{% block content %}<div class="row justify-content-center"><div class="col-md-5"><div class="card"><div class="card-header bg-primary"><h3>Change Password</h3></div><div class="card-body"><form method="POST">{{ form.hidden_tag() }}{{ form.current_password.label }} {{ form.current_password(class="form-control") }}{{ form.new_password.label }} {{ form.new_password(class="form-control") }}{{ form.confirm_password.label }} {{ form.confirm_password(class="form-control") }}<button type="submit" class="btn btn-primary w-100 mt-3">Update</button></form></div></div></div></div>{% endblock %}''',
}

for filename, content in files.items():
    with open(filename, "w") as f:
        f.write(content)
    print(f"Created: {filename}")

for filename, content in html_files.items():
    with open(filename, "w") as f:
        f.write(content)
    print(f"Created: {filename}")

print("\n✅ ALL files created successfully!")
print("Final system includes:")
print("- Self-registration with M-Pesa and fee calculator")
print("- Treasurer approval for registration payments")
print("- Registration payment shown on member's profile with PDF receipt")
print("- Treasurer approval for regular givings (including 'Registration' type)")
print("- Department statistics including Sunday School, Teens, KAYO")
print("- Membership card with photo (print-only card, no spouse details)")
print("- PDF membership card download")
print("- Roles: Admin, Vicar, Vice Chairman, Treasurer, Secretary, HBC Leader, Peoples Warden, Vicars Warden, Member")
print("- HBC Leader, Peoples Warden, Vicars Warden can add members and record givings, but cannot see financial reports")
print("- Admin can reset member passwords")
print("- All previous features (notices, reports, search, etc.)")
print("\nNext steps:")
print("1. Delete old church.db")
print("2. Run: python -m pip install -r requirements.txt")
print("3. Run: python app.py")
print("4. Login: admin / admin123")