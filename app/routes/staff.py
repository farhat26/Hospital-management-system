from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.staff import Nurse, Staff, Shift, StaffAttendance, Department, Doctor
from app.forms.staff_forms import NurseForm, StaffForm, ShiftForm, StaffAttendanceForm
from app.services.audit_service import log_audit
from datetime import datetime, date

staff_bp = Blueprint('staff', __name__, url_prefix='/staff')

@staff_bp.route('/')
@login_required
def index():
    nurses = Nurse.query.filter_by(is_deleted=False).order_by(Nurse.created_at.desc()).all()
    general_staff = Staff.query.filter_by(is_deleted=False).order_by(Staff.created_at.desc()).all()
    return render_template('staff/index.html', nurses=nurses, general_staff=general_staff)

# ----------------- Nurse Routes -----------------
@staff_bp.route('/nurses/create', methods=['GET', 'POST'])
@login_required
def create_nurse():
    form = NurseForm()
    depts = Department.query.filter_by(is_deleted=False, status='Active').all()
    form.department_id.choices = [(d.id, d.name) for d in depts]

    if request.method == 'GET' and not form.nurse_code.data:
        count = Nurse.query.count() + 1
        form.nurse_code.data = f'NUR-{datetime.utcnow().year}-{count:03d}'

    if form.validate_on_submit():
        nurse = Nurse(
            nurse_code=form.nurse_code.data.strip(),
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            department_id=form.department_id.data,
            license_number=form.license_number.data.strip(),
            qualification=form.qualification.data.strip(),
            phone=form.phone.data.strip(),
            email=form.email.data.strip() if form.email.data else None,
            created_by_id=current_user.id
        )
        db.session.add(nurse)
        db.session.commit()
        log_audit('CREATE', 'nurses', nurse.id, f'Registered nurse {nurse.full_name} ({nurse.nurse_code})')
        flash(f'Nurse {nurse.full_name} registered successfully!', 'success')
        return redirect(url_for('staff.index'))

    return render_template('staff/nurse_form.html', form=form, title='Add Nursing Staff')

