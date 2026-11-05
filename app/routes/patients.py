from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.patients import (
    Patient, PatientContact, PatientAddress, EmergencyContact,
    Allergy, PatientAllergy, MedicalRecord, Diagnosis
)
from app.forms.patient_forms import (
    PatientForm, PatientContactForm, PatientAddressForm,
    EmergencyContactForm, AllergyForm, PatientAllergyForm, MedicalRecordForm, DiagnosisForm
)
from app.services.audit_service import log_audit
from datetime import datetime

patients_bp = Blueprint('patients', __name__, url_prefix='/patients')

@patients_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '').strip()
    blood_group = request.args.get('blood_group', '').strip()
    page = request.args.get('page', 1, type=int)
    
    query = Patient.query.filter_by(is_deleted=False)
    
    if search:
        query = query.filter(
            (Patient.patient_code.ilike(f'%{search}%')) |
            (Patient.first_name.ilike(f'%{search}%')) |
            (Patient.last_name.ilike(f'%{search}%'))
        )
    if blood_group:
        query = query.filter_by(blood_group=blood_group)
        
    pagination = query.order_by(Patient.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    patients = pagination.items

    return render_template('patients/index.html', patients=patients, pagination=pagination, search=search, blood_group=blood_group)

@patients_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = PatientForm()
    if request.method == 'GET' and not form.patient_code.data:
        # Auto-suggest code
        count = Patient.query.count() + 1
        form.patient_code.data = f'PAT-{datetime.utcnow().year}-{count:04d}'

    if form.validate_on_submit():
        existing = Patient.query.filter_by(patient_code=form.patient_code.data.strip()).first()
        if existing:
            flash(f'Patient Code {form.patient_code.data} already exists.', 'warning')
            return render_template('patients/form.html', form=form, title='Register New Patient')

        patient = Patient(
            patient_code=form.patient_code.data.strip(),
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            date_of_birth=form.date_of_birth.data,
            gender=form.gender.data,
            blood_group=form.blood_group.data if form.blood_group.data else None,
            marital_status=form.marital_status.data if form.marital_status.data else None,
            occupation=form.occupation.data.strip() if form.occupation.data else None,
            status=form.status.data,
            created_by_id=current_user.id
        )
        db.session.add(patient)
        db.session.commit()
        
        log_audit('CREATE', 'patients', patient.id, f'Registered patient {patient.full_name} ({patient.patient_code})')
        flash(f'Patient {patient.full_name} registered successfully!', 'success')
        return redirect(url_for('patients.view', id=patient.id))

    return render_template('patients/form.html', form=form, title='Register New Patient')

@patients_bp.route('/<int:id>')
@login_required
def view(id):
    patient = Patient.query.get_or_404(id)
    if patient.is_deleted:
        flash('This patient record has been soft-deleted.', 'warning')
    available_allergies = Allergy.query.filter_by(is_deleted=False).all()
    return render_template('patients/view.html', patient=patient, available_allergies=available_allergies)

@patients_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    patient = Patient.query.get_or_404(id)
    form = PatientForm(obj=patient)

    if form.validate_on_submit():
        patient.patient_code = form.patient_code.data.strip()
        patient.first_name = form.first_name.data.strip()
        patient.last_name = form.last_name.data.strip()
        patient.date_of_birth = form.date_of_birth.data
        patient.gender = form.gender.data
        patient.blood_group = form.blood_group.data if form.blood_group.data else None
        patient.marital_status = form.marital_status.data if form.marital_status.data else None
        patient.occupation = form.occupation.data.strip() if form.occupation.data else None
        patient.status = form.status.data
        patient.updated_by_id = current_user.id
        
        db.session.commit()
        log_audit('UPDATE', 'patients', patient.id, f'Updated demographic details for {patient.full_name}')
        flash('Patient record updated successfully!', 'success')
        return redirect(url_for('patients.view', id=patient.id))

    return render_template('patients/form.html', form=form, title=f'Edit Patient: {patient.full_name}', patient=patient)

@patients_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    patient = Patient.query.get_or_404(id)
    patient.soft_delete(user_id=current_user.id)
    log_audit('SOFT_DELETE', 'patients', patient.id, f'Soft-deleted patient {patient.full_name}')
    flash(f'Patient {patient.full_name} moved to Recycle Bin (Soft Deleted).', 'info')
    return redirect(url_for('patients.index'))

@patients_bp.route('/<int:id>/toggle-status', methods=['POST'])
@login_required
def toggle_status(id):
    patient = Patient.query.get_or_404(id)
    patient.toggle_status()
    patient.updated_by_id = current_user.id
    db.session.commit()
    log_audit('UPDATE', 'patients', patient.id, f'Toggled patient status to {patient.status}')
    flash(f'Patient status updated to {patient.status}.', 'success')
    return redirect(request.referrer or url_for('patients.view', id=patient.id))

# Sub-record: Add Contact
@patients_bp.route('/<int:id>/add-contact', methods=['POST'])
@login_required
def add_contact(id):
    patient = Patient.query.get_or_404(id)
    form = PatientContactForm()
    if form.validate_on_submit():
        contact = PatientContact(
            patient_id=patient.id,
            phone_primary=form.phone_primary.data.strip(),
            phone_secondary=form.phone_secondary.data.strip() if form.phone_secondary.data else None,
            email=form.email.data.strip() if form.email.data else None,
            created_by_id=current_user.id
        )
        db.session.add(contact)
        db.session.commit()
        log_audit('CREATE', 'patient_contacts', contact.id, f'Added contact for patient #{patient.id}')
        flash('Contact details added successfully.', 'success')
    else:
        flash('Error adding contact. Please verify phone number.', 'danger')
    return redirect(url_for('patients.view', id=patient.id))

# Sub-record: Add Address
@patients_bp.route('/<int:id>/add-address', methods=['POST'])
@login_required
def add_address(id):
    patient = Patient.query.get_or_404(id)
    form = PatientAddressForm()
    if form.validate_on_submit():
        address = PatientAddress(
            patient_id=patient.id,
            address_type=form.address_type.data,
            street_address=form.street_address.data.strip(),
            city=form.city.data.strip(),
            state=form.state.data.strip() if form.state.data else None,
            postal_code=form.postal_code.data.strip() if form.postal_code.data else None,
            country=form.country.data.strip(),
            created_by_id=current_user.id
        )
        db.session.add(address)
        db.session.commit()
        log_audit('CREATE', 'patient_addresses', address.id, f'Added address for patient #{patient.id}')
        flash('Address added successfully.', 'success')
    else:
        flash('Error adding address. Please fill all required fields.', 'danger')
    return redirect(url_for('patients.view', id=patient.id))

# Sub-record: Add Emergency Contact
@patients_bp.route('/<int:id>/add-emergency-contact', methods=['POST'])
@login_required
def add_emergency_contact(id):
    patient = Patient.query.get_or_404(id)
    form = EmergencyContactForm()
    if form.validate_on_submit():
        ec = EmergencyContact(
            patient_id=patient.id,
            contact_name=form.contact_name.data.strip(),
            relationship=form.relationship.data.strip(),
            phone_number=form.phone_number.data.strip(),
            alternate_phone=form.alternate_phone.data.strip() if form.alternate_phone.data else None,
            address=form.address.data.strip() if form.address.data else None,
            created_by_id=current_user.id
        )
        db.session.add(ec)
        db.session.commit()
        log_audit('CREATE', 'emergency_contacts', ec.id, f'Added emergency contact for patient #{patient.id}')
        flash('Emergency contact recorded successfully.', 'success')
    else:
        flash('Error adding emergency contact.', 'danger')
    return redirect(url_for('patients.view', id=patient.id))

# Sub-record: Add Medical Record
@patients_bp.route('/<int:id>/add-medical-record', methods=['POST'])
@login_required
def add_medical_record(id):
    patient = Patient.query.get_or_404(id)
    form = MedicalRecordForm()
    if form.validate_on_submit():
        mr = MedicalRecord(
            patient_id=patient.id,
            record_date=datetime.utcnow(),
            chief_complaint=form.chief_complaint.data.strip(),
            history_of_present_illness=form.history_of_present_illness.data.strip() if form.history_of_present_illness.data else None,
            past_medical_history=form.past_medical_history.data.strip() if form.past_medical_history.data else None,
            family_history=form.family_history.data.strip() if form.family_history.data else None,
            social_history=form.social_history.data.strip() if form.social_history.data else None,
            notes=form.notes.data.strip() if form.notes.data else None,
            created_by_id=current_user.id
        )
        db.session.add(mr)
        db.session.commit()
        log_audit('CREATE', 'medical_records', mr.id, f'Added medical record entry for patient #{patient.id}')
        flash('Medical record entry saved successfully.', 'success')
    else:
        flash('Error saving medical record. Chief complaint is required.', 'danger')
    return redirect(url_for('patients.view', id=patient.id))

# Sub-record: Add Allergy
@patients_bp.route('/<int:id>/add-allergy', methods=['POST'])
@login_required
def add_allergy(id):
    patient = Patient.query.get_or_404(id)
    allergy_id = request.form.get('allergy_id', type=int)
    reaction = request.form.get('reaction_description', '').strip()
    notes = request.form.get('notes', '').strip()

    if allergy_id:
        pa = PatientAllergy(
            patient_id=patient.id,
            allergy_id=allergy_id,
            diagnosed_date=datetime.utcnow().date(),
            reaction_description=reaction or None,
            notes=notes or None,
            created_by_id=current_user.id
        )
        db.session.add(pa)
        db.session.commit()
        log_audit('CREATE', 'patient_allergies', pa.id, f'Recorded allergy for patient #{patient.id}')
        flash('Allergy added to patient profile.', 'success')
    else:
        flash('Please select a valid allergen.', 'warning')
    return redirect(url_for('patients.view', id=patient.id))

# Master Allergies Catalog View & Create
@patients_bp.route('/allergies', methods=['GET', 'POST'])
@login_required
def allergies():
    form = AllergyForm()
    if form.validate_on_submit():
        existing = Allergy.query.filter_by(allergen_name=form.allergen_name.data.strip()).first()
        if existing:
            flash('An allergen with that name already exists.', 'warning')
        else:
            al = Allergy(
                allergen_name=form.allergen_name.data.strip(),
                allergy_type=form.allergy_type.data,
                severity=form.severity.data,
                common_symptoms=form.common_symptoms.data.strip() if form.common_symptoms.data else None,
                created_by_id=current_user.id
            )
            db.session.add(al)
            db.session.commit()
            log_audit('CREATE', 'allergies', al.id, f'Created master allergy {al.allergen_name}')
            flash(f'Allergen {al.allergen_name} added to master catalog.', 'success')
            return redirect(url_for('patients.allergies'))

    allergies_list = Allergy.query.filter_by(is_deleted=False).order_by(Allergy.allergen_name).all()
    return render_template('patients/allergies.html', form=form, allergies=allergies_list)

# Master Diagnoses Catalog View & Create
@patients_bp.route('/diagnoses', methods=['GET', 'POST'])
@login_required
def diagnoses():
    form = DiagnosisForm()
    if form.validate_on_submit():
        existing = Diagnosis.query.filter_by(icd_code=form.icd_code.data.strip().upper()).first()
        if existing:
            flash(f'Diagnosis with ICD code {form.icd_code.data} already exists.', 'warning')
        else:
            diag = Diagnosis(
                icd_code=form.icd_code.data.strip().upper(),
                diagnosis_name=form.diagnosis_name.data.strip(),
                category=form.category.data.strip() if form.category.data else None,
                description=form.description.data.strip() if form.description.data else None,
                is_chronic=form.is_chronic.data,
                created_by_id=current_user.id
            )
            db.session.add(diag)
            db.session.commit()
            log_audit('CREATE', 'diagnoses', diag.id, f'Created diagnosis {diag.icd_code} - {diag.diagnosis_name}')
            flash(f'Diagnosis {diag.icd_code} saved to ICD catalog.', 'success')
            return redirect(url_for('patients.diagnoses'))

    diagnoses_list = Diagnosis.query.filter_by(is_deleted=False).order_by(Diagnosis.icd_code).all()
    return render_template('patients/diagnoses.html', form=form, diagnoses=diagnoses_list)
