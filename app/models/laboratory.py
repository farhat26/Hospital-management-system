from datetime import datetime
from app.extensions import db
from app.models.base import BaseModelMixin

class LabTest(BaseModelMixin, db.Model):
    """37. lab_tests - Diagnostic and pathology investigation test catalog"""
    __tablename__ = 'lab_tests'
    
    test_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    test_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(50), default='Hematology', nullable=False) # 'Hematology', 'Biochemistry', 'Microbiology', 'Radiology'
    cost = db.Column(db.Float, default=500.0, nullable=False)
    normal_range = db.Column(db.String(100), nullable=True) # e.g. "13.5 - 17.5 g/dL"
    unit_of_measure = db.Column(db.String(30), nullable=True) # e.g. "g/dL", "mg/dL"
    description = db.Column(db.Text, nullable=True)

    order_items = db.relationship('LabOrderItem', back_populates='lab_test', lazy='dynamic')

    def __repr__(self):
        return f'<LabTest {self.test_code} - {self.test_name}>'


class LabOrder(BaseModelMixin, db.Model):
    """38. lab_orders - Clinical laboratory investigation requisitions"""
    __tablename__ = 'lab_orders'
    
    order_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id'), nullable=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    priority = db.Column(db.String(20), default='Routine', nullable=False) # 'Routine', 'Urgent', 'STAT'
    order_status = db.Column(db.String(30), default='Pending', nullable=False) # 'Pending', 'Sample Collected', 'In Process', 'Completed', 'Cancelled'

    patient = db.relationship('Patient', back_populates='lab_orders')
    doctor = db.relationship('Doctor', back_populates='lab_orders')
    visit = db.relationship('Visit', back_populates='lab_orders')
    items = db.relationship('LabOrderItem', back_populates='lab_order', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<LabOrder {self.order_number} Status:{self.order_status}>'


class LabOrderItem(BaseModelMixin, db.Model):
    """39. lab_order_items - Individual diagnostic tests ordered in a requisition"""
    __tablename__ = 'lab_order_items'
    
    lab_order_id = db.Column(db.Integer, db.ForeignKey('lab_orders.id'), nullable=False)
    lab_test_id = db.Column(db.Integer, db.ForeignKey('lab_tests.id'), nullable=False)
    item_status = db.Column(db.String(30), default='Pending', nullable=False) # 'Pending', 'Processing', 'Completed'
    sample_type = db.Column(db.String(50), default='Blood', nullable=False) # 'Blood', 'Urine', 'Serum', 'Tissue', 'Swab'

    lab_order = db.relationship('LabOrder', back_populates='items')
    lab_test = db.relationship('LabTest', back_populates='order_items')
    result = db.relationship('LabResult', back_populates='order_item', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<LabOrderItem Order:{self.lab_order_id} Test:{self.lab_test_id}>'


class LabResult(BaseModelMixin, db.Model):
    """40. lab_results - Clinical laboratory analytical findings and readings"""
    __tablename__ = 'lab_results'
    
    lab_order_item_id = db.Column(db.Integer, db.ForeignKey('lab_order_items.id'), unique=True, nullable=False)
    technician_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    result_value = db.Column(db.String(100), nullable=False)
    reference_range_snapshot = db.Column(db.String(100), nullable=True)
    remarks = db.Column(db.Text, nullable=True)
    is_abnormal = db.Column(db.Boolean, default=False, nullable=False)
    verified_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    order_item = db.relationship('LabOrderItem', back_populates='result')
    technician = db.relationship('User', foreign_keys=[technician_id])

    def __repr__(self):
        return f'<LabResult Item:{self.lab_order_item_id} Value:{self.result_value} Abnormal:{self.is_abnormal}>'
