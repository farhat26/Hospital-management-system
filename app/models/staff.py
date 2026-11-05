from datetime import datetime
from app.extensions import db
from app.models.base import BaseModelMixin

class Department(BaseModelMixin, db.Model):
    """15. departments - Hospital medical and administrative departments"""
    __tablename__ = 'departments'
    
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    floor_location = db.Column(db.String(50), nullable=True)

    # Relationships
    doctor_associations = db.relationship('DoctorDepartment', back_populates='department', cascade='all, delete-orphan')
    nurses = db.relationship('Nurse', back_populates='department', lazy='dynamic')
    general_staff = db.relationship('Staff', back_populates='department', lazy='dynamic')
    surgeries = db.relationship('Surgery', back_populates='department', lazy='dynamic')

    @property
    def doctors(self):
        return [da.doctor for da in self.doctor_associations if da.doctor]

    def __repr__(self):
        return f'<Department {self.name} ({self.code})>'


class Doctor(BaseModelMixin, db.Model):
    """16. doctors - Practicing medical physicians"""
    __tablename__ = 'doctors'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=True)
    doctor_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    qualification = db.Column(db.String(100), nullable=False) # MBBS, MD, FCPS, etc.
    experience_years = db.Column(db.Integer, default=0, nullable=False)
    consultation_fee = db.Column(db.Float, default=1000.0, nullable=False)
    phone = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(120), nullable=True)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])
    specializations = db.relationship('DoctorSpecialization', back_populates='doctor', cascade='all, delete-orphan')
    department_associations = db.relationship('DoctorDepartment', back_populates='doctor', cascade='all, delete-orphan')
    appointments = db.relationship('Appointment', back_populates='doctor', lazy='dynamic')
    visits = db.relationship('Visit', back_populates='doctor', lazy='dynamic')
    prescriptions = db.relationship('Prescription', back_populates='doctor', lazy='dynamic')
    lab_orders = db.relationship('LabOrder', back_populates='doctor', lazy='dynamic')
    admissions = db.relationship('Admission', back_populates='doctor', lazy='dynamic')
    surgery_schedules = db.relationship('SurgerySchedule', back_populates='lead_surgeon', lazy='dynamic')
    attendances = db.relationship('StaffAttendance', back_populates='doctor', lazy='dynamic')

    @property
    def full_name(self):
        return f'Dr. {self.first_name} {self.last_name}'

    def __repr__(self):
        return f'<Doctor {self.doctor_code} - {self.full_name}>'


class DoctorSpecialization(BaseModelMixin, db.Model):
    """17. doctor_specializations - Clinical specializations of doctors"""
    __tablename__ = 'doctor_specializations'
    
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    specialization_name = db.Column(db.String(100), nullable=False) # 'Cardiology', 'Pediatrics', etc.
    certification_board = db.Column(db.String(100), nullable=True)
    year_obtained = db.Column(db.Integer, nullable=True)

    doctor = db.relationship('Doctor', back_populates='specializations')

    def __repr__(self):
        return f'<DoctorSpecialization {self.specialization_name} for Doctor:{self.doctor_id}>'


class DoctorDepartment(BaseModelMixin, db.Model):
    """18. doctor_departments - Many-to-many junction between doctors and departments"""
    __tablename__ = 'doctor_departments'
    
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    is_primary_dept = db.Column(db.Boolean, default=True, nullable=False)

    doctor = db.relationship('Doctor', back_populates='department_associations')
    department = db.relationship('Department', back_populates='doctor_associations')

    def __repr__(self):
        return f'<DoctorDepartment Doctor:{self.doctor_id} Dept:{self.department_id}>'


class Nurse(BaseModelMixin, db.Model):
    """19. nurses - Nursing staff"""
    __tablename__ = 'nurses'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=True)
    nurse_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    qualification = db.Column(db.String(100), nullable=False) # BSN, RN, etc.
    phone = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(120), nullable=True)

    user = db.relationship('User', foreign_keys=[user_id])
    department = db.relationship('Department', back_populates='nurses')
    attendances = db.relationship('StaffAttendance', back_populates='nurse', lazy='dynamic')

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __repr__(self):
        return f'<Nurse {self.nurse_code} - {self.full_name}>'


class Staff(BaseModelMixin, db.Model):
    """20. staff - General and administrative hospital personnel"""
    __tablename__ = 'staff'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=True)
    staff_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role_title = db.Column(db.String(100), nullable=False) # 'Receptionist', 'Accountant', 'Lab Tech', etc.
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    phone = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    hire_date = db.Column(db.Date, nullable=False)

    user = db.relationship('User', foreign_keys=[user_id])
    department = db.relationship('Department', back_populates='general_staff')
    attendances = db.relationship('StaffAttendance', back_populates='staff', lazy='dynamic')

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __repr__(self):
        return f'<Staff {self.staff_code} - {self.full_name}>'


class Shift(BaseModelMixin, db.Model):
    """21. shifts - Working shift schedules"""
    __tablename__ = 'shifts'
    
    name = db.Column(db.String(50), unique=True, nullable=False) # 'Morning', 'Evening', 'Night'
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    attendances = db.relationship('StaffAttendance', back_populates='shift', lazy='dynamic')

    def __repr__(self):
        return f'<Shift {self.name} ({self.start_time}-{self.end_time})>'


class StaffAttendance(BaseModelMixin, db.Model):
    """22. staff_attendance - Daily attendance tracking for hospital personnel"""
    __tablename__ = 'staff_attendance'
    
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=True)
    nurse_id = db.Column(db.Integer, db.ForeignKey('nurses.id'), nullable=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=True)
    shift_id = db.Column(db.Integer, db.ForeignKey('shifts.id'), nullable=False)
    attendance_date = db.Column(db.Date, nullable=False)
    check_in_time = db.Column(db.Time, nullable=True)
    check_out_time = db.Column(db.Time, nullable=True)
    attendance_status = db.Column(db.String(20), default='Present', nullable=False) # 'Present', 'Absent', 'Late', 'On Leave'

    staff = db.relationship('Staff', back_populates='attendances')
    nurse = db.relationship('Nurse', back_populates='attendances')
    doctor = db.relationship('Doctor', back_populates='attendances')
    shift = db.relationship('Shift', back_populates='attendances')

    def __repr__(self):
        return f'<StaffAttendance Date:{self.attendance_date} Status:{self.attendance_status}>'
