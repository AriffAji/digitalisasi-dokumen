import os
from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import current_user
from blueprints.admin import admin_bp
from decorators import admin_required
from models import db, User, Kamar, SubKamar, Dokumen, ShareLink
from werkzeug.utils import secure_filename

def validate_password(password):
    import re
    if len(password) < 8:
        return False, "Password minimal 8 karakter"
    if not re.search(r'[A-Za-z]', password):
        return False, "Password harus mengandung huruf"
    if not re.search(r'[0-9]', password):
        return False, "Password harus mengandung angka"
    return True, ""

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf'}

def is_valid_pdf(file_obj):
    # Cek magic bytes - PDF asli selalu mulai dengan %PDF
    # Mencegah file berbahaya yang di-rename jadi .pdf
    header = file_obj.read(4)
    file_obj.seek(0)
    return header == b'%PDF'

# ===== DASHBOARD =====
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    # Superadmin redirect ke dashboard superadmin
    if current_user.is_superadmin():
        return redirect(url_for('superadmin.dashboard'))

    kamar = Kamar.query.get(current_user.kamar_id)
    if not kamar:
        flash('Kamar Anda belum dikonfigurasi. Hubungi superadmin.', 'warning')
        return redirect(url_for('public.index'))

    sub_kamar_list   = SubKamar.query.filter_by(kamar_id=kamar.id).all()
    total_dokumen    = sum(sk.total_dokumen for sk in sub_kamar_list)
    total_sub_kamar  = len(sub_kamar_list)
    total_user       = User.query.filter_by(role='user').count()

    from datetime import datetime
    bulan_ini = datetime.now().month
    tahun_ini = datetime.now().year
    upload_bulan_ini = Dokumen.query.join(SubKamar).filter(
        SubKamar.kamar_id == kamar.id,
        db.extract('month', Dokumen.created_at) == bulan_ini,
        db.extract('year',  Dokumen.created_at) == tahun_ini
    ).count()

    dokumen_terbaru = Dokumen.query.join(SubKamar).filter(
        SubKamar.kamar_id == kamar.id
    ).order_by(Dokumen.created_at.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
        kamar            = kamar,
        total_dokumen    = total_dokumen,
        total_sub_kamar  = total_sub_kamar,
        total_user       = total_user,
        upload_bulan_ini = upload_bulan_ini,
        dokumen_terbaru  = dokumen_terbaru,
        sub_kamar_list   = sub_kamar_list,
    )

# ===== SUB-KAMAR =====
@admin_bp.route('/sub-kamar')
@admin_required
def sub_kamar():
    kamar = Kamar.query.get(current_user.kamar_id)
    sub_kamar_list = SubKamar.query.filter_by(kamar_id=kamar.id).all()
    return render_template('admin/sub_kamar.html', kamar=kamar, sub_kamar_list=sub_kamar_list)

@admin_bp.route('/sub-kamar/tambah', methods=['POST'])
@admin_required
def sub_kamar_tambah():
    nama      = request.form.get('nama', '').strip()
    deskripsi = request.form.get('deskripsi', '').strip()
    if not nama:
        flash('Nama sub-kamar tidak boleh kosong.', 'danger')
        return redirect(url_for('admin.sub_kamar'))
    sk = SubKamar(kamar_id=current_user.kamar_id, nama=nama, deskripsi=deskripsi)
    db.session.add(sk)
    db.session.commit()
    flash(f'Sub-kamar "{nama}" berhasil ditambahkan.', 'success')
    return redirect(url_for('admin.sub_kamar'))

@admin_bp.route('/sub-kamar/<int:sk_id>/edit', methods=['POST'])
@admin_required
def sub_kamar_edit(sk_id):
    sk = SubKamar.query.get_or_404(sk_id)
    if sk.kamar_id != current_user.kamar_id:
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('admin.sub_kamar'))
    sk.nama      = request.form.get('nama', sk.nama).strip()
    sk.deskripsi = request.form.get('deskripsi', '').strip()
    db.session.commit()
    flash(f'Sub-kamar "{sk.nama}" berhasil diperbarui.', 'success')
    return redirect(url_for('admin.sub_kamar'))

