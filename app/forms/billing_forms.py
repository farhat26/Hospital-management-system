from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, FloatField, DateField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, Email

class InsuranceProviderForm(FlaskForm):
    provider_name = StringField('Insurance Provider Name', validators=[DataRequired(), Length(max=150)])
    policy_type = SelectField('Coverage Type', choices=[('Comprehensive', 'Comprehensive'), ('Basic', 'Basic Health'), ('Corporate', 'Corporate TPA'), ('Government', 'Government Program (Sehat Sahulat)')], default='Comprehensive')
    contact_person = StringField('Contact Representative', validators=[Optional(), Length(max=100)])
    phone = StringField('Helpdesk / Contact Phone', validators=[DataRequired(), Length(max=25)])
    email = StringField('Claims Email', validators=[Optional(), Email(), Length(max=120)])
    claim_address = StringField('Claims Submission Office', validators=[Optional(), Length(max=255)])
    co_pay_percentage = FloatField('Patient Co-Pay %', default=10.0, validators=[DataRequired(), NumberRange(min=0, max=100)])
    submit = SubmitField('Save Provider')

class PatientInsuranceForm(FlaskForm):
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    provider_id = SelectField('Insurance Company', coerce=int, validators=[DataRequired()])
    policy_number = StringField('Member / Policy ID #', validators=[DataRequired(), Length(max=50)])
    coverage_limit = FloatField('Total Annual Limit (PKR)', validators=[DataRequired(), NumberRange(min=0)])
    valid_from = DateField('Valid From', validators=[DataRequired()])
    valid_to = DateField('Valid To', validators=[DataRequired()])
    is_verified = BooleanField('Verified with Provider?', default=True)
    submit = SubmitField('Link Insurance Policy')

class InvoiceForm(FlaskForm):
    invoice_number = StringField('Invoice #', validators=[DataRequired(), Length(max=30)])
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    admission_id = SelectField('Admission (Optional)', coerce=int, validators=[Optional()])
    visit_id = SelectField('Visit (Optional)', coerce=int, validators=[Optional()])
    due_date = DateField('Payment Due Date', validators=[DataRequired()])
    discount_amount = FloatField('Discount (PKR)', default=0.0, validators=[Optional(), NumberRange(min=0)])
    tax_amount = FloatField('Tax (PKR)', default=0.0, validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Create Invoice')

class InvoiceItemForm(FlaskForm):
    item_description = StringField('Service / Item Description', validators=[DataRequired(), Length(max=200)])
    service_type = SelectField('Service Category', choices=[('Consultation', 'Consultation'), ('Lab Test', 'Laboratory Test'), ('Medicine', 'Pharmacy Medicine'), ('Room Charge', 'Ward / Room Stay'), ('Surgery', 'Surgery & OT Fee'), ('Ambulance', 'Emergency Transport'), ('Miscellaneous', 'Miscellaneous Charge')], default='Consultation')
    unit_price = FloatField('Unit Price (PKR)', validators=[DataRequired(), NumberRange(min=0)])
    quantity = IntegerField('Quantity', default=1, validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Add Charge Item')

class PaymentForm(FlaskForm):
    amount = FloatField('Payment Amount (PKR)', validators=[DataRequired(), NumberRange(min=0.1)])
    payment_method = SelectField('Payment Channel', choices=[('Cash', 'Cash'), ('Credit Card', 'Credit Card (POS)'), ('Debit Card', 'Debit Card (POS)'), ('Bank Transfer', 'Online / Bank Wire'), ('Insurance Claim', 'Insurance Direct Settlement'), ('Online UPI', 'Raast / Digital Wallet')], default='Cash')
    transaction_reference = StringField('Receipt / Slip / Ref #', validators=[Optional(), Length(max=100)])
    notes = TextAreaField('Payment Remarks', validators=[Optional()])
    submit = SubmitField('Post Settlement')
