import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, session
from flask_login import LoginManager
from config import config
from models import db, init_db, User
from extensions import csrf

def setup_logging(app):
    # Setup logging ke file logs/siadik.log dengan auto-rotation
    # Max 5MB per file, simpan 5 file terakhir
    log_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    handler = RotatingFileHandler(
        os.path.join(log_dir, 'siadik.log'),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('=== SIADIK Started ===')


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Pastikan folder uploads ada
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Init database
    init_db(app)

    # Setup logging ke file logs/siadik.log
    setup_logging(app)

    # Init CSRF Protection
    csrf.init_app(app)

    # Aktifkan permanent session
    @app.before_request
    def make_session_permanent():
        session.permanent = True

    # Init Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Silakan login untuk mengakses halaman ini.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Daftarkan blueprints
    from blueprints.public import public_bp
    from blueprints.auth import auth_bp
    from blueprints.admin import admin_bp
    from blueprints.superadmin import superadmin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(superadmin_bp, url_prefix='/superadmin')

    # Error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(429)
    def too_many_requests(e):
        return render_template('429.html'), 429

    # Inject variabel global ke semua template
    @app.context_processor
    def inject_globals():
        return dict(
            SISTEM_NAMA      = app.config['SISTEM_NAMA'],
            SISTEM_LENGKAP   = app.config['SISTEM_LENGKAP'],
            INSTANSI_NAMA    = app.config['INSTANSI_NAMA'],
            INSTANSI_LENGKAP = app.config['INSTANSI_LENGKAP'],
            TAHUN_FOKUS      = app.config['TAHUN_FOKUS'],
        )

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
