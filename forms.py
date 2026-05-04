from flask_wtf import FlaskForm
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
