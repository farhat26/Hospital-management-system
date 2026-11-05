import pytest

def test_dashboard_renders(admin_client):
    """Test dashboard index loads with all KPI metrics and charts."""
    response = admin_client.get('/dashboard/')
    assert response.status_code == 200
    assert b'Executive Hospital Dashboard' in response.data
    assert b'Total Patients' in response.data
    assert b'Total Doctors' in response.data
    assert b'Total Admissions' in response.data
    assert b'Available Beds' in response.data
    assert b'Total Revenue' in response.data
    # Check Chart.js canvas elements
    assert b'appointmentStatusChart' in response.data
    assert b'deptDistributionChart' in response.data
    assert b'bloodGroupChart' in response.data

@pytest.mark.parametrize('url,expected_heading', [
    ('/patients/', b'Patient Management'),
    ('/doctors/', b'Doctors & Medical Consultants'),
    ('/doctors/departments', b'Hospital Departments'),
    ('/staff/', b'Hospital Staff & Personnel'),
    ('/staff/shifts', b'Duty Shift Schedules'),
    ('/appointments/', b'Appointment Management'),
    ('/appointments/queue', b'Queue Tokens'),
    ('/appointments/visits', b'Clinical Encounters & Consultations'),
    ('/pharmacy/', b'Pharmacy & Medicine Formulary'),
    ('/pharmacy/categories', b'Therapeutic Drug Categories'),
    ('/pharmacy/suppliers', b'Pharmaceutical Suppliers'),
    ('/pharmacy/prescriptions', b'Prescriptions'),
    ('/pharmacy/sales', b'Pharmacy Point of Sale (POS)'),
    ('/laboratory/', b'Pathology & Clinical Laboratory'),
    ('/laboratory/tests', b'Diagnostic Investigations Catalog'),
    ('/wards/', b'Inpatient Wards'),
    ('/wards/admissions', b'Admissions'),
    ('/billing/', b'Hospital Billing'),
    ('/billing/insurance', b'Insurance Providers'),
    ('/surgery/', b'Surgery Suites & Emergency Transport'),
    ('/feedback/', b'Patient Feedback'),
    ('/admin/', b'System Administration'),
    ('/admin/users', b'User Accounts'),
    ('/admin/audit-logs', b'System Audit Trail'),
    ('/admin/login-history', b'Authentication History'),
    ('/admin/recycle-bin', b'Recycle Bin'),
])
def test_all_modules_load_200(admin_client, url, expected_heading):
    """Verify that all hospital management system modules load successfully with status 200."""
    response = admin_client.get(url)
    assert response.status_code == 200
    assert expected_heading in response.data

def test_404_page(admin_client):
    """Test custom 404 page for missing endpoints."""
    response = admin_client.get('/nonexistent-path-abc-123')
    assert response.status_code == 404
    assert b'Resource or Page Not Found' in response.data
