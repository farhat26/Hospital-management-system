from datetime import datetime, date, time
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.patients import Patient
from app.models.staff import Doctor, Staff, Nurse, Department
from app.models.appointments import Appointment, QueueToken, Visit
from app.models.wards import Ward, Room, Bed, Admission, BedAllocation
from app.models.pharmacy import (
    Medicine, MedicineCategory, Prescription, PharmacySale,
    PurchaseOrder, MedicineBatch
)
from app.models.laboratory import LabTest, LabOrder, LabOrderItem, LabResult
from app.models.billing import Invoice
from app.models.auth import AuditLog
from sqlalchemy import func

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@dashboard_bp.route('/dashboard/')
@login_required
def index():
    """Dispatch to role-specific dashboard based on current_user.role.name."""
    role_name = current_user.role.name if (current_user.role and current_user.role.name) else 'Admin'

    if role_name == 'Doctor':
        return doctor_dashboard()
    elif role_name == 'Receptionist':
        return receptionist_dashboard()
    elif role_name == 'Nurse':
        return nurse_dashboard()
    elif role_name == 'Pharmacist':
        return pharmacist_dashboard()
    elif role_name == 'Laboratory Technician':
        return labtech_dashboard()
    else:
        return admin_dashboard()

# -------------------------------------------------------------------------
# 1. Admin Dashboard (Complete Hospital Executive Overview)
# -------------------------------------------------------------------------
def admin_dashboard():
    total_patients = Patient.query.filter_by(is_deleted=False).count()
    total_doctors = Doctor.query.filter_by(is_deleted=False).count()
    total_staff = Staff.query.filter_by(is_deleted=False).count() + Nurse.query.filter_by(is_deleted=False).count()
    total_appointments = Appointment.query.filter_by(is_deleted=False).count()
    total_admissions = Admission.query.filter_by(is_deleted=False, admission_status='Admitted').count()
    available_beds = Bed.query.filter_by(is_deleted=False, status='Active', bed_status='Available').count()
    pending_lab_orders = LabOrder.query.filter(LabOrder.is_deleted == False, LabOrder.order_status.in_(['Pending', 'In Process', 'Sample Collected'])).count()
    revenue_total = db.session.query(func.coalesce(func.sum(Invoice.paid_amount), 0.0)).filter(Invoice.is_deleted == False).scalar() or 0.0

    appt_status_counts = db.session.query(Appointment.current_status, func.count(Appointment.id)).filter(Appointment.is_deleted == False).group_by(Appointment.current_status).all()
    appt_status_dict = {status: count for status, count in appt_status_counts}

    dept_rows = db.session.query(Department.name, func.count(Doctor.id)).join(Doctor.department_associations).join(Department).filter(Doctor.is_deleted == False, Department.is_deleted == False).group_by(Department.name).all()
    dept_distribution = [[row[0], int(row[1])] for row in dept_rows]

    blood_rows = db.session.query(Patient.blood_group, func.count(Patient.id)).filter(Patient.is_deleted == False, Patient.blood_group != None).group_by(Patient.blood_group).all()
    blood_group_counts = [[row[0], int(row[1])] for row in blood_rows]

    recent_audits = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(8).all()
    recent_appointments = Appointment.query.filter_by(is_deleted=False).order_by(Appointment.created_at.desc()).limit(5).all()
    recent_admissions = Admission.query.filter_by(is_deleted=False).order_by(Admission.created_at.desc()).limit(5).all()

    return render_template(
        'dashboard/index.html',
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_staff=total_staff,
        total_appointments=total_appointments,
        total_admissions=total_admissions,
        available_beds=available_beds,
        pending_lab_orders=pending_lab_orders,
        revenue_total=revenue_total,
        appt_status_dict=appt_status_dict,
        dept_distribution=dept_distribution,
        blood_group_counts=blood_group_counts,
        recent_audits=recent_audits,
        recent_appointments=recent_appointments,
        recent_admissions=recent_admissions
    )

