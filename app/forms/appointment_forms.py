from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, TimeField, TextAreaField, IntegerField, FloatField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange

class AppointmentForm(FlaskForm):
    appointment_number = StringField('Appointment #', validators=[DataRequired(), Length(max=30)])
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    doctor_id = SelectField('Doctor', coerce=int, validators=[DataRequired()])
    department_id = SelectField('Department', coerce=int, validators=[DataRequired()])
    appointment_date = DateField('Appointment Date', validators=[DataRequired()])
    appointment_time = TimeField('Appointment Time', validators=[DataRequired()])
    appointment_type = SelectField('Type', choices=[('New Visit', 'New Visit'), ('Follow-up', 'Follow-up'), ('Emergency', 'Emergency'), ('Routine', 'Routine Checkup')], default='New Visit')
    reason = TextAreaField('Reason / Symptoms', validators=[Optional()])
    current_status = SelectField('Status', choices=[('Scheduled', 'Scheduled'), ('Confirmed', 'Confirmed'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled'), ('No-Show', 'No-Show')], default='Scheduled')
    submit = SubmitField('Save Appointment')

class VisitForm(FlaskForm):
    visit_number = StringField('Visit #', validators=[DataRequired(), Length(max=30)])
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    doctor_id = SelectField('Doctor', coerce=int, validators=[DataRequired()])
    appointment_id = SelectField('Appointment (Optional)', coerce=int, validators=[Optional()])
    visit_type = SelectField('Visit Type', choices=[('OPD', 'OPD (Outpatient)'), ('IPD', 'IPD (Inpatient)'), ('Emergency', 'Emergency')], default='OPD')
    
    # Vital signs
    systolic_bp = IntegerField('Systolic BP (mmHg)', validators=[Optional(), NumberRange(min=50, max=260)])
    diastolic_bp = IntegerField('Diastolic BP (mmHg)', validators=[Optional(), NumberRange(min=30, max=160)])
    heart_rate = IntegerField('Heart Rate (bpm)', validators=[Optional(), NumberRange(min=30, max=220)])
    temperature = FloatField('Temperature (°F)', validators=[Optional(), NumberRange(min=90, max=108)])
    weight_kg = FloatField('Weight (kg)', validators=[Optional(), NumberRange(min=1, max=300)])
    height_cm = FloatField('Height (cm)', validators=[Optional(), NumberRange(min=30, max=250)])
    symptoms = TextAreaField('Reported Symptoms', validators=[Optional()])
    clinical_notes = TextAreaField('Clinical Examination & Doctor Notes', validators=[Optional()])
    submit = SubmitField('Record Encounter / Visit')

class QueueTokenForm(FlaskForm):
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    doctor_id = SelectField('Doctor', coerce=int, validators=[DataRequired()])
    appointment_id = SelectField('Linked Appointment (Optional)', coerce=int, validators=[Optional()])
    token_date = DateField('Token Date', validators=[DataRequired()])
    token_status = SelectField('Status', choices=[('Waiting', 'Waiting'), ('In-Consultation', 'In-Consultation'), ('Completed', 'Completed'), ('Skipped', 'Skipped')], default='Waiting')
    submit = SubmitField('Issue Queue Token')

class VisitDiagnosisForm(FlaskForm):
    diagnosis_id = SelectField('Diagnosis (ICD-10)', coerce=int, validators=[DataRequired()])
    diagnosis_type = SelectField('Type', choices=[('Primary', 'Primary'), ('Secondary', 'Secondary'), ('Differential', 'Differential')], default='Primary')
    notes = TextAreaField('Clinical Notes', validators=[Optional()])
    submit = SubmitField('Add Diagnosis to Visit')