@staff_bp.route('/nurses/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_nurse(id):
    nurse = Nurse.query.get_or_404(id)
    form = NurseForm(obj=nurse)
    depts = Department.query.filter_by(is_deleted=False, status='Active').all()
    form.department_id.choices = [(d.id, d.name) for d in depts]

    if form.validate_on_submit():
        nurse.nurse_code = form.nurse_code.data.strip()
        nurse.first_name = form.first_name.data.strip()
        nurse.last_name = form.last_name.data.strip()
        nurse.department_id = form.department_id.data
        nurse.license_number = form.license_number.data.strip()
        nurse.qualification = form.qualification.data.strip()
        nurse.phone = form.phone.data.strip()
        nurse.email = form.email.data.strip() if form.email.data else None
        nurse.updated_by_id = current_user.id
        db.session.commit()
        log_audit('UPDATE', 'nurses', nurse.id, f'Updated nurse record for {nurse.full_name}')
        flash('Nurse details updated.', 'success')
        return redirect(url_for('staff.index'))

    return render_template('staff/nurse_form.html', form=form, title=f'Edit Nurse: {nurse.full_name}')

@staff_bp.route('/nurses/<int:id>/delete', methods=['POST'])
@login_required
def delete_nurse(id):
    nurse = Nurse.query.get_or_404(id)
    nurse.soft_delete(user_id=current_user.id)
    log_audit('SOFT_DELETE', 'nurses', nurse.id, f'Soft-deleted nurse {nurse.full_name}')
    flash(f'Nurse {nurse.full_name} soft-deleted.', 'info')
    return redirect(url_for('staff.index'))

# ----------------- Staff Routes -----------------
@staff_bp.route('/general/create', methods=['GET', 'POST'])
@login_required
def create_staff():
    form = StaffForm()
    depts = Department.query.filter_by(is_deleted=False, status='Active').all()
    form.department_id.choices = [(0, '-- None / Administrative --')] + [(d.id, d.name) for d in depts]

    if request.method == 'GET' and not form.staff_code.data:
        count = Staff.query.count() + 1
        form.staff_code.data = f'STF-{datetime.utcnow().year}-{count:03d}'
        form.hire_date.data = date.today()

    if form.validate_on_submit():
        staff_member = Staff(
            staff_code=form.staff_code.data.strip(),
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            role_title=form.role_title.data.strip(),
            department_id=form.department_id.data if form.department_id.data != 0 else None,
            phone=form.phone.data.strip(),
            email=form.email.data.strip() if form.email.data else None,
            hire_date=form.hire_date.data,
            created_by_id=current_user.id
        )
        db.session.add(staff_member)
        db.session.commit()
        log_audit('CREATE', 'staff', staff_member.id, f'Registered staff {staff_member.full_name} ({staff_member.role_title})')
        flash(f'Staff member {staff_member.full_name} registered successfully!', 'success')
        return redirect(url_for('staff.index'))

    return render_template('staff/staff_form.html', form=form, title='Add Staff Member')

@staff_bp.route('/general/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_staff(id):
    staff_member = Staff.query.get_or_404(id)
    form = StaffForm(obj=staff_member)
    depts = Department.query.filter_by(is_deleted=False, status='Active').all()
    form.department_id.choices = [(0, '-- None / Administrative --')] + [(d.id, d.name) for d in depts]

    if form.validate_on_submit():
        staff_member.staff_code = form.staff_code.data.strip()
        staff_member.first_name = form.first_name.data.strip()
        staff_member.last_name = form.last_name.data.strip()
        staff_member.role_title = form.role_title.data.strip()
        staff_member.department_id = form.department_id.data if form.department_id.data != 0 else None
        staff_member.phone = form.phone.data.strip()
        staff_member.email = form.email.data.strip() if form.email.data else None
        staff_member.hire_date = form.hire_date.data
        staff_member.updated_by_id = current_user.id
        db.session.commit()
        log_audit('UPDATE', 'staff', staff_member.id, f'Updated staff record for {staff_member.full_name}')
        flash('Staff details updated.', 'success')
        return redirect(url_for('staff.index'))

    return render_template('staff/staff_form.html', form=form, title=f'Edit Staff: {staff_member.full_name}')

@staff_bp.route('/general/<int:id>/delete', methods=['POST'])
@login_required
def delete_staff(id):
    staff_member = Staff.query.get_or_404(id)
    staff_member.soft_delete(user_id=current_user.id)
    log_audit('SOFT_DELETE', 'staff', staff_member.id, f'Soft-deleted staff {staff_member.full_name}')
    flash(f'Staff member {staff_member.full_name} soft-deleted.', 'info')
    return redirect(url_for('staff.index'))

# ----------------- Shifts & Attendance -----------------
@staff_bp.route('/shifts', methods=['GET', 'POST'])
@login_required
def shifts():
    form = ShiftForm()
    if form.validate_on_submit():
        shift = Shift(
            name=form.name.data.strip(),
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            description=form.description.data.strip() if form.description.data else None,
            created_by_id=current_user.id
        )
        db.session.add(shift)
        db.session.commit()
        log_audit('CREATE', 'shifts', shift.id, f'Created duty shift {shift.name}')
        flash(f'Shift {shift.name} created successfully!', 'success')
        return redirect(url_for('staff.shifts'))

    shifts_list = Shift.query.filter_by(is_deleted=False).all()
    return render_template('staff/shifts.html', form=form, shifts=shifts_list)

@staff_bp.route('/attendance', methods=['GET', 'POST'])
@login_required
def attendance():
    target_date_str = request.args.get('date', date.today().isoformat())
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
    except ValueError:
        target_date = date.today()

    form = StaffAttendanceForm()
    doctors = Doctor.query.filter_by(is_deleted=False, status='Active').all()
    nurses = Nurse.query.filter_by(is_deleted=False, status='Active').all()
    general_staff = Staff.query.filter_by(is_deleted=False, status='Active').all()
    shifts_list = Shift.query.filter_by(is_deleted=False, status='Active').all()

    form.doctor_id.choices = [(0, '-- None --')] + [(d.id, d.full_name) for d in doctors]
    form.nurse_id.choices = [(0, '-- None --')] + [(n.id, n.full_name) for n in nurses]
    form.staff_id.choices = [(0, '-- None --')] + [(s.id, f"{s.full_name} ({s.role_title})") for s in general_staff]
    form.shift_id.choices = [(sh.id, f"{sh.name} ({sh.start_time.strftime('%H:%M')}-{sh.end_time.strftime('%H:%M')})") for sh in shifts_list]

    if request.method == 'GET':
        form.attendance_date.data = target_date

    if form.validate_on_submit():
        doc_id = form.doctor_id.data if form.doctor_id.data != 0 else None
        nur_id = form.nurse_id.data if form.nurse_id.data != 0 else None
        stf_id = form.staff_id.data if form.staff_id.data != 0 else None

        if not any([doc_id, nur_id, stf_id]):
            flash('Please select at least one personnel (Doctor, Nurse, or Staff).', 'warning')
        else:
            att = StaffAttendance(
                doctor_id=doc_id,
                nurse_id=nur_id,
                staff_id=stf_id,
                shift_id=form.shift_id.data,
                attendance_date=form.attendance_date.data,
                check_in_time=form.check_in_time.data,
                check_out_time=form.check_out_time.data,
                attendance_status=form.attendance_status.data,
                created_by_id=current_user.id
            )
            db.session.add(att)
            db.session.commit()
            log_audit('CREATE', 'staff_attendance', att.id, f'Recorded attendance for {att.attendance_date}')
            flash('Attendance recorded successfully!', 'success')
            return redirect(url_for('staff.attendance', date=form.attendance_date.data.isoformat()))

    attendances = StaffAttendance.query.filter_by(is_deleted=False, attendance_date=target_date).all()
    return render_template('staff/attendance.html', form=form, attendances=attendances, target_date=target_date)
