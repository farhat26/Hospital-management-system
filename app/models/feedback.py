from datetime import datetime
from app.extensions import db
from app.models.base import BaseModelMixin

class Feedback(BaseModelMixin, db.Model):
    """56. feedback - Patient satisfaction surveys and service feedback"""
    __tablename__ = 'feedback'
    
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True)
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id'), nullable=True)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    rating = db.Column(db.Integer, default=5, nullable=False) # 1 to 5 stars
    category = db.Column(db.String(50), default='Overall Experience', nullable=False) # 'Doctor Care', 'Staff Behavior', 'Cleanliness', 'Wait Time', 'Overall Experience'
    comments = db.Column(db.Text, nullable=False)
    is_anonymous = db.Column(db.Boolean, default=False, nullable=False)
    resolution_status = db.Column(db.String(30), default='Submitted', nullable=False) # 'Submitted', 'Reviewed', 'Action Taken'

    patient = db.relationship('Patient', back_populates='feedback_records')
    visit = db.relationship('Visit', back_populates='feedback_records')
    department = db.relationship('Department')

    def __repr__(self):
        return f'<Feedback Rating:{self.rating} Category:{self.category}>'
