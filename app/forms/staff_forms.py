from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, FloatField, DateField, TimeField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, Email, NumberRange

class DepartmentForm(FlaskForm):
    name = StringField('Department Name', validators=[DataRequired(), Length(max=100)])
    code = StringField('Code (e.g. CARD)', validators=[DataRequired(), Length(max=20)])
    description = TextAreaField('Description', validators=[Optional()])
    floor_location = StringField('Floor / Location', validators=[Optional(), Length(max=50)])
    submit = SubmitField('Save Department')

class DoctorForm(FlaskForm):
    doctor_code = StringField('Doctor Code', validators=[DataRequired(), Length(max=30)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    license_number = StringField('Medical License #', validators=[DataRequired(), Length(max=50)])
    qualification = StringField('Qualification (e.g. MBBS, FCPS)', validators=[DataRequired(), Length(max=100)])
    experience_years = IntegerField('Years of Experience', validators=[DataRequired(), NumberRange(min=0, max=60)])
    consultation_fee = FloatField('Consultation Fee (PKR)', validators=[DataRequired(), NumberRange(min=0)])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=25)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    department_id = SelectField('Primary Department', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Doctor')

class DoctorSpecializationForm(FlaskForm):
    specialization_name = StringField('Specialization Title', validators=[DataRequired(), Length(max=100)])
    certification_board = StringField('Certification Board', validators=[Optional(), Length(max=100)])
    year_obtained = IntegerField('Year Obtained', validators=[Optional(), NumberRange(min=1950, max=2030)])
    submit = SubmitField('Add Specialization')

class NurseForm(FlaskForm):
    nurse_code = StringField('Nurse Code', validators=[DataRequired(), Length(max=30)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    department_id = SelectField('Assigned Department', coerce=int, validators=[DataRequired()])
    license_number = StringField('Nursing License #', validators=[DataRequired(), Length(max=50)])
    qualification = StringField('Qualification', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=25)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    submit = SubmitField('Save Nurse')

class StaffForm(FlaskForm):
    staff_code = StringField('Staff Code', validators=[DataRequired(), Length(max=30)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    role_title = StringField('Designation / Role Title', validators=[DataRequired(), Length(max=100)])
    department_id = SelectField('Department (Optional)', coerce=int, validators=[Optional()])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=25)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    hire_date = DateField('Hire Date', validators=[DataRequired()])
    submit = SubmitField('Save Staff Member')

class ShiftForm(FlaskForm):
    name = StringField('Shift Name', validators=[DataRequired(), Length(max=50)])
    start_time = TimeField('Start Time', validators=[DataRequired()])
    end_time = TimeField('End Time', validators=[DataRequired()])
    description = StringField('Description', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Save Shift')

class StaffAttendanceForm(FlaskForm):
    doctor_id = SelectField('Doctor (Optional)', coerce=int, validators=[Optional()])
    nurse_id = SelectField('Nurse (Optional)', coerce=int, validators=[Optional()])
    staff_id = SelectField('Staff (Optional)', coerce=int, validators=[Optional()])
    shift_id = SelectField('Shift', coerce=int, validators=[DataRequired()])
    attendance_date = DateField('Date', validators=[DataRequired()])
    check_in_time = TimeField('Check-in Time', validators=[Optional()])
    check_out_time = TimeField('Check-out Time', validators=[Optional()])
    attendance_status = SelectField('Status', choices=[('Present', 'Present'), ('Absent', 'Absent'), ('Late', 'Late'), ('On Leave', 'On Leave')], default='Present')
    submit = SubmitField('Record Attendance')
