from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, TextAreaField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Optional, Length, Email

class PatientForm(FlaskForm):
    patient_code = StringField('Patient Code', validators=[DataRequired(), Length(max=30)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], validators=[DataRequired()])
    blood_group = SelectField('Blood Group', choices=[('', '-- Select Blood Group --'), ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')], validators=[Optional()])
    marital_status = SelectField('Marital Status', choices=[('', '-- Select Marital Status --'), ('Single', 'Single'), ('Married', 'Married'), ('Divorced', 'Divorced'), ('Widowed', 'Widowed')], validators=[Optional()])
    occupation = StringField('Occupation', validators=[Optional(), Length(max=100)])
    status = SelectField('Status', choices=[('Active', 'Active'), ('Deactive', 'Deactive')], default='Active')
    submit = SubmitField('Save Patient')

class PatientContactForm(FlaskForm):
    phone_primary = StringField('Primary Phone', validators=[DataRequired(), Length(max=25)])
    phone_secondary = StringField('Secondary Phone', validators=[Optional(), Length(max=25)])
    email = StringField('Email Address', validators=[Optional(), Email(), Length(max=120)])
    submit = SubmitField('Save Contact')

class PatientAddressForm(FlaskForm):
    address_type = SelectField('Address Type', choices=[('Home', 'Home'), ('Work', 'Work'), ('Permanent', 'Permanent')], default='Home')
    street_address = StringField('Street Address', validators=[DataRequired(), Length(max=255)])
    city = StringField('City', validators=[DataRequired(), Length(max=100)])
    state = StringField('State / Province', validators=[Optional(), Length(max=100)])
    postal_code = StringField('Postal Code', validators=[Optional(), Length(max=20)])
    country = StringField('Country', default='Pakistan', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Save Address')

class EmergencyContactForm(FlaskForm):
    contact_name = StringField('Contact Name', validators=[DataRequired(), Length(max=100)])
    relationship = StringField('Relationship (e.g. Spouse, Parent)', validators=[DataRequired(), Length(max=50)])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(max=25)])
    alternate_phone = StringField('Alternate Phone', validators=[Optional(), Length(max=25)])
    address = StringField('Address', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Save Emergency Contact')

class AllergyForm(FlaskForm):
    allergen_name = StringField('Allergen Name', validators=[DataRequired(), Length(max=100)])
    allergy_type = SelectField('Allergy Type', choices=[('Drug', 'Drug'), ('Food', 'Food'), ('Environmental', 'Environmental'), ('Other', 'Other')], default='Drug')
    severity = SelectField('Severity', choices=[('Mild', 'Mild'), ('Moderate', 'Moderate'), ('Severe', 'Severe')], default='Moderate')
    common_symptoms = StringField('Common Symptoms', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Save Allergen')

class PatientAllergyForm(FlaskForm):
    allergy_id = SelectField('Select Allergy', coerce=int, validators=[DataRequired()])
    diagnosed_date = DateField('Diagnosed Date', validators=[Optional()])
    reaction_description = StringField('Reaction Description', validators=[Optional(), Length(max=255)])
    notes = TextAreaField('Clinical Notes', validators=[Optional()])
    submit = SubmitField('Record Allergy')

class MedicalRecordForm(FlaskForm):
    chief_complaint = TextAreaField('Chief Complaint', validators=[DataRequired()])
    history_of_present_illness = TextAreaField('History of Present Illness', validators=[Optional()])
    past_medical_history = TextAreaField('Past Medical History', validators=[Optional()])
    family_history = TextAreaField('Family Medical History', validators=[Optional()])
    social_history = TextAreaField('Social History', validators=[Optional()])
    notes = TextAreaField('Additional Notes', validators=[Optional()])
    submit = SubmitField('Save Medical Record')

class DiagnosisForm(FlaskForm):
    icd_code = StringField('ICD-10 Code', validators=[DataRequired(), Length(max=20)])
    diagnosis_name = StringField('Diagnosis Name', validators=[DataRequired(), Length(max=150)])
    category = StringField('Category', validators=[Optional(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    is_chronic = BooleanField('Is Chronic Condition?')
    submit = SubmitField('Save Diagnosis')
