from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.laboratory import LabTest, LabOrder, LabOrderItem, LabResult
from app.models.patients import Patient
from app.models.staff import Doctor
from app.models.appointments import Visit
from app.forms.lab_forms import LabTestForm, LabOrderForm, LabOrderItemForm, LabResultForm
from app.services.audit_service import log_audit
from app.utils.decorators import role_required
from datetime import datetime

laboratory_bp = Blueprint('laboratory', __name__, url_prefix='/laboratory')

@laboratory_bp.route('/')
@login_required
def index():
    priority = request.args.get('priority', '').strip()
    status = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)

    query = LabOrder.query.filter_by(is_deleted=False)
    if priority:
        query = query.filter_by(priority=priority)
    if status:
        query = query.filter_by(order_status=status)

    pagination = query.order_by(LabOrder.order_date.desc()).paginate(page=page, per_page=10, error_out=False)
    orders = pagination.items
    total_tests = LabTest.query.filter_by(is_deleted=False).count()
    pending_orders = LabOrder.query.filter(LabOrder.is_deleted == False, LabOrder.order_status.in_(['Pending', 'Sample Collected', 'In Process'])).count()

    return render_template('laboratory/index.html', orders=orders, pagination=pagination, total_tests=total_tests, pending_orders=pending_orders, selected_priority=priority, selected_status=status)

# ----------------- Tests Catalog -----------------
@laboratory_bp.route('/tests', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'Laboratory Technician')
def tests():
    form = LabTestForm()
    if form.validate_on_submit():
        test = LabTest(
            test_code=form.test_code.data.strip().upper(),
            test_name=form.test_name.data.strip(),
            category=form.category.data,
            cost=form.cost.data,
            normal_range=form.normal_range.data.strip() if form.normal_range.data else None,
            unit_of_measure=form.unit_of_measure.data.strip() if form.unit_of_measure.data else None,
            description=form.description.data.strip() if form.description.data else None,
            created_by_id=current_user.id
        )
        db.session.add(test)
        db.session.commit()
        log_audit('CREATE', 'lab_tests', test.id, f'Added lab test {test.test_name} ({test.test_code})')
        flash(f'Diagnostic test {test.test_name} added to catalog.', 'success')
        return redirect(url_for('laboratory.tests'))

    tests_list = LabTest.query.filter_by(is_deleted=False).order_by(LabTest.test_name).all()
    return render_template('laboratory/tests.html', form=form, tests=tests_list)

