from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from blueprints.auth import auth_bp
from models import db, User

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Kalau sudah login, redirect sesuai role
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Email atau password salah. Silakan coba lagi.', 'danger')
            return render_template('auth/login.html')

        if not user.is_active:
            flash('Akun Anda telah dinonaktifkan. Hubungi administrator.', 'danger')
            return render_template('auth/login.html')

        login_user(user, remember=remember)
        flash(f'Selamat datang, {user.nama}!', 'success')
        return _redirect_by_role(user)

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    nama = current_user.nama
    logout_user()
    flash(f'Sampai jumpa, {nama}! Anda telah keluar.', 'success')
    return redirect(url_for('auth.login'))


def _redirect_by_role(user):
    """Redirect ke dashboard sesuai role."""
    if user.role == 'superadmin':
        return redirect(url_for('superadmin.dashboard'))
    elif user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    else:
        return redirect(url_for('public.index'))