@admin_bp.route('/sub-kamar/<int:sk_id>/hapus', methods=['POST'])
@admin_required
def sub_kamar_hapus(sk_id):
    sk = SubKamar.query.get_or_404(sk_id)
    if sk.kamar_id != current_user.kamar_id:
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('admin.sub_kamar'))
    if sk.total_dokumen > 0:
        flash(f'Sub-kamar "{sk.nama}" masih memiliki dokumen. Hapus dokumen terlebih dahulu.', 'danger')
        return redirect(url_for('admin.sub_kamar'))
    nama = sk.nama
    db.session.delete(sk)
    db.session.commit()
    flash(f'Sub-kamar "{nama}" berhasil dihapus.', 'success')
    return redirect(url_for('admin.sub_kamar'))

# ===== DOKUMEN =====
@admin_bp.route('/dokumen')
@admin_required
def dokumen():
    kamar          = Kamar.query.get(current_user.kamar_id)
    sub_kamar_list = SubKamar.query.filter_by(kamar_id=kamar.id).all()
    sk_id          = request.args.get('sub_kamar_id', type=int)

    if sk_id:
        dokumen_list = Dokumen.query.filter_by(sub_kamar_id=sk_id).order_by(Dokumen.created_at.desc()).all()
        sub_kamar_aktif = SubKamar.query.get(sk_id)
    else:
        dokumen_list = Dokumen.query.join(SubKamar).filter(
            SubKamar.kamar_id == kamar.id
        ).order_by(Dokumen.created_at.desc()).all()
        sub_kamar_aktif = None

    return render_template('admin/dokumen.html',
        kamar           = kamar,
        sub_kamar_list  = sub_kamar_list,
        dokumen_list    = dokumen_list,
        sub_kamar_aktif = sub_kamar_aktif,
        sk_id           = sk_id,
    )

@admin_bp.route('/dokumen/upload', methods=['POST'])
@admin_required
def dokumen_upload():
    kamar = Kamar.query.get(current_user.kamar_id)
    sub_kamar_id  = request.form.get('sub_kamar_id', type=int)
    nomor         = request.form.get('nomor_dokumen', '').strip()
    judul         = request.form.get('judul', '').strip()
    status        = request.form.get('status', 'aktif')
    visibilitas   = request.form.get('visibilitas', 'internal')
    file          = request.files.get('file')

    # Validasi
    if not sub_kamar_id or not judul or not file:
        flash('Sub-kamar, judul, dan file wajib diisi.', 'danger')
        return redirect(url_for('admin.dokumen'))

    # Pastikan sub-kamar milik kamar admin ini
    sk = SubKamar.query.get(sub_kamar_id)
    if not sk or sk.kamar_id != current_user.kamar_id:
        flash('Sub-kamar tidak valid.', 'danger')
        return redirect(url_for('admin.dokumen'))

    if not allowed_file(file.filename):
        flash('Hanya file PDF yang diizinkan.', 'danger')
        return redirect(url_for('admin.dokumen'))

    if not is_valid_pdf(file):
        flash('File tidak valid. Pastikan file adalah PDF asli.', 'danger')
        return redirect(url_for('admin.dokumen'))

    # Simpan file — potong nama jika terlalu panjang, judul tetap utuh di DB
    filename = secure_filename(file.filename)
    if len(filename) > 200:
        name, ext = filename.rsplit('.', 1)
        filename  = name[:195] + '.' + ext
    import time
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
        f'UPLOAD: {current_user.email} | dokumen="{judul}" | sub_kamar={sk.nama}'
    )
    clear_dokumen_cache(sub_kamar_id=sub_kamar_id, kamar_id=current_user.kamar_id)
    flash(f'Dokumen "{judul}" berhasil diupload.', 'success')
    return redirect(url_for('admin.dokumen', sub_kamar_id=sub_kamar_id))

@admin_bp.route('/dokumen/<int:dok_id>/edit', methods=['POST'])
@admin_required
def dokumen_edit(dok_id):
    dok = Dokumen.query.get_or_404(dok_id)
    # Pastikan dokumen milik kamar admin ini
    if dok.sub_kamar.kamar_id != current_user.kamar_id:
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('admin.dokumen'))

    dok.nomor_dokumen = request.form.get('nomor_dokumen', '').strip()
    dok.judul         = request.form.get('judul', dok.judul).strip()
    dok.status        = request.form.get('status', dok.status)
    dok.visibilitas   = request.form.get('visibilitas', dok.visibilitas)

    # Ganti file jika ada upload baru
    file = request.files.get('file')
    if file and file.filename and allowed_file(file.filename) and is_valid_pdf(file):
        # Hapus file lama
        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], dok.file_path)
        if os.path.exists(old_path):
            os.remove(old_path)
        filename = secure_filename(file.filename)
        if len(filename) > 200:
            name, ext = filename.rsplit('.', 1)
            filename  = name[:195] + '.' + ext
        import time
        unique_name = f"{int(time.time())}_{filename}"
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name))
        dok.file_path = unique_name

    db.session.commit()
    flash(f'Dokumen "{dok.judul}" berhasil diperbarui.', 'success')
    return redirect(url_for('admin.dokumen', sub_kamar_id=dok.sub_kamar_id))

