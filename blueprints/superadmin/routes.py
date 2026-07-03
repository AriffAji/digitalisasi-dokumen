import os
import re
import time
from datetime import datetime

from flask import (
    render_template, redirect, url_for, flash, request, current_app, jsonify
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from blueprints.superadmin import superadmin_bp
from decorators import superadmin_required
from models import db, User, Kamar, SubKamar, Dokumen, ShareLink


# ===== PASSWORD VALIDATION =====
def _validate_password(password):
    """
    Validasi password sesuai policy:
    - Minimal 8 karakter
    - Harus ada huruf
    - Harus ada angka
    """
    if len(password) < 8:
        return False, "Password minimal 8 karakter"
    if not re.search(r'[A-Za-z]', password):
        return False, "Password harus mengandung huruf"
    if not re.search(r'[0-9]', password):
        return False, "Password harus mengandung angka"
    return True, ""


# ===== DASHBOARD =====
@superadmin_bp.route('/dashboard')
@superadmin_required
def dashboard():
    """Dashboard superadmin — overview sistem."""
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


# ===== LOG VIEWER =====
@superadmin_bp.route('/log')
@superadmin_required
def log_viewer():
    """Viewer untuk siadik.log — 200 baris terakhir dengan filter."""
    log_path = os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')),
        'logs', 'siadik.log'
    )
    filter_type = request.args.get('filter', '').upper()
    logs  = []
    stats = {'login': 0, 'gagal': 0, 'upload': 0, 'hapus': 0}

    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Parse setiap baris log
        pattern = re.compile(r'\[(.+?)\] (\w+) - (.+)')
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            match = pattern.match(line)
            if not match:
                continue
            waktu, level, pesan = match.groups()

            # Hitung statistik
            if 'LOGIN:' in pesan:        stats['login'] += 1
            if 'LOGIN GAGAL' in pesan:   stats['gagal'] += 1
            if 'UPLOAD:' in pesan:       stats['upload'] += 1
            if 'HAPUS DOKUMEN' in pesan: stats['hapus'] += 1

            # Apply filter
            if filter_type and filter_type not in pesan:
                continue

            logs.append({'waktu': waktu, 'level': level, 'pesan': pesan})

        # Batasi 200 baris terakhir
        logs = logs[:200]

    return render_template('superadmin/log_viewer.html',
        logs        = logs,
        stats       = stats,
        filter      = filter_type,
    )


# ===== KAMAR MANAGEMENT =====
@superadmin_bp.route('/kamar')
@superadmin_required
def kamar():
    """List dan manage semua kamar."""
    kamar_list = Kamar.query.order_by(Kamar.urutan).all()
    return render_template('superadmin/kamar.html', kamar_list=kamar_list)


@superadmin_bp.route('/kamar/tambah', methods=['POST'])
@superadmin_required
def kamar_tambah():
    """Tambah kamar baru."""
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
    """Edit kamar."""
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
    """Hapus kamar (hanya jika tidak ada dokumen)."""
    k = Kamar.query.get_or_404(kamar_id)
    if k.total_dokumen > 0:
        flash(f'Kamar "{k.nama}" masih memiliki dokumen. Tidak bisa dihapus.', 'danger')
        return redirect(url_for('superadmin.kamar'))
    nama = k.nama
    db.session.delete(k)
    db.session.commit()
    flash(f'Kamar "{nama}" berhasil dihapus.', 'success')
    return redirect(url_for('superadmin.kamar'))


# ===== ADMIN MANAGEMENT =====
@superadmin_bp.route('/admin-list')
@superadmin_required
def admin_list():
    """List dan manage semua admin."""
    kamar_list = Kamar.query.filter_by(status='aktif').order_by(Kamar.urutan).all()
    admin_list = User.query.filter_by(role='admin').order_by(User.nama).all()
    return render_template('superadmin/admin.html',
        admin_list = admin_list,
        kamar_list = kamar_list,
    )


@superadmin_bp.route('/admin-list/tambah', methods=['POST'])
@superadmin_required
def admin_tambah():
    """Tambah admin baru."""
    nama     = request.form.get('nama', '').strip()
    email    = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '').strip()
    kamar_id = request.form.get('kamar_id', type=int)

    if not nama or not email or not password or not kamar_id:
        flash('Semua field wajib diisi.', 'danger')
        return redirect(url_for('superadmin.admin_list'))

    valid, pesan = _validate_password(password)
    if not valid:
        flash(pesan, 'danger')
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
    current_app.logger.info(
        f'TAMBAH ADMIN: {current_user.email} | admin_baru="{nama}" | kamar="{kamar.nama}"'
    )
    flash(f'Admin "{nama}" untuk kamar "{kamar.nama}" berhasil ditambahkan.', 'success')
    return redirect(url_for('superadmin.admin_list'))


