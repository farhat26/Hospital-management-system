from datetime import datetime
from app.extensions import db

class BaseModelMixin:
    """
    Common Base Mixin for ALL 56 Hospital Management System database tables.
    Provides standard audit tracking, Active/Deactive state, and soft deletion.
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Audit tracking fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    updated_by_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # Active / Deactive status (independent from soft deletion)
    status = db.Column(db.String(20), default='Active', nullable=False)
    
    # Soft deletion fields
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    def soft_delete(self, user_id=None):
        """Soft delete the record without removing it from database."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        if user_id:
            self.deleted_by_id = user_id
        db.session.commit()

    def restore(self):
        """Restore a soft-deleted record back to active state."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by_id = None
        db.session.commit()

    def toggle_status(self, user_id=None):
        """Toggle status between Active and Deactive."""
        self.status = 'Deactive' if self.status == 'Active' else 'Active'
        if user_id:
            self.updated_by_id = user_id
        db.session.commit()
