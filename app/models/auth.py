from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models.base import BaseModelMixin

class Role(BaseModelMixin, db.Model):
    """1. roles - User access roles (Admin, Doctor, Nurse, etc.)"""
    __tablename__ = 'roles'
    
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    
    users = db.relationship('User', back_populates='role', lazy='dynamic', foreign_keys='User.role_id')

    def __repr__(self):
        return f'<Role {self.name}>'


class User(BaseModelMixin, UserMixin, db.Model):
    """2. users - System authentication accounts"""
    __tablename__ = 'users'
    
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    is_account_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)
    
    role = db.relationship('Role', back_populates='users', foreign_keys=[role_id])
    profile = db.relationship('UserProfile', back_populates='user', uselist=False, cascade='all, delete-orphan', foreign_keys='UserProfile.user_id')
    login_history = db.relationship('LoginHistory', back_populates='user', lazy='dynamic', foreign_keys='LoginHistory.user_id')
    audit_logs = db.relationship('AuditLog', back_populates='user', lazy='dynamic', foreign_keys='AuditLog.user_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        # Override Flask-Login is_active to respect is_account_active & is_deleted & status
        return self.is_account_active and not self.is_deleted and self.status == 'Active'

    def has_role(self, *role_names):
        if not self.role:
            return False
        return self.role.name in role_names

    def __repr__(self):
        return f'<User {self.username} ({self.role.name if self.role else "No Role"})>'


class UserProfile(BaseModelMixin, db.Model):
    """3. user_profiles - Detailed profile information for users"""
    __tablename__ = 'user_profiles'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(25), nullable=True)
    national_id = db.Column(db.String(50), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    address = db.Column(db.String(255), nullable=True)

    user = db.relationship('User', back_populates='profile', foreign_keys=[user_id])

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __repr__(self):
        return f'<UserProfile {self.full_name}>'


class LoginHistory(BaseModelMixin, db.Model):
    """4. login_history - Audit log of user authentications"""
    __tablename__ = 'login_history'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    login_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    logout_time = db.Column(db.DateTime, nullable=True)
    status_result = db.Column(db.String(20), default='Success', nullable=False) # 'Success', 'Failed'

    user = db.relationship('User', back_populates='login_history', foreign_keys=[user_id])

    def __repr__(self):
        return f'<LoginHistory User:{self.user_id} Time:{self.login_time}>'


class AuditLog(BaseModelMixin, db.Model):
    """5. audit_logs - Granular system activity and audit trail"""
    __tablename__ = 'audit_logs'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False) # 'CREATE', 'UPDATE', 'SOFT_DELETE', 'RESTORE', 'LOGIN'
    table_name = db.Column(db.String(80), nullable=False)
    record_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', back_populates='audit_logs', foreign_keys=[user_id])

    def __repr__(self):
        return f'<AuditLog {self.action} on {self.table_name}:{self.record_id}>'
