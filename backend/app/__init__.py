import os
import sys

# Ensure root workspace directory is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from flask import Flask
from flask_login import LoginManager
from backend.app.config import Config
from backend.app.models import db, Admin

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access the Admin Panel.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Admin, int(user_id))

def create_app(config_class=Config):
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    app.config.from_object(config_class)

    # Ensure instance folder exists or use /tmp on Vercel read-only filesystem
    if os.environ.get('VERCEL') or os.environ.get('VERCEL_ENV'):
        app.instance_path = '/tmp'
    else:
        try:
            os.makedirs(app.instance_path, exist_ok=True)
        except Exception:
            app.instance_path = '/tmp'

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from backend.app.routes.auth import auth_bp
    from backend.app.routes.admin import admin_bp
    from backend.app.routes.attendance import attendance_bp
    from backend.app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(api_bp)

    # Database initialization & Admin Seeding
    with app.app_context():
        db.create_all()
        if not app.config.get('TESTING'):
            seed_admin_account(app)

    return app

def seed_admin_account(app):
    admin_username = app.config.get('ADMIN_USERNAME', 'admin')
    admin_password = app.config.get('ADMIN_PASSWORD', 'Admin@123')
    admin_email = app.config.get('ADMIN_EMAIL', 'admin@college.edu')

    existing_admin = Admin.query.filter_by(username=admin_username).first()
    if not existing_admin:
        new_admin = Admin(
            username=admin_username,
            email=admin_email
        )
        new_admin.set_password(admin_password)
        db.session.add(new_admin)
        db.session.commit()
        print(f"[*] Default Admin account initialized: '{admin_username}'")