# -------------------------------------------------------------------------
# 2. Doctor Dashboard (Clinical Appointments, Encounters, Rx, Diagnoses)
# -------------------------------------------------------------------------
def doctor_dashboard():
    # Identify doctor profile for current user
    doctor = Doctor.query.filter_by(user_id=current_user.id, is_deleted=False).first()
    if not doctor:
        doctor = Doctor.query.filter_by(is_deleted=False).first()

    doctor_id = doctor.id if doctor else None

    # Doctor specific consultations
    today_consultations = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.is_deleted == False
    ).order_by(Appointment.appointment_time).all() if doctor_id else []

    pending_today_count = sum(1 for a in today_consultations if a.current_status in ['Scheduled', 'Confirmed'])
    completed_today_count = sum(1 for a in today_consultations if a.current_status == 'Completed')

    # Total distinct assigned patients
    assigned_patients_count = db.session.query(func.count(func.distinct(Appointment.patient_id))).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.is_deleted == False
    ).scalar() or 0 if doctor_id else 0

    # Clinical Encounters & Prescriptions
    total_encounters_count = Visit.query.filter_by(doctor_id=doctor_id, is_deleted=False).count() if doctor_id else 0
    active_prescriptions_count = Prescription.query.filter_by(doctor_id=doctor_id, is_deleted=False).count() if doctor_id else 0
    pending_labs_count = LabOrder.query.filter(
        LabOrder.doctor_id == doctor_id,
        LabOrder.is_deleted == False,
        LabOrder.order_status.in_(['Pending', 'Sample Collected', 'In Process'])
    ).count() if doctor_id else 0

    recent_encounters = Visit.query.filter_by(
        doctor_id=doctor_id,
        is_deleted=False
    ).order_by(Visit.visit_date.desc()).limit(6).all() if doctor_id else []

    recent_prescriptions = Prescription.query.filter_by(
        doctor_id=doctor_id,
        is_deleted=False
    ).order_by(Prescription.prescription_date.desc()).limit(5).all() if doctor_id else []

    # Chart: Doctor appointments by status
    status_rows = db.session.query(Appointment.current_status, func.count(Appointment.id)).filter(
        Appointment.doctor_id == doctor_id,
        Appointment.is_deleted == False
    ).group_by(Appointment.current_status).all() if doctor_id else []
    doctor_status_dict = {s: int(c) for s, c in status_rows}

    return render_template(
        'dashboard/doctor_dashboard.html',
        doctor=doctor,
        today_consultations=today_consultations,
        pending_today_count=pending_today_count,
        completed_today_count=completed_today_count,
        assigned_patients_count=assigned_patients_count,
        total_encounters_count=total_encounters_count,
        active_prescriptions_count=active_prescriptions_count,
        pending_labs_count=pending_labs_count,
        recent_encounters=recent_encounters,
        recent_prescriptions=recent_prescriptions,
        doctor_status_dict=doctor_status_dict
    )

# -------------------------------------------------------------------------
# 3. Receptionist Dashboard (Registration, Appointments & Live OPD Queue)
# -------------------------------------------------------------------------
def receptionist_dashboard():
    today_start = datetime.combine(date.today(), time.min)

    # Patients registered today
    registered_today = Patient.query.filter(Patient.is_deleted == False, Patient.created_at >= today_start).count()
    total_patients = Patient.query.filter_by(is_deleted=False).count()

    # Today's appointments
    today_appointments = Appointment.query.filter_by(is_deleted=False).order_by(Appointment.appointment_time).all()
    today_appts_count = len(today_appointments)

    # Live Queue Tokens
    live_queue_tokens = QueueToken.query.filter(
        QueueToken.is_deleted == False,
        QueueToken.token_status.in_(['Waiting', 'In-Consultation'])
    ).order_by(QueueToken.created_at).all()
    active_tokens_count = len(live_queue_tokens)

    # Available Inpatient Beds
    available_beds = Bed.query.filter_by(is_deleted=False, status='Active', bed_status='Available').count()
    total_beds = Bed.query.filter_by(is_deleted=False, status='Active').count()

    # Recent Registrations
    recent_patients = Patient.query.filter_by(is_deleted=False).order_by(Patient.created_at.desc()).limit(6).all()

    # Chart: Tokens by status
    token_rows = db.session.query(QueueToken.token_status, func.count(QueueToken.id)).filter(QueueToken.is_deleted == False).group_by(QueueToken.token_status).all()
    queue_status_dict = {s: int(c) for s, c in token_rows}

    return render_template(
        'dashboard/receptionist_dashboard.html',
        registered_today=registered_today,
        total_patients=total_patients,
        today_appointments=today_appointments,
        today_appts_count=today_appts_count,
        live_queue_tokens=live_queue_tokens,
        active_tokens_count=active_tokens_count,
        available_beds=available_beds,
        total_beds=total_beds,
        recent_patients=recent_patients,
        queue_status_dict=queue_status_dict
    )

