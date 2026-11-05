from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def role_required(*allowed_roles):
    """
    Decorator to restrict access to routes based on user roles.
    Example: @role_required('Admin', 'Doctor')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if not current_user.role or current_user.role.name not in allowed_roles:
                flash(f'Access denied. This section requires one of these roles: {", ".join(allowed_roles)}.', 'danger')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
