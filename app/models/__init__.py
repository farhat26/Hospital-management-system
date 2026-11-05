from app.models.base import BaseModelMixin
from app.models.auth import Role, User, UserProfile, LoginHistory, AuditLog
from app.models.patients import (
    Patient, PatientContact, PatientAddress, EmergencyContact,
    Allergy, PatientAllergy, MedicalRecord, Diagnosis, VisitDiagnosis
)
from app.models.staff import (
    Department, Doctor, DoctorSpecialization, DoctorDepartment,
    Nurse, Staff, Shift, StaffAttendance
)
from app.models.appointments import (
    Appointment, AppointmentStatusHistory, QueueToken, Visit
)
from app.models.pharmacy import (
    MedicineCategory, Medicine, Prescription, PrescriptionItem,
    Supplier, PurchaseOrder, PurchaseOrderItem, MedicineBatch,
    PharmacySale, PharmacySaleItem
)
from app.models.laboratory import (
    LabTest, LabOrder, LabOrderItem, LabResult
)
from app.models.wards import (
    Ward, Room, Bed, Admission, BedAllocation, Discharge
)
from app.models.billing import (
    InsuranceProvider, PatientInsurance, Invoice, InvoiceItem, Payment
)
from app.models.surgery import (
    OperationTheatre, Surgery, SurgerySchedule, Ambulance
)
from app.models.feedback import (
    Feedback
)

# Registry of all 56 Models for introspection, soft delete management, and audit tracking
ALL_MODELS = [
    Role, User, UserProfile, LoginHistory, AuditLog,
    Patient, PatientContact, PatientAddress, EmergencyContact,
    Allergy, PatientAllergy, MedicalRecord, Diagnosis, VisitDiagnosis,
    Department, Doctor, DoctorSpecialization, DoctorDepartment,
    Nurse, Staff, Shift, StaffAttendance,
    Appointment, AppointmentStatusHistory, QueueToken, Visit,
    MedicineCategory, Medicine, Prescription, PrescriptionItem,
    Supplier, PurchaseOrder, PurchaseOrderItem, MedicineBatch,
    PharmacySale, PharmacySaleItem,
    LabTest, LabOrder, LabOrderItem, LabResult,
    Ward, Room, Bed, Admission, BedAllocation, Discharge,
    InsuranceProvider, PatientInsurance, Invoice, InvoiceItem, Payment,
    OperationTheatre, Surgery, SurgerySchedule, Ambulance,
    Feedback
]

MODEL_MAP = {model.__tablename__: model for model in ALL_MODELS}

__all__ = [
    'BaseModelMixin',
    # Auth & Admin (1-5)
    'Role', 'User', 'UserProfile', 'LoginHistory', 'AuditLog',
    # Patients (6-14)
    'Patient', 'PatientContact', 'PatientAddress', 'EmergencyContact',
    'Allergy', 'PatientAllergy', 'MedicalRecord', 'Diagnosis', 'VisitDiagnosis',
    # Staff (15-22)
    'Department', 'Doctor', 'DoctorSpecialization', 'DoctorDepartment',
    'Nurse', 'Staff', 'Shift', 'StaffAttendance',
    # Appointments (23-26)
    'Appointment', 'AppointmentStatusHistory', 'QueueToken', 'Visit',
    # Pharmacy (27-36)
    'MedicineCategory', 'Medicine', 'Prescription', 'PrescriptionItem',
    'Supplier', 'PurchaseOrder', 'PurchaseOrderItem', 'MedicineBatch',
    'PharmacySale', 'PharmacySaleItem',
    # Laboratory (37-40)
    'LabTest', 'LabOrder', 'LabOrderItem', 'LabResult',
    # Wards & Inpatient (41-46)
    'Ward', 'Room', 'Bed', 'Admission', 'BedAllocation', 'Discharge',
    # Billing & Insurance (47-51)
    'InsuranceProvider', 'PatientInsurance', 'Invoice', 'InvoiceItem', 'Payment',
    # Surgery & Emergency (52-55)
    'OperationTheatre', 'Surgery', 'SurgerySchedule', 'Ambulance',
    # Feedback (56)
    'Feedback',
    'ALL_MODELS',
    'MODEL_MAP'
]