@superadmin_bp.route('/admin-list/<int:admin_id>/hapus', methods=['POST'])
@superadmin_required
def admin_hapus(admin_id):
    """Hapus admin."""
    u = User.query.get_or_404(admin_id)
    if u.role != 'admin':
        flash('Bukan akun admin.', 'danger')
        return redirect(url_for('superadmin.admin_list'))
    nama = u.nama
    email_admin = u.email
    db.session.delete(u)
    db.session.commit()
    current_app.logger.warning(
        f'HAPUS ADMIN: {current_user.email} | admin="{nama}" ({email_admin})'
    )
    flash(f'Admin "{nama}" berhasil dihapus.', 'success')
    return redirect(url_for('superadmin.admin_list'))


@superadmin_bp.route('/admin-list/<int:admin_id>/toggle', methods=['POST'])
@superadmin_required
def admin_toggle(admin_id):
    """Aktifkan/nonaktifkan admin."""
    u = User.query.get_or_404(admin_id)
    u.is_active = not u.is_active
    db.session.commit()
    status = 'diaktifkan' if u.is_active else 'dinonaktifkan'
    flash(f'Admin "{u.nama}" berhasil {status}.', 'success')
    return redirect(url_for('superadmin.admin_list'))


@superadmin_bp.route('/admin-list/<int:admin_id>/reset-password', methods=['POST'])
@superadmin_required
def admin_reset_password(admin_id):
    """Reset password admin."""
    u = User.query.get_or_404(admin_id)
    password_baru = request.form.get('password_baru', '').strip()
    if not password_baru:
        flash('Password baru tidak boleh kosong.', 'danger')
        return redirect(url_for('superadmin.admin_list'))

    valid, pesan = _validate_password(password_baru)
    if not valid:
        flash(pesan, 'danger')
        return redirect(url_for('superadmin.admin_list'))

    u.set_password(password_baru)
    db.session.commit()
    current_app.logger.warning(
        f'RESET PASSWORD: {current_user.email} | target="{u.nama}" ({u.email})'
    )
    flash(f'Password admin "{u.nama}" berhasil direset.', 'success')
    return redirect(url_for('superadmin.admin_list'))


# ===== DOKUMEN MANAGEMENT (SEMUA KAMAR) =====
@superadmin_bp.route('/dokumen')
@superadmin_required
def dokumen():
    """List dan manage dokumen dari semua kamar."""
    kamar_list     = Kamar.query.filter_by(status='aktif').order_by(Kamar.urutan).all()
    kamar_id       = request.args.get('kamar_id', type=int)
    sub_kamar_id   = request.args.get('sub_kamar_id', type=int)

    sub_kamar_list = []
    if kamar_id:
        sub_kamar_list = SubKamar.query.filter_by(kamar_id=kamar_id).all()

    query = Dokumen.query.join(SubKamar).join(Kamar)
    if sub_kamar_id:
        query = query.filter(Dokumen.sub_kamar_id == sub_kamar_id)
    elif kamar_id:
        query = query.filter(SubKamar.kamar_id == kamar_id)

    dokumen_list    = query.order_by(Dokumen.created_at.desc()).all()
    kamar_aktif     = Kamar.query.get(kamar_id) if kamar_id else None
    sub_kamar_aktif = SubKamar.query.get(sub_kamar_id) if sub_kamar_id else None

    return render_template('superadmin/dokumen.html',
        kamar_list      = kamar_list,
        sub_kamar_list  = sub_kamar_list,
        dokumen_list    = dokumen_list,
        kamar_aktif     = kamar_aktif,
        sub_kamar_aktif = sub_kamar_aktif,
        kamar_id        = kamar_id,
        sub_kamar_id    = sub_kamar_id,
    )


