from datetime import datetime, date, time, timedelta
from app.extensions import db
from app.models import (
    Role, User, UserProfile, LoginHistory, AuditLog,
    Patient, PatientContact, PatientAddress, EmergencyContact,
    Allergy, PatientAllergy, MedicalRecord, Diagnosis, VisitDiagnosis,
    Department, Doctor, DoctorSpecialization, DoctorDepartment,
    Nurse, Staff, Shift, StaffAttendance,
    Appointment, AppointmentStatusHistory, QueueToken, Visit,
    MedicineCategory, Medicine, Prescription, PrescriptionItem,
    Supplier, PurchaseOrder, PurchaseOrderItem, MedicineBatch,
    PharmacySale, PharmacySaleItem,
    LabTest, LabOrder, LabOrderItem, LabResult,
    Ward, Room, Bed, Admission, BedAllocation, Discharge,
    InsuranceProvider, PatientInsurance, Invoice, InvoiceItem, Payment,
    OperationTheatre, Surgery, SurgerySchedule, Ambulance,
    Feedback
)

def seed_database():
    """Populate database with rich, realistic hospital data for all 56 tables."""
    # Check if already seeded
    if Role.query.first():
        print("Database already seeded.")
        return

    print("Seeding Hospital Management System database (56 tables)...")

    # -------------------------------------------------------------
    # 1. Roles
    # -------------------------------------------------------------
    roles_data = [
        ('Admin', 'Complete hospital system administration and oversight'),
        ('Doctor', 'Clinical consultations, prescriptions, and medical records'),
        ('Receptionist', 'Front-desk operations, appointments, admissions, queue'),
        ('Nurse', 'Inpatient care, vitals monitoring, and ward management'),
        ('Pharmacist', 'Medicine inventory, dispensing, and purchase orders'),
        ('Laboratory Technician', 'Diagnostic tests, specimens, and laboratory results')
    ]
    roles_dict = {}
    for name, desc in roles_data:
        role = Role(name=name, description=desc)
        db.session.add(role)
        roles_dict[name] = role
    db.session.flush()

    # -------------------------------------------------------------
    # 2. Users & User Profiles
    # -------------------------------------------------------------
    users_data = [
        ('admin', 'admin@hospital.com', 'Admin@123', 'Admin', 'Chief', 'Administrator', '+92 300 1112233', '10001-ADMIN', 'System Administrator Office'),
        ('dr_sarah', 'sarah.ahmed@hospital.com', 'Doctor@123', 'Doctor', 'Sarah', 'Ahmed', '+92 301 2233445', '10002-DOC-SA', 'Consultant Cardiologist'),
        ('dr_tariq', 'tariq.mahmood@hospital.com', 'Doctor@123', 'Doctor', 'Tariq', 'Mahmood', '+92 302 3344556', '10003-DOC-TM', 'Consultant Neurologist'),
        ('dr_ayesha', 'ayesha.khan@hospital.com', 'Doctor@123', 'Doctor', 'Ayesha', 'Khan', '+92 303 4455667', '10004-DOC-AK', 'Consultant Pediatrician'),
        ('receptionist', 'reception@hospital.com', 'Reception@123', 'Receptionist', 'Usman', 'Tariq', '+92 304 5566778', '10005-REC', 'Lead OPD Receptionist'),
        ('nurse_fatima', 'nurse.fatima@hospital.com', 'Nurse@123', 'Nurse', 'Fatima', 'Noor', '+92 305 6677889', '10006-NUR', 'Head Inpatient Nurse'),
        ('pharmacist_ali', 'pharma@hospital.com', 'Pharma@123', 'Pharmacist', 'Ali', 'Raza', '+92 306 7788990', '10007-PHARM', 'Chief Hospital Pharmacist'),
        ('labtech_sana', 'lab@hospital.com', 'Lab@123', 'Laboratory Technician', 'Sana', 'Javed', '+92 307 8899001', '10008-LAB', 'Senior Pathology Technician')
    ]
    users_dict = {}
    for username, email, pwd, role_name, fname, lname, phone, nid, bio in users_data:
        user = User(
            username=username,
            email=email,
            role_id=roles_dict[role_name].id,
            is_account_active=True
        )
        user.set_password(pwd)
        db.session.add(user)
        db.session.flush()
        
        profile = UserProfile(
            user_id=user.id,
            first_name=fname,
            last_name=lname,
            phone=phone,
            national_id=nid,
            bio=bio,
            address='Hospital Staff Quarters, Medical Complex Road'
        )
        db.session.add(profile)
        users_dict[username] = user
    db.session.flush()

    admin_user = users_dict['admin']

    # -------------------------------------------------------------
    # 4. Login History & 5. Audit Logs
    # -------------------------------------------------------------
    for user in users_dict.values():
        hist = LoginHistory(
            user_id=user.id,
            ip_address='127.0.0.1',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0',
            login_time=datetime.utcnow() - timedelta(hours=2),
            status_result='Success'
        )
        db.session.add(hist)
        
        audit = AuditLog(
            user_id=admin_user.id,
            action='SEED_INITIALIZE',
            table_name='users',
            record_id=user.id,
            details=f'Initial seed creation for user {user.username}',
            timestamp=datetime.utcnow()
        )
        db.session.add(audit)
    db.session.flush()

    # -------------------------------------------------------------
    # 15. Departments
    # -------------------------------------------------------------
    departments_data = [
        ('Cardiology', 'CARD', 'Comprehensive cardiovascular medicine and interventional cardiac care', '2nd Floor, Wing A'),
        ('Neurology', 'NEUR', 'Advanced diagnostic and clinical management of neurological disorders', '3rd Floor, Wing B'),
        ('Pediatrics', 'PED', 'Child health, neonatal care, and adolescent general medicine', '1st Floor, Wing C'),
        ('Orthopedics', 'ORTHO', 'Musculoskeletal surgery, trauma treatment, and rehabilitation', '2nd Floor, Wing B'),
        ('General Surgery', 'SURG', 'Elective, minimally invasive, and emergency general surgery', '4th Floor, Surgical Complex'),
        ('Emergency Medicine', 'ER', '24/7 Level-1 trauma and acute critical resuscitation services', 'Ground Floor, North Gate'),
        ('Pathology & Lab', 'PATH', 'Automated diagnostic pathology, microbiology, and blood banking', 'Basement 1, Diagnostic Wing')
    ]
    dept_dict = {}
    for name, code, desc, loc in departments_data:
        dept = Department(name=name, code=code, description=desc, floor_location=loc, created_by_id=admin_user.id)
        db.session.add(dept)
        dept_dict[code] = dept
        dept_dict[name] = dept
    db.session.flush()

    # -------------------------------------------------------------
    # 16. Doctors, 17. Specializations, 18. Doctor Departments
    # -------------------------------------------------------------
    doctors_seed = [
        ('dr_sarah', 'DOC-2025-001', 'Sarah', 'Ahmed', 'PMC-45920-A', 'MBBS, FCPS (Cardiology), FACC', 12, 2500.0, '+92 301 2233445', 'sarah.ahmed@hospital.com', 'Cardiology', [('Interventional Cardiology', 'College of Physicians', 2016)]),
        ('dr_tariq', 'DOC-2025-002', 'Tariq', 'Mahmood', 'PMC-38810-B', 'MBBS, MRCP (UK), FCPS (Neurology)', 15, 3000.0, '+92 302 3344556', 'tariq.mahmood@hospital.com', 'Neurology', [('Clinical Neurophysiology', 'Royal College of Physicians', 2014)]),
        ('dr_ayesha', 'DOC-2025-003', 'Ayesha', 'Khan', 'PMC-51203-C', 'MBBS, DCH, FCPS (Pediatrics)', 9, 2000.0, '+92 303 4455667', 'ayesha.khan@hospital.com', 'Pediatrics', [('Pediatric Intensive Care', 'CPS Pakistan', 2018)])
    ]
    doctor_objs = []
    for uname, code, fn, ln, lic, qual, exp, fee, phone, email, dept_code, specs in doctors_seed:
        user_rec = users_dict.get(uname)
        doc = Doctor(
            user_id=user_rec.id if user_rec else None,
            doctor_code=code,
            first_name=fn,
            last_name=ln,
            license_number=lic,
            qualification=qual,
            experience_years=exp,
            consultation_fee=fee,
            phone=phone,
            email=email,
            created_by_id=admin_user.id
        )
        db.session.add(doc)
        db.session.flush()
        doctor_objs.append(doc)
        
        # 18. DoctorDepartment
        doc_dept = DoctorDepartment(
            doctor_id=doc.id,
            department_id=dept_dict[dept_code].id,
            is_primary_dept=True,
            created_by_id=admin_user.id
        )
        db.session.add(doc_dept)

        # 17. Specializations
        for s_name, board, yr in specs:
            doc_spec = DoctorSpecialization(
                doctor_id=doc.id,
                specialization_name=s_name,
                certification_board=board,
                year_obtained=yr,
                created_by_id=admin_user.id
            )
            db.session.add(doc_spec)
    db.session.flush()

    # -------------------------------------------------------------
    # 19. Nurses & 20. Staff & 21. Shifts & 22. Attendance
    # -------------------------------------------------------------
    shifts_data = [
        ('Morning Shift', time(8, 0), time(16, 0), 'Daytime standard clinical duties'),
        ('Evening Shift', time(16, 0), time(0, 0), 'Afternoon & evening clinical coverage'),
        ('Night Emergency', time(0, 0), time(8, 0), 'Overnight intensive monitoring and trauma')
    ]
    shift_objs = []
    for sname, st, et, sdesc in shifts_data:
        sh = Shift(name=sname, start_time=st, end_time=et, description=sdesc, created_by_id=admin_user.id)
        db.session.add(sh)
        shift_objs.append(sh)
    db.session.flush()

    nurse_user = users_dict['nurse_fatima']
    nurse_fatima = Nurse(
        user_id=nurse_user.id,
        nurse_code='NUR-2025-001',
        first_name='Fatima',
        last_name='Noor',
        department_id=dept_dict['ER'].id,
        license_number='PNC-88219-N',
        qualification='B.Sc Nursing, Critical Care Certified',
        phone='+92 305 6677889',
        email='nurse.fatima@hospital.com',
        created_by_id=admin_user.id
    )
    db.session.add(nurse_fatima)
    db.session.flush()

    rec_user = users_dict['receptionist']
    staff_usman = Staff(
        user_id=rec_user.id,
        staff_code='STF-2025-001',
        first_name='Usman',
        last_name='Tariq',
        role_title='Lead OPD Receptionist',
        department_id=dept_dict['ER'].id,
        phone='+92 304 5566778',
        email='reception@hospital.com',
        hire_date=date(2022, 5, 10),
        created_by_id=admin_user.id
    )
    db.session.add(staff_usman)
    db.session.flush()

    # 22. Staff Attendance
    att_doc = StaffAttendance(doctor_id=doctor_objs[0].id, shift_id=shift_objs[0].id, attendance_date=date.today(), check_in_time=time(7, 55), attendance_status='Present', created_by_id=admin_user.id)
    att_nur = StaffAttendance(nurse_id=nurse_fatima.id, shift_id=shift_objs[0].id, attendance_date=date.today(), check_in_time=time(8, 0), attendance_status='Present', created_by_id=admin_user.id)
    att_stf = StaffAttendance(staff_id=staff_usman.id, shift_id=shift_objs[0].id, attendance_date=date.today(), check_in_time=time(7, 50), attendance_status='Present', created_by_id=admin_user.id)
    db.session.add_all([att_doc, att_nur, att_stf])
    db.session.flush()

    # -------------------------------------------------------------
    # 10. Allergies Catalog
    # -------------------------------------------------------------
    allergies_catalog = [
        ('Penicillin', 'Drug', 'Severe', 'Anaphylaxis, urticaria, bronchospasm'),
        ('Aspirin / NSAIDs', 'Drug', 'Moderate', 'Facial swelling, asthma exacerbation, hives'),
        ('Sulfa Antibiotics', 'Drug', 'Severe', 'Severe cutaneous adverse reactions, rash'),
        ('Peanuts', 'Food', 'Severe', 'Throat constriction, hypovolemic shock'),
        ('Latex', 'Environmental', 'Mild', 'Contact dermatitis, erythema'),
        ('Dust Mites', 'Environmental', 'Mild', 'Allergic rhinitis, sneezing, watery eyes')
    ]
    allergy_objs = []
    for aname, atype, asev, asymp in allergies_catalog:
        al = Allergy(allergen_name=aname, allergy_type=atype, severity=asev, common_symptoms=asymp, created_by_id=admin_user.id)
        db.session.add(al)
        allergy_objs.append(al)
    db.session.flush()

    # -------------------------------------------------------------
    # 13. Diagnoses Catalog (ICD-10)
    # -------------------------------------------------------------
    diagnoses_catalog = [
        ('I10', 'Essential (primary) hypertension', 'Cardiovascular', 'Systemic chronic arterial blood pressure elevation', True),
        ('E11.9', 'Type 2 diabetes mellitus without complications', 'Endocrine', 'Chronic metabolic disorder characterized by hyperglycemia', True),
        ('J45.909', 'Unspecified asthma, uncomplicated', 'Respiratory', 'Chronic airway inflammation with bronchial hyperresponsiveness', True),
        ('K21.9', 'Gastro-esophageal reflux disease without esophagitis', 'Gastrointestinal', 'Acid regurgitation, retrosternal burning discomfort', False),
        ('J06.9', 'Acute upper respiratory infection, unspecified', 'Infectious', 'Common acute viral rhinitis, pharyngitis', False),
        ('M54.5', 'Low back pain, unspecified', 'Musculoskeletal', 'Acute or chronic lumbago pain and muscle spasm', False)
    ]
    diag_objs = []
    for icd, dname, dcat, ddesc, dchron in diagnoses_catalog:
        d = Diagnosis(icd_code=icd, diagnosis_name=dname, category=dcat, description=ddesc, is_chronic=dchron, created_by_id=admin_user.id)
        db.session.add(d)
        diag_objs.append(d)
    db.session.flush()

    # -------------------------------------------------------------
    # 6. Patients, 7. Contacts, 8. Addresses, 9. Emergency Contacts, 11. Patient Allergies, 12. Medical Records
    # -------------------------------------------------------------
    patients_seed = [
        ('PAT-2025-001', 'Muhammad', 'Usman', date(1985, 4, 12), 'Male', 'O+', 'Married', 'Software Engineer', '+92 300 9876541', 'usman@gmail.com', 'House 42, Street 8, F-10/2', 'Islamabad', 'ICT', '44000', 'Sana Usman', 'Spouse', '+92 321 1122334', 'Occasional chest tightness and palpitations'),
        ('PAT-2025-002', 'Fatima', 'Bibi', date(1992, 8, 24), 'Female', 'B+', 'Married', 'Teacher', '+92 301 8765432', 'fatima.b@gmail.com', 'Flat 3B, Clifton Garden', 'Karachi', 'Sindh', '75600', 'Kamran Ali', 'Husband', '+92 333 4455667', 'Recurrent migraine attacks with photophobia'),
        ('PAT-2025-003', 'Ali', 'Imran', date(2018, 11, 5), 'Male', 'A+', 'Single', 'Student', '+92 302 7654321', 'imran.parent@gmail.com', 'House 112, Sector C, Bahria Town', 'Rawalpindi', 'Punjab', '46000', 'Imran Nazir', 'Father', '+92 345 5566778', 'High grade fever with persistent dry cough'),
        ('PAT-2025-004', 'Zainab', 'Akhtar', date(1974, 2, 18), 'Female', 'AB+', 'Widowed', 'Homemaker', '+92 303 6543210', 'zainab.akhtar@yahoo.com', 'House 19, Model Town', 'Lahore', 'Punjab', '54000', 'Bilal Akhtar', 'Son', '+92 322 9988776', 'Type 2 Diabetes follow-up and chronic knee pain'),
        ('PAT-2025-005', 'Ahmed', 'Raza', date(1999, 6, 30), 'Male', 'O-', 'Single', 'University Student', '+92 304 5432109', 'ahmed.raza@uni.edu.pk', 'Hostel 4, NUST Campus', 'Islamabad', 'ICT', '44000', 'Raza Ullah', 'Father', '+92 300 8877665', 'Sports knee ligament injury during football match')
    ]
    patient_objs = []
    for code, fn, ln, dob, gender, bg, ms, occ, ph, em, str_addr, city, st, zipc, ec_name, ec_rel, ec_ph, complaint in patients_seed:
        p = Patient(
            patient_code=code,
            first_name=fn,
            last_name=ln,
            date_of_birth=dob,
            gender=gender,
            blood_group=bg,
            marital_status=ms,
            occupation=occ,
            created_by_id=admin_user.id
        )
        db.session.add(p)
        db.session.flush()
        patient_objs.append(p)

        # 7. Contact
        p_contact = PatientContact(patient_id=p.id, phone_primary=ph, email=em, created_by_id=admin_user.id)
        db.session.add(p_contact)

        # 8. Address
        p_addr = PatientAddress(patient_id=p.id, street_address=str_addr, city=city, state=st, postal_code=zipc, country='Pakistan', created_by_id=admin_user.id)
        db.session.add(p_addr)

        # 9. Emergency Contact
        p_em = EmergencyContact(patient_id=p.id, contact_name=ec_name, relationship=ec_rel, phone_number=ec_ph, created_by_id=admin_user.id)
        db.session.add(p_em)

        # 12. Medical Record
        mr = MedicalRecord(
            patient_id=p.id,
            record_date=datetime.utcnow() - timedelta(days=5),
            chief_complaint=complaint,
            history_of_present_illness=f'Patient presented with symptoms ongoing for approximately 1-2 weeks. {complaint}.',
            past_medical_history='No prior history of major surgery or cardiac arrest.',
            family_history='Hypertension and diabetes reported in maternal family history.',
            social_history='Non-smoker, active lifestyle.',
            notes='Patient oriented to time, place and person.',
            created_by_id=admin_user.id
        )
        db.session.add(mr)

    # 11. Patient Allergies
    pa1 = PatientAllergy(patient_id=patient_objs[0].id, allergy_id=allergy_objs[0].id, diagnosed_date=date(2019, 3, 10), reaction_description='Developed rash after oral amoxicillin', created_by_id=admin_user.id)
    pa2 = PatientAllergy(patient_id=patient_objs[3].id, allergy_id=allergy_objs[1].id, diagnosed_date=date(2015, 7, 22), reaction_description='Gastric irritation and facial flushing', created_by_id=admin_user.id)
    db.session.add_all([pa1, pa2])
    db.session.flush()

    # -------------------------------------------------------------
    # 23. Appointments, 24. Status History, 25. Queue Tokens, 26. Visits, 14. Visit Diagnoses
    # -------------------------------------------------------------
    appts_seed = [
        ('APT-2025-001', patient_objs[0], doctor_objs[0], dept_dict['CARD'], date.today(), time(9, 30), 'New Visit', 'Routine cardiology consultation for chest discomfort', 'Completed'),
        ('APT-2025-002', patient_objs[1], doctor_objs[1], dept_dict['NEUR'], date.today(), time(10, 15), 'New Visit', 'Severe headaches and neurological evaluation', 'Confirmed'),
        ('APT-2025-003', patient_objs[2], doctor_objs[2], dept_dict['PED'], date.today(), time(11, 0), 'Routine', 'High fever and pediatric cough checkup', 'Scheduled'),
        ('APT-2025-004', patient_objs[3], doctor_objs[0], dept_dict['CARD'], date.today() + timedelta(days=1), time(14, 0), 'Follow-up', 'Blood pressure regulation follow-up', 'Scheduled'),
        ('APT-2025-005', patient_objs[4], doctor_objs[1], dept_dict['NEUR'], date.today() + timedelta(days=2), time(11, 30), 'New Visit', 'Concussion evaluation and sports injury', 'Scheduled')
    ]
    appt_objs = []
    for code, pat, doc, dep, adate, atime, atype, rsn, st in appts_seed:
        apt = Appointment(
            appointment_number=code,
            patient_id=pat.id,
            doctor_id=doc.id,
            department_id=dep.id,
            appointment_date=adate,
            appointment_time=atime,
            appointment_type=atype,
            reason=rsn,
            current_status=st,
            created_by_id=admin_user.id
        )
        db.session.add(apt)
        db.session.flush()
        appt_objs.append(apt)

        # 24. Appointment Status History
        hist = AppointmentStatusHistory(
            appointment_id=apt.id,
            old_status='Scheduled',
            new_status=st,
            change_reason='Initial appointment confirmation and scheduling',
            changed_at=datetime.utcnow(),
            created_by_id=admin_user.id
        )
        db.session.add(hist)

        # 25. Queue Token
        token = QueueToken(
            appointment_id=apt.id,
            patient_id=pat.id,
            doctor_id=doc.id,
            token_number=len(appt_objs),
            token_date=adate,
            token_status='Completed' if st == 'Completed' else ('In-Consultation' if st == 'Confirmed' else 'Waiting'),
            created_by_id=admin_user.id
        )
        db.session.add(token)

    db.session.flush()

    # 26. Visit for the completed appointment
    v1 = Visit(
        visit_number='VIS-2025-001',
        patient_id=patient_objs[0].id,
        doctor_id=doctor_objs[0].id,
        appointment_id=appt_objs[0].id,
        visit_date=datetime.utcnow() - timedelta(hours=2),
        visit_type='OPD',
        systolic_bp=135,
        diastolic_bp=88,
        heart_rate=78,
        temperature=98.6,
        weight_kg=78.5,
        height_cm=175.0,
        symptoms='Patient reports exertional chest heaviness, mild dyspnea on stair climbing.',
        clinical_notes='Heart sounds S1 S2 normal, no murmurs. Advised baseline ECG and lipid profile.',
        created_by_id=admin_user.id
    )
    db.session.add(v1)
    db.session.flush()

    # 14. Visit Diagnosis
    vd1 = VisitDiagnosis(
        visit_id=v1.id,
        diagnosis_id=diag_objs[0].id, # Essential hypertension
        diagnosis_type='Primary',
        notes='Stage 1 essential hypertension confirmed. Low sodium diet and medication started.',
        created_by_id=admin_user.id
    )
    db.session.add(vd1)
    db.session.flush()

    # -------------------------------------------------------------
    # 30. Medicine Categories & 29. Medicines
    # -------------------------------------------------------------
    med_cats = [
        ('Cardiovascular', 'Drugs affecting heart rate, blood pressure, and vascular tone'),
        ('Antibiotics & Anti-infectives', 'Antimicrobial agents for systemic and local bacterial infections'),
        ('Analgesics & NSAIDs', 'Pain relievers, antipyretics, and anti-inflammatory compounds'),
        ('Endocrine & Diabetes', 'Blood glucose regulators, insulin sensitizers, and hormones'),
        ('Gastrointestinal', 'Proton pump inhibitors, antacids, and antiemetics')
    ]
    med_cat_objs = []
    for cname, cdesc in med_cats:
        mc = MedicineCategory(name=cname, description=cdesc, created_by_id=admin_user.id)
        db.session.add(mc)
        med_cat_objs.append(mc)
    db.session.flush()

    meds_seed = [
        (med_cat_objs[0], 'MED-001', 'Amlodipine 5mg', 'Amlodipine Besylate', 'Tablet', '5mg', 12.0, 100),
        (med_cat_objs[0], 'MED-002', 'Atorvastatin 20mg', 'Atorvastatin Calcium', 'Tablet', '20mg', 25.0, 80),
        (med_cat_objs[1], 'MED-003', 'Augmentin 625mg', 'Co-amoxiclav', 'Tablet', '625mg', 45.0, 50),
        (med_cat_objs[1], 'MED-004', 'Azithromycin 500mg', 'Azithromycin Dihydrate', 'Tablet', '500mg', 55.0, 60),
        (med_cat_objs[2], 'MED-005', 'Panadol 500mg', 'Paracetamol', 'Tablet', '500mg', 5.0, 500),
        (med_cat_objs[2], 'MED-006', 'Brufen 400mg', 'Ibuprofen', 'Tablet', '400mg', 8.0, 200),
        (med_cat_objs[3], 'MED-007', 'Glucophage 500mg', 'Metformin HCl', 'Tablet', '500mg', 10.0, 150),
        (med_cat_objs[4], 'MED-008', 'Risek 20mg', 'Omeprazole', 'Capsule', '20mg', 28.0, 120)
    ]
    med_objs = []
    for cat, mcode, mname, gen, form, strg, price, reorder in meds_seed:
        m = Medicine(
            category_id=cat.id,
            medicine_code=mcode,
            name=mname,
            generic_name=gen,
            dosage_form=form,
            strength=strg,
            unit_price=price,
            reorder_level=reorder,
            created_by_id=admin_user.id
        )
        db.session.add(m)
        med_objs.append(m)
    db.session.flush()

    # -------------------------------------------------------------
    # 31. Suppliers, 32. Purchase Orders, 33. PO Items, 34. Batches
    # -------------------------------------------------------------
    sup1 = Supplier(supplier_name='Medix Pharma Distributors', contact_person='Khurram Shah', phone='+92 51 2233441', email='orders@medixpharma.com', address='Plot 15, I-9 Industrial Area, Islamabad', tax_number='NTN-882190-2', created_by_id=admin_user.id)
    sup2 = Supplier(supplier_name='Shifa Medical Logistics', contact_person='Zahid Munir', phone='+92 42 3556677', email='sales@shifalogistics.com', address='Gulberg III, Main Boulevard, Lahore', tax_number='NTN-773412-9', created_by_id=admin_user.id)
    db.session.add_all([sup1, sup2])
    db.session.flush()

    po1 = PurchaseOrder(po_number='PO-2025-001', supplier_id=sup1.id, order_date=datetime.utcnow() - timedelta(days=20), expected_delivery_date=date.today() - timedelta(days=15), total_amount=15500.0, order_status='Received', created_by_id=admin_user.id)
    db.session.add(po1)
    db.session.flush()

    poi1 = PurchaseOrderItem(purchase_order_id=po1.id, medicine_id=med_objs[0].id, quantity_ordered=500, unit_price=8.0, total_cost=4000.0, created_by_id=admin_user.id)
    poi2 = PurchaseOrderItem(purchase_order_id=po1.id, medicine_id=med_objs[4].id, quantity_ordered=1500, unit_price=3.0, total_cost=4500.0, created_by_id=admin_user.id)
    poi3 = PurchaseOrderItem(purchase_order_id=po1.id, medicine_id=med_objs[7].id, quantity_ordered=400, unit_price=17.5, total_cost=7000.0, created_by_id=admin_user.id)
    db.session.add_all([poi1, poi2, poi3])
    db.session.flush()

    # 34. Medicine Batches
    b1 = MedicineBatch(medicine_id=med_objs[0].id, purchase_order_id=po1.id, batch_number='AML-24B01', manufacture_date=date(2024, 2, 1), expiry_date=date(2027, 2, 1), quantity_in_stock=480, unit_cost=8.0, sale_price=12.0, created_by_id=admin_user.id)
    b2 = MedicineBatch(medicine_id=med_objs[4].id, purchase_order_id=po1.id, batch_number='PAN-24E09', manufacture_date=date(2024, 5, 15), expiry_date=date(2027, 5, 15), quantity_in_stock=1450, unit_cost=3.0, sale_price=5.0, created_by_id=admin_user.id)
    b3 = MedicineBatch(medicine_id=med_objs[7].id, purchase_order_id=po1.id, batch_number='RSK-24H12', manufacture_date=date(2024, 8, 1), expiry_date=date(2026, 8, 1), quantity_in_stock=380, unit_cost=17.5, sale_price=28.0, created_by_id=admin_user.id)
    db.session.add_all([b1, b2, b3])
    db.session.flush()

    # -------------------------------------------------------------
    # 27. Prescriptions & 28. Prescription Items
    # -------------------------------------------------------------
    rx1 = Prescription(prescription_code='RX-2025-001', visit_id=v1.id, patient_id=patient_objs[0].id, doctor_id=doctor_objs[0].id, prescription_date=datetime.utcnow() - timedelta(hours=1), instructions='Take daily after breakfast. Monitor BP weekly.', validity_days=14, created_by_id=admin_user.id)
    db.session.add(rx1)
    db.session.flush()

    rxi1 = PrescriptionItem(prescription_id=rx1.id, medicine_id=med_objs[0].id, dosage='1 tablet', frequency='Once daily in the morning', duration_days=30, quantity=30, instructions='Take with a full glass of water', created_by_id=admin_user.id)
    rxi2 = PrescriptionItem(prescription_id=rx1.id, medicine_id=med_objs[7].id, dosage='1 capsule', frequency='Once daily before breakfast', duration_days=14, quantity=14, instructions='Take on an empty stomach', created_by_id=admin_user.id)
    db.session.add_all([rxi1, rxi2])
    db.session.flush()

    # -------------------------------------------------------------
    # 35. Pharmacy Sales & 36. Pharmacy Sale Items
    # -------------------------------------------------------------
    sale1 = PharmacySale(invoice_number='PH-INV-001', patient_id=patient_objs[0].id, sale_date=datetime.utcnow() - timedelta(minutes=45), total_amount=752.0, discount_amount=52.0, net_amount=700.0, payment_status='Paid', created_by_id=admin_user.id)
    db.session.add(sale1)
    db.session.flush()

    psi1 = PharmacySaleItem(pharmacy_sale_id=sale1.id, batch_id=b1.id, medicine_id=med_objs[0].id, quantity_sold=30, unit_price=12.0, subtotal=360.0, created_by_id=admin_user.id)
    psi2 = PharmacySaleItem(pharmacy_sale_id=sale1.id, batch_id=b3.id, medicine_id=med_objs[7].id, quantity_sold=14, unit_price=28.0, subtotal=392.0, created_by_id=admin_user.id)
    db.session.add_all([psi1, psi2])
    db.session.flush()

    # -------------------------------------------------------------
    # 37. Lab Tests, 38. Lab Orders, 39. Lab Items, 40. Lab Results
    # -------------------------------------------------------------
    tests_seed = [
        ('CBC-01', 'Complete Blood Count (CBC)', 'Hematology', 650.0, 'Hb: 13.0-17.0 g/dL, TLC: 4-11 x10^3/uL', 'Automated Cell Counter', 'Full hematological profile including differential count'),
        ('FBS-01', 'Fasting Blood Sugar (FBS)', 'Biochemistry', 350.0, '70 - 99 mg/dL', 'mg/dL', 'Enzymatic hexokinase assay after 8-10h fasting'),
        ('LIPID-01', 'Lipid Profile Screen', 'Biochemistry', 1400.0, 'Total Chol: <200, LDL: <100, HDL: >40', 'mg/dL', 'Complete fasting lipid fractions'),
        ('LFT-01', 'Liver Function Tests (LFT)', 'Biochemistry', 1200.0, 'Bilirubin: 0.2-1.2 mg/dL, ALT: 7-56 U/L', 'U/L', 'Comprehensive hepatic enzyme assessment'),
        ('CXR-01', 'Chest X-Ray PA View', 'Radiology', 1000.0, 'Clear lung fields, normal cardiothoracic ratio', 'Digital Radiograph', 'Digital plain radiograph examination of thorax')
    ]
    test_objs = []
    for tcode, tname, tcat, tcost, trange, tuom, tdesc in tests_seed:
        lt = LabTest(test_code=tcode, test_name=tname, category=tcat, cost=tcost, normal_range=trange, unit_of_measure=tuom, description=tdesc, created_by_id=admin_user.id)
        db.session.add(lt)
        test_objs.append(lt)
    db.session.flush()

    lo1 = LabOrder(order_number='LAB-2025-001', visit_id=v1.id, patient_id=patient_objs[0].id, doctor_id=doctor_objs[0].id, order_date=datetime.utcnow() - timedelta(hours=2), priority='Routine', order_status='Completed', created_by_id=admin_user.id)
    db.session.add(lo1)
    db.session.flush()

    loi1 = LabOrderItem(lab_order_id=lo1.id, lab_test_id=test_objs[0].id, item_status='Completed', sample_type='Blood (EDTA)', created_by_id=admin_user.id)
    loi2 = LabOrderItem(lab_order_id=lo1.id, lab_test_id=test_objs[2].id, item_status='Completed', sample_type='Blood (Serum)', created_by_id=admin_user.id)
    db.session.add_all([loi1, loi2])
    db.session.flush()

    res1 = LabResult(lab_order_item_id=loi1.id, technician_id=users_dict['labtech_sana'].id, result_value='Hb: 14.2 g/dL, Platelets: 280,000, TLC: 7,400', reference_range_snapshot='Hb: 13.0-17.0 g/dL', remarks='Normal complete blood counts', is_abnormal=False, created_by_id=admin_user.id)
    res2 = LabResult(lab_order_item_id=loi2.id, technician_id=users_dict['labtech_sana'].id, result_value='Total Cholesterol: 228 mg/dL, LDL: 142 mg/dL, HDL: 44 mg/dL', reference_range_snapshot='Total Chol: <200 mg/dL', remarks='Borderline hypercholesterolemia observed', is_abnormal=True, created_by_id=admin_user.id)
    db.session.add_all([res1, res2])
    db.session.flush()

    # -------------------------------------------------------------
    # 41. Wards, 42. Rooms, 43. Beds, 44. Admissions, 45. Bed Allocations, 46. Discharges
    # -------------------------------------------------------------
    wards_seed = [
        ('Cardiology CCU & Stepdown', 'ICU', 'Mixed', 12, 2),
        ('General Medical Ward (Male)', 'General', 'Male', 20, 1),
        ('General Medical Ward (Female)', 'General', 'Female', 20, 1),
        ('Surgical Post-Op Ward', 'Surgical', 'Mixed', 15, 3)
    ]
    ward_objs = []
    for wname, wtype, wgender, wcap, wflr in wards_seed:
        w = Ward(ward_name=wname, ward_type=wtype, gender_type=wgender, total_capacity=wcap, floor_number=wflr, created_by_id=admin_user.id)
        db.session.add(w)
        ward_objs.append(w)
    db.session.flush()

    # Rooms & Beds
    r1 = Room(ward_id=ward_objs[0].id, room_number='CCU-201', room_type='Deluxe', daily_rate=5000.0, created_by_id=admin_user.id)
    r2 = Room(ward_id=ward_objs[1].id, room_number='GWM-101', room_type='Standard', daily_rate=1500.0, created_by_id=admin_user.id)
    r3 = Room(ward_id=ward_objs[1].id, room_number='GWM-102', room_type='Standard', daily_rate=1500.0, created_by_id=admin_user.id)
    db.session.add_all([r1, r2, r3])
    db.session.flush()

    bed1 = Bed(room_id=r1.id, bed_number='B-201-A', bed_type='ICU Bed', bed_status='Occupied', created_by_id=admin_user.id)
    bed2 = Bed(room_id=r1.id, bed_number='B-201-B', bed_type='ICU Bed', bed_status='Available', created_by_id=admin_user.id)
    bed3 = Bed(room_id=r2.id, bed_number='B-101-1', bed_type='Regular', bed_status='Occupied', created_by_id=admin_user.id)
    bed4 = Bed(room_id=r2.id, bed_number='B-101-2', bed_type='Regular', bed_status='Available', created_by_id=admin_user.id)
    bed5 = Bed(room_id=r3.id, bed_number='B-102-1', bed_type='Regular', bed_status='Available', created_by_id=admin_user.id)
    db.session.add_all([bed1, bed2, bed3, bed4, bed5])
    db.session.flush()

    # 44. Admissions
    adm1 = Admission(
        admission_number='ADM-2025-001',
        patient_id=patient_objs[4].id,
        doctor_id=doctor_objs[0].id,
        admission_date=datetime.utcnow() - timedelta(days=2),
        admission_type='Emergency',
        reason_for_admission='Acute unstable angina observation and cardiac enzymes monitoring',
        admission_status='Admitted',
        created_by_id=admin_user.id
    )
    db.session.add(adm1)
    db.session.flush()

    # 45. Bed Allocation
    balloc1 = BedAllocation(admission_id=adm1.id, bed_id=bed1.id, allocated_from=datetime.utcnow() - timedelta(days=2), allocation_notes='Patient assigned to cardiac monitoring bed', created_by_id=admin_user.id)
    db.session.add(balloc1)
    db.session.flush()

    # An admission that was discharged for testing 46. Discharges
    adm2 = Admission(
        admission_number='ADM-2025-002',
        patient_id=patient_objs[3].id,
        doctor_id=doctor_objs[1].id,
        admission_date=datetime.utcnow() - timedelta(days=6),
        admission_type='Elective',
        reason_for_admission='Severe complicated diabetic ketoacidosis stabilization',
        admission_status='Discharged',
        created_by_id=admin_user.id
    )
    db.session.add(adm2)
    db.session.flush()

    balloc2 = BedAllocation(admission_id=adm2.id, bed_id=bed3.id, allocated_from=datetime.utcnow() - timedelta(days=6), allocated_to=datetime.utcnow() - timedelta(days=1), allocation_notes='Stay completed and discharged', created_by_id=admin_user.id)
    db.session.add(balloc2)

    disch1 = Discharge(
        admission_id=adm2.id,
        discharge_date=datetime.utcnow() - timedelta(days=1),
        discharge_type='Normal',
        discharge_summary='Patient achieved glycemic stability. Ketones negative, electrolyte balance normalized.',
        follow_up_instructions='Strict diabetic diet, insulin as charted, follow up in OPD in 1 week.',
        follow_up_date=date.today() + timedelta(days=6),
        created_by_id=admin_user.id
    )
    db.session.add(disch1)
    db.session.flush()

    # -------------------------------------------------------------
    # 50. Insurance Providers & 51. Patient Insurances
    # -------------------------------------------------------------
    ip1 = InsuranceProvider(provider_name='State Life Health Care', policy_type='Comprehensive', contact_person='Tariq Qureshi', phone='+92 51 9201122', email='claims@statelifehealth.com.pk', claim_address='State Life Tower, Jinnah Avenue, Islamabad', co_pay_percentage=10.0, created_by_id=admin_user.id)
    ip2 = InsuranceProvider(provider_name='Jubilee Life Insurance', policy_type='Corporate', contact_person='Amna Bashir', phone='+92 21 111111582', email='healthcorp@jubileelife.com', claim_address='Jubilee Life Building, I.I. Chundrigar Road, Karachi', co_pay_percentage=15.0, created_by_id=admin_user.id)
    db.session.add_all([ip1, ip2])
    db.session.flush()

    pins1 = PatientInsurance(patient_id=patient_objs[0].id, provider_id=ip1.id, policy_number='SLH-POL-88412', coverage_limit=500000.0, valid_from=date(2025, 1, 1), valid_to=date(2026, 12, 31), is_verified=True, created_by_id=admin_user.id)
    pins2 = PatientInsurance(patient_id=patient_objs[3].id, provider_id=ip2.id, policy_number='JUB-CORP-99201', coverage_limit=1000000.0, valid_from=date(2025, 1, 1), valid_to=date(2026, 12, 31), is_verified=True, created_by_id=admin_user.id)
    db.session.add_all([pins1, pins2])
    db.session.flush()

    # -------------------------------------------------------------
    # 47. Invoices, 48. Invoice Items, 49. Payments
    # -------------------------------------------------------------
    inv1 = Invoice(
        invoice_number='INV-2025-001',
        patient_id=patient_objs[0].id,
        visit_id=v1.id,
        invoice_date=datetime.utcnow() - timedelta(hours=1),
        due_date=date.today() + timedelta(days=7),
        total_amount=4550.0,
        discount_amount=250.0,
        tax_amount=0.0,
        net_amount=4300.0,
        paid_amount=4300.0,
        payment_status='Paid',
        created_by_id=admin_user.id
    )
    db.session.add(inv1)
    db.session.flush()

    ii1 = InvoiceItem(invoice_id=inv1.id, item_description='Cardiology Consultation Fee (Dr. Sarah Ahmed)', service_type='Consultation', unit_price=2500.0, quantity=1, subtotal=2500.0, created_by_id=admin_user.id)
    ii2 = InvoiceItem(invoice_id=inv1.id, item_description='Complete Blood Count (CBC)', service_type='Lab Test', unit_price=650.0, quantity=1, subtotal=650.0, created_by_id=admin_user.id)
    ii3 = InvoiceItem(invoice_id=inv1.id, item_description='Lipid Profile Screen', service_type='Lab Test', unit_price=1400.0, quantity=1, subtotal=1400.0, created_by_id=admin_user.id)
    db.session.add_all([ii1, ii2, ii3])

    pay1 = Payment(
        invoice_id=inv1.id,
        payment_date=datetime.utcnow() - timedelta(minutes=30),
        amount=4300.0,
        payment_method='Credit Card',
        transaction_reference='TXN-CC-9948210',
        notes='Paid in full at OPD accounts counter via POS terminal',
        created_by_id=admin_user.id
    )
    db.session.add(pay1)

    # Inpatient invoice for adm2
    inv2 = Invoice(
        invoice_number='INV-2025-002',
        patient_id=patient_objs[3].id,
        admission_id=adm2.id,
        invoice_date=datetime.utcnow() - timedelta(days=1),
        due_date=date.today() + timedelta(days=14),
        total_amount=22500.0,
        discount_amount=1500.0,
        tax_amount=0.0,
        net_amount=21000.0,
        paid_amount=15000.0,
        payment_status='Partially Paid',
        created_by_id=admin_user.id
    )
    db.session.add(inv2)
    db.session.flush()

    ii4 = InvoiceItem(invoice_id=inv2.id, item_description='Room & Nursing Charges (5 Nights Standard Ward)', service_type='Room Charge', unit_price=1500.0, quantity=5, subtotal=7500.0, created_by_id=admin_user.id)
    ii5 = InvoiceItem(invoice_id=inv2.id, item_description='Physician Inpatient Rounds & Specialist Care', service_type='Consultation', unit_price=10000.0, quantity=1, subtotal=10000.0, created_by_id=admin_user.id)
    ii6 = InvoiceItem(invoice_id=inv2.id, item_description='IV Fluids, Infusions and Laboratory Monitoring', service_type='Medicine', unit_price=5000.0, quantity=1, subtotal=5000.0, created_by_id=admin_user.id)
    db.session.add_all([ii4, ii5, ii6])

    pay2 = Payment(
        invoice_id=inv2.id,
        payment_date=datetime.utcnow() - timedelta(days=1),
        amount=15000.0,
        payment_method='Bank Transfer',
        transaction_reference='FT-RAAST-448190',
        notes='Interbank transfer received. Remaining PKR 6,000 co-pay pending insurance verification.',
        created_by_id=admin_user.id
    )
    db.session.add(pay2)
    db.session.flush()

    # -------------------------------------------------------------
    # 53. Operation Theatres, 52. Surgeries, 54. Surgery Schedules, 55. Ambulances
    # -------------------------------------------------------------
    ot1 = OperationTheatre(ot_number='OT-01', name='Cardiac & Vascular Suite', floor=4, theatre_type='Cardiac', is_equipped=True, maintenance_status='Operational', created_by_id=admin_user.id)
    ot2 = OperationTheatre(ot_number='OT-02', name='General & Laparoscopic OT', floor=4, theatre_type='Major', is_equipped=True, maintenance_status='Operational', created_by_id=admin_user.id)
    ot3 = OperationTheatre(ot_number='OT-03', name='Orthopedic & Trauma Suite', floor=4, theatre_type='Orthopedic', is_equipped=True, maintenance_status='Operational', created_by_id=admin_user.id)
    db.session.add_all([ot1, ot2, ot3])
    db.session.flush()

    surg1 = Surgery(surgery_code='SURG-CARD-01', surgery_name='Coronary Angiography & Stenting', department_id=dept_dict['CARD'].id, estimated_duration_minutes=90, standard_cost=150000.0, description='Percutaneous coronary intervention with drug-eluting stent placement', created_by_id=admin_user.id)
    surg2 = Surgery(surgery_code='SURG-GEN-01', surgery_name='Laparoscopic Cholecystectomy', department_id=dept_dict['SURG'].id, estimated_duration_minutes=60, standard_cost=65000.0, description='Minimally invasive gallbladder removal', created_by_id=admin_user.id)
    surg3 = Surgery(surgery_code='SURG-ORTH-01', surgery_name='Arthroscopic ACL Reconstruction', department_id=dept_dict['ORTHO'].id, estimated_duration_minutes=120, standard_cost=95000.0, description='Anterior cruciate ligament repair using autograft', created_by_id=admin_user.id)
    db.session.add_all([surg1, surg2, surg3])
    db.session.flush()

    ssched1 = SurgerySchedule(
        surgery_id=surg1.id,
        patient_id=patient_objs[0].id,
        lead_surgeon_id=doctor_objs[0].id,
        theatre_id=ot1.id,
        scheduled_start_time=datetime.utcnow() + timedelta(days=3, hours=9),
        scheduled_end_time=datetime.utcnow() + timedelta(days=3, hours=11),
        surgery_status='Scheduled',
        pre_op_notes='Pre-anesthesia checkup cleared. Echocardiogram normal. NPO after midnight.',
        created_by_id=admin_user.id
    )
    db.session.add(ssched1)
    db.session.flush()

    # 55. Ambulances
    amb1 = Ambulance(vehicle_number='ICT-AMB-101', vehicle_model='Toyota Hiace High-Roof ICU', ambulance_type='Advanced Life Support', driver_name='Muhammad Bashir', driver_phone='+92 300 5511223', current_location='Hospital Station Bay 1', operational_status='Available', created_by_id=admin_user.id)
    amb2 = Ambulance(vehicle_number='ICT-AMB-102', vehicle_model='Hyundai H-100 Rescue', ambulance_type='Basic Life Support', driver_name='Sultan Mehmood', driver_phone='+92 301 6622334', current_location='Blue Area Dispatched', operational_status='On Trip', created_by_id=admin_user.id)
    amb3 = Ambulance(vehicle_number='ICT-AMB-103', vehicle_model='Toyota Coaster Patient Transport', ambulance_type='Patient Transport', driver_name='Akbar Khan', driver_phone='+92 302 7733445', current_location='Hospital Garage', operational_status='Under Maintenance', created_by_id=admin_user.id)
    db.session.add_all([amb1, amb2, amb3])
    db.session.flush()

    # -------------------------------------------------------------
    # 56. Feedback
    # -------------------------------------------------------------
    fb1 = Feedback(
        patient_id=patient_objs[0].id,
        visit_id=v1.id,
        department_id=dept_dict['CARD'].id,
        rating=5,
        category='Doctor Care',
        comments='Dr. Sarah Ahmed was extremely professional and thorough in explaining the diagnosis and tests. Highly satisfied!',
        is_anonymous=False,
        resolution_status='Reviewed',
        created_by_id=admin_user.id
    )
    fb2 = Feedback(
        patient_id=patient_objs[1].id,
        department_id=dept_dict['ER'].id,
        rating=4,
        category='Wait Time',
        comments='Staff behavior was very courteous. The queue token system worked well although waiting area seats were full.',
        is_anonymous=False,
        resolution_status='Submitted',
        created_by_id=admin_user.id
    )
    db.session.add_all([fb1, fb2])

    db.session.commit()
    print("Database successfully seeded with comprehensive hospital data across all 56 tables!")
