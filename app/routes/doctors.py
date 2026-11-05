from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.staff import Doctor, DoctorSpecialization, Department, DoctorDepartment
from app.forms.staff_forms import DoctorForm, DoctorSpecializationForm, DepartmentForm
from app.services.audit_service import log_audit
from datetime import datetime

doctors_bp = Blueprint('doctors', __name__, url_prefix='/doctors')

@doctors_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '').strip()
    dept_id = request.args.get('dept_id', type=int)
    page = request.args.get('page', 1, type=int)

    query = Doctor.query.filter_by(is_deleted=False)
    if search:
        query = query.filter(
            (Doctor.doctor_code.ilike(f'%{search}%')) |
            (Doctor.first_name.ilike(f'%{search}%')) |
            (Doctor.last_name.ilike(f'%{search}%')) |
            (Doctor.qualification.ilike(f'%{search}%'))
        )
    if dept_id:
        query = query.join(Doctor.department_associations).filter(DoctorDepartment.department_id == dept_id)

    pagination = query.order_by(Doctor.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    doctors = pagination.items
    departments = Department.query.filter_by(is_deleted=False, status='Active').all()

    return render_template('doctors/index.html', doctors=doctors, pagination=pagination, departments=departments, search=search, selected_dept=dept_id)

@doctors_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = DoctorForm()
    departments = Department.query.filter_by(is_deleted=False, status='Active').all()
    form.department_id.choices = [(d.id, f"{d.name} ({d.code})") for d in departments]

    if request.method == 'GET' and not form.doctor_code.data:
        count = Doctor.query.count() + 1
        form.doctor_code.data = f'DOC-{datetime.utcnow().year}-{count:03d}'

    if form.validate_on_submit():
        existing = Doctor.query.filter(
            (Doctor.doctor_code == form.doctor_code.data.strip()) |
            (Doctor.license_number == form.license_number.data.strip())
        ).first()
        if existing:
            flash('Doctor Code or Medical License number already exists.', 'warning')
            return render_template('doctors/form.html', form=form, title='Add New Doctor')

        doctor = Doctor(
            doctor_code=form.doctor_code.data.strip(),
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            license_number=form.license_number.data.strip(),
            qualification=form.qualification.data.strip(),
            experience_years=form.experience_years.data,
            consultation_fee=form.consultation_fee.data,
            phone=form.phone.data.strip(),
            email=form.email.data.strip() if form.email.data else None,
            created_by_id=current_user.id
        )
        db.session.add(doctor)
        db.session.flush()

        # Link primary department
        doc_dept = DoctorDepartment(
            doctor_id=doctor.id,
            department_id=form.department_id.data,
            is_primary_dept=True,
            created_by_id=current_user.id
        )
        db.session.add(doc_dept)
        db.session.commit()

        log_audit('CREATE', 'doctors', doctor.id, f'Registered doctor {doctor.full_name} ({doctor.doctor_code})')
        flash(f'Doctor {doctor.full_name} added successfully!', 'success')
        return redirect(url_for('doctors.view', id=doctor.id))

    return render_template('doctors/form.html', form=form, title='Add New Doctor')

@doctors_bp.route('/<int:id>')
@login_required
def view(id):
    doctor = Doctor.query.get_or_404(id)
    spec_form = DoctorSpecializationForm()
    return render_template('doctors/view.html', doctor=doctor, spec_form=spec_form)

@doctors_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    doctor = Doctor.query.get_or_404(id)
    form = DoctorForm(obj=doctor)
    departments = Department.query.filter_by(is_deleted=False, status='Active').all()
    form.department_id.choices = [(d.id, f"{d.name} ({d.code})") for d in departments]

    if request.method == 'GET':
        prim = next((assoc.department_id for assoc in doctor.department_associations if assoc.is_primary_dept), None)
        if prim:
            form.department_id.data = prim

    if form.validate_on_submit():
        doctor.doctor_code = form.doctor_code.data.strip()
        doctor.first_name = form.first_name.data.strip()
        doctor.last_name = form.last_name.data.strip()
        doctor.license_number = form.license_number.data.strip()
        doctor.qualification = form.qualification.data.strip()
        doctor.experience_years = form.experience_years.data
        doctor.consultation_fee = form.consultation_fee.data
        doctor.phone = form.phone.data.strip()
        doctor.email = form.email.data.strip() if form.email.data else None
        doctor.updated_by_id = current_user.id

        # Update primary department association
        DoctorDepartment.query.filter_by(doctor_id=doctor.id).delete()
        doc_dept = DoctorDepartment(
            doctor_id=doctor.id,
            department_id=form.department_id.data,
            is_primary_dept=True,
            created_by_id=current_user.id
        )
        db.session.add(doc_dept)
        db.session.commit()

        log_audit('UPDATE', 'doctors', doctor.id, f'Updated profile for doctor {doctor.full_name}')
        flash('Doctor profile updated successfully!', 'success')
        return redirect(url_for('doctors.view', id=doctor.id))

    return render_template('doctors/form.html', form=form, title=f'Edit Doctor: {doctor.full_name}', doctor=doctor)

@doctors_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    doctor = Doctor.query.get_or_404(id)
    doctor.soft_delete(user_id=current_user.id)
    log_audit('SOFT_DELETE', 'doctors', doctor.id, f'Soft-deleted doctor {doctor.full_name}')
    flash(f'Doctor {doctor.full_name} moved to Recycle Bin (Soft Deleted).', 'info')
    return redirect(url_for('doctors.index'))

@doctors_bp.route('/<int:id>/toggle-status', methods=['POST'])
@login_required
def toggle_status(id):
    doctor = Doctor.query.get_or_404(id)
    doctor.toggle_status()
    doctor.updated_by_id = current_user.id
    db.session.commit()
    log_audit('UPDATE', 'doctors', doctor.id, f'Toggled doctor status to {doctor.status}')
    flash(f'Doctor status changed to {doctor.status}.', 'success')
    return redirect(request.referrer or url_for('doctors.view', id=doctor.id))

@doctors_bp.route('/<int:id>/add-specialization', methods=['POST'])
@login_required
def add_specialization(id):
    doctor = Doctor.query.get_or_404(id)
    form = DoctorSpecializationForm()
    if form.validate_on_submit():
        spec = DoctorSpecialization(
            doctor_id=doctor.id,
            specialization_name=form.specialization_name.data.strip(),
            certification_board=form.certification_board.data.strip() if form.certification_board.data else None,
            year_obtained=form.year_obtained.data,
            created_by_id=current_user.id
        )
        db.session.add(spec)
        db.session.commit()
        log_audit('CREATE', 'doctor_specializations', spec.id, f'Added specialization {spec.specialization_name} to doctor #{doctor.id}')
        flash('Specialization added successfully.', 'success')
    else:
        flash('Error adding specialization. Name is required.', 'danger')
    return redirect(url_for('doctors.view', id=doctor.id))

# -------------------------------------------------------------
# Department Management
# -------------------------------------------------------------
@doctors_bp.route('/departments', methods=['GET', 'POST'])
@login_required
def departments():
    form = DepartmentForm()
    if form.validate_on_submit():
        existing = Department.query.filter(
            (Department.name == form.name.data.strip()) |
            (Department.code == form.code.data.strip().upper())
        ).first()
        if existing:
            flash('Department name or code already exists.', 'warning')
        else:
            dept = Department(
                name=form.name.data.strip(),
                code=form.code.data.strip().upper(),
                description=form.description.data.strip() if form.description.data else None,
                floor_location=form.floor_location.data.strip() if form.floor_location.data else None,
                created_by_id=current_user.id
            )
            db.session.add(dept)
            db.session.commit()
            log_audit('CREATE', 'departments', dept.id, f'Created department {dept.name} ({dept.code})')
            flash(f'Department {dept.name} created successfully!', 'success')
            return redirect(url_for('doctors.departments'))

    departments_list = Department.query.filter_by(is_deleted=False).order_by(Department.name).all()
    return render_template('doctors/departments.html', form=form, departments=departments_list)

@doctors_bp.route('/departments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_department(id):
    dept = Department.query.get_or_404(id)
    form = DepartmentForm(obj=dept)
    if form.validate_on_submit():
        dept.name = form.name.data.strip()
        dept.code = form.code.data.strip().upper()
        dept.description = form.description.data.strip() if form.description.data else None
        dept.floor_location = form.floor_location.data.strip() if form.floor_location.data else None
        dept.updated_by_id = current_user.id
        db.session.commit()
        log_audit('UPDATE', 'departments', dept.id, f'Updated department {dept.name}')
        flash('Department updated successfully.', 'success')
        return redirect(url_for('doctors.departments'))
    return render_template('doctors/department_form.html', form=form, department=dept)

@doctors_bp.route('/departments/<int:id>/delete', methods=['POST'])
@login_required
def delete_department(id):
    dept = Department.query.get_or_404(id)
    dept.soft_delete(user_id=current_user.id)
    log_audit('SOFT_DELETE', 'departments', dept.id, f'Soft-deleted department {dept.name}')
    flash(f'Department {dept.name} soft-deleted.', 'info')
    return redirect(url_for('doctors.departments'))
