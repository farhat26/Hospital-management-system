from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.billing import Invoice, InvoiceItem, Payment, InsuranceProvider, PatientInsurance
from app.models.patients import Patient
from app.models.wards import Admission
from app.models.appointments import Visit
from app.forms.billing_forms import InvoiceForm, InvoiceItemForm, PaymentForm, InsuranceProviderForm, PatientInsuranceForm
from app.services.audit_service import log_audit
from datetime import datetime, date, timedelta
from app.utils.decorators import role_required

billing_bp = Blueprint('billing', __name__, url_prefix='/billing')

@billing_bp.route('/')
@login_required
@role_required('Admin', 'Receptionist')
def index():
    status = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)

    query = Invoice.query.filter_by(is_deleted=False)
    if status:
        query = query.filter_by(payment_status=status)

    pagination = query.order_by(Invoice.invoice_date.desc()).paginate(page=page, per_page=10, error_out=False)
    invoices = pagination.items

    total_billed = sum(inv.net_amount for inv in Invoice.query.filter_by(is_deleted=False).all())
    total_collected = sum(inv.paid_amount for inv in Invoice.query.filter_by(is_deleted=False).all())
    total_outstanding = max(0.0, round(total_billed - total_collected, 2))

    return render_template(
        'billing/index.html',
        invoices=invoices,
        pagination=pagination,
        selected_status=status,
        total_billed=total_billed,
        total_collected=total_collected,
        total_outstanding=total_outstanding
    )

@billing_bp.route('/invoices/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Receptionist')
def create_invoice():
    form = InvoiceForm()
    patients = Patient.query.filter_by(is_deleted=False, status='Active').all()
    admissions = Admission.query.filter_by(is_deleted=False).all()
    visits = Visit.query.filter_by(is_deleted=False).all()

    form.patient_id.choices = [(p.id, f"{p.patient_code} - {p.full_name}") for p in patients]
    form.admission_id.choices = [(0, '-- None / Outpatient --')] + [(a.id, f"{a.admission_number} ({a.admission_status})") for a in admissions]
    form.visit_id.choices = [(0, '-- None --')] + [(v.id, f"{v.visit_number} ({v.visit_date.date()})") for v in visits]

    if request.method == 'GET' and not form.invoice_number.data:
        count = Invoice.query.count() + 1
        form.invoice_number.data = f'INV-{datetime.utcnow().year}-{count:04d}'
        form.due_date.data = date.today() + timedelta(days=7)

    if form.validate_on_submit():
        adm_id = form.admission_id.data if form.admission_id.data != 0 else None
        v_id = form.visit_id.data if form.visit_id.data != 0 else None

        invoice = Invoice(
            invoice_number=form.invoice_number.data.strip(),
            patient_id=form.patient_id.data,
            admission_id=adm_id,
            visit_id=v_id,
            invoice_date=datetime.utcnow(),
            due_date=form.due_date.data,
            total_amount=0.0,
            discount_amount=form.discount_amount.data,
            tax_amount=form.tax_amount.data,
            net_amount=0.0,
            paid_amount=0.0,
            payment_status='Unpaid',
            created_by_id=current_user.id
        )
        db.session.add(invoice)
        db.session.commit()
        log_audit('CREATE', 'invoices', invoice.id, f'Created invoice {invoice.invoice_number}')
        flash(f'Invoice {invoice.invoice_number} generated. Now add item charges.', 'success')
        return redirect(url_for('billing.view_invoice', id=invoice.id))

    return render_template('billing/invoice_form.html', form=form, title='Generate Patient Invoice')

@billing_bp.route('/invoices/<int:id>')
@login_required
def view_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    item_form = InvoiceItemForm()
    payment_form = PaymentForm()
    payment_form.amount.data = invoice.balance_due
    return render_template('billing/invoice_view.html', invoice=invoice, item_form=item_form, payment_form=payment_form)

@billing_bp.route('/invoices/<int:id>/add-item', methods=['POST'])
@login_required
def add_item(id):
    invoice = Invoice.query.get_or_404(id)
    form = InvoiceItemForm()

    if form.validate_on_submit():
        sub = form.unit_price.data * form.quantity.data
        item = InvoiceItem(
            invoice_id=invoice.id,
            item_description=form.item_description.data.strip(),
            service_type=form.service_type.data,
            unit_price=form.unit_price.data,
            quantity=form.quantity.data,
            subtotal=sub,
            created_by_id=current_user.id
        )
        db.session.add(item)
        invoice.update_totals()
        db.session.commit()
        log_audit('CREATE', 'invoice_items', item.id, f'Added item to invoice #{invoice.id}')
        flash(f'Added {item.item_description} to invoice.', 'success')
    else:
        flash('Error adding invoice item.', 'danger')
    return redirect(url_for('billing.view_invoice', id=invoice.id))