@superadmin_bp.route('/dokumen/upload', methods=['POST'])
@superadmin_required
def dokumen_upload():
    """Upload dokumen ke sub-kamar."""
    kamar_id     = request.form.get('kamar_id', type=int)
    sub_kamar_id = request.form.get('sub_kamar_id', type=int)
    nomor        = request.form.get('nomor_dokumen', '').strip()
    judul        = request.form.get('judul', '').strip()
    status       = request.form.get('status', 'aktif')
    visibilitas  = request.form.get('visibilitas', 'internal')
    file         = request.files.get('file')

    if not sub_kamar_id or not judul or not file:
        flash('Sub-kamar, judul, dan file wajib diisi.', 'danger')
        return redirect(url_for('superadmin.dokumen', kamar_id=kamar_id))

    sk = SubKamar.query.get(sub_kamar_id)
    if not sk:
        flash('Sub-kamar tidak valid.', 'danger')
        return redirect(url_for('superadmin.dokumen'))

    # Validasi file — hanya PDF
    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() == 'pdf'):
        flash('Hanya file PDF yang diizinkan.', 'danger')
        return redirect(url_for('superadmin.dokumen', kamar_id=kamar_id))

    # Validasi magic bytes PDF
    header = file.read(4)
    file.seek(0)
    if header != b'%PDF':
        flash('File tidak valid. Pastikan file adalah PDF asli.', 'danger')
        return redirect(url_for('superadmin.dokumen', kamar_id=kamar_id))

    # Potong nama file kalau > 200 karakter, judul tetap utuh di DB
    filename = secure_filename(file.filename)
    if len(filename) > 200:
        name, ext = filename.rsplit('.', 1)
        filename  = name[:195] + '.' + ext
    unique_name = f"{int(time.time())}_{filename}"
    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name))

    dok = Dokumen(
        sub_kamar_id  = sub_kamar_id,
        nomor_dokumen = nomor,
        judul         = judul,
        file_path     = unique_name,
        status        = status,
        visibilitas   = visibilitas,
        uploaded_by   = current_user.id,
    )
    db.session.add(dok)
    db.session.commit()

    current_app.logger.info(
        f'UPLOAD (SA): {current_user.email} | dokumen="{judul}" | kamar="{sk.kamar.nama}"'
    )
    from blueprints.public.routes import clear_dokumen_cache
    clear_dokumen_cache(sub_kamar_id=sub_kamar_id, kamar_id=sk.kamar_id)

    flash(f'Dokumen "{judul}" berhasil diupload.', 'success')
    return redirect(url_for('superadmin.dokumen', kamar_id=sk.kamar_id, sub_kamar_id=sub_kamar_id))


# @superadmin_bp.route('/dokumen/<int:dok_id>/hapus', methods=['POST'])
# @superadmin_required
# def dokumen_hapus(dok_id):
#     """Hapus dokumen dan file fisik-nya."""
#     dok = Dokumen.query.get_or_404(dok_id)

#     file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], dok.file_path)
#     if os.path.exists(file_path):
#         os.remove(file_path)

#     kamar_id     = dok.sub_kamar.kamar_id
#     sub_kamar_id = dok.sub_kamar_id
#     judul        = dok.judul

#     db.session.delete(dok)
#     db.session.commit()

#     current_app.logger.warning(
#         f'HAPUS DOKUMEN (SA): {current_user.email} | dokumen="{judul}"'
#     )
#     from blueprints.public.routes import clear_dokumen_cache
#     clear_dokumen_cache(sub_kamar_id=sub_kamar_id, kamar_id=kamar_id)

#     flash(f'Dokumen "{judul}" berhasil dihapus.', 'success')
#     return redirect(url_for('superadmin.dokumen', kamar_id=kamar_id))

@superadmin_bp.route('/dokumen/<int:dok_id>/hapus', methods=['POST'])
@superadmin_required
def dokumen_hapus(dok_id):
    """Hapus dokumen (cek share_links aktif dulu)."""
    import os
    from flask import current_app
    from datetime import datetime
    
    dok = Dokumen.query.get_or_404(dok_id)

    # CEK: Ada share_link aktif yang masih valid?
    active_shares = ShareLink.query.filter_by(
        dokumen_id=dok_id,
        is_aktif=True
    ).all()
    
    # Filter share_links yang benar-benar masih valid (belum expired)
    valid_shares = [s for s in active_shares if datetime.utcnow() <= s.expired_at]
    
    # Jika ada share_link yang masih aktif dan belum expired, tolak delete
    if valid_shares:
        flash(
            f'Dokumen "{dok.judul}" tidak bisa dihapus karena masih ada share link yang aktif. '
            f'Silakan matikan share link terlebih dahulu.',
            'danger'
        )
        return redirect(url_for('superadmin.dokumen', kamar_id=dok.sub_kamar.kamar_id))

    # Jika aman, hapus semua share_links (yang sudah expired atau inactive)
    ShareLink.query.filter_by(dokumen_id=dok_id).delete()

    # Hapus file fisik
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], dok.file_path)
    if os.path.exists(file_path):
        os.remove(file_path)

    kamar_id     = dok.sub_kamar.kamar_id
    sub_kamar_id = dok.sub_kamar_id
    judul        = dok.judul

    # Baru hapus dokumen
    db.session.delete(dok)
    db.session.commit()

    current_app.logger.warning(
        f'HAPUS DOKUMEN (SA): {current_user.email} | dokumen="{judul}"'
    )
    from blueprints.public.routes import clear_dokumen_cache
    clear_dokumen_cache(sub_kamar_id=sub_kamar_id, kamar_id=kamar_id)

    flash(f'Dokumen "{judul}" berhasil dihapus.', 'success')
    return redirect(url_for('superadmin.dokumen', kamar_id=kamar_id))


