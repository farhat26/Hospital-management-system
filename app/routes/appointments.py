from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.appointments import Appointment, AppointmentStatusHistory, QueueToken, Visit
from app.models.patients import Patient, Diagnosis
from app.models.staff import Doctor, Department
from app.forms.appointment_forms import AppointmentForm, VisitForm, QueueTokenForm, VisitDiagnosisForm
from app.models.patients import VisitDiagnosis
from app.services.audit_service import log_audit
from app.utils.decorators import role_required
from datetime import datetime, date

appointments_bp = Blueprint('appointments', __name__, url_prefix='/appointments')

@appointments_bp.route('/')
@login_required
def index():
    status = request.args.get('status', '').strip()
    doctor_id = request.args.get('doctor_id', type=int)
    date_filter = request.args.get('date', '').strip()
    page = request.args.get('page', 1, type=int)

    query = Appointment.query.filter_by(is_deleted=False)
    if status:
        query = query.filter_by(current_status=status)
    if doctor_id:
        query = query.filter_by(doctor_id=doctor_id)
    if date_filter:
        try:
            d_val = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter_by(appointment_date=d_val)
        except ValueError:
            pass

    pagination = query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).paginate(page=page, per_page=10, error_out=False)
    appointments = pagination.items
    doctors = Doctor.query.filter_by(is_deleted=False, status='Active').all()

    return render_template(
        'appointments/index.html',
        appointments=appointments,
        pagination=pagination,
        doctors=doctors,
        selected_status=status,
        selected_doctor=doctor_id,
        selected_date=date_filter
    )

@appointments_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = AppointmentForm()
    patients = Patient.query.filter_by(is_deleted=False, status='Active').all()
    doctors = Doctor.query.filter_by(is_deleted=False, status='Active').all()
    depts = Department.query.filter_by(is_deleted=False, status='Active').all()

    form.patient_id.choices = [(p.id, f"{p.patient_code} - {p.full_name}") for p in patients]
    form.doctor_id.choices = [(d.id, f"{d.full_name} ({d.qualification})") for d in doctors]
    form.department_id.choices = [(dep.id, dep.name) for dep in depts]

    if request.method == 'GET' and not form.appointment_number.data:
        count = Appointment.query.count() + 1
        form.appointment_number.data = f'APT-{datetime.utcnow().year}-{count:04d}'
        form.appointment_date.data = date.today()

    if form.validate_on_submit():
        apt = Appointment(
            appointment_number=form.appointment_number.data.strip(),
            patient_id=form.patient_id.data,
            doctor_id=form.doctor_id.data,
            department_id=form.department_id.data,
            appointment_date=form.appointment_date.data,
            appointment_time=form.appointment_time.data,
            appointment_type=form.appointment_type.data,
            reason=form.reason.data.strip() if form.reason.data else None,
            current_status=form.current_status.data,
            created_by_id=current_user.id
        )
        db.session.add(apt)
        db.session.flush()

        # Audit initial status
        hist = AppointmentStatusHistory(
            appointment_id=apt.id,
            old_status=None,
            new_status=apt.current_status,
            change_reason='Initial appointment booking',
            changed_at=datetime.utcnow(),
            created_by_id=current_user.id
        )
        db.session.add(hist)

        # Automatically issue a queue token if scheduled for today
        if apt.appointment_date == date.today():
            today_tokens = QueueToken.query.filter_by(token_date=date.today(), doctor_id=apt.doctor_id).count()
            token = QueueToken(
                appointment_id=apt.id,
                patient_id=apt.patient_id,
                doctor_id=apt.doctor_id,
                token_number=today_tokens + 1,
                token_date=date.today(),
                token_status='Waiting',
                created_by_id=current_user.id
            )
            db.session.add(token)

        db.session.commit()
        log_audit('CREATE', 'appointments', apt.id, f'Booked appointment {apt.appointment_number}')
        flash(f'Appointment {apt.appointment_number} booked successfully!', 'success')
        return redirect(url_for('appointments.view', id=apt.id))

    return render_template('appointments/form.html', form=form, title='Book New Appointment')

