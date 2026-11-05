from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, FloatField, DateField, DateTimeLocalField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange

class WardForm(FlaskForm):
    ward_name = StringField('Ward Name', validators=[DataRequired(), Length(max=100)])
    ward_type = SelectField('Ward Type', choices=[('General', 'General'), ('ICU', 'ICU / CCU'), ('Pediatric', 'Pediatric'), ('Maternity', 'Maternity'), ('Surgical', 'Surgical'), ('Isolation', 'Isolation')], default='General')
    gender_type = SelectField('Gender Specification', choices=[('Mixed', 'Mixed'), ('Male', 'Male Only'), ('Female', 'Female Only')], default='Mixed')
    total_capacity = IntegerField('Bed Capacity', validators=[DataRequired(), NumberRange(min=1)])
    floor_number = IntegerField('Floor Level', validators=[DataRequired(), NumberRange(min=0, max=20)])
    submit = SubmitField('Save Ward')

class RoomForm(FlaskForm):
    ward_id = SelectField('Ward', coerce=int, validators=[DataRequired()])
    room_number = StringField('Room #', validators=[DataRequired(), Length(max=30)])
    room_type = SelectField('Room Type', choices=[('Standard', 'Standard (Shared)'), ('Semi-Private', 'Semi-Private'), ('Private', 'Private'), ('Deluxe', 'Deluxe VIP Suite')], default='Standard')
    daily_rate = FloatField('Daily Room Tariff (PKR)', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Save Room')

class BedForm(FlaskForm):
    room_id = SelectField('Room', coerce=int, validators=[DataRequired()])
    bed_number = StringField('Bed Number / Tag', validators=[DataRequired(), Length(max=30)])
    bed_type = SelectField('Bed Type', choices=[('Regular', 'Regular Inpatient'), ('ICU Bed', 'ICU Multi-parameter Bed'), ('Electric', 'Motorized Electric Bed'), ('Bariatric', 'Bariatric Bed')], default='Regular')
    bed_status = SelectField('Current Status', choices=[('Available', 'Available'), ('Occupied', 'Occupied'), ('Maintenance', 'Maintenance / Sanitizing'), ('Reserved', 'Reserved')], default='Available')
    submit = SubmitField('Save Bed')

class AdmissionForm(FlaskForm):
    admission_number = StringField('Admission #', validators=[DataRequired(), Length(max=30)])
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    doctor_id = SelectField('Admitting Consultant', coerce=int, validators=[DataRequired()])
    admission_type = SelectField('Admission Type', choices=[('Emergency', 'Emergency Admission'), ('Elective', 'Elective / Planned'), ('Day Care', 'Day Care Procedure')], default='Emergency')
    reason_for_admission = TextAreaField('Indication / Reason for Inpatient Care', validators=[DataRequired()])
    bed_id = SelectField('Assign Initial Bed', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Admit Patient')

class BedAllocationForm(FlaskForm):
    bed_id = SelectField('Transfer to Bed', coerce=int, validators=[DataRequired()])
    allocation_notes = StringField('Transfer / Allocation Reason', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Transfer / Reallocate Bed')

class DischargeForm(FlaskForm):
    discharge_type = SelectField('Discharge Classification', choices=[('Normal', 'Routine / Normal Discharge'), ('Transfer', 'Transfer to Higher Center'), ('AMA', 'Against Medical Advice (AMA / LAMA)'), ('Deceased', 'Deceased')], default='Normal')
    discharge_summary = TextAreaField('Clinical Summary & Course in Hospital', validators=[DataRequired()])
    follow_up_instructions = TextAreaField('Discharge Medications & Instructions', validators=[Optional()])
    follow_up_date = DateField('Follow-up Review Date', validators=[Optional()])
    submit = SubmitField('Process Formal Discharge')
