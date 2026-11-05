from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import ALL_MODELS, MODEL_MAP
from app.models.auth import User, Role, UserProfile, AuditLog, LoginHistory
from app.forms.auth_forms import RegisterForm
from app.utils.decorators import role_required
from app.services.audit_service import log_audit
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
@role_required('Admin')
def index():
    user_count = User.query.filter_by(is_deleted=False).count()
    audit_count = AuditLog.query.count()
    login_count = LoginHistory.query.count()
    
    # Calculate total deleted records across all 56 tables
    total_deleted = 0
    for model in ALL_MODELS:
        try:
            total_deleted += model.query.filter_by(is_deleted=True).count()
        except Exception:
            pass

    return render_template(
        'admin/index.html',
        user_count=user_count,
        audit_count=audit_count,
        login_count=login_count,
        total_deleted=total_deleted,
        all_models_count=len(ALL_MODELS)
    )

# ----------------- User Management -----------------
@admin_bp.route('/users')
@login_required
@role_required('Admin')
def users():
    users_list = User.query.order_by(User.id).all()
    roles = Role.query.filter_by(is_deleted=False).all()
    return render_template('admin/users.html', users=users_list, roles=roles)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def create_user():
    form = RegisterForm()
    roles = Role.query.filter_by(is_deleted=False, status='Active').all()
    form.role_id.choices = [(r.id, r.name) for r in roles]

    if form.validate_on_submit():
        existing = User.query.filter((User.username == form.username.data.strip()) | (User.email == form.email.data.strip().lower())).first()
        if existing:
            flash('Username or Email already exists in the system.', 'warning')
            return render_template('admin/user_form.html', form=form, title='Provision User Account')

        new_user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            role_id=form.role_id.data,
            is_account_active=True,
            created_by_id=current_user.id
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.flush()

        profile = UserProfile(
            user_id=new_user.id,
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            phone=form.phone.data.strip() if form.phone.data else None,
            created_by_id=current_user.id
        )
        db.session.add(profile)
        db.session.commit()

        log_audit('CREATE', 'users', new_user.id, f'Admin provisioned user {new_user.username} with role {new_user.role.name}')
        flash(f'User account {new_user.username} created successfully.', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/user_form.html', form=form, title='Provision User Account')

@admin_bp.route('/users/<int:id>/toggle-status', methods=['POST'])
@login_required
@role_required('Admin')
def toggle_user_status(id):
    if id == current_user.id:
        flash('You cannot deactivate your own administrative account.', 'danger')
        return redirect(url_for('admin.users'))
        
    user = User.query.get_or_404(id)
    user.is_account_active = not user.is_account_active
    user.status = 'Active' if user.is_account_active else 'Deactive'
    user.updated_by_id = current_user.id
    db.session.commit()
    log_audit('UPDATE', 'users', user.id, f'Admin toggled account active status to {user.is_account_active}')
    flash(f'User {user.username} account {"activated" if user.is_account_active else "disabled"}.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:id>/change-role', methods=['POST'])
@login_required
@role_required('Admin')
def change_user_role(id):
    user = User.query.get_or_404(id)
    new_role_id = request.form.get('role_id', type=int)
    if new_role_id:
        role = Role.query.get(new_role_id)
        if role:
            user.role_id = role.id
            user.updated_by_id = current_user.id
            db.session.commit()
            log_audit('UPDATE', 'users', user.id, f'Changed role to {role.name}')
            flash(f'Role updated to {role.name} for user {user.username}.', 'success')
    return redirect(url_for('admin.users'))

# ----------------- Audit Logs & Login History -----------------
@admin_bp.route('/audit-logs')
@login_required
@role_required('Admin')
def audit_logs():
    page = request.args.get('page', 1, type=int)
    table_filter = request.args.get('table', '').strip()
    action_filter = request.args.get('action', '').strip()

    query = AuditLog.query
    if table_filter:
        query = query.filter_by(table_name=table_filter)
    if action_filter:
        query = query.filter_by(action=action_filter)

    pagination = query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=15, error_out=False)
    logs = pagination.items

    # List of unique tables in audit log
    tables_in_audit = [r[0] for r in db.session.query(AuditLog.table_name).distinct().all()]

    return render_template(
        'admin/audit_logs.html',
        logs=logs,
        pagination=pagination,
        tables=tables_in_audit,
        selected_table=table_filter,
        selected_action=action_filter
    )

@admin_bp.route('/login-history')
@login_required
@role_required('Admin')
def login_history():
    page = request.args.get('page', 1, type=int)
    pagination = LoginHistory.query.order_by(LoginHistory.login_time.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template('admin/login_history.html', history=pagination.items, pagination=pagination)

# -------------------------------------------------------------
# Recycle Bin / Deleted Records (Soft Delete & Restore Center)
# -------------------------------------------------------------
@admin_bp.route('/recycle-bin')
@login_required
@role_required('Admin')
def recycle_bin():
    selected_table = request.args.get('table', '').strip()
    
    deleted_items = []
    
    # Scan models for soft deleted records
    targets = [MODEL_MAP[selected_table]] if selected_table in MODEL_MAP else ALL_MODELS
    
    for model in targets:
        try:
            records = model.query.filter_by(is_deleted=True).all()
            for r in records:
                deleted_items.append({
                    'table_name': model.__tablename__,
                    'model_class': model.__name__,
                    'id': r.id,
                    'record_repr': str(r),
                    'deleted_at': r.deleted_at,
                    'deleted_by_id': r.deleted_by_id,
                    'created_at': r.created_at
                })
        except Exception:
            pass

    # Sort descending by deletion time
    deleted_items.sort(key=lambda x: x['deleted_at'] or datetime.min, reverse=True)

    available_tables = sorted(list(MODEL_MAP.keys()))

    return render_template(
        'admin/recycle_bin.html',
        deleted_items=deleted_items,
        available_tables=available_tables,
        selected_table=selected_table,
        total_found=len(deleted_items)
    )

@admin_bp.route('/recycle-bin/restore/<string:table_name>/<int:id>', methods=['POST'])
@login_required
@role_required('Admin')
def restore_record(table_name, id):
    model = MODEL_MAP.get(table_name)
    if not model:
        flash(f'Invalid table: {table_name}', 'danger')
        return redirect(url_for('admin.recycle_bin'))

    record = model.query.get_or_404(id)
    record.restore()
    log_audit('RESTORE', table_name, record.id, f'Admin restored soft-deleted record #{record.id} in {table_name}')
    flash(f'Successfully restored record #{record.id} in {table_name}.', 'success')
    return redirect(request.referrer or url_for('admin.recycle_bin'))

@admin_bp.route('/recycle-bin/purge/<string:table_name>/<int:id>', methods=['POST'])
@login_required
@role_required('Admin')
def permanent_purge(table_name, id):
    model = MODEL_MAP.get(table_name)
    if not model:
        flash(f'Invalid table: {table_name}', 'danger')
        return redirect(url_for('admin.recycle_bin'))

    record = model.query.get_or_404(id)
    try:
        db.session.delete(record)
        db.session.commit()
        log_audit('PURGE', table_name, id, f'Admin permanently purged record #{id} from {table_name}')
        flash(f'Record #{id} permanently purged from {table_name}.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Cannot purge record due to foreign key constraints: {e}', 'danger')

    return redirect(request.referrer or url_for('admin.recycle_bin'))
