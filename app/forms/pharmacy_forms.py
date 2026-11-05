from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, FloatField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, Email

class MedicineCategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=100)])
    description = StringField('Description', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Save Category')

class MedicineForm(FlaskForm):
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    medicine_code = StringField('Medicine Code', validators=[DataRequired(), Length(max=30)])
    name = StringField('Brand Name', validators=[DataRequired(), Length(max=150)])
    generic_name = StringField('Generic Formula', validators=[Optional(), Length(max=150)])
    dosage_form = SelectField('Dosage Form', choices=[('Tablet', 'Tablet'), ('Capsule', 'Capsule'), ('Syrup', 'Syrup'), ('Injection', 'Injection'), ('Ointment', 'Ointment'), ('Drops', 'Drops')], default='Tablet')
    strength = StringField('Strength (e.g. 500mg)', validators=[Optional(), Length(max=50)])
    unit_price = FloatField('Unit Price (PKR)', validators=[DataRequired(), NumberRange(min=0)])
    reorder_level = IntegerField('Reorder Alert Threshold', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Save Medicine')

class PrescriptionForm(FlaskForm):
    prescription_code = StringField('Prescription Code', validators=[DataRequired(), Length(max=30)])
    patient_id = SelectField('Patient', coerce=int, validators=[DataRequired()])
    doctor_id = SelectField('Prescribing Doctor', coerce=int, validators=[DataRequired()])
    visit_id = SelectField('Linked Visit (Optional)', coerce=int, validators=[Optional()])
    instructions = TextAreaField('General Instructions', validators=[Optional()])
    validity_days = IntegerField('Validity (Days)', default=7, validators=[DataRequired(), NumberRange(min=1, max=365)])
    submit = SubmitField('Save Prescription')

class PrescriptionItemForm(FlaskForm):
    medicine_id = SelectField('Medicine', coerce=int, validators=[DataRequired()])
    dosage = StringField('Dosage (e.g. 1 Tab)', validators=[DataRequired(), Length(max=50)])
    frequency = SelectField('Frequency', choices=[('Once daily', 'Once daily'), ('Twice daily', 'Twice daily'), ('Thrice daily', 'Thrice daily'), ('Four times daily', 'Four times daily'), ('As needed (SOS)', 'As needed (SOS)')], default='Twice daily')
    duration_days = IntegerField('Duration (Days)', default=5, validators=[DataRequired(), NumberRange(min=1, max=180)])
    quantity = IntegerField('Total Quantity to Dispense', default=10, validators=[DataRequired(), NumberRange(min=1)])
    instructions = StringField('Specific Instructions (e.g. After meals)', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Add Medicine to Prescription')

class SupplierForm(FlaskForm):
    supplier_name = StringField('Supplier Company Name', validators=[DataRequired(), Length(max=150)])
    contact_person = StringField('Contact Person', validators=[Optional(), Length(max=100)])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=25)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    address = StringField('Address', validators=[Optional(), Length(max=255)])
    tax_number = StringField('NTN / Tax #', validators=[Optional(), Length(max=50)])
    submit = SubmitField('Save Supplier')

class PurchaseOrderForm(FlaskForm):
    po_number = StringField('Purchase Order #', validators=[DataRequired(), Length(max=30)])
    supplier_id = SelectField('Supplier', coerce=int, validators=[DataRequired()])
    expected_delivery_date = DateField('Expected Delivery Date', validators=[Optional()])
    order_status = SelectField('Order Status', choices=[('Draft', 'Draft'), ('Ordered', 'Ordered'), ('Received', 'Received'), ('Cancelled', 'Cancelled')], default='Ordered')
    submit = SubmitField('Save Purchase Order')

class PurchaseOrderItemForm(FlaskForm):
    medicine_id = SelectField('Medicine', coerce=int, validators=[DataRequired()])
    quantity_ordered = IntegerField('Quantity Ordered', validators=[DataRequired(), NumberRange(min=1)])
    unit_price = FloatField('Unit Purchase Cost (PKR)', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Add Item to Order')

class MedicineBatchForm(FlaskForm):
    medicine_id = SelectField('Medicine', coerce=int, validators=[DataRequired()])
    purchase_order_id = SelectField('Purchase Order (Optional)', coerce=int, validators=[Optional()])
    batch_number = StringField('Batch / Lot #', validators=[DataRequired(), Length(max=50)])
    manufacture_date = DateField('Manufacture Date', validators=[DataRequired()])
    expiry_date = DateField('Expiry Date', validators=[DataRequired()])
    quantity_in_stock = IntegerField('Quantity in Stock', validators=[DataRequired(), NumberRange(min=0)])
    unit_cost = FloatField('Unit Cost (PKR)', validators=[DataRequired(), NumberRange(min=0)])
    sale_price = FloatField('Retail Sale Price (PKR)', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Save Batch')

class PharmacySaleForm(FlaskForm):
    invoice_number = StringField('Sale Invoice #', validators=[DataRequired(), Length(max=30)])
    patient_id = SelectField('Patient (Optional for Walk-in)', coerce=int, validators=[Optional()])
    discount_amount = FloatField('Discount (PKR)', default=0.0, validators=[Optional(), NumberRange(min=0)])
    payment_status = SelectField('Payment Status', choices=[('Paid', 'Paid'), ('Pending', 'Pending'), ('Partially Paid', 'Partially Paid')], default='Paid')
    submit = SubmitField('Create Pharmacy Sale')

class PharmacySaleItemForm(FlaskForm):
    batch_id = SelectField('Medicine Batch', coerce=int, validators=[DataRequired()])
    quantity_sold = IntegerField('Quantity Sold', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Add Item to Sale')
