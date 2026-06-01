from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from blueprints.auth import auth_bp
from models import db, User

# Tracking percobaan login gagal per IP (in-memory)
# Key: IP address, Value: {'count': int, 'reset_time': datetime}
_login_attempts = {}

def _check_rate_limit(ip):
    """Cek apakah IP sudah melebihi batas percobaan login (5x per 5 menit)."""
    from datetime import datetime, timedelta
    now = datetime.now()

    if ip not in _login_attempts:
        _login_attempts[ip] = {'count': 0, 'reset_time': now + timedelta(minutes=5)}

    data = _login_attempts[ip]

    # Reset counter kalau sudah lewat waktu
    if now > data['reset_time']:
        _login_attempts[ip] = {'count': 0, 'reset_time': now + timedelta(minutes=5)}
        return False, 0

    return data['count'] >= 5, data['count']

def _increment_attempt(ip):
    """Tambah counter percobaan gagal."""
    from datetime import datetime, timedelta
    now = datetime.now()
    if ip not in _login_attempts:
        _login_attempts[ip] = {'count': 0, 'reset_time': now + timedelta(minutes=5)}
    _login_attempts[ip]['count'] += 1

def _reset_attempt(ip):
    """Reset counter setelah login berhasil."""
    if ip in _login_attempts:
        del _login_attempts[ip]

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Kalau sudah login, redirect sesuai role
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    if request.method == 'POST':
        ip = request.remote_addr
        blocked, attempts = _check_rate_limit(ip)

        # Blokir jika sudah 5x gagal
        if blocked:
            flash('Terlalu banyak percobaan login. Coba lagi dalam 5 menit.', 'danger')
            return render_template('auth/login.html'), 429

        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            _increment_attempt(ip)
            sisa = 5 - (_login_attempts.get(ip, {}).get('count', 0))
            current_app.logger.warning(f'LOGIN GAGAL: {email} | ip={ip} | sisa={sisa}x')
            flash(f'Email atau password salah. Sisa percobaan: {sisa}x', 'danger')
            return render_template('auth/login.html')

        if not user.is_active:
            flash('Akun Anda telah dinonaktifkan. Hubungi administrator.', 'danger')
            return render_template('auth/login.html')

        # Login berhasil — reset counter
        _reset_attempt(ip)
        login_user(user, remember=remember)
        current_app.logger.info(f'LOGIN: {user.email} | role={user.role} | ip={ip}')
        flash(f'Selamat datang, {user.nama}!', 'success')
        return _redirect_by_role(user)

    return render_template('auth/login.html')


@auth_bp.route('/profil', methods=['GET', 'POST'])
@login_required
def profil():
    import re
    if request.method == 'POST':
        password_lama  = request.form.get('password_lama', '')
        password_baru  = request.form.get('password_baru', '')
        konfirmasi     = request.form.get('konfirmasi', '')

        # Cek password lama
        if not current_user.check_password(password_lama):
            flash('Password lama salah.', 'danger')
            return redirect(url_for('auth.profil'))

        # Cek konfirmasi
        if password_baru != konfirmasi:
            flash('Konfirmasi password tidak cocok.', 'danger')
            return redirect(url_for('auth.profil'))

        # Cek policy password
        if len(password_baru) < 8:
            flash('Password minimal 8 karakter.', 'danger')
            return redirect(url_for('auth.profil'))
        if not re.search(r'[A-Za-z]', password_baru):
            flash('Password harus mengandung huruf.', 'danger')
            return redirect(url_for('auth.profil'))
        if not re.search(r'[0-9]', password_baru):
            flash('Password harus mengandung angka.', 'danger')
            return redirect(url_for('auth.profil'))

        current_user.set_password(password_baru)
        from models import db
        db.session.commit()
        current_app.logger.info(f'GANTI PASSWORD: {current_user.email}')
        flash('Password berhasil diubah!', 'success')
        return redirect(url_for('auth.profil'))

    return render_template('auth/profil.html')


@auth_bp.route('/logout')
@login_required
def logout():
    nama  = current_user.nama
    email = current_user.email
    current_app.logger.info(f'LOGOUT: {email}')
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
