from datetime import datetime
from app.extensions import db
from app.models.base import BaseModelMixin

class Appointment(BaseModelMixin, db.Model):
    """23. appointments - Outpatient and consultation appointment bookings"""
    __tablename__ = 'appointments'
    
    appointment_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    appointment_type = db.Column(db.String(30), default='New Visit', nullable=False) # 'New Visit', 'Follow-up', 'Emergency', 'Routine'
    reason = db.Column(db.Text, nullable=True)
    current_status = db.Column(db.String(30), default='Scheduled', nullable=False) # 'Scheduled', 'Confirmed', 'Completed', 'Cancelled', 'No-Show'

    # Relationships
    patient = db.relationship('Patient', back_populates='appointments')
    doctor = db.relationship('Doctor', back_populates='appointments')
    department = db.relationship('Department')
    status_history = db.relationship('AppointmentStatusHistory', back_populates='appointment', cascade='all, delete-orphan')
    queue_token = db.relationship('QueueToken', back_populates='appointment', uselist=False)
    visit = db.relationship('Visit', back_populates='appointment', uselist=False)

    def __repr__(self):
        return f'<Appointment {self.appointment_number} Status:{self.current_status}>'


class AppointmentStatusHistory(BaseModelMixin, db.Model):
    """24. appointment_status_history - Audit log of appointment status transitions"""
    __tablename__ = 'appointment_status_history'
    
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    old_status = db.Column(db.String(30), nullable=True)
    new_status = db.Column(db.String(30), nullable=False)
    change_reason = db.Column(db.String(255), nullable=True)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    appointment = db.relationship('Appointment', back_populates='status_history')

    def __repr__(self):
        return f'<AppointmentStatusHistory Appt:{self.appointment_id} {self.old_status}->{self.new_status}>'


class QueueToken(BaseModelMixin, db.Model):
    """25. queue_tokens - Daily OPD clinic queue management tokens"""
    __tablename__ = 'queue_tokens'
    
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    token_number = db.Column(db.Integer, nullable=False)
    token_date = db.Column(db.Date, nullable=False)
    token_status = db.Column(db.String(30), default='Waiting', nullable=False) # 'Waiting', 'In-Consultation', 'Completed', 'Skipped'

    appointment = db.relationship('Appointment', back_populates='queue_token')
    patient = db.relationship('Patient')
    doctor = db.relationship('Doctor')

    def __repr__(self):
        return f'<QueueToken #{self.token_number} Date:{self.token_date} Status:{self.token_status}>'


class Visit(BaseModelMixin, db.Model):
    """26. visits - Clinical encounters (OPD/Emergency consultations)"""
    __tablename__ = 'visits'
    
    visit_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=True)
    visit_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    visit_type = db.Column(db.String(30), default='OPD', nullable=False) # 'OPD', 'IPD', 'Emergency'
    
    # Vital signs
    systolic_bp = db.Column(db.Integer, nullable=True)
    diastolic_bp = db.Column(db.Integer, nullable=True)
    heart_rate = db.Column(db.Integer, nullable=True)
    temperature = db.Column(db.Float, nullable=True)
    weight_kg = db.Column(db.Float, nullable=True)
    height_cm = db.Column(db.Float, nullable=True)
    symptoms = db.Column(db.Text, nullable=True)
    clinical_notes = db.Column(db.Text, nullable=True)

    # Relationships
    patient = db.relationship('Patient', back_populates='visits')
    doctor = db.relationship('Doctor', back_populates='visits')
    appointment = db.relationship('Appointment', back_populates='visit')
    visit_diagnoses = db.relationship('VisitDiagnosis', back_populates='visit', cascade='all, delete-orphan')
    prescriptions = db.relationship('Prescription', back_populates='visit')
    lab_orders = db.relationship('LabOrder', back_populates='visit')
    invoices = db.relationship('Invoice', back_populates='visit')
    feedback_records = db.relationship('Feedback', back_populates='visit')

    def __repr__(self):
        return f'<Visit {self.visit_number} Patient:{self.patient_id}>'
