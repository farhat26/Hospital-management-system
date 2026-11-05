from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.feedback import Feedback
from app.models.patients import Patient
from app.models.appointments import Visit
from app.models.staff import Department
from app.forms.feedback_forms import FeedbackForm
from app.services.audit_service import log_audit
from datetime import datetime

feedback_bp = Blueprint('feedback', __name__, url_prefix='/feedback')

@feedback_bp.route('/')
@login_required
def index():
    category = request.args.get('category', '').strip()
    status = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)

    query = Feedback.query.filter_by(is_deleted=False)
    if category:
        query = query.filter_by(category=category)
    if status:
        query = query.filter_by(resolution_status=status)

    pagination = query.order_by(Feedback.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    feedbacks = pagination.items

    avg_rating = db.session.query(db.func.avg(Feedback.rating)).filter(Feedback.is_deleted == False).scalar() or 0.0

    return render_template(
        'feedback/index.html',
        feedbacks=feedbacks,
        pagination=pagination,
        avg_rating=round(float(avg_rating), 1),
        selected_category=category,
        selected_status=status
    )

@feedback_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = FeedbackForm()
    patients = Patient.query.filter_by(is_deleted=False, status='Active').all()
    visits = Visit.query.filter_by(is_deleted=False).order_by(Visit.visit_date.desc()).all()
    depts = Department.query.filter_by(is_deleted=False, status='Active').all()

    form.patient_id.choices = [(0, '-- Anonymous / Walk-in --')] + [(p.id, f"{p.patient_code} - {p.full_name}") for p in patients]
    form.visit_id.choices = [(0, '-- None --')] + [(v.id, f"{v.visit_number} ({v.visit_date.date()})") for v in visits]
    form.department_id.choices = [(0, '-- General Hospital --')] + [(d.id, d.name) for d in depts]

    if form.validate_on_submit():
        p_id = form.patient_id.data if form.patient_id.data != 0 else None
        v_id = form.visit_id.data if form.visit_id.data != 0 else None
        d_id = form.department_id.data if form.department_id.data != 0 else None

        fb = Feedback(
            patient_id=p_id,
            visit_id=v_id,
            department_id=d_id,
            rating=form.rating.data,
            category=form.category.data,
            comments=form.comments.data.strip(),
            is_anonymous=form.is_anonymous.data or (p_id is None),
            resolution_status=form.resolution_status.data,
            created_by_id=current_user.id
        )
        db.session.add(fb)
        db.session.commit()
        log_audit('CREATE', 'feedback', fb.id, f'Submitted patient feedback rating {fb.rating} stars')
        flash('Thank you! Patient feedback recorded successfully.', 'success')
        return redirect(url_for('feedback.index'))

    return render_template('feedback/form.html', form=form, title='Submit Patient Feedback')

@feedback_bp.route('/<int:id>/status', methods=['POST'])
@login_required
def update_status(id):
    fb = Feedback.query.get_or_404(id)
    new_status = request.form.get('resolution_status')
    if new_status:
        fb.resolution_status = new_status
        fb.updated_by_id = current_user.id
        db.session.commit()
        log_audit('UPDATE', 'feedback', fb.id, f'Updated feedback status to {new_status}')
        flash(f'Feedback status changed to {new_status}.', 'success')
    return redirect(url_for('feedback.index'))

@feedback_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    fb = Feedback.query.get_or_404(id)
    fb.soft_delete(user_id=current_user.id)
    log_audit('SOFT_DELETE', 'feedback', fb.id, f'Soft-deleted feedback entry #{fb.id}')
    flash('Feedback entry soft-deleted.', 'info')
    return redirect(url_for('feedback.index'))
