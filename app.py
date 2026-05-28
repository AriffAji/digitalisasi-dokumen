import os
from flask import Flask, render_template
from flask_login import LoginManager
from config import config
from models import db, init_db, User

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Pastikan folder uploads ada
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Init database
    init_db(app)

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