# @admin_bp.route('/dokumen/<int:dok_id>/hapus', methods=['POST'])
# @admin_required
# def dokumen_hapus(dok_id):
#     dok = Dokumen.query.get_or_404(dok_id)
#     if dok.sub_kamar.kamar_id != current_user.kamar_id:
#         flash('Akses ditolak.', 'danger')
#         return redirect(url_for('admin.dokumen'))

#     # Hapus file fisik
#     file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], dok.file_path)
#     if os.path.exists(file_path):
#         os.remove(file_path)

#     judul        = dok.judul
#     sub_kamar_id = dok.sub_kamar_id
#     db.session.delete(dok)
#     db.session.commit()
#     current_app.logger.warning(
#         f'HAPUS DOKUMEN: {current_user.email} | dokumen="{judul}"'
#     )
#     clear_dokumen_cache(sub_kamar_id=sub_kamar_id, kamar_id=current_user.kamar_id)
#     flash(f'Dokumen "{judul}" berhasil dihapus.', 'success')
#     return redirect(url_for('admin.dokumen'))

@admin_bp.route('/dokumen/<int:dok_id>/hapus', methods=['POST'])
@admin_required
def dokumen_hapus(dok_id):
    """Hapus dokumen (cek share_links aktif dulu)."""
    import os
    from flask import current_app
    
    dok = Dokumen.query.get_or_404(dok_id)

    # CEK: Ada share_link aktif yang masih valid?
    active_shares = ShareLink.query.filter_by(
        dokumen_id=dok_id,
        is_aktif=True
    ).all()
    
    # Filter share_links yang benar-benar masih valid (belum expired)
    from datetime import datetime
    valid_shares = [s for s in active_shares if not s.is_expired]
    
    # Jika ada share_link yang masih aktif dan belum expired, tolak delete
    if valid_shares:
        flash(
            f'Dokumen "{dok.judul}" tidak bisa dihapus karena masih ada share link yang aktif. '
            f'Silakan matikan share link terlebih dahulu.',
            'danger'
        )
        return redirect(url_for('admin.dokumen', sub_kamar_id=dok.sub_kamar_id))

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
        f'HAPUS DOKUMEN: {current_user.email} | dokumen="{judul}"'
    )
    clear_dokumen_cache(sub_kamar_id=sub_kamar_id, kamar_id=kamar_id)

    flash(f'Dokumen "{judul}" berhasil dihapus.', 'success')
    return redirect(url_for('admin.dokumen', sub_kamar_id=sub_kamar_id))

# ===== USER =====
@admin_bp.route('/user')
@admin_required
def user():
    user_list = User.query.filter_by(role='user').order_by(User.nama).all()
    return render_template('admin/user.html', user_list=user_list)

@admin_bp.route('/user/tambah', methods=['POST'])
@admin_required
def user_tambah():
    nama     = request.form.get('nama', '').strip()
    email    = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '').strip()

    if not nama or not email or not password:
        flash('Semua field wajib diisi.', 'danger')
        return redirect(url_for('admin.user'))

    valid, pesan = validate_password(password)
    if not valid:
        flash(pesan, 'danger')
        return redirect(url_for('admin.user'))

    if User.query.filter_by(email=email).first():
        flash(f'Email "{email}" sudah terdaftar.', 'danger')
        return redirect(url_for('admin.user'))

    u = User(nama=nama, email=email, role='user')
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    current_app.logger.info(
        f'TAMBAH USER: {current_user.email} | user_baru="{nama}" ({email})'
    )
    flash(f'User "{nama}" berhasil ditambahkan.', 'success')
    return redirect(url_for('admin.user'))

