from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.pharmacy import (
    MedicineCategory, Medicine, Prescription, PrescriptionItem,
    Supplier, PurchaseOrder, PurchaseOrderItem, MedicineBatch,
    PharmacySale, PharmacySaleItem
)
from app.models.patients import Patient
from app.models.staff import Doctor
from app.models.appointments import Visit
from app.forms.pharmacy_forms import (
    MedicineCategoryForm, MedicineForm, PrescriptionForm, PrescriptionItemForm,
    SupplierForm, PurchaseOrderForm, PurchaseOrderItemForm, MedicineBatchForm,
    PharmacySaleForm, PharmacySaleItemForm
)
from app.services.audit_service import log_audit
from app.utils.decorators import role_required
from datetime import datetime, date

pharmacy_bp = Blueprint('pharmacy', __name__, url_prefix='/pharmacy')

@pharmacy_bp.route('/')
@login_required
def index():
    search = request.args.get('search', '').strip()
    cat_id = request.args.get('category_id', type=int)
    page = request.args.get('page', 1, type=int)

    query = Medicine.query.filter_by(is_deleted=False)
    if search:
        query = query.filter((Medicine.name.ilike(f'%{search}%')) | (Medicine.generic_name.ilike(f'%{search}%')) | (Medicine.medicine_code.ilike(f'%{search}%')))
    if cat_id:
        query = query.filter_by(category_id=cat_id)

    pagination = query.order_by(Medicine.name).paginate(page=page, per_page=12, error_out=False)
    medicines = pagination.items
    categories = MedicineCategory.query.filter_by(is_deleted=False).all()

    # Alerts
    low_stock = [m for m in Medicine.query.filter_by(is_deleted=False).all() if m.total_stock <= m.reorder_level]
    batches_expiring_soon = MedicineBatch.query.filter(
        MedicineBatch.is_deleted == False,
        MedicineBatch.expiry_date <= (date.today() + db.func.date('now', '+90 days'))
    ).all()

    return render_template(
        'pharmacy/index.html',
        medicines=medicines,
        pagination=pagination,
        categories=categories,
        selected_cat=cat_id,
        search=search,
        low_stock=low_stock,
        expiring_batches=batches_expiring_soon
    )

# ----------------- Medicine CRUD -----------------
@pharmacy_bp.route('/medicines/create', methods=['GET', 'POST'])
@login_required
def create_medicine():
    form = MedicineForm()
    cats = MedicineCategory.query.filter_by(is_deleted=False).all()
    form.category_id.choices = [(c.id, c.name) for c in cats]

    if request.method == 'GET' and not form.medicine_code.data:
        count = Medicine.query.count() + 1
        form.medicine_code.data = f'MED-{count:04d}'

    if form.validate_on_submit():
        med = Medicine(
            category_id=form.category_id.data,
            medicine_code=form.medicine_code.data.strip(),
            name=form.name.data.strip(),
            generic_name=form.generic_name.data.strip() if form.generic_name.data else None,
            dosage_form=form.dosage_form.data,
            strength=form.strength.data.strip() if form.strength.data else None,
            unit_price=form.unit_price.data,
            reorder_level=form.reorder_level.data,
            created_by_id=current_user.id
        )
        db.session.add(med)
        db.session.commit()
        log_audit('CREATE', 'medicines', med.id, f'Added medicine {med.name} ({med.strength})')
        flash(f'Medicine {med.name} added to pharmacy inventory.', 'success')
        return redirect(url_for('pharmacy.view_medicine', id=med.id))

    return render_template('pharmacy/medicine_form.html', form=form, title='Add Formulary Drug')

@pharmacy_bp.route('/medicines/<int:id>')
@login_required
def view_medicine(id):
    medicine = Medicine.query.get_or_404(id)
    batch_form = MedicineBatchForm()
    pos = PurchaseOrder.query.filter_by(is_deleted=False).all()
    batch_form.purchase_order_id.choices = [(0, '-- None / Direct Receipt --')] + [(po.id, f"{po.po_number} ({po.supplier.supplier_name})") for po in pos]
    return render_template('pharmacy/medicine_view.html', medicine=medicine, batch_form=batch_form)

