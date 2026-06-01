import os
from flask import render_template, abort, send_from_directory, current_app, make_response, request
from flask_login import current_user
from blueprints.public import public_bp
from models import db, Kamar, SubKamar, Dokumen

@public_bp.route('/')
def index():
    """Halaman beranda publik — tampilkan grid kamar dan statistik."""
    kamar_list = Kamar.query.order_by(Kamar.urutan).all()

    total_dokumen = Dokumen.query.count()
    kamar_aktif   = Kamar.query.filter_by(status='aktif').count()

    from datetime import datetime
    bulan_ini = datetime.now().month
    tahun_ini = datetime.now().year
    upload_bulan_ini = Dokumen.query.filter(
        db.extract('month', Dokumen.created_at) == bulan_ini,
        db.extract('year',  Dokumen.created_at) == tahun_ini
    ).count()

    return render_template('public/index.html',
        kamar_list       = kamar_list,
        total_dokumen    = total_dokumen,
        kamar_aktif      = kamar_aktif,
        upload_bulan_ini = upload_bulan_ini,
    )

@public_bp.route('/kamar/<int:kamar_id>')
def kamar(kamar_id):
    """Halaman list sub-kamar dalam satu kamar."""
    kamar = Kamar.query.get_or_404(kamar_id)
    if kamar.status == 'terkunci':
        abort(403)
    sub_kamar_list = SubKamar.query.filter_by(kamar_id=kamar_id).all()
    return render_template('public/kamar.html',
        kamar          = kamar,
        sub_kamar_list = sub_kamar_list,
    )

@public_bp.route('/kamar/<int:kamar_id>/sub/<int:sub_kamar_id>')
def dokumen(kamar_id, sub_kamar_id):
    """
    Halaman daftar dokumen dalam sub-kamar.
    Support filter: cari (judul/nomor), tahun, status.
    Visibilitas: publik saja untuk tamu, semua untuk user login.
    """
    kamar     = Kamar.query.get_or_404(kamar_id)
    sub_kamar = SubKamar.query.get_or_404(sub_kamar_id)

    if kamar.status == 'terkunci':
        abort(403)

    # Ambil parameter filter dari URL
    cari          = request.args.get('cari', '').strip()
    tahun         = request.args.get('tahun', '').strip()
    filter_status = request.args.get('status', '').strip()

    # Base query
    query = Dokumen.query.filter_by(sub_kamar_id=sub_kamar_id)

    # Filter visibilitas berdasarkan login
    if not current_user.is_authenticated:
        query = query.filter_by(visibilitas='publik')

    # Filter pencarian judul atau nomor dokumen
    if cari:
        query = query.filter(
            db.or_(
                Dokumen.judul.ilike(f'%{cari}%'),
                Dokumen.nomor_dokumen.ilike(f'%{cari}%')
            )
        )

    # Filter tahun upload
    if tahun:
        try:
            query = query.filter(
                db.extract('year', Dokumen.created_at) == int(tahun)
            )
        except ValueError:
            pass

    # Filter status (aktif/arsip)
    if filter_status in ('aktif', 'arsip'):
        query = query.filter_by(status=filter_status)

    dokumen_list = query.order_by(Dokumen.created_at.desc()).all()

    # Ambil daftar tahun unik untuk dropdown filter
    tahun_query = db.session.query(
        db.distinct(db.extract('year', Dokumen.created_at))
    ).filter(Dokumen.sub_kamar_id == sub_kamar_id)

    if not current_user.is_authenticated:
        tahun_query = tahun_query.filter(Dokumen.visibilitas == 'publik')

    tahun_list = sorted(
        [int(t[0]) for t in tahun_query.all() if t[0]],
        reverse=True
    )

    return render_template('public/dokumen.html',
        kamar         = kamar,
        sub_kamar     = sub_kamar,
        dokumen_list  = dokumen_list,
        tahun_list    = tahun_list,
        cari          = cari,
        tahun         = tahun,
        filter_status = filter_status,
    )

@public_bp.route('/uploads/<path:filename>')
def serve_pdf(filename):
    """Serve PDF inline di browser (untuk Preview)."""
    response = make_response(send_from_directory(
        current_app.config['UPLOAD_FOLDER'], filename
    ))
    response.headers['Content-Disposition'] = 'inline'
    response.headers['Content-Type'] = 'application/pdf'
    return response

@public_bp.route('/download/<path:filename>')
def download_pdf(filename):
    """Force download PDF (untuk tombol Unduh)."""
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'], filename,
        as_attachment=True
    )
