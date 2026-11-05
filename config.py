import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'hospital-management-secret-key-2026-secure-uni-project')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join(BASE_DIR, "hospital.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session and Cookie settings for Web Engineering Rubric
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('RENDER') is not None  # HTTPS only when hosted on Render
    REMEMBER_COOKIE_DURATION = 86400 * 7  # 7 days
    PERMANENT_SESSION_LIFETIME = 86400    # 24 hours
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
