from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, FloatField, DateTimeLocalField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange

class OperationTheatreForm(FlaskForm):
    ot_number = StringField('OT Unit # (e.g. OT-01)', validators=[DataRequired(), Length(max=30)])
    name = StringField('Theatre Name', validators=[DataRequired(), Length(max=100)])
    floor = IntegerField('Floor Level', default=3, validators=[DataRequired(), NumberRange(min=0, max=20)])
    theatre_type = SelectField('Type', choices=[('Major', 'Major Surgical OT'), ('Minor', 'Minor OT / Day Surgery'), ('Cardiac', 'Dedicated Cardiac OT'), ('Orthopedic', 'Orthopedic / Laminar Flow OT')], default='Major')
    is_equipped = BooleanField('Fully Equipped & Ready?', default=True)
    maintenance_status = SelectField('Maintenance Status', choices=[('Operational', 'Operational'), ('Under Maintenance', 'Under Maintenance'), ('Sterilizing', 'Sterilizing / Fumigation')], default='Operational')
    submit = SubmitField('Save Operation Theatre')

class SurgeryForm(FlaskForm):
    surgery_code = StringField('Procedure Code', validators=[DataRequired(), Length(max=30)])
    surgery_name = StringField('Procedure Name', validators=[DataRequired(), Length(max=150)])
    department_id = SelectField('Surgical Specialty / Dept', coerce=int, validators=[DataRequired()])
    estimated_duration_minutes = IntegerField('Estimated Duration (Minutes)', default=60, validators=[DataRequired(), NumberRange(min=10, max=1440)])
    standard_cost = FloatField('Standard Package Cost (PKR)', validators=[DataRequired(), NumberRange(min=0)])
    description = TextAreaField('Procedure Details & Protocol', validators=[Optional()])
    submit = SubmitField('Save Surgery Catalog Entry')

class SurgeryScheduleForm(FlaskForm):
    surgery_id = SelectField('Surgical Procedure', coerce=int, validators=[DataRequired()])
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    lead_surgeon_id = SelectField('Lead Surgeon (Doctor)', coerce=int, validators=[DataRequired()])
    theatre_id = SelectField('Operation Theatre', coerce=int, validators=[DataRequired()])
    scheduled_start_time = DateTimeLocalField('Scheduled Start Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    scheduled_end_time = DateTimeLocalField('Scheduled End Time', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    surgery_status = SelectField('Status', choices=[('Scheduled', 'Scheduled'), ('In-Progress', 'In-Progress'), ('Completed', 'Completed'), ('Postponed', 'Postponed'), ('Cancelled', 'Cancelled')], default='Scheduled')
    pre_op_notes = TextAreaField('Pre-operative Anesthesia & Clinical Clearance', validators=[Optional()])
    post_op_notes = TextAreaField('Post-operative Findings & Recovery Plan', validators=[Optional()])
    submit = SubmitField('Book / Update Surgery Schedule')

class AmbulanceForm(FlaskForm):
    vehicle_number = StringField('Registration Plate #', validators=[DataRequired(), Length(max=30)])
    vehicle_model = StringField('Vehicle Make & Model', validators=[DataRequired(), Length(max=100)])
    ambulance_type = SelectField('Fleet Type', choices=[('Advanced Life Support', 'Advanced Life Support (ALS)'), ('Basic Life Support', 'Basic Life Support (BLS)'), ('Patient Transport', 'Patient Transport Non-Emergency')], default='Advanced Life Support')
    driver_name = StringField('Driver Name', validators=[DataRequired(), Length(max=100)])
    driver_phone = StringField('Emergency Phone Number', validators=[DataRequired(), Length(max=25)])
    current_location = StringField('Current Station / Location', default='Hospital Bay 1', validators=[DataRequired(), Length(max=150)])
    operational_status = SelectField('Status', choices=[('Available', 'Available on Standby'), ('On Trip', 'Dispatched / On Trip'), ('Under Maintenance', 'In Workshop / Maintenance')], default='Available')
    submit = SubmitField('Save Ambulance')
