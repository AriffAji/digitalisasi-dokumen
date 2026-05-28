from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user
from blueprints.superadmin import superadmin_bp
from decorators import superadmin_required
from models import db, User, Kamar, SubKamar, Dokumen
from datetime import datetime

# ===== DASHBOARD =====
@superadmin_bp.route('/dashboard')
@superadmin_required
def dashboard():
    total_dokumen   = Dokumen.query.count()
    total_kamar     = Kamar.query.count()
    total_admin     = User.query.filter_by(role='admin').count()
    total_user      = User.query.filter_by(role='user').count()
    kamar_aktif     = Kamar.query.filter_by(status='aktif').count()

    bulan_ini = datetime.now().month
    tahun_ini = datetime.now().year
    upload_bulan_ini = Dokumen.query.filter(
        db.extract('month', Dokumen.created_at) == bulan_ini,
        db.extract('year',  Dokumen.created_at) == tahun_ini
    ).count()

    kamar_list      = Kamar.query.order_by(Kamar.urutan).all()
    dokumen_terbaru = Dokumen.query.order_by(Dokumen.created_at.desc()).limit(5).all()
    admin_list      = User.query.filter_by(role='admin').all()

    return render_template('superadmin/dashboard.html',
        total_dokumen    = total_dokumen,
        total_kamar      = total_kamar,
        total_admin      = total_admin,
        total_user       = total_user,
        kamar_aktif      = kamar_aktif,
        upload_bulan_ini = upload_bulan_ini,
        kamar_list       = kamar_list,
        dokumen_terbaru  = dokumen_terbaru,
        admin_list       = admin_list,
    )

# ===== KAMAR =====
@superadmin_bp.route('/kamar')
@superadmin_required
def kamar():
    kamar_list = Kamar.query.order_by(Kamar.urutan).all()
    return render_template('superadmin/kamar.html', kamar_list=kamar_list)

@superadmin_bp.route('/kamar/tambah', methods=['POST'])
@superadmin_required
def kamar_tambah():
    nama      = request.form.get('nama', '').strip()
    deskripsi = request.form.get('deskripsi', '').strip()
    status    = request.form.get('status', 'terkunci')
    urutan    = request.form.get('urutan', 99, type=int)

    if not nama:
        flash('Nama kamar tidak boleh kosong.', 'danger')
        return redirect(url_for('superadmin.kamar'))

    k = Kamar(nama=nama, deskripsi=deskripsi, status=status, urutan=urutan)
    db.session.add(k)
    db.session.commit()
    flash(f'Kamar "{nama}" berhasil ditambahkan.', 'success')
    return redirect(url_for('superadmin.kamar'))

@superadmin_bp.route('/kamar/<int:kamar_id>/edit', methods=['POST'])
@superadmin_required
def kamar_edit(kamar_id):
    k = Kamar.query.get_or_404(kamar_id)
    k.nama      = request.form.get('nama', k.nama).strip()
    k.deskripsi = request.form.get('deskripsi', '').strip()
    k.status    = request.form.get('status', k.status)
    k.urutan    = request.form.get('urutan', k.urutan, type=int)
    db.session.commit()
    flash(f'Kamar "{k.nama}" berhasil diperbarui.', 'success')
    return redirect(url_for('superadmin.kamar'))

@superadmin_bp.route('/kamar/<int:kamar_id>/hapus', methods=['POST'])
@superadmin_required
def kamar_hapus(kamar_id):
    k = Kamar.query.get_or_404(kamar_id)
    if k.total_dokumen > 0:
        flash(f'Kamar "{k.nama}" masih memiliki dokumen. Tidak bisa dihapus.', 'danger')
        return redirect(url_for('superadmin.kamar'))
    nama = k.nama
    db.session.delete(k)
    db.session.commit()
    flash(f'Kamar "{nama}" berhasil dihapus.', 'success')
    return redirect(url_for('superadmin.kamar'))

# ===== ADMIN =====
@superadmin_bp.route('/admin-list')
@superadmin_required
def admin_list():
    kamar_list = Kamar.query.filter_by(status='aktif').order_by(Kamar.urutan).all()
    admin_list = User.query.filter_by(role='admin').order_by(User.nama).all()
    return render_template('superadmin/admin.html',
        admin_list = admin_list,
        kamar_list = kamar_list,
    )

@superadmin_bp.route('/admin-list/tambah', methods=['POST'])
@superadmin_required
def admin_tambah():
    nama     = request.form.get('nama', '').strip()
    email    = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '').strip()
    kamar_id = request.form.get('kamar_id', type=int)

    if not nama or not email or not password or not kamar_id:
        flash('Semua field wajib diisi.', 'danger')
        return redirect(url_for('superadmin.admin_list'))

    if User.query.filter_by(email=email).first():
        flash(f'Email "{email}" sudah terdaftar.', 'danger')
        return redirect(url_for('superadmin.admin_list'))

    kamar = Kamar.query.get(kamar_id)
    if not kamar:
        flash('Kamar tidak valid.', 'danger')
        return redirect(url_for('superadmin.admin_list'))

    u = User(nama=nama, email=email, role='admin', kamar_id=kamar_id)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    flash(f'Admin "{nama}" untuk kamar "{kamar.nama}" berhasil ditambahkan.', 'success')
    return redirect(url_for('superadmin.admin_list'))

@superadmin_bp.route('/admin-list/<int:admin_id>/hapus', methods=['POST'])
@superadmin_required
def admin_hapus(admin_id):
    u = User.query.get_or_404(admin_id)
    if u.role != 'admin':
        flash('Bukan akun admin.', 'danger')
        return redirect(url_for('superadmin.admin_list'))
    nama = u.nama
    db.session.delete(u)
    db.session.commit()
    flash(f'Admin "{nama}" berhasil dihapus.', 'success')
    return redirect(url_for('superadmin.admin_list'))

@superadmin_bp.route('/admin-list/<int:admin_id>/toggle', methods=['POST'])
@superadmin_required
def admin_toggle(admin_id):
    u = User.query.get_or_404(admin_id)
    u.is_active = not u.is_active
    db.session.commit()
    status = 'diaktifkan' if u.is_active else 'dinonaktifkan'
    flash(f'Admin "{u.nama}" berhasil {status}.', 'success')
    return redirect(url_for('superadmin.admin_list'))

@superadmin_bp.route('/admin-list/<int:admin_id>/reset-password', methods=['POST'])
@superadmin_required
def admin_reset_password(admin_id):
    u = User.query.get_or_404(admin_id)
    password_baru = request.form.get('password_baru', '').strip()
    if not password_baru:
        flash('Password baru tidak boleh kosong.', 'danger')
        return redirect(url_for('superadmin.admin_list'))
    u.set_password(password_baru)
    db.session.commit()
    flash(f'Password admin "{u.nama}" berhasil direset.', 'success')
    return redirect(url_for('superadmin.admin_list'))
