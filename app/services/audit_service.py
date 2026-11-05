from flask_login import current_user
from app.extensions import db
from app.models.auth import AuditLog, LoginHistory
from datetime import datetime

def log_audit(action, table_name, record_id, details=None, user_id=None):
    """
    Log system modifications (CREATE, UPDATE, SOFT_DELETE, RESTORE) to the audit_logs table.
    """
    try:
        actor_id = user_id
        if actor_id is None and current_user and current_user.is_authenticated:
            actor_id = current_user.id
            
        log_entry = AuditLog(
            user_id=actor_id,
            action=action.upper(),
            table_name=table_name,
            record_id=record_id,
            details=details or f"{action} operation executed on {table_name} record #{record_id}",
            timestamp=datetime.utcnow()
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # Non-blocking for primary transaction
        print(f"Audit log error: {e}")

def record_login_attempt(user_id, ip_address, user_agent, status_result='Success'):
    """
    Record user authentication attempt in login_history table.
    """
    try:
        history = LoginHistory(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent[:250] if user_agent else 'Unknown',
            login_time=datetime.utcnow(),
            status_result=status_result
        )
        db.session.add(history)
        db.session.commit()
        return history
    except Exception as e:
        db.session.rollback()
        print(f"Login history recording error: {e}")
        return None
