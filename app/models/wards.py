from datetime import datetime
from app.extensions import db
from app.models.base import BaseModelMixin

class Ward(BaseModelMixin, db.Model):
    """41. wards - Inpatient hospitalization wards and wings"""
    __tablename__ = 'wards'
    
    ward_name = db.Column(db.String(100), unique=True, nullable=False)
    ward_type = db.Column(db.String(50), default='General', nullable=False) # 'General', 'ICU', 'Pediatric', 'Maternity', 'Surgical'
    gender_type = db.Column(db.String(20), default='Mixed', nullable=False) # 'Male', 'Female', 'Mixed'
    total_capacity = db.Column(db.Integer, default=20, nullable=False)
    floor_number = db.Column(db.Integer, default=1, nullable=False)

    rooms = db.relationship('Room', back_populates='ward', cascade='all, delete-orphan')

    @property
    def total_beds(self):
        return sum(len(r.beds) for r in self.rooms if not r.is_deleted)

    @property
    def available_beds_count(self):
        count = 0
        for r in self.rooms:
            if not r.is_deleted and r.status == 'Active':
                count += sum(1 for b in r.beds if not b.is_deleted and b.status == 'Active' and b.bed_status == 'Available')
        return count

    def __repr__(self):
        return f'<Ward {self.ward_name} ({self.ward_type})>'


class Room(BaseModelMixin, db.Model):
    """42. rooms - Individual rooms inside hospital wards"""
    __tablename__ = 'rooms'
    
    ward_id = db.Column(db.Integer, db.ForeignKey('wards.id'), nullable=False)
    room_number = db.Column(db.String(30), nullable=False)
    room_type = db.Column(db.String(50), default='Standard', nullable=False) # 'Standard', 'Deluxe', 'Private', 'Semi-Private'
    daily_rate = db.Column(db.Float, default=1500.0, nullable=False)

    ward = db.relationship('Ward', back_populates='rooms')
    beds = db.relationship('Bed', back_populates='room', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Room {self.room_number} in Ward:{self.ward_id}>'


class Bed(BaseModelMixin, db.Model):
    """43. beds - Physical patient beds for inpatient allocation"""
    __tablename__ = 'beds'
    
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    bed_number = db.Column(db.String(30), nullable=False)
    bed_type = db.Column(db.String(50), default='Regular', nullable=False) # 'Regular', 'ICU Bed', 'Electric', 'Bariatric'
    bed_status = db.Column(db.String(30), default='Available', nullable=False) # 'Available', 'Occupied', 'Maintenance', 'Reserved'

    room = db.relationship('Room', back_populates='beds')
    allocations = db.relationship('BedAllocation', back_populates='bed', lazy='dynamic')

    def __repr__(self):
        return f'<Bed {self.bed_number} Status:{self.bed_status}>'


class Admission(BaseModelMixin, db.Model):
    """44. admissions - Inpatient hospital admissions"""
    __tablename__ = 'admissions'
    
    admission_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    admission_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    admission_type = db.Column(db.String(30), default='Elective', nullable=False) # 'Emergency', 'Elective', 'Day Care'
    reason_for_admission = db.Column(db.Text, nullable=False)
    admission_status = db.Column(db.String(30), default='Admitted', nullable=False) # 'Admitted', 'Transferred', 'Discharged'

    patient = db.relationship('Patient', back_populates='admissions')
    doctor = db.relationship('Doctor', back_populates='admissions')
    bed_allocations = db.relationship('BedAllocation', back_populates='admission', cascade='all, delete-orphan')
    discharge = db.relationship('Discharge', back_populates='admission', uselist=False, cascade='all, delete-orphan')
    invoices = db.relationship('Invoice', back_populates='admission')

    def __repr__(self):
        return f'<Admission {self.admission_number} Patient:{self.patient_id} Status:{self.admission_status}>'


class BedAllocation(BaseModelMixin, db.Model):
    """45. bed_allocations - Bed assignments throughout an admission stay"""
    __tablename__ = 'bed_allocations'
    
    admission_id = db.Column(db.Integer, db.ForeignKey('admissions.id'), nullable=False)
    bed_id = db.Column(db.Integer, db.ForeignKey('beds.id'), nullable=False)
    allocated_from = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    allocated_to = db.Column(db.DateTime, nullable=True)
    allocation_notes = db.Column(db.String(255), nullable=True)

    admission = db.relationship('Admission', back_populates='bed_allocations')
    bed = db.relationship('Bed', back_populates='allocations')

    def __repr__(self):
        return f'<BedAllocation Adm:{self.admission_id} Bed:{self.bed_id}>'


class Discharge(BaseModelMixin, db.Model):
    """46. discharges - Formal medical discharge process and summary"""
    __tablename__ = 'discharges'
    
    admission_id = db.Column(db.Integer, db.ForeignKey('admissions.id'), unique=True, nullable=False)
    discharge_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    discharge_type = db.Column(db.String(50), default='Normal', nullable=False) # 'Normal', 'Transfer', 'AMA', 'Deceased'
    discharge_summary = db.Column(db.Text, nullable=False)
    follow_up_instructions = db.Column(db.Text, nullable=True)
    follow_up_date = db.Column(db.Date, nullable=True)

    admission = db.relationship('Admission', back_populates='discharge')

    def __repr__(self):
        return f'<Discharge Adm:{self.admission_id} Date:{self.discharge_date}>'
