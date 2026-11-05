from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.auth import User, Role, UserProfile
from app.forms.auth_forms import LoginForm, RegisterForm, ChangePasswordForm, ProfileForm
from app.services.audit_service import log_audit, record_login_attempt

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        ident = form.username_or_email.data.strip()
        user = User.query.filter((User.username == ident) | (User.email == ident)).first()
        
        ip_addr = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')

        if user and user.check_password(form.password.data):
            if user.is_deleted or user.status != 'Active' or not user.is_account_active:
                flash('Your account has been deactivated or disabled. Please contact the administrator.', 'danger')
                record_login_attempt(user.id, ip_addr, user_agent, 'Failed (Deactivated)')
                return render_template('auth/login.html', form=form)
                
            login_user(user, remember=form.remember_me.data)
            record_login_attempt(user.id, ip_addr, user_agent, 'Success')
            log_audit('LOGIN', 'users', user.id, f'User {user.username} logged in successfully', user.id)
            
            flash(f'Welcome back, {user.profile.full_name if user.profile else user.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            if user:
                record_login_attempt(user.id, ip_addr, user_agent, 'Failed (Invalid Password)')
            flash('Invalid username/email or password. Please check your credentials.', 'danger')
            
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    log_audit('LOGOUT', 'users', current_user.id, f'User {current_user.username} logged out')
    logout_user()
    flash('You have been securely logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Only allow Admin or Receptionist to register accounts or allow self-registration for demo
    form = RegisterForm()
    roles = Role.query.filter_by(is_deleted=False, status='Active').all()
    form.role_id.choices = [(r.id, r.name) for r in roles]

    if form.validate_on_submit():
        existing_user = User.query.filter((User.username == form.username.data) | (User.email == form.email.data)).first()
        if existing_user:
            flash('A user with that username or email already exists.', 'warning')
            return render_template('auth/register.html', form=form)

        new_user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            role_id=form.role_id.data,
            is_account_active=True
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.flush()

        profile = UserProfile(
            user_id=new_user.id,
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            phone=form.phone.data.strip() if form.phone.data else None
        )
        db.session.add(profile)
        db.session.commit()

        log_audit('CREATE', 'users', new_user.id, f'Registered user {new_user.username}')
        flash('Account registered successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user.profile)
    pwd_form = ChangePasswordForm()

    if form.validate_on_submit() and 'submit_profile' in request.form:
        if not current_user.profile:
            current_user.profile = UserProfile(user_id=current_user.id)
            
        current_user.profile.first_name = form.first_name.data.strip()
        current_user.profile.last_name = form.last_name.data.strip()
        current_user.profile.phone = form.phone.data.strip() if form.phone.data else None
        current_user.profile.national_id = form.national_id.data.strip() if form.national_id.data else None
        current_user.profile.bio = form.bio.data.strip() if form.bio.data else None
        current_user.profile.address = form.address.data.strip() if form.address.data else None
        
        db.session.commit()
        log_audit('UPDATE', 'user_profiles', current_user.profile.id, 'Updated personal profile details')
        flash('Your profile details have been updated.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html', form=form, pwd_form=pwd_form)

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    pwd_form = ChangePasswordForm()
    if pwd_form.validate_on_submit():
        if not current_user.check_password(pwd_form.current_password.data):
            flash('Current password is incorrect.', 'danger')
        else:
            current_user.set_password(pwd_form.new_password.data)
            db.session.commit()
            log_audit('UPDATE', 'users', current_user.id, 'Changed login password')
            flash('Your password has been updated successfully.', 'success')
            return redirect(url_for('auth.profile'))
    else:
        for field, errors in pwd_form.errors.items():
            for error in errors:
                flash(f'Password error: {error}', 'danger')
    return redirect(url_for('auth.profile'))
