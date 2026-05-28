from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def role_required(*roles):
    """Decorator: hanya role tertentu yang bisa akses."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Silakan login untuk mengakses halaman ini.', 'warning')
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                flash('Anda tidak memiliki akses ke halaman ini.', 'danger')
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def superadmin_required(f):
    return role_required('superadmin')(f)

def admin_required(f):
    return role_required('admin', 'superadmin')(f)

def user_required(f):
    return role_required('user', 'admin', 'superadmin')(f)