# -------------------------------------------------------------------------
# 4. Nurse Dashboard (Inpatient Wards, Bed Census & Vitals Recording)
# -------------------------------------------------------------------------
def nurse_dashboard():
    nurse = Nurse.query.filter_by(user_id=current_user.id, is_deleted=False).first()
    if not nurse:
        nurse = Nurse.query.filter_by(is_deleted=False).first()

    # Current Admitted Inpatients
    active_admissions = Admission.query.filter_by(
        is_deleted=False,
        admission_status='Admitted'
    ).order_by(Admission.admission_date.desc()).all()
    active_admissions_count = len(active_admissions)

    # Bed Census
    occupied_beds_count = Bed.query.filter_by(is_deleted=False, status='Active', bed_status='Occupied').count()
    available_beds_count = Bed.query.filter_by(is_deleted=False, status='Active', bed_status='Available').count()
    total_beds_count = Bed.query.filter_by(is_deleted=False, status='Active').count()

    # Wards list with capacity and beds
    wards_list = Ward.query.filter_by(is_deleted=False).all()

    # Recent clinical encounters with vitals
    recent_vitals_visits = Visit.query.filter(
        Visit.is_deleted == False,
        Visit.systolic_bp != None
    ).order_by(Visit.visit_date.desc()).limit(6).all()

    # Ward occupancy chart data: [[ward_name, occupied_count]]
    ward_occupancy_data = []
    for w in wards_list:
        occ = sum(1 for r in w.rooms for b in r.beds if b.bed_status == 'Occupied' and not b.is_deleted)
        ward_occupancy_data.append([w.ward_name, occ])

    return render_template(
        'dashboard/nurse_dashboard.html',
        nurse=nurse,
        active_admissions=active_admissions,
        active_admissions_count=active_admissions_count,
        occupied_beds_count=occupied_beds_count,
        available_beds_count=available_beds_count,
        total_beds_count=total_beds_count,
        wards_list=wards_list,
        recent_vitals_visits=recent_vitals_visits,
        ward_occupancy_data=ward_occupancy_data
    )