@pharmacy_bp.route('/medicines/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_medicine(id):
    medicine = Medicine.query.get_or_404(id)
    form = MedicineForm(obj=medicine)
    cats = MedicineCategory.query.filter_by(is_deleted=False).all()
    form.category_id.choices = [(c.id, c.name) for c in cats]

    if form.validate_on_submit():
        medicine.category_id = form.category_id.data
        medicine.medicine_code = form.medicine_code.data.strip()
        medicine.name = form.name.data.strip()
        medicine.generic_name = form.generic_name.data.strip() if form.generic_name.data else None
        medicine.dosage_form = form.dosage_form.data
        medicine.strength = form.strength.data.strip() if form.strength.data else None
        medicine.unit_price = form.unit_price.data
        medicine.reorder_level = form.reorder_level.data
        medicine.updated_by_id = current_user.id
        db.session.commit()
        log_audit('UPDATE', 'medicines', medicine.id, f'Updated medicine {medicine.name}')
        flash('Medicine details updated successfully.', 'success')
        return redirect(url_for('pharmacy.view_medicine', id=medicine.id))

    return render_template('pharmacy/medicine_form.html', form=form, title=f'Edit Medicine: {medicine.name}')

@pharmacy_bp.route('/medicines/<int:id>/delete', methods=['POST'])
@login_required
def delete_medicine(id):
    medicine = Medicine.query.get_or_404(id)
    medicine.soft_delete(user_id=current_user.id)
    log_audit('SOFT_DELETE', 'medicines', medicine.id, f'Soft-deleted medicine {medicine.name}')
    flash(f'Medicine {medicine.name} soft-deleted.', 'info')
    return redirect(url_for('pharmacy.index'))

# ----------------- Batches -----------------
@pharmacy_bp.route('/medicines/<int:id>/add-batch', methods=['POST'])
@login_required
def add_batch(id):
    medicine = Medicine.query.get_or_404(id)
    form = MedicineBatchForm()
    pos = PurchaseOrder.query.filter_by(is_deleted=False).all()
    form.purchase_order_id.choices = [(0, '-- None --')] + [(po.id, po.po_number) for po in pos]

    if form.validate_on_submit():
        po_id = form.purchase_order_id.data if form.purchase_order_id.data != 0 else None
        batch = MedicineBatch(
            medicine_id=medicine.id,
            purchase_order_id=po_id,
            batch_number=form.batch_number.data.strip(),
            manufacture_date=form.manufacture_date.data,
            expiry_date=form.expiry_date.data,
            quantity_in_stock=form.quantity_in_stock.data,
            unit_cost=form.unit_cost.data,
            sale_price=form.sale_price.data,
            created_by_id=current_user.id
        )
        db.session.add(batch)
        db.session.commit()
        log_audit('CREATE', 'medicine_batches', batch.id, f'Added batch {batch.batch_number} for medicine #{medicine.id}')
        flash(f'Batch #{batch.batch_number} added with {batch.quantity_in_stock} units.', 'success')
    else:
        flash('Error adding batch. Please check dates and quantities.', 'danger')
    return redirect(url_for('pharmacy.view_medicine', id=medicine.id))

# ----------------- Categories -----------------
@pharmacy_bp.route('/categories', methods=['GET', 'POST'])
@login_required
def categories():
    form = MedicineCategoryForm()
    if form.validate_on_submit():
        cat = MedicineCategory(
            name=form.name.data.strip(),
            description=form.description.data.strip() if form.description.data else None,
            created_by_id=current_user.id
        )
        db.session.add(cat)
        db.session.commit()
        log_audit('CREATE', 'medicine_categories', cat.id, f'Created medicine category {cat.name}')
        flash(f'Category {cat.name} created successfully.', 'success')
        return redirect(url_for('pharmacy.categories'))

    cats = MedicineCategory.query.filter_by(is_deleted=False).all()
    return render_template('pharmacy/categories.html', form=form, categories=cats)

# ----------------- Suppliers & Purchase Orders -----------------
@pharmacy_bp.route('/suppliers', methods=['GET', 'POST'])
@login_required
def suppliers():
    form = SupplierForm()
    if form.validate_on_submit():
        sup = Supplier(
            supplier_name=form.supplier_name.data.strip(),
            contact_person=form.contact_person.data.strip() if form.contact_person.data else None,
            phone=form.phone.data.strip(),
            email=form.email.data.strip() if form.email.data else None,
            address=form.address.data.strip() if form.address.data else None,
            tax_number=form.tax_number.data.strip() if form.tax_number.data else None,
            created_by_id=current_user.id
        )
        db.session.add(sup)
        db.session.commit()
        log_audit('CREATE', 'suppliers', sup.id, f'Created supplier {sup.supplier_name}')
        flash(f'Supplier {sup.supplier_name} registered successfully.', 'success')
        return redirect(url_for('pharmacy.suppliers'))

    sups = Supplier.query.filter_by(is_deleted=False).all()
    return render_template('pharmacy/suppliers.html', form=form, suppliers=sups)

@pharmacy_bp.route('/purchase-orders')
@login_required
def purchase_orders():
    pos = PurchaseOrder.query.filter_by(is_deleted=False).order_by(PurchaseOrder.order_date.desc()).all()
    return render_template('pharmacy/purchase_orders.html', purchase_orders=pos)

@pharmacy_bp.route('/purchase-orders/create', methods=['GET', 'POST'])
@login_required
def create_purchase_order():
    form = PurchaseOrderForm()
    sups = Supplier.query.filter_by(is_deleted=False, status='Active').all()
    form.supplier_id.choices = [(s.id, s.supplier_name) for s in sups]

    if request.method == 'GET' and not form.po_number.data:
        count = PurchaseOrder.query.count() + 1
        form.po_number.data = f'PO-{datetime.utcnow().year}-{count:03d}'

    if form.validate_on_submit():
        po = PurchaseOrder(
            po_number=form.po_number.data.strip(),
            supplier_id=form.supplier_id.data,
            order_date=datetime.utcnow(),
            expected_delivery_date=form.expected_delivery_date.data,
            order_status=form.order_status.data,
            total_amount=0.0,
            created_by_id=current_user.id
        )
        db.session.add(po)
        db.session.commit()
        log_audit('CREATE', 'purchase_orders', po.id, f'Created purchase order {po.po_number}')
        flash(f'Purchase Order {po.po_number} created. Now add line items.', 'success')
        return redirect(url_for('pharmacy.view_purchase_order', id=po.id))

    return render_template('pharmacy/po_form.html', form=form, title='New Procurement Purchase Order')

@pharmacy_bp.route('/purchase-orders/<int:id>')
@login_required
def view_purchase_order(id):
    po = PurchaseOrder.query.get_or_404(id)
    item_form = PurchaseOrderItemForm()
    meds = Medicine.query.filter_by(is_deleted=False, status='Active').all()
    item_form.medicine_id.choices = [(m.id, f"{m.name} ({m.strength})") for m in meds]
    return render_template('pharmacy/po_view.html', po=po, item_form=item_form)

@pharmacy_bp.route('/purchase-orders/<int:id>/add-item', methods=['POST'])
@login_required
def add_po_item(id):
    po = PurchaseOrder.query.get_or_404(id)
    form = PurchaseOrderItemForm()
    meds = Medicine.query.filter_by(is_deleted=False, status='Active').all()
    form.medicine_id.choices = [(m.id, f"{m.name} ({m.strength})") for m in meds]

    if form.validate_on_submit():
        cost = form.quantity_ordered.data * form.unit_price.data
        item = PurchaseOrderItem(
            purchase_order_id=po.id,
            medicine_id=form.medicine_id.data,
            quantity_ordered=form.quantity_ordered.data,
            unit_price=form.unit_price.data,
            total_cost=cost,
            created_by_id=current_user.id
        )
        db.session.add(item)
        po.total_amount += cost
        db.session.commit()
        log_audit('CREATE', 'purchase_order_items', item.id, f'Added item to PO #{po.id}')
        flash('Item added to purchase order.', 'success')
    return redirect(url_for('pharmacy.view_purchase_order', id=po.id))

@pharmacy_bp.route('/purchase-orders/<int:id>/receive', methods=['POST'])
@login_required
def receive_po(id):
    po = PurchaseOrder.query.get_or_404(id)
    po.order_status = 'Received'
    po.updated_by_id = current_user.id
    db.session.commit()
    log_audit('UPDATE', 'purchase_orders', po.id, f'Marked PO {po.po_number} as Received')
    flash(f'Purchase Order {po.po_number} marked as Received.', 'success')
    return redirect(url_for('pharmacy.view_purchase_order', id=po.id))

# ----------------- Prescriptions -----------------
@pharmacy_bp.route('/prescriptions')
@login_required
def prescriptions():
    page = request.args.get('page', 1, type=int)
    rx_list = Prescription.query.filter_by(is_deleted=False).order_by(Prescription.prescription_date.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('pharmacy/prescriptions.html', prescriptions=rx_list.items, pagination=rx_list)

@pharmacy_bp.route('/prescriptions/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Doctor')
def create_prescription():
    form = PrescriptionForm()
    patients = Patient.query.filter_by(is_deleted=False, status='Active').all()
    doctors = Doctor.query.filter_by(is_deleted=False, status='Active').all()
    visits_list = Visit.query.filter_by(is_deleted=False).order_by(Visit.visit_date.desc()).all()

    form.patient_id.choices = [(p.id, f"{p.patient_code} - {p.full_name}") for p in patients]
    form.doctor_id.choices = [(d.id, d.full_name) for d in doctors]
    form.visit_id.choices = [(0, '-- None / Direct Consultation --')] + [(v.id, f"{v.visit_number} ({v.visit_date.date()})") for v in visits_list]

    if request.method == 'GET' and not form.prescription_code.data:
        count = Prescription.query.count() + 1
        form.prescription_code.data = f'RX-{datetime.utcnow().year}-{count:04d}'

    if form.validate_on_submit():
        v_id = form.visit_id.data if form.visit_id.data != 0 else None
        rx = Prescription(
            prescription_code=form.prescription_code.data.strip(),
            patient_id=form.patient_id.data,
            doctor_id=form.doctor_id.data,
            visit_id=v_id,
            prescription_date=datetime.utcnow(),
            instructions=form.instructions.data.strip() if form.instructions.data else None,
            validity_days=form.validity_days.data,
            created_by_id=current_user.id
        )
        db.session.add(rx)
        db.session.commit()
        log_audit('CREATE', 'prescriptions', rx.id, f'Issued prescription {rx.prescription_code}')
        flash(f'Prescription {rx.prescription_code} created. Now add medicines.', 'success')
        return redirect(url_for('pharmacy.view_prescription', id=rx.id))

    return render_template('pharmacy/prescription_form.html', form=form, title='Issue Medical Prescription')

@pharmacy_bp.route('/prescriptions/<int:id>')
@login_required
def view_prescription(id):
    rx = Prescription.query.get_or_404(id)
    item_form = PrescriptionItemForm()
    meds = Medicine.query.filter_by(is_deleted=False, status='Active').all()
    item_form.medicine_id.choices = [(m.id, f"{m.name} ({m.strength})") for m in meds]
    return render_template('pharmacy/prescription_view.html', rx=rx, item_form=item_form)

@pharmacy_bp.route('/prescriptions/<int:id>/add-item', methods=['POST'])
@login_required
def add_prescription_item(id):
    rx = Prescription.query.get_or_404(id)
    form = PrescriptionItemForm()
    meds = Medicine.query.filter_by(is_deleted=False, status='Active').all()
    form.medicine_id.choices = [(m.id, f"{m.name} ({m.strength})") for m in meds]

    if form.validate_on_submit():
        item = PrescriptionItem(
            prescription_id=rx.id,
            medicine_id=form.medicine_id.data,
            dosage=form.dosage.data.strip(),
            frequency=form.frequency.data,
            duration_days=form.duration_days.data,
            quantity=form.quantity.data,
            instructions=form.instructions.data.strip() if form.instructions.data else None,
            created_by_id=current_user.id
        )
        db.session.add(item)
        db.session.commit()
        log_audit('CREATE', 'prescription_items', item.id, f'Added medicine to prescription #{rx.id}')
        flash('Medicine added to prescription.', 'success')
    return redirect(url_for('pharmacy.view_prescription', id=rx.id))

# ----------------- Pharmacy Counter Sales -----------------
@pharmacy_bp.route('/sales')
@login_required
@role_required('Admin', 'Pharmacist')
def sales():
    page = request.args.get('page', 1, type=int)
    sales_list = PharmacySale.query.filter_by(is_deleted=False).order_by(PharmacySale.sale_date.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('pharmacy/sales.html', sales=sales_list.items, pagination=sales_list)

@pharmacy_bp.route('/sales/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Pharmacist')
def create_sale():
    form = PharmacySaleForm()
    patients = Patient.query.filter_by(is_deleted=False, status='Active').all()
    form.patient_id.choices = [(0, '-- Walk-in Customer --')] + [(p.id, f"{p.patient_code} - {p.full_name}") for p in patients]

    if request.method == 'GET' and not form.invoice_number.data:
        count = PharmacySale.query.count() + 1
        form.invoice_number.data = f'PH-INV-{datetime.utcnow().year}-{count:04d}'

    if form.validate_on_submit():
        p_id = form.patient_id.data if form.patient_id.data != 0 else None
        sale = PharmacySale(
            invoice_number=form.invoice_number.data.strip(),
            patient_id=p_id,
            sale_date=datetime.utcnow(),
            total_amount=0.0,
            discount_amount=form.discount_amount.data,
            net_amount=0.0,
            payment_status=form.payment_status.data,
            created_by_id=current_user.id
        )
        db.session.add(sale)
        db.session.commit()
        log_audit('CREATE', 'pharmacy_sales', sale.id, f'Initiated pharmacy sale {sale.invoice_number}')
        flash(f'Sale bill {sale.invoice_number} created. Now dispense medicines.', 'success')
        return redirect(url_for('pharmacy.view_sale', id=sale.id))

    return render_template('pharmacy/sale_form.html', form=form, title='Point of Sale (POS) Counter')

@pharmacy_bp.route('/sales/<int:id>')
@login_required
def view_sale(id):
    sale = PharmacySale.query.get_or_404(id)
    item_form = PharmacySaleItemForm()
    active_batches = MedicineBatch.query.filter(MedicineBatch.is_deleted == False, MedicineBatch.quantity_in_stock > 0).all()
    item_form.batch_id.choices = [(b.id, f"{b.medicine.name} (Batch: {b.batch_number}, Stock: {b.quantity_in_stock}, PKR {b.sale_price})") for b in active_batches]
    return render_template('pharmacy/sale_view.html', sale=sale, item_form=item_form)

@pharmacy_bp.route('/sales/<int:id>/add-item', methods=['POST'])
@login_required
def add_sale_item(id):
    sale = PharmacySale.query.get_or_404(id)
    form = PharmacySaleItemForm()
    active_batches = MedicineBatch.query.filter(MedicineBatch.is_deleted == False, MedicineBatch.quantity_in_stock > 0).all()
    form.batch_id.choices = [(b.id, f"{b.medicine.name} ({b.batch_number})") for b in active_batches]

    if form.validate_on_submit():
        batch = MedicineBatch.query.get(form.batch_id.data)
        qty = form.quantity_sold.data
        if batch and batch.quantity_in_stock >= qty:
            sub = qty * batch.sale_price
            item = PharmacySaleItem(
                pharmacy_sale_id=sale.id,
                batch_id=batch.id,
                medicine_id=batch.medicine_id,
                quantity_sold=qty,
                unit_price=batch.sale_price,
                subtotal=sub,
                created_by_id=current_user.id
            )
            batch.quantity_in_stock -= qty
            db.session.add(item)
            sale.total_amount += sub
            sale.net_amount = max(0.0, sale.total_amount - sale.discount_amount)
            db.session.commit()
            log_audit('CREATE', 'pharmacy_sale_items', item.id, f'Sold {qty} units of {batch.medicine.name}')
            flash(f'Added {qty}x {batch.medicine.name} to bill.', 'success')
        else:
            flash(f'Insufficient stock in batch. Available: {batch.quantity_in_stock if batch else 0}', 'danger')
    return redirect(url_for('pharmacy.view_sale', id=sale.id))
