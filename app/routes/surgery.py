from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.surgery import OperationTheatre, Surgery, SurgerySchedule, Ambulance
from app.models.patients import Patient
from app.models.staff import Doctor, Department
from app.forms.surgery_forms import OperationTheatreForm, SurgeryForm, SurgeryScheduleForm, AmbulanceForm
from app.services.audit_service import log_audit
from datetime import datetime
from app.utils.decorators import role_required

surgery_bp = Blueprint('surgery', __name__, url_prefix='/surgery')

@surgery_bp.route('/')
@login_required
@role_required('Admin', 'Doctor', 'Nurse')
def index():
    theatres = OperationTheatre.query.filter_by(is_deleted=False).all()
    schedules = SurgerySchedule.query.filter_by(is_deleted=False).order_by(SurgerySchedule.scheduled_start_time.desc()).all()
    ambulances = Ambulance.query.filter_by(is_deleted=False).all()
    surgeries_list = Surgery.query.filter_by(is_deleted=False).all()

    return render_template('surgery/index.html', theatres=theatres, schedules=schedules, ambulances=ambulances, surgeries=surgeries_list)

# ----------------- Theatres & Surgeries Catalog -----------------
@surgery_bp.route('/theatres/create', methods=['GET', 'POST'])
@login_required
def create_theatre():
    form = OperationTheatreForm()
    if form.validate_on_submit():
        ot = OperationTheatre(
            ot_number=form.ot_number.data.strip(),
            name=form.name.data.strip(),
            floor=form.floor.data,
            theatre_type=form.theatre_type.data,
            is_equipped=form.is_equipped.data,
            maintenance_status=form.maintenance_status.data,
            created_by_id=current_user.id
        )
        db.session.add(ot)
        db.session.commit()
        log_audit('CREATE', 'operation_theatres', ot.id, f'Created operation theatre {ot.ot_number}')
        flash(f'Operation Theatre {ot.ot_number} registered.', 'success')
        return redirect(url_for('surgery.index'))
    return render_template('surgery/theatre_form.html', form=form, title='Add Operation Theatre')

@surgery_bp.route('/catalog/create', methods=['GET', 'POST'])
@login_required
def create_procedure():
    form = SurgeryForm()
    depts = Department.query.filter_by(is_deleted=False, status='Active').all()
    form.department_id.choices = [(d.id, d.name) for d in depts]

    if form.validate_on_submit():
        surg = Surgery(
            surgery_code=form.surgery_code.data.strip().upper(),
            surgery_name=form.surgery_name.data.strip(),
            department_id=form.department_id.data,
            estimated_duration_minutes=form.estimated_duration_minutes.data,
            standard_cost=form.standard_cost.data,
            description=form.description.data.strip() if form.description.data else None,
            created_by_id=current_user.id
        )
        db.session.add(surg)
        db.session.commit()
        log_audit('CREATE', 'surgeries', surg.id, f'Created surgery catalog procedure {surg.surgery_name}')
        flash(f'Procedure {surg.surgery_name} added to catalog.', 'success')
        return redirect(url_for('surgery.index'))
    return render_template('surgery/procedure_form.html', form=form, title='Add Surgical Procedure')

# ----------------- Schedules -----------------
@surgery_bp.route('/schedules/create', methods=['GET', 'POST'])
@login_required
def create_schedule():
    form = SurgeryScheduleForm()
    surgeries = Surgery.query.filter_by(is_deleted=False).all()
    patients = Patient.query.filter_by(is_deleted=False, status='Active').all()
    doctors = Doctor.query.filter_by(is_deleted=False, status='Active').all()
    theatres = OperationTheatre.query.filter_by(is_deleted=False, maintenance_status='Operational').all()

    form.surgery_id.choices = [(s.id, f"{s.surgery_name} ({s.surgery_code})") for s in surgeries]
    form.patient_id.choices = [(p.id, f"{p.patient_code} - {p.full_name}") for p in patients]
    form.lead_surgeon_id.choices = [(d.id, d.full_name) for d in doctors]
    form.theatre_id.choices = [(ot.id, f"{ot.ot_number} - {ot.name}") for ot in theatres]

    if form.validate_on_submit():
        sched = SurgerySchedule(
            surgery_id=form.surgery_id.data,
            patient_id=form.patient_id.data,
            lead_surgeon_id=form.lead_surgeon_id.data,
            theatre_id=form.theatre_id.data,
            scheduled_start_time=form.scheduled_start_time.data,
            scheduled_end_time=form.scheduled_end_time.data,
            surgery_status=form.surgery_status.data,
            pre_op_notes=form.pre_op_notes.data.strip() if form.pre_op_notes.data else None,
            post_op_notes=form.post_op_notes.data.strip() if form.post_op_notes.data else None,
            created_by_id=current_user.id
        )
        db.session.add(sched)
        db.session.commit()
        log_audit('CREATE', 'surgery_schedules', sched.id, f'Scheduled surgery #{sched.surgery_id} for patient #{sched.patient_id}')
        flash('Surgery schedule booked successfully.', 'success')
        return redirect(url_for('surgery.index'))

    return render_template('surgery/schedule_form.html', form=form, title='Book Surgical OT Slot')

@surgery_bp.route('/schedules/<int:id>/status', methods=['POST'])
@login_required
def update_schedule_status(id):
    sched = SurgerySchedule.query.get_or_404(id)
    new_status = request.form.get('surgery_status')
    if new_status:
        sched.surgery_status = new_status
        sched.updated_by_id = current_user.id
        db.session.commit()
        log_audit('UPDATE', 'surgery_schedules', sched.id, f'Changed surgery schedule status to {new_status}')
        flash(f'Surgery status changed to {new_status}.', 'success')
    return redirect(url_for('surgery.index'))

# ----------------- Ambulances -----------------
@surgery_bp.route('/ambulances/create', methods=['GET', 'POST'])
@login_required
def create_ambulance():
    form = AmbulanceForm()
    if form.validate_on_submit():
        amb = Ambulance(
            vehicle_number=form.vehicle_number.data.strip().upper(),
            vehicle_model=form.vehicle_model.data.strip(),
            ambulance_type=form.ambulance_type.data,
            driver_name=form.driver_name.data.strip(),
            driver_phone=form.driver_phone.data.strip(),
            current_location=form.current_location.data.strip(),
            operational_status=form.operational_status.data,
            created_by_id=current_user.id
        )
        db.session.add(amb)
        db.session.commit()
        log_audit('CREATE', 'ambulances', amb.id, f'Registered ambulance {amb.vehicle_number}')
        flash(f'Ambulance {amb.vehicle_number} registered in fleet.', 'success')
        return redirect(url_for('surgery.index'))
    return render_template('surgery/ambulance_form.html', form=form, title='Register Ambulance')

@surgery_bp.route('/ambulances/<int:id>/status', methods=['POST'])
@login_required
def update_ambulance_status(id):
    amb = Ambulance.query.get_or_404(id)
    new_status = request.form.get('operational_status')
    location = request.form.get('current_location', '').strip()
    if new_status:
        amb.operational_status = new_status
        if location:
            amb.current_location = location
        amb.updated_by_id = current_user.id
        db.session.commit()
        log_audit('UPDATE', 'ambulances', amb.id, f'Updated ambulance status to {new_status}')
        flash(f'Ambulance {amb.vehicle_number} status updated to {new_status}.', 'success')
    return redirect(url_for('surgery.index'))
