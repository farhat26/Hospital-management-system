from datetime import datetime
from app.extensions import db
from app.models.base import BaseModelMixin

class MedicineCategory(BaseModelMixin, db.Model):
    """30. medicine_categories - Therapeutic classes of pharmaceuticals"""
    __tablename__ = 'medicine_categories'
    
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)

    medicines = db.relationship('Medicine', back_populates='category', lazy='dynamic')

    def __repr__(self):
        return f'<MedicineCategory {self.name}>'


class Medicine(BaseModelMixin, db.Model):
    """29. medicines - Drug formulary and medicine catalog"""
    __tablename__ = 'medicines'
    
    category_id = db.Column(db.Integer, db.ForeignKey('medicine_categories.id'), nullable=False)
    medicine_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    generic_name = db.Column(db.String(150), nullable=True)
    dosage_form = db.Column(db.String(50), default='Tablet', nullable=False) # 'Tablet', 'Capsule', 'Syrup', 'Injection'
    strength = db.Column(db.String(50), nullable=True) # '500mg', '10ml', etc.
    unit_price = db.Column(db.Float, default=0.0, nullable=False)
    reorder_level = db.Column(db.Integer, default=50, nullable=False)

    category = db.relationship('MedicineCategory', back_populates='medicines')
    batches = db.relationship('MedicineBatch', back_populates='medicine', lazy='dynamic')
    prescription_items = db.relationship('PrescriptionItem', back_populates='medicine', lazy='dynamic')
    po_items = db.relationship('PurchaseOrderItem', back_populates='medicine', lazy='dynamic')
    sale_items = db.relationship('PharmacySaleItem', back_populates='medicine', lazy='dynamic')

    @property
    def total_stock(self):
        return sum(b.quantity_in_stock for b in self.batches if not b.is_deleted and b.status == 'Active')

    def __repr__(self):
        return f'<Medicine {self.name} ({self.strength})>'


class Prescription(BaseModelMixin, db.Model):
    """27. prescriptions - Doctor prescriptions issued to patients"""
    __tablename__ = 'prescriptions'
    
    prescription_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id'), nullable=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    prescription_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    instructions = db.Column(db.Text, nullable=True)
    validity_days = db.Column(db.Integer, default=7, nullable=False)

    patient = db.relationship('Patient', back_populates='prescriptions')
    doctor = db.relationship('Doctor', back_populates='prescriptions')
    visit = db.relationship('Visit', back_populates='prescriptions')
    items = db.relationship('PrescriptionItem', back_populates='prescription', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Prescription {self.prescription_code} Patient:{self.patient_id}>'


class PrescriptionItem(BaseModelMixin, db.Model):
    """28. prescription_items - Line items specifying medicines, dosage, and frequency"""
    __tablename__ = 'prescription_items'
    
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    dosage = db.Column(db.String(50), nullable=False) # '1 tablet', '5ml'
    frequency = db.Column(db.String(50), default='Twice daily', nullable=False) # 'Once daily', 'Twice daily', etc.
    duration_days = db.Column(db.Integer, default=5, nullable=False)
    quantity = db.Column(db.Integer, default=10, nullable=False)
    instructions = db.Column(db.String(255), nullable=True) # 'After meals', etc.

    prescription = db.relationship('Prescription', back_populates='items')
    medicine = db.relationship('Medicine', back_populates='prescription_items')

    def __repr__(self):
        return f'<PrescriptionItem Rx:{self.prescription_id} Med:{self.medicine_id}>'


class Supplier(BaseModelMixin, db.Model):
    """31. suppliers - Pharmaceutical vendors and medical equipment suppliers"""
    __tablename__ = 'suppliers'
    
    supplier_name = db.Column(db.String(150), unique=True, nullable=False)
    contact_person = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    tax_number = db.Column(db.String(50), nullable=True)

    purchase_orders = db.relationship('PurchaseOrder', back_populates='supplier', lazy='dynamic')

    def __repr__(self):
        return f'<Supplier {self.supplier_name}>'


class PurchaseOrder(BaseModelMixin, db.Model):
    """32. purchase_orders - Inventory procurement orders placed with suppliers"""
    __tablename__ = 'purchase_orders'
    
    po_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expected_delivery_date = db.Column(db.Date, nullable=True)
    total_amount = db.Column(db.Float, default=0.0, nullable=False)
    order_status = db.Column(db.String(30), default='Ordered', nullable=False) # 'Draft', 'Ordered', 'Received', 'Cancelled'

    supplier = db.relationship('Supplier', back_populates='purchase_orders')
    items = db.relationship('PurchaseOrderItem', back_populates='purchase_order', cascade='all, delete-orphan')
    batches = db.relationship('MedicineBatch', back_populates='purchase_order', lazy='dynamic')

    def __repr__(self):
        return f'<PurchaseOrder {self.po_number} Status:{self.order_status}>'


class PurchaseOrderItem(BaseModelMixin, db.Model):
    """33. purchase_order_items - Line items in medicine purchase orders"""
    __tablename__ = 'purchase_order_items'
    
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    quantity_ordered = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Float, nullable=False)

    purchase_order = db.relationship('PurchaseOrder', back_populates='items')
    medicine = db.relationship('Medicine', back_populates='po_items')

    def __repr__(self):
        return f'<PurchaseOrderItem PO:{self.purchase_order_id} Med:{self.medicine_id}>'


