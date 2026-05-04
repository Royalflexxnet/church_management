from flask import Flask, render_template, request, redirect, url_for, flash, abort, jsonify, send_file
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
