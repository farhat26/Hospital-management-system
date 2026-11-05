from datetime import datetime
from app.extensions import db
from app.models.base import BaseModelMixin

class Patient(BaseModelMixin, db.Model):
    """6. patients - Core patient demographic records"""
    __tablename__ = 'patients'
    
    patient_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(15), nullable=False) # 'Male', 'Female', 'Other'
    blood_group = db.Column(db.String(10), nullable=True) # 'A+', 'O+', etc.
    marital_status = db.Column(db.String(20), nullable=True) # 'Single', 'Married', etc.
    occupation = db.Column(db.String(100), nullable=True)
    
    # Relationships
    contacts = db.relationship('PatientContact', back_populates='patient', cascade='all, delete-orphan')
    addresses = db.relationship('PatientAddress', back_populates='patient', cascade='all, delete-orphan')
    emergency_contacts = db.relationship('EmergencyContact', back_populates='patient', cascade='all, delete-orphan')
    allergies = db.relationship('PatientAllergy', back_populates='patient', cascade='all, delete-orphan')
    medical_records = db.relationship('MedicalRecord', back_populates='patient', cascade='all, delete-orphan')
    appointments = db.relationship('Appointment', back_populates='patient', lazy='dynamic')
    visits = db.relationship('Visit', back_populates='patient', lazy='dynamic')
    prescriptions = db.relationship('Prescription', back_populates='patient', lazy='dynamic')
    lab_orders = db.relationship('LabOrder', back_populates='patient', lazy='dynamic')
    admissions = db.relationship('Admission', back_populates='patient', lazy='dynamic')
    invoices = db.relationship('Invoice', back_populates='patient', lazy='dynamic')
    insurances = db.relationship('PatientInsurance', back_populates='patient', lazy='dynamic')
    surgeries = db.relationship('SurgerySchedule', back_populates='patient', lazy='dynamic')
    feedback_records = db.relationship('Feedback', back_populates='patient', lazy='dynamic')

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def age(self):
        if not self.date_of_birth:
            return 0
        today = datetime.utcnow().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    def __repr__(self):
        return f'<Patient {self.patient_code} - {self.full_name}>'


class PatientContact(BaseModelMixin, db.Model):
    """7. patient_contacts - Contact channels for patients"""
    __tablename__ = 'patient_contacts'
    
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    phone_primary = db.Column(db.String(25), nullable=False)
    phone_secondary = db.Column(db.String(25), nullable=True)
    email = db.Column(db.String(120), nullable=True)

    patient = db.relationship('Patient', back_populates='contacts')

    def __repr__(self):
        return f'<PatientContact {self.phone_primary}>'


class PatientAddress(BaseModelMixin, db.Model):
    """8. patient_addresses - Physical and postal addresses"""
    __tablename__ = 'patient_addresses'
    
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    address_type = db.Column(db.String(30), default='Home', nullable=False) # 'Home', 'Work', 'Permanent'
    street_address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(100), default='Pakistan', nullable=False)

    patient = db.relationship('Patient', back_populates='addresses')

    def __repr__(self):
        return f'<PatientAddress {self.city}, {self.country}>'


class EmergencyContact(BaseModelMixin, db.Model):
    """9. emergency_contacts - Next of kin and emergency details"""
    __tablename__ = 'emergency_contacts'
    
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    contact_name = db.Column(db.String(100), nullable=False)
    relationship = db.Column(db.String(50), nullable=False) # 'Spouse', 'Parent', 'Sibling', etc.
    phone_number = db.Column(db.String(25), nullable=False)
    alternate_phone = db.Column(db.String(25), nullable=True)
    address = db.Column(db.String(255), nullable=True)

    patient = db.relationship('Patient', back_populates='emergency_contacts')

    def __repr__(self):
        return f'<EmergencyContact {self.contact_name} ({self.relationship})>'


class Allergy(BaseModelMixin, db.Model):
    """10. allergies - Master catalog of known allergens"""
    __tablename__ = 'allergies'
    
    allergen_name = db.Column(db.String(100), unique=True, nullable=False)
    allergy_type = db.Column(db.String(50), nullable=False) # 'Drug', 'Food', 'Environmental', 'Other'
    severity = db.Column(db.String(30), default='Moderate', nullable=False) # 'Mild', 'Moderate', 'Severe'
    common_symptoms = db.Column(db.String(255), nullable=True)

    patient_allergies = db.relationship('PatientAllergy', back_populates='allergy')

    def __repr__(self):
        return f'<Allergy {self.allergen_name}>'


class PatientAllergy(BaseModelMixin, db.Model):
    """11. patient_allergies - Junction table for patient-specific allergies"""
    __tablename__ = 'patient_allergies'
    
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    allergy_id = db.Column(db.Integer, db.ForeignKey('allergies.id'), nullable=False)
    diagnosed_date = db.Column(db.Date, nullable=True)
    reaction_description = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    patient = db.relationship('Patient', back_populates='allergies')
    allergy = db.relationship('Allergy', back_populates='patient_allergies')

    def __repr__(self):
        return f'<PatientAllergy Patient:{self.patient_id} Allergy:{self.allergy_id}>'


class MedicalRecord(BaseModelMixin, db.Model):
    """12. medical_records - Longitudinal clinical medical history"""
    __tablename__ = 'medical_records'
    
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    record_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    chief_complaint = db.Column(db.Text, nullable=False)
    history_of_present_illness = db.Column(db.Text, nullable=True)
    past_medical_history = db.Column(db.Text, nullable=True)
    family_history = db.Column(db.Text, nullable=True)
    social_history = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    patient = db.relationship('Patient', back_populates='medical_records')

    def __repr__(self):
        return f'<MedicalRecord Patient:{self.patient_id} Date:{self.record_date.date()}>'


class Diagnosis(BaseModelMixin, db.Model):
    """13. diagnoses - Master ICD / Clinical diagnosis list"""
    __tablename__ = 'diagnoses'
    
    icd_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    diagnosis_name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    is_chronic = db.Column(db.Boolean, default=False, nullable=False)

    visit_diagnoses = db.relationship('VisitDiagnosis', back_populates='diagnosis')

    def __repr__(self):
        return f'<Diagnosis {self.icd_code} - {self.diagnosis_name}>'


class VisitDiagnosis(BaseModelMixin, db.Model):
    """14. visit_diagnoses - Specific diagnoses assigned during a clinical visit"""
    __tablename__ = 'visit_diagnoses'
    
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id'), nullable=False)
    diagnosis_id = db.Column(db.Integer, db.ForeignKey('diagnoses.id'), nullable=False)
    diagnosis_type = db.Column(db.String(30), default='Primary', nullable=False) # 'Primary', 'Secondary', 'Differential'
    notes = db.Column(db.Text, nullable=True)

    visit = db.relationship('Visit', back_populates='visit_diagnoses')
    diagnosis = db.relationship('Diagnosis', back_populates='visit_diagnoses')

    def __repr__(self):
        return f'<VisitDiagnosis Visit:{self.visit_id} Diagnosis:{self.diagnosis_id}>'