class MedicineBatch(BaseModelMixin, db.Model):
    """34. medicine_batches - Specific production lots with expiry tracking"""
    __tablename__ = 'medicine_batches'
    
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=True)
    batch_number = db.Column(db.String(50), nullable=False, index=True)
    manufacture_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    quantity_in_stock = db.Column(db.Integer, default=0, nullable=False)
    unit_cost = db.Column(db.Float, default=0.0, nullable=False)
    sale_price = db.Column(db.Float, default=0.0, nullable=False)

    medicine = db.relationship('Medicine', back_populates='batches')
    purchase_order = db.relationship('PurchaseOrder', back_populates='batches')
    sale_items = db.relationship('PharmacySaleItem', back_populates='batch', lazy='dynamic')

    @property
    def is_expired(self):
        return self.expiry_date < datetime.utcnow().date()

    def __repr__(self):
        return f'<MedicineBatch #{self.batch_number} Med:{self.medicine_id} Stock:{self.quantity_in_stock}>'


class PharmacySale(BaseModelMixin, db.Model):
    """35. pharmacy_sales - Retail counter sales invoices for patients/walk-ins"""
    __tablename__ = 'pharmacy_sales'
    
    invoice_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    total_amount = db.Column(db.Float, default=0.0, nullable=False)
    discount_amount = db.Column(db.Float, default=0.0, nullable=False)
    net_amount = db.Column(db.Float, default=0.0, nullable=False)
    payment_status = db.Column(db.String(30), default='Paid', nullable=False) # 'Paid', 'Pending', 'Partially Paid'

    patient = db.relationship('Patient')
    items = db.relationship('PharmacySaleItem', back_populates='sale', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<PharmacySale {self.invoice_number} Net:{self.net_amount}>'


class PharmacySaleItem(BaseModelMixin, db.Model):
    """36. pharmacy_sale_items - Line items dispensed in a pharmacy sale"""
    __tablename__ = 'pharmacy_sale_items'
    
    pharmacy_sale_id = db.Column(db.Integer, db.ForeignKey('pharmacy_sales.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('medicine_batches.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    quantity_sold = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    sale = db.relationship('PharmacySale', back_populates='items')
    batch = db.relationship('MedicineBatch', back_populates='sale_items')
    medicine = db.relationship('Medicine', back_populates='sale_items')

    def __repr__(self):
        return f'<PharmacySaleItem Sale:{self.pharmacy_sale_id} Med:{self.medicine_id}>'
