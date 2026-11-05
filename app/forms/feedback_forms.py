from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Optional

class FeedbackForm(FlaskForm):
    patient_id = SelectField('Patient (Optional for Anonymous)', coerce=int, validators=[Optional()])
    visit_id = SelectField('Linked Visit (Optional)', coerce=int, validators=[Optional()])
    department_id = SelectField('Department', coerce=int, validators=[Optional()])
    rating = SelectField('Experience Rating', choices=[(5, '★★★★★ (5 Stars - Excellent)'), (4, '★★★★☆ (4 Stars - Very Good)'), (3, '★★★☆☆ (3 Stars - Satisfactory)'), (2, '★★☆☆☆ (2 Stars - Needs Improvement)'), (1, '★☆☆☆☆ (1 Star - Poor)')], coerce=int, default=5, validators=[DataRequired()])
    category = SelectField('Feedback Domain', choices=[('Doctor Care', 'Doctor & Clinical Care'), ('Staff Behavior', 'Nursing & Staff Courtesy'), ('Cleanliness', 'Cleanliness & Hygiene'), ('Wait Time', 'Queue & Waiting Duration'), ('Overall Experience', 'Overall Hospital Experience')], default='Overall Experience')
    comments = TextAreaField('Detailed Comments & Recommendations', validators=[DataRequired()])
    is_anonymous = BooleanField('Submit Anonymously')
    resolution_status = SelectField('Status', choices=[('Submitted', 'Submitted'), ('Reviewed', 'Under Review'), ('Action Taken', 'Action Taken & Resolved')], default='Submitted')
    submit = SubmitField('Submit Feedback')
