import os
from flask import Flask, render_template, request, session
from config import Config
from app.extensions import db, login_manager, csrf
from app.models.auth import User
from app.models import ALL_MODELS
from app.routes import (
    auth_bp, dashboard_bp, patients_bp, doctors_bp, staff_bp,
    appointments_bp, pharmacy_bp, laboratory_bp, wards_bp,
    billing_bp, surgery_bp, feedback_bp, admin_bp
)
from app.routes.preferences import preferences_bp, THEME_COOKIE, VALID_THEMES
from app.services.seed_data import seed_database
from flask_login import current_user
from datetime import datetime

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # User loader callback for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except (ValueError, TypeError):
            return None

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(doctors_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(pharmacy_bp)
    app.register_blueprint(laboratory_bp)
    app.register_blueprint(wards_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(surgery_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(preferences_bp)

    # Session state: remember the last pages a signed-in user opened
    @app.before_request
    def track_recent_pages():
        if (request.method != 'GET' or request.endpoint is None
                or request.endpoint == 'static'
                or request.endpoint.startswith('preferences.')
                or request.endpoint.startswith('auth.')
                or not current_user.is_authenticated):
            return
        recent = [r for r in session.get('recent_pages', []) if r['url'] != request.path]
        recent.insert(0, {'url': request.path, 'label': request.endpoint.replace('.', ' / ').replace('_', ' ').title()})
        session['recent_pages'] = recent[:5]
        session['page_views'] = session.get('page_views', 0) + 1

    # Global template context processor
    @app.context_processor
    def inject_global_context():
        # Soft delete recycle bin badge count for Admin
        recycle_count = 0
        try:
            for m in ALL_MODELS:
                recycle_count += m.query.filter_by(is_deleted=True).count()
        except Exception:
            recycle_count = 0

        theme = request.cookies.get(THEME_COOKIE, 'light')
        return {
            'theme': theme if theme in VALID_THEMES else 'light',
            'recent_pages': session.get('recent_pages', []),
            'page_views': session.get('page_views', 0),
            'now': datetime.utcnow(),
            'total_models_count': len(ALL_MODELS),
            'recycle_bin_count': recycle_count
        }

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # Custom Flask CLI command: flask seed
    @app.cli.command("seed")
    def seed_cli():
        """Seed the database with complete initial data."""
        with app.app_context():
            db.create_all()
            seed_database()
            print("Database tables created and seeded successfully!")

    return app
