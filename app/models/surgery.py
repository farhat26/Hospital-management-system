from datetime import datetime
from app.extensions import db
from app.models.base import BaseModelMixin

class OperationTheatre(BaseModelMixin, db.Model):
    """53. operation_theatres - Surgical suites and OT facilities"""
    __tablename__ = 'operation_theatres'
    
    ot_number = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    floor = db.Column(db.Integer, default=2, nullable=False)
    theatre_type = db.Column(db.String(50), default='Major', nullable=False) # 'Major', 'Minor', 'Cardiac', 'Orthopedic'
    is_equipped = db.Column(db.Boolean, default=True, nullable=False)
    maintenance_status = db.Column(db.String(30), default='Operational', nullable=False) # 'Operational', 'Under Maintenance', 'Sterilizing'

    schedules = db.relationship('SurgerySchedule', back_populates='theatre', lazy='dynamic')

    def __repr__(self):
        return f'<OperationTheatre {self.ot_number} - {self.name}>'


class Surgery(BaseModelMixin, db.Model):
    """52. surgeries - Catalog of surgical procedures and protocols"""
    __tablename__ = 'surgeries'
    
    surgery_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    surgery_name = db.Column(db.String(150), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    estimated_duration_minutes = db.Column(db.Integer, default=60, nullable=False)
    standard_cost = db.Column(db.Float, default=25000.0, nullable=False)
    description = db.Column(db.Text, nullable=True)

    department = db.relationship('Department', back_populates='surgeries')
    schedules = db.relationship('SurgerySchedule', back_populates='surgery', lazy='dynamic')

    def __repr__(self):
        return f'<Surgery {self.surgery_code} - {self.surgery_name}>'


class SurgerySchedule(BaseModelMixin, db.Model):
    """54. surgery_schedules - Scheduled surgical bookings and execution logs"""
    __tablename__ = 'surgery_schedules'
    
    surgery_id = db.Column(db.Integer, db.ForeignKey('surgeries.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    lead_surgeon_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    theatre_id = db.Column(db.Integer, db.ForeignKey('operation_theatres.id'), nullable=False)
    scheduled_start_time = db.Column(db.DateTime, nullable=False)
    scheduled_end_time = db.Column(db.DateTime, nullable=False)
    actual_start_time = db.Column(db.DateTime, nullable=True)
    actual_end_time = db.Column(db.DateTime, nullable=True)
    surgery_status = db.Column(db.String(30), default='Scheduled', nullable=False) # 'Scheduled', 'In-Progress', 'Completed', 'Postponed', 'Cancelled'
    pre_op_notes = db.Column(db.Text, nullable=True)
    post_op_notes = db.Column(db.Text, nullable=True)

    surgery = db.relationship('Surgery', back_populates='schedules')
    patient = db.relationship('Patient', back_populates='surgeries')
    lead_surgeon = db.relationship('Doctor', back_populates='surgery_schedules')
    theatre = db.relationship('OperationTheatre', back_populates='schedules')

    def __repr__(self):
        return f'<SurgerySchedule Surgery:{self.surgery_id} Patient:{self.patient_id} Status:{self.surgery_status}>'


class Ambulance(BaseModelMixin, db.Model):
    """55. ambulances - Emergency ambulance fleet and dispatch management"""
    __tablename__ = 'ambulances'
    
    vehicle_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    vehicle_model = db.Column(db.String(100), nullable=False)
    ambulance_type = db.Column(db.String(50), default='Advanced Life Support', nullable=False) # 'Basic Life Support', 'Advanced Life Support', 'Patient Transport'
    driver_name = db.Column(db.String(100), nullable=False)
    driver_phone = db.Column(db.String(25), nullable=False)
    current_location = db.Column(db.String(150), default='Hospital Station', nullable=False)
    operational_status = db.Column(db.String(30), default='Available', nullable=False) # 'Available', 'On Trip', 'Under Maintenance'

    def __repr__(self):
        return f'<Ambulance {self.vehicle_number} ({self.operational_status})>'
