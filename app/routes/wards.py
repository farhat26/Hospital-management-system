from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.wards import Ward, Room, Bed, Admission, BedAllocation, Discharge
from app.models.patients import Patient
from app.models.staff import Doctor
from app.forms.ward_forms import WardForm, RoomForm, BedForm, AdmissionForm, BedAllocationForm, DischargeForm
from app.services.audit_service import log_audit
from datetime import datetime, date

wards_bp = Blueprint('wards', __name__, url_prefix='/wards')

@wards_bp.route('/')
@login_required
def index():
    wards_list = Ward.query.filter_by(is_deleted=False).all()
    admissions_active = Admission.query.filter_by(is_deleted=False, admission_status='Admitted').order_by(Admission.admission_date.desc()).all()
    available_beds = Bed.query.filter_by(is_deleted=False, status='Active', bed_status='Available').count()
    occupied_beds = Bed.query.filter_by(is_deleted=False, status='Active', bed_status='Occupied').count()

    return render_template('wards/index.html', wards=wards_list, active_admissions=admissions_active, available_beds=available_beds, occupied_beds=occupied_beds)

# ----------------- Wards & Rooms & Beds -----------------
@wards_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_ward():
    form = WardForm()
    if form.validate_on_submit():
        ward = Ward(
            ward_name=form.ward_name.data.strip(),
            ward_type=form.ward_type.data,
            gender_type=form.gender_type.data,
            total_capacity=form.total_capacity.data,
            floor_number=form.floor_number.data,
            created_by_id=current_user.id
        )
        db.session.add(ward)
        db.session.commit()
        log_audit('CREATE', 'wards', ward.id, f'Created ward {ward.ward_name}')
        flash(f'Ward {ward.ward_name} created successfully.', 'success')
        return redirect(url_for('wards.view_ward', id=ward.id))

    return render_template('wards/ward_form.html', form=form, title='Add New Inpatient Ward')

@wards_bp.route('/<int:id>')
@login_required
def view_ward(id):
    ward = Ward.query.get_or_404(id)
    room_form = RoomForm()
    bed_form = BedForm()
    rooms = Room.query.filter_by(ward_id=ward.id, is_deleted=False).all()
    bed_form.room_id.choices = [(r.id, f"Room {r.room_number} ({r.room_type})") for r in rooms]
    return render_template('wards/ward_view.html', ward=ward, room_form=room_form, bed_form=bed_form)

@wards_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ward(id):
    ward = Ward.query.get_or_404(id)
    form = WardForm(obj=ward)
    if form.validate_on_submit():
        ward.ward_name = form.ward_name.data.strip()
        ward.ward_type = form.ward_type.data
        ward.gender_type = form.gender_type.data
        ward.total_capacity = form.total_capacity.data
        ward.floor_number = form.floor_number.data
        ward.updated_by_id = current_user.id
        db.session.commit()
        log_audit('UPDATE', 'wards', ward.id, f'Updated ward {ward.ward_name}')
        flash('Ward details updated.', 'success')
        return redirect(url_for('wards.view_ward', id=ward.id))
    return render_template('wards/ward_form.html', form=form, title=f'Edit Ward: {ward.ward_name}')

@wards_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_ward(id):
    ward = Ward.query.get_or_404(id)
    ward.soft_delete(user_id=current_user.id)
    log_audit('SOFT_DELETE', 'wards', ward.id, f'Soft-deleted ward {ward.ward_name}')
    flash(f'Ward {ward.ward_name} soft-deleted.', 'info')
    return redirect(url_for('wards.index'))

@wards_bp.route('/<int:id>/add-room', methods=['POST'])
@login_required
def add_room(id):
    ward = Ward.query.get_or_404(id)
    form = RoomForm()
    form.ward_id.choices = [(ward.id, ward.ward_name)]
    if form.validate_on_submit():
        room = Room(
            ward_id=ward.id,
            room_number=form.room_number.data.strip(),
            room_type=form.room_type.data,
            daily_rate=form.daily_rate.data,
            created_by_id=current_user.id
        )
        db.session.add(room)
        db.session.commit()
        log_audit('CREATE', 'rooms', room.id, f'Added room {room.room_number} to ward #{ward.id}')
        flash(f'Room {room.room_number} added to ward.', 'success')
    return redirect(url_for('wards.view_ward', id=ward.id))