@appointments_bp.route('/<int:id>')
@login_required
def view(id):
    appointment = Appointment.query.get_or_404(id)
    return render_template('appointments/view.html', appointment=appointment)

@appointments_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    appointment = Appointment.query.get_or_404(id)
    form = AppointmentForm(obj=appointment)
    patients = Patient.query.filter_by(is_deleted=False, status='Active').all()
    doctors = Doctor.query.filter_by(is_deleted=False, status='Active').all()
    depts = Department.query.filter_by(is_deleted=False, status='Active').all()

    form.patient_id.choices = [(p.id, f"{p.patient_code} - {p.full_name}") for p in patients]
    form.doctor_id.choices = [(d.id, f"{d.full_name} ({d.qualification})") for d in doctors]
    form.department_id.choices = [(dep.id, dep.name) for dep in depts]

    if form.validate_on_submit():
        old_st = appointment.current_status
        appointment.appointment_number = form.appointment_number.data.strip()
        appointment.patient_id = form.patient_id.data
        appointment.doctor_id = form.doctor_id.data
        appointment.department_id = form.department_id.data
        appointment.appointment_date = form.appointment_date.data
        appointment.appointment_time = form.appointment_time.data
        appointment.appointment_type = form.appointment_type.data
        appointment.reason = form.reason.data.strip() if form.reason.data else None
        new_st = form.current_status.data
        appointment.updated_by_id = current_user.id

        if old_st != new_st:
            appointment.current_status = new_st
            hist = AppointmentStatusHistory(
                appointment_id=appointment.id,
                old_status=old_st,
                new_status=new_st,
                change_reason=request.form.get('change_reason', 'Status updated by user'),
                changed_at=datetime.utcnow(),
                created_by_id=current_user.id
            )
            db.session.add(hist)

        db.session.commit()
        log_audit('UPDATE', 'appointments', appointment.id, f'Updated appointment {appointment.appointment_number}')
        flash('Appointment details updated successfully.', 'success')
        return redirect(url_for('appointments.view', id=appointment.id))

    return render_template('appointments/form.html', form=form, title=f'Edit Appointment: {appointment.appointment_number}', appointment=appointment)

@appointments_bp.route('/<int:id>/update-status', methods=['POST'])
@login_required
def update_status(id):
    appointment = Appointment.query.get_or_404(id)
    new_status = request.form.get('status')
    reason = request.form.get('reason', 'Routine status transition').strip()

    if new_status and new_status != appointment.current_status:
        old_status = appointment.current_status
        appointment.current_status = new_status
        appointment.updated_by_id = current_user.id

        hist = AppointmentStatusHistory(
            appointment_id=appointment.id,
            old_status=old_status,
            new_status=new_status,
            change_reason=reason,
            changed_at=datetime.utcnow(),
            created_by_id=current_user.id
        )
        db.session.add(hist)

        if appointment.queue_token:
            if new_status == 'Confirmed':
                appointment.queue_token.token_status = 'In-Consultation'
            elif new_status == 'Completed':
                appointment.queue_token.token_status = 'Completed'
            elif new_status == 'Cancelled':
                appointment.queue_token.token_status = 'Skipped'

        db.session.commit()
        log_audit('UPDATE', 'appointments', appointment.id, f'Status changed from {old_status} to {new_status}')
        flash(f'Appointment status updated to {new_status}.', 'success')
    return redirect(request.referrer or url_for('appointments.view', id=appointment.id))

@appointments_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    appointment = Appointment.query.get_or_404(id)
    appointment.soft_delete(user_id=current_user.id)
    log_audit('SOFT_DELETE', 'appointments', appointment.id, f'Soft-deleted appointment {appointment.appointment_number}')
    flash(f'Appointment {appointment.appointment_number} soft-deleted.', 'info')
    return redirect(url_for('appointments.index'))

