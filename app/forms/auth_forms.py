from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional

class LoginForm(FlaskForm):
    username_or_email = StringField('Username or Email', validators=[DataRequired(), Length(min=3, max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=100)])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=25)])
    role_id = SelectField('Assigned Role', coerce=int, validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=100)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Create Account')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6, max=100)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Update Password')

class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=25)])
    national_id = StringField('National ID / CNIC', validators=[Optional(), Length(max=50)])
    bio = TextAreaField('Professional Bio', validators=[Optional(), Length(max=500)])
    address = StringField('Address', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Save Profile')