@wards_bp.route('/add-bed', methods=['POST'])
@login_required
def add_bed():
    form = BedForm()
    rooms = Room.query.filter_by(is_deleted=False).all()
    form.room_id.choices = [(r.id, r.room_number) for r in rooms]
    if form.validate_on_submit():
        bed = Bed(
            room_id=form.room_id.data,
            bed_number=form.bed_number.data.strip(),
            bed_type=form.bed_type.data,
            bed_status=form.bed_status.data,
            created_by_id=current_user.id
        )
        db.session.add(bed)
        db.session.commit()
        log_audit('CREATE', 'beds', bed.id, f'Added bed {bed.bed_number}')
        flash(f'Bed {bed.bed_number} registered.', 'success')
        return redirect(url_for('wards.view_ward', id=bed.room.ward_id))
    flash('Error adding bed.', 'danger')
    return redirect(url_for('wards.index'))

@wards_bp.route('/beds/<int:id>/status', methods=['POST'])
@login_required
def update_bed_status(id):
    bed = Bed.query.get_or_404(id)
    new_status = request.form.get('bed_status')
    if new_status:
        bed.bed_status = new_status
        bed.updated_by_id = current_user.id
        db.session.commit()
        log_audit('UPDATE', 'beds', bed.id, f'Changed bed status to {new_status}')
        flash(f'Bed {bed.bed_number} status changed to {new_status}.', 'success')
    return redirect(request.referrer or url_for('wards.index'))