# ----------------- Queue Tokens -----------------
@appointments_bp.route('/queue', methods=['GET', 'POST'])
@login_required
def queue():
    target_date_str = request.args.get('date', date.today().isoformat())
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
    except ValueError:
        target_date = date.today()

    doc_id = request.args.get('doctor_id', type=int)
    form = QueueTokenForm()
    patients = Patient.query.filter_by(is_deleted=False, status='Active').all()
    doctors = Doctor.query.filter_by(is_deleted=False, status='Active').all()

    form.patient_id.choices = [(p.id, f"{p.patient_code} - {p.full_name}") for p in patients]
    form.doctor_id.choices = [(d.id, d.full_name) for d in doctors]
    form.appointment_id.choices = [(0, '-- None / Walk-in OPD --')]

    if request.method == 'GET':
        form.token_date.data = target_date

    if form.validate_on_submit():
        existing_count = QueueToken.query.filter_by(token_date=form.token_date.data, doctor_id=form.doctor_id.data).count()
        token = QueueToken(
            patient_id=form.patient_id.data,
            doctor_id=form.doctor_id.data,
            appointment_id=None,
            token_number=existing_count + 1,
            token_date=form.token_date.data,
            token_status=form.token_status.data,
            created_by_id=current_user.id
        )
        db.session.add(token)
        db.session.commit()
        log_audit('CREATE', 'queue_tokens', token.id, f'Issued queue token #{token.token_number} for doctor #{token.doctor_id}')
        flash(f'Queue Token #{token.token_number} issued successfully!', 'success')
        return redirect(url_for('appointments.queue', date=form.token_date.data.isoformat(), doctor_id=form.doctor_id.data))

    tokens_query = QueueToken.query.filter_by(is_deleted=False, token_date=target_date)
    if doc_id:
        tokens_query = tokens_query.filter_by(doctor_id=doc_id)
    tokens = tokens_query.order_by(QueueToken.token_number).all()

    return render_template('appointments/queue.html', form=form, tokens=tokens, target_date=target_date, doctors=doctors, selected_doctor=doc_id)

@appointments_bp.route('/queue/<int:id>/status', methods=['POST'])
@login_required
def update_token_status(id):
    token = QueueToken.query.get_or_404(id)
    new_status = request.form.get('token_status')
    if new_status not in ('Waiting', 'In-Consultation', 'Completed', 'Skipped'):
        flash('Invalid token status.', 'danger')
    else:
        token.token_status = new_status
        token.updated_by_id = current_user.id
        db.session.commit()
        log_audit('UPDATE', 'queue_tokens', token.id, f'Updated token #{token.token_number} status to {new_status}')
        flash(f'Token #{token.token_number} status updated to {new_status}.', 'success')
    return redirect(request.referrer or url_for('appointments.queue'))