# -------------------------------------------------------------------------
# 5. Pharmacist Dashboard (Formulary, Stock Alerts, Prescriptions & POS)
# -------------------------------------------------------------------------
def pharmacist_dashboard():
    all_active_meds = Medicine.query.filter_by(is_deleted=False).all()
    total_medicines = len(all_active_meds)

    # Low Stock Alerts (at or below reorder level)
    low_stock_medicines = [m for m in all_active_meds if m.total_stock <= m.reorder_level]
    low_stock_count = len(low_stock_medicines)

    # Today's Sales
    today_start = datetime.combine(date.today(), time.min)
    today_sales = PharmacySale.query.filter(
        PharmacySale.is_deleted == False,
        PharmacySale.sale_date >= today_start
    ).all()
    today_sales_count = len(today_sales)
    today_revenue = sum(s.total_amount for s in today_sales)

    # Pending Prescriptions to dispense
    pending_prescriptions = Prescription.query.filter(
        Prescription.is_deleted == False,
        Prescription.status == 'Active'
    ).order_by(Prescription.prescription_date.desc()).all()
    pending_rx_count = len(pending_prescriptions)

    # Recent POS Counter Sales
    recent_sales = PharmacySale.query.filter_by(
        is_deleted=False
    ).order_by(PharmacySale.sale_date.desc()).limit(6).all()

    # Top categories stock chart
    cat_counts = db.session.query(MedicineCategory.name, func.count(Medicine.id)).join(Medicine).filter(
        Medicine.is_deleted == False,
        MedicineCategory.is_deleted == False
    ).group_by(MedicineCategory.name).all()
    category_stock_data = [[c[0], int(c[1])] for c in cat_counts]

    return render_template(
        'dashboard/pharmacist_dashboard.html',
        total_medicines=total_medicines,
        low_stock_medicines=low_stock_medicines,
        low_stock_count=low_stock_count,
        today_sales_count=today_sales_count,
        today_revenue=today_revenue,
        pending_prescriptions=pending_prescriptions,
        pending_rx_count=pending_rx_count,
        recent_sales=recent_sales,
        category_stock_data=category_stock_data
    )

# -------------------------------------------------------------------------
# 6. Laboratory Technician Dashboard (Diagnostic Orders, Specimen, Results)
# -------------------------------------------------------------------------
def labtech_dashboard():
    # Diagnostic Requisitions
    pending_orders = LabOrder.query.filter(
        LabOrder.is_deleted == False,
        LabOrder.order_status.in_(['Pending', 'Sample Collected'])
    ).order_by(LabOrder.order_date.desc()).all()
    pending_orders_count = len(pending_orders)

    in_process_orders = LabOrder.query.filter(
        LabOrder.is_deleted == False,
        LabOrder.order_status == 'In Process'
    ).order_by(LabOrder.order_date.desc()).all()
    in_process_count = len(in_process_orders)

    completed_orders_count = LabOrder.query.filter(
        LabOrder.is_deleted == False,
        LabOrder.order_status == 'Completed'
    ).count()

    total_tests_catalog = LabTest.query.filter_by(is_deleted=False).count()

    # Abnormal / Critical Flagged Test Results
    abnormal_results = LabResult.query.filter(
        LabResult.is_deleted == False,
        LabResult.is_abnormal == True
    ).order_by(LabResult.verified_at.desc()).limit(6).all()
    abnormal_count = LabResult.query.filter(
        LabResult.is_deleted == False,
        LabResult.is_abnormal == True
    ).count()

    # Active Lab Orders Worklist (all pending and in process)
    worklist_orders = LabOrder.query.filter(
        LabOrder.is_deleted == False,
        LabOrder.order_status != 'Completed'
    ).order_by(LabOrder.order_date.desc()).limit(8).all()

    # Chart: Tests by Department / Category
    test_cat_rows = db.session.query(LabTest.category, func.count(LabTest.id)).filter(
        LabTest.is_deleted == False
    ).group_by(LabTest.category).all()
    test_category_data = [[t[0], int(t[1])] for t in test_cat_rows]

    return render_template(
        'dashboard/labtech_dashboard.html',
        pending_orders_count=pending_orders_count,
        in_process_count=in_process_count,
        completed_orders_count=completed_orders_count,
        total_tests_catalog=total_tests_catalog,
        abnormal_results=abnormal_results,
        abnormal_count=abnormal_count,
        worklist_orders=worklist_orders,
        test_category_data=test_category_data
    )

@dashboard_bp.route('/api/dashboard/stats')
@login_required
def api_stats():
    """Return JSON statistics for dynamic charts."""
    status_data = db.session.query(Appointment.current_status, func.count(Appointment.id)).filter(Appointment.is_deleted == False).group_by(Appointment.current_status).all()
    return jsonify({
        'appointments_by_status': dict(status_data),
        'total_revenue': float(db.session.query(func.coalesce(func.sum(Invoice.paid_amount), 0.0)).filter(Invoice.is_deleted == False).scalar() or 0.0)
    })
