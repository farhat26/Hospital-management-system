from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.patients import patients_bp
from app.routes.doctors import doctors_bp
from app.routes.staff import staff_bp
from app.routes.appointments import appointments_bp
from app.routes.pharmacy import pharmacy_bp
from app.routes.laboratory import laboratory_bp
from app.routes.wards import wards_bp
from app.routes.billing import billing_bp
from app.routes.surgery import surgery_bp
from app.routes.feedback import feedback_bp
from app.routes.admin import admin_bp

__all__ = [
    'auth_bp',
    'dashboard_bp',
    'patients_bp',
    'doctors_bp',
    'staff_bp',
    'appointments_bp',
    'pharmacy_bp',
    'laboratory_bp',
    'wards_bp',
    'billing_bp',
    'surgery_bp',
    'feedback_bp',
    'admin_bp'
]
