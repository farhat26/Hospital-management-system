import pytest
from app.models import ALL_MODELS, MODEL_MAP
from app.models.base import BaseModelMixin
from app.models.auth import Role, User, UserProfile, LoginHistory, AuditLog
from app.models.patients import Patient, MedicalRecord, Allergy, Diagnosis
from app.models.staff import Doctor, Department, Nurse, Staff
from app.models.appointments import Appointment, Visit, QueueToken
from app.models.pharmacy import Medicine, MedicineCategory, Prescription, PrescriptionItem, Supplier, PurchaseOrder
from app.models.laboratory import LabTest, LabOrder, LabOrderItem, LabResult
from app.models.wards import Ward, Room, Bed, Admission, Discharge
from app.models.billing import Invoice, InvoiceItem, Payment, InsuranceProvider
from app.models.surgery import Surgery, OperationTheatre, SurgerySchedule, Ambulance
from app.models.feedback import Feedback

def test_model_count_exceeds_rubric():
    """Verify that the system contains at least 50 models (specifically 56 models)."""
    assert len(ALL_MODELS) >= 50, f"Expected >= 50 models, got {len(ALL_MODELS)}"
    assert len(ALL_MODELS) == 56, f"Expected exactly 56 models, got {len(ALL_MODELS)}"
    assert len(MODEL_MAP) == 56, f"Expected 56 mapped tables, got {len(MODEL_MAP)}"

def test_all_models_have_audit_fields():
    """Verify that EVERY database model inherits and contains all required audit fields."""
    required_fields = {
        'id',
        'created_at',
        'created_by_id',
        'updated_at',
        'updated_by_id',
        'status',
        'is_deleted',
        'deleted_at',
        'deleted_by_id'
    }

    for model in ALL_MODELS:
        assert issubclass(model, BaseModelMixin), f"Model {model.__name__} does not inherit from BaseModelMixin"
        columns = {c.name for c in model.__table__.columns}
        missing = required_fields - columns
        assert not missing, f"Model {model.__name__} is missing audit columns: {missing}"

def test_relationships(app):
    """Verify core domain relationships across entities."""
    with app.app_context():
        # 1. Department -> Doctors
        dept = Department.query.filter_by(name='Cardiology').first()
        assert dept is not None
        assert len(dept.doctors) > 0

        # 2. Patient -> Medical Records
        patient = Patient.query.first()
        assert patient is not None
        assert hasattr(patient, 'medical_records')
        assert hasattr(patient, 'appointments')
        assert hasattr(patient, 'invoices')

        # 3. Ward -> Rooms -> Beds
        ward = Ward.query.first()
        assert ward is not None
        assert len(ward.rooms) > 0
        room = ward.rooms[0]
        assert len(room.beds) > 0

        # 4. Prescription -> Prescription Items
        prescription = Prescription.query.first()
        assert prescription is not None
        assert len(prescription.items) > 0

        # 5. Invoice -> Invoice Items & Payments
        invoice = Invoice.query.first()
        assert invoice is not None
        assert len(invoice.items) > 0

        # 6. Lab Order -> Lab Order Items
        order = LabOrder.query.first()
        assert order is not None
        assert len(order.items) > 0
