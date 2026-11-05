"""Production entry point (used by Render / gunicorn).

Creates the tables and seeds demo data on first start, because Render's free
tier gives a fresh, empty filesystem after every deploy or restart.
"""
from app import create_app
from app.extensions import db
from app.models.auth import Role
from app.services.seed_data import seed_database

app = create_app()

with app.app_context():
    db.create_all()
    if not Role.query.first():
        seed_database()