@billing_bp.route('/invoices/<int:id>/pay', methods=['POST'])
@login_required
def post_payment(id):
    invoice = Invoice.query.get_or_404(id)
    form = PaymentForm()

    if form.validate_on_submit():
        amt = form.amount.data
        payment = Payment(
            invoice_id=invoice.id,
            payment_date=datetime.utcnow(),
            amount=amt,
            payment_method=form.payment_method.data,
            transaction_reference=form.transaction_reference.data.strip() if form.transaction_reference.data else None,
            notes=form.notes.data.strip() if form.notes.data else None,
            created_by_id=current_user.id
        )
        db.session.add(payment)
        invoice.paid_amount += amt
        if invoice.paid_amount >= invoice.net_amount:
            invoice.payment_status = 'Paid'
        else:
            invoice.payment_status = 'Partially Paid'
        db.session.commit()
        log_audit('CREATE', 'payments', payment.id, f'Recorded payment of PKR {amt} for invoice #{invoice.id}')
        flash(f'Payment of PKR {amt:,.2f} recorded successfully ({payment.payment_method}).', 'success')
    else:
        flash('Error processing payment.', 'danger')
    return redirect(url_for('billing.view_invoice', id=invoice.id))

@billing_bp.route('/invoices/<int:id>/delete', methods=['POST'])
@login_required
def delete_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    invoice.soft_delete(user_id=current_user.id)
    log_audit('SOFT_DELETE', 'invoices', invoice.id, f'Soft-deleted invoice {invoice.invoice_number}')
    flash(f'Invoice {invoice.invoice_number} soft-deleted.', 'info')
    return redirect(url_for('billing.index'))

# ----------------- Insurance Management -----------------
@billing_bp.route('/insurance')
@login_required
def insurance():
    providers = InsuranceProvider.query.filter_by(is_deleted=False).all()
    policies = PatientInsurance.query.filter_by(is_deleted=False).order_by(PatientInsurance.created_at.desc()).all()
    return render_template('billing/insurance.html', providers=providers, policies=policies)

@billing_bp.route('/insurance/providers/create', methods=['GET', 'POST'])
@login_required
def create_provider():
    form = InsuranceProviderForm()
    if form.validate_on_submit():
        provider = InsuranceProvider(
            provider_name=form.provider_name.data.strip(),
            policy_type=form.policy_type.data,
            contact_person=form.contact_person.data.strip() if form.contact_person.data else None,
            phone=form.phone.data.strip(),
            email=form.email.data.strip() if form.email.data else None,
            claim_address=form.claim_address.data.strip() if form.claim_address.data else None,
            co_pay_percentage=form.co_pay_percentage.data,
            created_by_id=current_user.id
        )
        db.session.add(provider)
        db.session.commit()
        log_audit('CREATE', 'insurance_providers', provider.id, f'Created insurance provider {provider.provider_name}')
        flash(f'Insurance Provider {provider.provider_name} added.', 'success')
        return redirect(url_for('billing.insurance'))
    return render_template('billing/provider_form.html', form=form, title='Add Insurance Provider')

@billing_bp.route('/insurance/policies/create', methods=['GET', 'POST'])
@login_required
def create_patient_policy():
    form = PatientInsuranceForm()
    patients = Patient.query.filter_by(is_deleted=False, status='Active').all()
    providers = InsuranceProvider.query.filter_by(is_deleted=False, status='Active').all()
    form.patient_id.choices = [(p.id, f"{p.patient_code} - {p.full_name}") for p in patients]
    form.provider_id.choices = [(pr.id, pr.provider_name) for pr in providers]

    if form.validate_on_submit():
        policy = PatientInsurance(
            patient_id=form.patient_id.data,
            provider_id=form.provider_id.data,
            policy_number=form.policy_number.data.strip(),
            coverage_limit=form.coverage_limit.data,
            valid_from=form.valid_from.data,
            valid_to=form.valid_to.data,
            is_verified=form.is_verified.data,
            created_by_id=current_user.id
        )
        db.session.add(policy)
        db.session.commit()
        log_audit('CREATE', 'patient_insurances', policy.id, f'Linked policy {policy.policy_number} to patient #{policy.patient_id}')
        flash(f'Insurance policy {policy.policy_number} linked to patient.', 'success')
        return redirect(url_for('billing.insurance'))

    return render_template('billing/policy_form.html', form=form, title='Link Patient Insurance Policy')