# ----------------- Admissions -----------------
@wards_bp.route('/admissions')
@login_required
def admissions():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '').strip()
    query = Admission.query.filter_by(is_deleted=False)
    if status:
        query = query.filter_by(admission_status=status)
    pagination = query.order_by(Admission.admission_date.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('wards/admissions.html', admissions=pagination.items, pagination=pagination, selected_status=status)

@wards_bp.route('/admissions/create', methods=['GET', 'POST'])
@login_required
def create_admission():
    form = AdmissionForm()
    patients = Patient.query.filter_by(is_deleted=False, status='Active').all()
    doctors = Doctor.query.filter_by(is_deleted=False, status='Active').all()
    available_beds = Bed.query.filter_by(is_deleted=False, status='Active', bed_status='Available').all()

    form.patient_id.choices = [(p.id, f"{p.patient_code} - {p.full_name}") for p in patients]
    form.doctor_id.choices = [(d.id, d.full_name) for d in doctors]
    form.bed_id.choices = [(b.id, f"{b.bed_number} - {b.room.ward.ward_name} ({b.room.room_number})") for b in available_beds]

    if request.method == 'GET' and not form.admission_number.data:
        count = Admission.query.count() + 1
        form.admission_number.data = f'ADM-{datetime.utcnow().year}-{count:04d}'

    if form.validate_on_submit():
        bed = Bed.query.get(form.bed_id.data)
        if not bed or bed.bed_status != 'Available':
            flash('The selected bed is no longer available.', 'danger')
            return render_template('wards/admission_form.html', form=form, title='Inpatient Admission')

        admission = Admission(
            admission_number=form.admission_number.data.strip(),
            patient_id=form.patient_id.data,
            doctor_id=form.doctor_id.data,
            admission_date=datetime.utcnow(),
            admission_type=form.admission_type.data,
            reason_for_admission=form.reason_for_admission.data.strip(),
            admission_status='Admitted',
            created_by_id=current_user.id
        )
        db.session.add(admission)
        db.session.flush()

        # Allocate bed
        allocation = BedAllocation(
            admission_id=admission.id,
            bed_id=bed.id,
            allocated_from=datetime.utcnow(),
            allocation_notes='Initial admission bed assignment',
            created_by_id=current_user.id
        )
        bed.bed_status = 'Occupied'
        db.session.add(allocation)
        db.session.commit()

        log_audit('CREATE', 'admissions', admission.id, f'Admitted patient #{admission.patient_id} to bed {bed.bed_number}')
        flash(f'Patient successfully admitted ({admission.admission_number}). Allocated to bed {bed.bed_number}.', 'success')
        return redirect(url_for('wards.view_admission', id=admission.id))

    return render_template('wards/admission_form.html', form=form, title='Inpatient Admission')

@wards_bp.route('/admissions/<int:id>')
@login_required
def view_admission(id):
    admission = Admission.query.get_or_404(id)
    alloc_form = BedAllocationForm()
    available_beds = Bed.query.filter_by(is_deleted=False, status='Active', bed_status='Available').all()
    alloc_form.bed_id.choices = [(b.id, f"{b.bed_number} ({b.room.ward.ward_name})") for b in available_beds]
    discharge_form = DischargeForm()
    return render_template('wards/admission_view.html', admission=admission, alloc_form=alloc_form, discharge_form=discharge_form)

@wards_bp.route('/admissions/<int:id>/transfer-bed', methods=['POST'])
@login_required
def transfer_bed(id):
    admission = Admission.query.get_or_404(id)
    form = BedAllocationForm()
    available_beds = Bed.query.filter_by(is_deleted=False, status='Active', bed_status='Available').all()
    form.bed_id.choices = [(b.id, b.bed_number) for b in available_beds]

    if form.validate_on_submit():
        new_bed = Bed.query.get(form.bed_id.data)
        if new_bed and new_bed.bed_status == 'Available':
            # Close active allocation
            active_alloc = BedAllocation.query.filter_by(admission_id=admission.id, allocated_to=None).first()
            if active_alloc:
                active_alloc.allocated_to = datetime.utcnow()
                active_alloc.bed.bed_status = 'Available'

            new_alloc = BedAllocation(
                admission_id=admission.id,
                bed_id=new_bed.id,
                allocated_from=datetime.utcnow(),
                allocation_notes=form.allocation_notes.data.strip() if form.allocation_notes.data else 'Transferred',
                created_by_id=current_user.id
            )
            new_bed.bed_status = 'Occupied'
            db.session.add(new_alloc)
            db.session.commit()
            log_audit('UPDATE', 'bed_allocations', new_alloc.id, f'Transferred patient in adm #{admission.id} to bed {new_bed.bed_number}')
            flash(f'Patient successfully transferred to bed {new_bed.bed_number}.', 'success')
        else:
            flash('Target bed is unavailable.', 'danger')
    return redirect(url_for('wards.view_admission', id=admission.id))

@wards_bp.route('/admissions/<int:id>/discharge', methods=['POST'])
@login_required
def process_discharge(id):
    admission = Admission.query.get_or_404(id)
    form = DischargeForm()

    if form.validate_on_submit():
        # Release bed
        active_alloc = BedAllocation.query.filter_by(admission_id=admission.id, allocated_to=None).first()
        if active_alloc:
            active_alloc.allocated_to = datetime.utcnow()
            active_alloc.bed.bed_status = 'Available'

        discharge = Discharge(
            admission_id=admission.id,
            discharge_date=datetime.utcnow(),
            discharge_type=form.discharge_type.data,
            discharge_summary=form.discharge_summary.data.strip(),
            follow_up_instructions=form.follow_up_instructions.data.strip() if form.follow_up_instructions.data else None,
            follow_up_date=form.follow_up_date.data,
            created_by_id=current_user.id
        )
        admission.admission_status = 'Discharged'
        admission.updated_by_id = current_user.id
        db.session.add(discharge)
        db.session.commit()

        log_audit('CREATE', 'discharges', discharge.id, f'Discharged admission #{admission.id}')
        flash(f'Patient discharged successfully ({discharge.discharge_type}). Bed released.', 'success')
    else:
        flash('Error processing discharge. Summary is mandatory.', 'danger')

    return redirect(url_for('wards.view_admission', id=admission.id))

@wards_bp.route('/admissions/<int:id>/delete', methods=['POST'])
@login_required
def delete_admission(id):
    admission = Admission.query.get_or_404(id)
    admission.soft_delete(user_id=current_user.id)
    log_audit('SOFT_DELETE', 'admissions', admission.id, f'Soft-deleted admission {admission.admission_number}')
    flash(f'Admission {admission.admission_number} soft-deleted.', 'info')
    return redirect(url_for('wards.admissions'))
