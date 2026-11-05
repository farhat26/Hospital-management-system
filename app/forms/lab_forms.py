from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, FloatField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange

class LabTestForm(FlaskForm):
    test_code = StringField('Test Code (e.g. CBC-01)', validators=[DataRequired(), Length(max=30)])
    test_name = StringField('Investigation / Test Name', validators=[DataRequired(), Length(max=150)])
    category = SelectField('Category', choices=[('Hematology', 'Hematology'), ('Biochemistry', 'Biochemistry'), ('Microbiology', 'Microbiology'), ('Radiology', 'Radiology'), ('Pathology', 'Pathology'), ('Immunology', 'Immunology')], default='Hematology')
    cost = FloatField('Standard Cost (PKR)', validators=[DataRequired(), NumberRange(min=0)])
    normal_range = StringField('Reference / Normal Range', validators=[Optional(), Length(max=100)])
    unit_of_measure = StringField('Unit of Measure', validators=[Optional(), Length(max=30)])
    description = TextAreaField('Description / Preparation Instructions', validators=[Optional()])
    submit = SubmitField('Save Test')

class LabOrderForm(FlaskForm):
    order_number = StringField('Lab Requisition #', validators=[DataRequired(), Length(max=30)])
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    doctor_id = SelectField('Requesting Doctor', coerce=int, validators=[DataRequired()])
    visit_id = SelectField('Visit (Optional)', coerce=int, validators=[Optional()])
    priority = SelectField('Priority', choices=[('Routine', 'Routine'), ('Urgent', 'Urgent'), ('STAT', 'STAT (Emergency immediate)')], default='Routine')
    order_status = SelectField('Status', choices=[('Pending', 'Pending'), ('Sample Collected', 'Sample Collected'), ('In Process', 'In Process'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')], default='Pending')
    submit = SubmitField('Create Requisition')

class LabOrderItemForm(FlaskForm):
    lab_test_id = SelectField('Test to Order', coerce=int, validators=[DataRequired()])
    sample_type = SelectField('Sample Type', choices=[('Blood', 'Blood'), ('Urine', 'Urine'), ('Serum', 'Serum'), ('Tissue', 'Tissue / Biopsy'), ('Swab', 'Swab'), ('Sputum', 'Sputum'), ('CSF', 'CSF')], default='Blood')
    submit = SubmitField('Add Test to Requisition')

class LabResultForm(FlaskForm):
    result_value = StringField('Result Value / Finding', validators=[DataRequired(), Length(max=100)])
    reference_range_snapshot = StringField('Reference Range', validators=[Optional(), Length(max=100)])
    remarks = TextAreaField('Technician / Pathologist Remarks', validators=[Optional()])
    is_abnormal = BooleanField('Mark as Abnormal Finding')
    submit = SubmitField('Record & Verify Result')