@laboratory_bp.route('/tests/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_test(id):
    test = LabTest.query.get_or_404(id)
    form = LabTestForm(obj=test)
    if form.validate_on_submit():
        test.test_code = form.test_code.data.strip().upper()
        test.test_name = form.test_name.data.strip()
        test.category = form.category.data
        test.cost = form.cost.data
        test.normal_range = form.normal_range.data.strip() if form.normal_range.data else None
        test.unit_of_measure = form.unit_of_measure.data.strip() if form.unit_of_measure.data else None
        test.description = form.description.data.strip() if form.description.data else None
        test.updated_by_id = current_user.id
        db.session.commit()
        log_audit('UPDATE', 'lab_tests', test.id, f'Updated lab test {test.test_name}')
        flash('Diagnostic test updated.', 'success')
        return redirect(url_for('laboratory.tests'))
    return render_template('laboratory/test_form.html', form=form, test=test)

@laboratory_bp.route('/tests/<int:id>/delete', methods=['POST'])
@login_required
def delete_test(id):
    test = LabTest.query.get_or_404(id)
    test.soft_delete(user_id=current_user.id)
    log_audit('SOFT_DELETE', 'lab_tests', test.id, f'Soft-deleted test {test.test_name}')
    flash(f'Test {test.test_name} soft-deleted.', 'info')
    return redirect(url_for('laboratory.tests'))

# ----------------- Orders & Results -----------------
@laboratory_bp.route('/orders/create', methods=['GET', 'POST'])
@login_required
def create_order():
    form = LabOrderForm()
    patients = Patient.query.filter_by(is_deleted=False, status='Active').all()
    doctors = Doctor.query.filter_by(is_deleted=False, status='Active').all()
    visits_list = Visit.query.filter_by(is_deleted=False).order_by(Visit.visit_date.desc()).all()

    form.patient_id.choices = [(p.id, f"{p.patient_code} - {p.full_name}") for p in patients]
    form.doctor_id.choices = [(d.id, d.full_name) for d in doctors]
    form.visit_id.choices = [(0, '-- None / Outpatient Lab Request --')] + [(v.id, f"{v.visit_number} ({v.visit_date.date()})") for v in visits_list]

    if request.method == 'GET' and not form.order_number.data:
        count = LabOrder.query.count() + 1
        form.order_number.data = f'LAB-{datetime.utcnow().year}-{count:04d}'

    if form.validate_on_submit():
        v_id = form.visit_id.data if form.visit_id.data != 0 else None
        order = LabOrder(
            order_number=form.order_number.data.strip(),
            patient_id=form.patient_id.data,
            doctor_id=form.doctor_id.data,
            visit_id=v_id,
            order_date=datetime.utcnow(),
            priority=form.priority.data,
            order_status=form.order_status.data,
            created_by_id=current_user.id
        )
        db.session.add(order)
        db.session.commit()
        log_audit('CREATE', 'lab_orders', order.id, f'Created lab order {order.order_number}')
        flash(f'Requisition {order.order_number} created. Now add test items.', 'success')
        return redirect(url_for('laboratory.view_order', id=order.id))

    return render_template('laboratory/order_form.html', form=form, title='New Laboratory Requisition')

@laboratory_bp.route('/orders/<int:id>')
@login_required
def view_order(id):
    order = LabOrder.query.get_or_404(id)
    item_form = LabOrderItemForm()
    tests_list = LabTest.query.filter_by(is_deleted=False).all()
    item_form.lab_test_id.choices = [(t.id, f"{t.test_code} - {t.test_name} (PKR {t.cost})") for t in tests_list]
    result_form = LabResultForm()
    return render_template('laboratory/order_view.html', order=order, item_form=item_form, result_form=result_form)

@laboratory_bp.route('/orders/<int:id>/add-item', methods=['POST'])
@login_required
def add_order_item(id):
    order = LabOrder.query.get_or_404(id)
    form = LabOrderItemForm()
    tests_list = LabTest.query.filter_by(is_deleted=False).all()
    form.lab_test_id.choices = [(t.id, t.test_name) for t in tests_list]

    if form.validate_on_submit():
        item = LabOrderItem(
            lab_order_id=order.id,
            lab_test_id=form.lab_test_id.data,
            item_status='Pending',
            sample_type=form.sample_type.data,
            created_by_id=current_user.id
        )
        db.session.add(item)
        db.session.commit()
        log_audit('CREATE', 'lab_order_items', item.id, f'Added test item to lab order #{order.id}')
        flash('Diagnostic test added to requisition.', 'success')
    return redirect(url_for('laboratory.view_order', id=order.id))

@laboratory_bp.route('/order-items/<int:item_id>/record-result', methods=['POST'])
@login_required
def record_result(item_id):
    item = LabOrderItem.query.get_or_404(item_id)
    form = LabResultForm()

    if form.validate_on_submit():
        if item.result:
            result = item.result
            result.result_value = form.result_value.data.strip()
            result.reference_range_snapshot = form.reference_range_snapshot.data.strip() if form.reference_range_snapshot.data else item.lab_test.normal_range
            result.remarks = form.remarks.data.strip() if form.remarks.data else None
            result.is_abnormal = form.is_abnormal.data
            result.verified_at = datetime.utcnow()
            result.updated_by_id = current_user.id
        else:
            result = LabResult(
                lab_order_item_id=item.id,
                technician_id=current_user.id,
                result_value=form.result_value.data.strip(),
                reference_range_snapshot=form.reference_range_snapshot.data.strip() if form.reference_range_snapshot.data else item.lab_test.normal_range,
                remarks=form.remarks.data.strip() if form.remarks.data else None,
                is_abnormal=form.is_abnormal.data,
                verified_at=datetime.utcnow(),
                created_by_id=current_user.id
            )
            db.session.add(result)

        item.item_status = 'Completed'
        
        # Check if all items in order are completed
        all_completed = all(i.item_status == 'Completed' for i in item.lab_order.items)
        if all_completed:
            item.lab_order.order_status = 'Completed'

        db.session.commit()
        log_audit('CREATE', 'lab_results', result.id, f'Recorded lab result for item #{item.id}')
        flash('Lab result recorded and verified successfully.', 'success')
    else:
        flash('Error saving lab result. Please provide a result value.', 'danger')

    return redirect(url_for('laboratory.view_order', id=item.lab_order_id))

@laboratory_bp.route('/orders/<int:id>/delete', methods=['POST'])
@login_required
def delete_order(id):
    order = LabOrder.query.get_or_404(id)
    order.soft_delete(user_id=current_user.id)
    log_audit('SOFT_DELETE', 'lab_orders', order.id, f'Soft-deleted lab order {order.order_number}')
    flash(f'Lab order {order.order_number} soft-deleted.', 'info')
    return redirect(url_for('laboratory.index'))