@admin_bp.route('/user/<int:user_id>/hapus', methods=['POST'])
@admin_required
def user_hapus(user_id):
    u = User.query.get_or_404(user_id)
    if u.role != 'user':
        flash('Hanya user kepegawaian yang bisa dihapus dari sini.', 'danger')
        return redirect(url_for('admin.user'))
    nama = u.nama
    db.session.delete(u)
    db.session.commit()
    current_app.logger.warning(
        f'HAPUS USER: {current_user.email} | user="{nama}" ({u.email if hasattr(u, "email") else ""})'
    )
    flash(f'User "{nama}" berhasil dihapus.', 'success')
    return redirect(url_for('admin.user'))

@admin_bp.route('/user/<int:user_id>/toggle', methods=['POST'])
@admin_required
def user_toggle(user_id):
    u = User.query.get_or_404(user_id)
    u.is_active = not u.is_active
    db.session.commit()
    status = 'diaktifkan' if u.is_active else 'dinonaktifkan'
    flash(f'User "{u.nama}" berhasil {status}.', 'success')
    return redirect(url_for('admin.user'))

# ===== AJAX: get sub-kamar by kamar =====
@admin_bp.route('/api/sub-kamar')
@admin_required
def api_sub_kamar():
    kamar_id = request.args.get('kamar_id', type=int) or current_user.kamar_id
    sub_kamar_list = SubKamar.query.filter_by(kamar_id=kamar_id).all()
    return jsonify([{'id': sk.id, 'nama': sk.nama} for sk in sub_kamar_list])

# ===== SHARE LINK =====
@admin_bp.route('/dokumen/<int:dok_id>/share/generate', methods=['POST'])
@admin_required
def share_link_generate(dok_id):
    """Generate temporary share link untuk dokumen internal."""
    import secrets
    from datetime import datetime, timedelta
    from models import ShareLink

    dok = Dokumen.query.get_or_404(dok_id)
    if dok.sub_kamar.kamar_id != current_user.kamar_id and not current_user.is_superadmin():
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('admin.dokumen'))

    if dok.visibilitas != 'internal':
        flash('Share link hanya untuk dokumen internal.', 'warning')
        return redirect(url_for('admin.dokumen'))

    durasi_jam = request.form.get('durasi', 24, type=int)
    max_akses  = request.form.get('max_akses', 0, type=int)

    # Generate token unik
    token = secrets.token_urlsafe(32)

    share = ShareLink(
        dokumen_id  = dok_id,
        token       = token,
        created_by  = current_user.id,
        expired_at  = datetime.utcnow() + timedelta(hours=durasi_jam),
        max_akses   = max_akses,
    )
    db.session.add(share)
    db.session.commit()

    current_app.logger.info(
        f'SHARE LINK: {current_user.email} | dokumen="{dok.judul}" | durasi={durasi_jam}jam'
    )

    share_url = request.host_url + f'share/{token}'
    flash(f'Share link berhasil dibuat! Berlaku {durasi_jam} jam.', 'success')
    return redirect(url_for('admin.dokumen_share_list', dok_id=dok_id, new_token=token))


@admin_bp.route('/dokumen/<int:dok_id>/share')
@admin_required
def dokumen_share_list(dok_id):
    """Halaman kelola share links untuk satu dokumen."""
    from models import ShareLink
    dok = Dokumen.query.get_or_404(dok_id)
    if dok.sub_kamar.kamar_id != current_user.kamar_id and not current_user.is_superadmin():
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('admin.dokumen'))

    share_links = ShareLink.query.filter_by(dokumen_id=dok_id)\
        .order_by(ShareLink.created_at.desc()).all()
    new_token   = request.args.get('new_token')

    return render_template('admin/share_link.html',
        dok         = dok,
        share_links = share_links,
        new_token   = new_token,
        host_url    = request.host_url,
    )


@admin_bp.route('/share/<int:share_id>/cabut', methods=['POST'])
@admin_required
def share_link_cabut(share_id):
    """Cabut/nonaktifkan share link."""
    from models import ShareLink
    share = ShareLink.query.get_or_404(share_id)
    dok   = share.dokumen
    if dok.sub_kamar.kamar_id != current_user.kamar_id and not current_user.is_superadmin():
        flash('Akses ditolak.', 'danger')
        return redirect(url_for('admin.dokumen'))

    share.is_aktif = False
    db.session.commit()
    current_app.logger.warning(
        f'CABUT SHARE LINK: {current_user.email} | dokumen="{dok.judul}"'
    )
    flash('Share link berhasil dicabut.', 'success')
    return redirect(url_for('admin.dokumen_share_list', dok_id=dok.id))