# ===== API ENDPOINTS =====

@superadmin_bp.route('/dokumen/<int:dok_id>/edit', methods=['POST'])
@superadmin_required
def dokumen_edit(dok_id):
    """Edit dokumen — ubah judul, nomor, status, visibilitas."""
    dok = Dokumen.query.get_or_404(dok_id)

    dok.judul         = request.form.get('judul', dok.judul).strip()
    dok.nomor_dokumen = request.form.get('nomor_dokumen', '').strip() or None
    dok.status        = request.form.get('status', dok.status)
    dok.visibilitas   = request.form.get('visibilitas', dok.visibilitas)
    dok.updated_at    = datetime.utcnow()

    # BUGFIX: Jika visibilitas diubah ke publik, hapus semua share link
    if dok.visibilitas == 'publik':
        deleted_count = ShareLink.query.filter_by(dokumen_id=dok.id).delete()
        if deleted_count > 0:
            current_app.logger.info(
                f'AUTO-HAPUS SHARE LINK (SA): {current_user.email} | dokumen="{dok.judul}" | {deleted_count} link dihapus (visibilitas → publik)'
            )

    db.session.commit()

    current_app.logger.info(
        f'EDIT DOKUMEN (SA): {current_user.email} | dokumen="{dok.judul}" | vis={dok.visibilitas}'
    )
    from blueprints.public.routes import clear_dokumen_cache
    clear_dokumen_cache(sub_kamar_id=dok.sub_kamar_id, kamar_id=dok.sub_kamar.kamar_id)

    flash(f'Dokumen "{dok.judul}" berhasil diperbarui.', 'success')
    return redirect(url_for('superadmin.dokumen', kamar_id=dok.sub_kamar.kamar_id))


@superadmin_bp.route('/dokumen/<int:dok_id>/share', methods=['GET'])
@superadmin_required
def dokumen_share_list(dok_id):
    """Halaman kelola share links untuk satu dokumen."""
    dok = Dokumen.query.get_or_404(dok_id)
    share_links = ShareLink.query.filter_by(dokumen_id=dok_id)\
        .order_by(ShareLink.created_at.desc()).all()
    new_token = request.args.get('new_token')

    return render_template('superadmin/share_link.html',
        dok         = dok,
        share_links = share_links,
        new_token   = new_token,
        host_url    = request.host_url,
    )


@superadmin_bp.route('/dokumen/<int:dok_id>/share/generate', methods=['POST'])
@superadmin_required
def share_link_generate(dok_id):
    """Generate temporary share link untuk dokumen internal."""
    import secrets
    from datetime import timedelta

    dok = Dokumen.query.get_or_404(dok_id)

    if dok.visibilitas != 'internal':
        flash('Share link hanya untuk dokumen internal.', 'warning')
        return redirect(url_for('superadmin.dokumen'))

    durasi_jam = request.form.get('durasi', 24, type=int)
    max_akses  = request.form.get('max_akses', 0, type=int)

    token = secrets.token_urlsafe(32)
    share = ShareLink(
        dokumen_id = dok.id,
        token      = token,
        created_by = current_user.id,
        expired_at = datetime.utcnow() + timedelta(hours=durasi_jam),
        max_akses  = max_akses,
    )
    db.session.add(share)
    db.session.commit()

    current_app.logger.info(
        f'SHARE LINK (SA): {current_user.email} | dokumen="{dok.judul}" | durasi={durasi_jam}jam'
    )

    flash(f'Share link berhasil dibuat! Berlaku {durasi_jam} jam.', 'success')
    return redirect(url_for('superadmin.dokumen_share_list', dok_id=dok_id, new_token=token))


@superadmin_bp.route('/share/<int:share_id>/cabut', methods=['POST'])
@superadmin_required
def share_link_cabut(share_id):
    """Cabut/nonaktifkan share link."""
    share = ShareLink.query.get_or_404(share_id)
    dok   = share.dokumen

    share.is_aktif = False
    db.session.commit()
    current_app.logger.warning(
        f'CABUT SHARE LINK (SA): {current_user.email} | dokumen="{dok.judul}"'
    )
    flash('Share link berhasil dicabut.', 'success')
    return redirect(url_for('superadmin.dokumen_share_list', dok_id=dok.id))


@superadmin_bp.route('/api/sub-kamar')
@superadmin_required
def api_sub_kamar():
    """API: list sub-kamar berdasarkan kamar_id (untuk AJAX)."""
    kamar_id       = request.args.get('kamar_id', type=int)
    sub_kamar_list = SubKamar.query.filter_by(kamar_id=kamar_id).all() if kamar_id else []
    return jsonify([{'id': sk.id, 'nama': sk.nama} for sk in sub_kamar_list])