import pytest
from datetime import datetime, date
from app.extensions import db
from app.models.patients import Patient, PatientContact, PatientAddress
from app.models.staff import Department
from app.models.pharmacy import Medicine, MedicineCategory
from app.models.feedback import Feedback

def test_soft_delete_and_restore(app):
    """Test standard soft delete lifecycle: delete, hide, restore, and status toggle."""
    with app.app_context():
        # Create a test department
        dept = Department(
            name='Temporary Pediatrics Wing',
            code='TPW-01',
            description='Temporary department for testing soft delete',
            status='Active',
            created_by_id=1
        )
        db.session.add(dept)
        db.session.commit()
        dept_id = dept.id

        # Verify active record exists
        found = Department.query.filter_by(id=dept_id, is_deleted=False).first()
        assert found is not None
        assert found.is_deleted is False
        assert found.deleted_at is None
        assert found.deleted_by_id is None

        # Perform soft delete
        dept.soft_delete(user_id=1)
        assert dept.is_deleted is True
        assert dept.deleted_at is not None
        assert dept.deleted_by_id == 1

        # Check normal query hides it
        active_query = Department.query.filter_by(id=dept_id, is_deleted=False).first()
        assert active_query is None

        # Check soft delete query finds it
        deleted_query = Department.query.filter_by(id=dept_id, is_deleted=True).first()
        assert deleted_query is not None
        assert deleted_query.name == 'Temporary Pediatrics Wing'

        # Test Restore
        dept.restore()
        assert dept.is_deleted is False
        assert dept.deleted_at is None
        assert dept.deleted_by_id is None

        # Check normal query sees it again
        restored = Department.query.filter_by(id=dept_id, is_deleted=False).first()
        assert restored is not None

        # Test Status Toggle
        assert dept.status == 'Active'
        dept.toggle_status(user_id=1)
        assert dept.status == 'Deactive'
        dept.toggle_status(user_id=1)
        assert dept.status == 'Active'

def test_patient_crud_route(admin_client, app):
    """Test full CRUD operations on Patient through application routes."""
    # 1. CREATE patient
    post_data = {
        'patient_code': 'PAT-TEST-999',
        'first_name': 'Alexander',
        'last_name': 'Hamilton',
        'date_of_birth': '1990-05-15',
        'gender': 'Male',
        'blood_group': 'O+',
        'marital_status': 'Married',
        'phone': '555-123-9999',
        'email': 'alex.hamilton@example.com',
        'address_line1': '10 Wall Street',
        'city': 'New York',
        'state': 'NY',
        'postal_code': '10005',
        'emergency_contact_name': 'Elizabeth Schuyler',
        'emergency_contact_relation': 'Spouse',
        'emergency_contact_phone': '555-123-8888',
        'status': 'Active'
    }

    create_resp = admin_client.post('/patients/create', data=post_data, follow_redirects=True)
    assert create_resp.status_code == 200
    assert b'Alexander' in create_resp.data

    with app.app_context():
        p = Patient.query.filter_by(patient_code='PAT-TEST-999').first()
        assert p is not None
        assert p.first_name == 'Alexander'
        p_id = p.id

    # 2. READ / VIEW patient
    view_resp = admin_client.get(f'/patients/{p_id}')
    assert view_resp.status_code == 200
    assert b'Alexander Hamilton' in view_resp.data

    # 3. UPDATE patient
    edit_data = post_data.copy()
    edit_data['first_name'] = 'Alexander-Updated'
    edit_resp = admin_client.post(f'/patients/{p_id}/edit', data=edit_data, follow_redirects=True)
    assert edit_resp.status_code == 200
    assert b'Alexander-Updated' in edit_resp.data

    # 4. SOFT DELETE patient
    del_resp = admin_client.post(f'/patients/{p_id}/delete', follow_redirects=True)
    assert del_resp.status_code == 200

    with app.app_context():
        # Should be soft-deleted
        deleted_p = Patient.query.get(p_id)
        assert deleted_p.is_deleted is True
        assert deleted_p.deleted_at is not None

    # 5. RESTORE via Admin Recycle Bin route
    restore_resp = admin_client.post(f'/admin/recycle-bin/restore/patients/{p_id}', follow_redirects=True)
    assert restore_resp.status_code == 200

    with app.app_context():
        restored_p = Patient.query.get(p_id)
        assert restored_p.is_deleted is False
        assert restored_p.deleted_at is None