# ----------------- Visits / Clinical Encounters -----------------
@appointments_bp.route('/visits')
@login_required
def visits():
    page = request.args.get('page', 1, type=int)
    visits_list = Visit.query.filter_by(is_deleted=False).order_by(Visit.visit_date.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('appointments/visits.html', visits=visits_list.items, pagination=visits_list)

@appointments_bp.route('/visits/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Doctor', 'Nurse')
def create_visit():
    form = VisitForm()
    patients = Patient.query.filter_by(is_deleted=False, status='Active').all()
    doctors = Doctor.query.filter_by(is_deleted=False, status='Active').all()
    appts = Appointment.query.filter_by(is_deleted=False).order_by(Appointment.appointment_date.desc()).all()

    form.patient_id.choices = [(p.id, f"{p.patient_code} - {p.full_name}") for p in patients]
    form.doctor_id.choices = [(d.id, d.full_name) for d in doctors]
    form.appointment_id.choices = [(0, '-- None / Walk-in Encounter --')] + [(a.id, f"{a.appointment_number} ({a.appointment_date})") for a in appts]

    if request.method == 'GET' and not form.visit_number.data:
        count = Visit.query.count() + 1
        form.visit_number.data = f'VIS-{datetime.utcnow().year}-{count:04d}'

    if form.validate_on_submit():
        appt_id = form.appointment_id.data if form.appointment_id.data != 0 else None
        visit = Visit(
            visit_number=form.visit_number.data.strip(),
            patient_id=form.patient_id.data,
            doctor_id=form.doctor_id.data,
            appointment_id=appt_id,
            visit_date=datetime.utcnow(),
            visit_type=form.visit_type.data,
            systolic_bp=form.systolic_bp.data,
            diastolic_bp=form.diastolic_bp.data,
            heart_rate=form.heart_rate.data,
            temperature=form.temperature.data,
            weight_kg=form.weight_kg.data,
            height_cm=form.height_cm.data,
            symptoms=form.symptoms.data.strip() if form.symptoms.data else None,
            clinical_notes=form.clinical_notes.data.strip() if form.clinical_notes.data else None,
            created_by_id=current_user.id
        )
        db.session.add(visit)

        # Mark linked appointment as completed
        if appt_id:
            apt = Appointment.query.get(appt_id)
            if apt:
                apt.current_status = 'Completed'
                if apt.queue_token:
                    apt.queue_token.token_status = 'Completed'

        db.session.commit()
        log_audit('CREATE', 'visits', visit.id, f'Recorded clinical visit {visit.visit_number}')
        flash(f'Clinical encounter {visit.visit_number} recorded successfully!', 'success')
        return redirect(url_for('appointments.view_visit', id=visit.id))

    return render_template('appointments/visit_form.html', form=form, title='Record Clinical Visit / Encounter')

@appointments_bp.route('/visits/<int:id>')
@login_required
def view_visit(id):
    visit = Visit.query.get_or_404(id)
    diag_form = VisitDiagnosisForm()
    diagnoses = Diagnosis.query.filter_by(is_deleted=False).all()
    diag_form.diagnosis_id.choices = [(d.id, f"{d.icd_code} - {d.diagnosis_name}") for d in diagnoses]
    return render_template('appointments/visit_view.html', visit=visit, diag_form=diag_form)

@appointments_bp.route('/visits/<int:id>/add-diagnosis', methods=['POST'])
@login_required
def add_visit_diagnosis(id):
    visit = Visit.query.get_or_404(id)
    form = VisitDiagnosisForm()
    diagnoses = Diagnosis.query.filter_by(is_deleted=False).all()
    form.diagnosis_id.choices = [(d.id, f"{d.icd_code} - {d.diagnosis_name}") for d in diagnoses]

    if form.validate_on_submit():
        vd = VisitDiagnosis(
            visit_id=visit.id,
            diagnosis_id=form.diagnosis_id.data,
            diagnosis_type=form.diagnosis_type.data,
            notes=form.notes.data.strip() if form.notes.data else None,
            created_by_id=current_user.id
        )
        db.session.add(vd)
        db.session.commit()
        log_audit('CREATE', 'visit_diagnoses', vd.id, f'Assigned diagnosis #{vd.diagnosis_id} to visit #{visit.id}')
        flash('Diagnosis added to visit.', 'success')
    else:
        flash('Error adding diagnosis.', 'danger')
    return redirect(url_for('appointments.view_visit', id=visit.id))

@appointments_bp.route('/visits/<int:id>/delete', methods=['POST'])
@login_required
def delete_visit(id):
    visit = Visit.query.get_or_404(id)
    visit.soft_delete(user_id=current_user.id)
    log_audit('SOFT_DELETE', 'visits', visit.id, f'Soft-deleted visit {visit.visit_number}')
    flash(f'Visit {visit.visit_number} soft-deleted.', 'info')
    return redirect(url_for('appointments.visits'))
