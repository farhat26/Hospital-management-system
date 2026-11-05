from datetime import datetime
from app.extensions import db
from app.models.base import BaseModelMixin

class InsuranceProvider(BaseModelMixin, db.Model):
    """50. insurance_providers - Health maintenance and insurance companies"""
    __tablename__ = 'insurance_providers'
    
    provider_name = db.Column(db.String(150), unique=True, nullable=False)
    policy_type = db.Column(db.String(50), default='Comprehensive', nullable=False) # 'Comprehensive', 'Basic', 'Corporate'
    contact_person = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    claim_address = db.Column(db.String(255), nullable=True)
    co_pay_percentage = db.Column(db.Float, default=10.0, nullable=False)

    patient_policies = db.relationship('PatientInsurance', back_populates='provider', lazy='dynamic')

    def __repr__(self):
        return f'<InsuranceProvider {self.provider_name}>'


class PatientInsurance(BaseModelMixin, db.Model):
    """51. patient_insurances - Patient active insurance coverage policies"""
    __tablename__ = 'patient_insurances'
    
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('insurance_providers.id'), nullable=False)
    policy_number = db.Column(db.String(50), nullable=False, index=True)
    coverage_limit = db.Column(db.Float, default=100000.0, nullable=False)
    valid_from = db.Column(db.Date, nullable=False)
    valid_to = db.Column(db.Date, nullable=False)
    is_verified = db.Column(db.Boolean, default=True, nullable=False)

    patient = db.relationship('Patient', back_populates='insurances')
    provider = db.relationship('InsuranceProvider', back_populates='patient_policies')

    def __repr__(self):
        return f'<PatientInsurance Policy:{self.policy_number} Patient:{self.patient_id}>'


class Invoice(BaseModelMixin, db.Model):
    """47. invoices - Comprehensive patient billing invoices"""
    __tablename__ = 'invoices'
    
    invoice_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    admission_id = db.Column(db.Integer, db.ForeignKey('admissions.id'), nullable=True)
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id'), nullable=True)
    invoice_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    total_amount = db.Column(db.Float, default=0.0, nullable=False)
    discount_amount = db.Column(db.Float, default=0.0, nullable=False)
    tax_amount = db.Column(db.Float, default=0.0, nullable=False)
    net_amount = db.Column(db.Float, default=0.0, nullable=False)
    paid_amount = db.Column(db.Float, default=0.0, nullable=False)
    payment_status = db.Column(db.String(30), default='Unpaid', nullable=False) # 'Unpaid', 'Partially Paid', 'Paid', 'Overdue'

    patient = db.relationship('Patient', back_populates='invoices')
    admission = db.relationship('Admission', back_populates='invoices')
    visit = db.relationship('Visit', back_populates='invoices')
    items = db.relationship('InvoiceItem', back_populates='invoice', cascade='all, delete-orphan')
    payments = db.relationship('Payment', back_populates='invoice', cascade='all, delete-orphan')

    @property
    def balance_due(self):
        return max(0.0, round(self.net_amount - self.paid_amount, 2))

    def update_totals(self):
        self.total_amount = sum(item.subtotal for item in self.items if not item.is_deleted)
        self.net_amount = round(self.total_amount - self.discount_amount + self.tax_amount, 2)
        self.paid_amount = sum(p.amount for p in self.payments if not p.is_deleted and p.status == 'Active')
        if self.paid_amount >= self.net_amount and self.net_amount > 0:
            self.payment_status = 'Paid'
        elif self.paid_amount > 0:
            self.payment_status = 'Partially Paid'
        else:
            self.payment_status = 'Unpaid'

    def __repr__(self):
        return f'<Invoice {self.invoice_number} Net:{self.net_amount} Status:{self.payment_status}>'


class InvoiceItem(BaseModelMixin, db.Model):
    """48. invoice_items - Itemized charges on hospital invoices"""
    __tablename__ = 'invoice_items'
    
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    item_description = db.Column(db.String(200), nullable=False)
    service_type = db.Column(db.String(50), default='Consultation', nullable=False) # 'Consultation', 'Lab Test', 'Medicine', 'Room Charge', 'Surgery', 'Ambulance'
    unit_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    invoice = db.relationship('Invoice', back_populates='items')

    def __repr__(self):
        return f'<InvoiceItem Inv:{self.invoice_id} {self.item_description} Subtotal:{self.subtotal}>'


class Payment(BaseModelMixin, db.Model):
    """49. payments - Financial transactions and settlement receipts"""
    __tablename__ = 'payments'
    
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), default='Cash', nullable=False) # 'Cash', 'Credit Card', 'Debit Card', 'Bank Transfer', 'Insurance Claim', 'Online UPI'
    transaction_reference = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    invoice = db.relationship('Invoice', back_populates='payments')

    def __repr__(self):
        return f'<Payment Inv:{self.invoice_id} Amount:{self.amount} via {self.payment_method}>'
