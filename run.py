import os
import sys
from app import create_app
from app.extensions import db
from app.services.seed_data import seed_database
from app.models.auth import Role

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Ensure database and all 56 tables are created
        db.create_all()
        # Auto-seed if not seeded yet
        if not Role.query.first():
            print("Detected empty database. Running automatic seeding for 56 tables...")
            seed_database()
            print("Auto-seeding complete! Ready for login.")

    print("\n" + "="*70)
    print("  HOSPITAL MANAGEMENT SYSTEM (HMS) - FLASK WEB ENGINEERING")
    print("="*70)
    print("  Status: Server running on http://127.0.0.1:5000")
    print("  Default Admin Credentials:")
    print("    Username / Email: admin@hospital.com")
    print("    Password:         Admin@123")
    print("  Other sample logins:")
    print("    Doctor:       sarah.ahmed@hospital.com  / Doctor@123")
    print("    Receptionist: reception@hospital.com    / Reception@123")
    print("    Nurse:        nurse.fatima@hospital.com / Nurse@123")
    print("    Pharmacist:   pharma@hospital.com       / Pharma@123")
    print("    Lab Tech:     lab@hospital.com          / Lab@123")
    print("="*70 + "\n")

    app.run(host='127.0.0.1', port=5000, debug=True)
