import os
from flask import render_template, abort, send_from_directory, current_app, make_response, request
from flask_login import current_user
from blueprints.public import public_bp
from models import db, Kamar, SubKamar, Dokumen
from extensions import cache

@public_bp.route('/')
def index():
    """Beranda publik — tampilkan grid kamar dan statistik."""
    kamar_list = _get_kamar_list()
    stats      = _get_statistik()
    return render_template('public/index.html',
        kamar_list       = kamar_list,
        total_dokumen    = stats['total_dokumen'],
        kamar_aktif      = stats['kamar_aktif'],
        upload_bulan_ini = stats['upload_bulan_ini'],
    )

@cache.cached(timeout=600, key_prefix='kamar_list')
def _get_kamar_list():
    """Cache list kamar selama 10 menit."""
    return Kamar.query.order_by(Kamar.urutan).all()

@cache.cached(timeout=300, key_prefix='statistik_beranda')
def _get_statistik():
    """Cache statistik beranda selama 5 menit."""
    from datetime import datetime
    bulan_ini = datetime.now().month
    tahun_ini = datetime.now().year
    return {
        'total_dokumen':    Dokumen.query.count(),
        'kamar_aktif':      Kamar.query.filter_by(status='aktif').count(),
        'upload_bulan_ini': Dokumen.query.filter(
            db.extract('month', Dokumen.created_at) == bulan_ini,
            db.extract('year',  Dokumen.created_at) == tahun_ini
        ).count()
    }

@public_bp.route('/kamar/<int:kamar_id>')
def kamar(kamar_id):
    """Halaman list sub-kamar dalam satu kamar."""
    kamar = Kamar.query.get_or_404(kamar_id)
    if kamar.status == 'terkunci':
        abort(403)
    sub_kamar_list = _get_sub_kamar_list(kamar_id)
    return render_template('public/kamar.html',
        kamar          = kamar,
        sub_kamar_list = sub_kamar_list,
    )

def _get_sub_kamar_list(kamar_id):
    """Cache list sub-kamar per kamar selama 10 menit."""
    key = f'sub_kamar_{kamar_id}'
    result = cache.get(key)
    if result is None:
        result = SubKamar.query.filter_by(kamar_id=kamar_id).all()
        cache.set(key, result, timeout=600)
    return result

@public_bp.route('/kamar/<int:kamar_id>/sub/<int:sub_kamar_id>')
def dokumen(kamar_id, sub_kamar_id):
    """
    Halaman daftar dokumen dalam sub-kamar.
    Support filter: cari, tahun, status.
    Cache hanya untuk request tanpa filter.
    """
    kamar     = Kamar.query.get_or_404(kamar_id)
    sub_kamar = SubKamar.query.get_or_404(sub_kamar_id)

    if kamar.status == 'terkunci':
        abort(403)

    cari          = request.args.get('cari', '').strip()
    tahun         = request.args.get('tahun', '').strip()
    filter_status = request.args.get('status', '').strip()
    page          = request.args.get('page', 1, type=int)

    # Gunakan cache hanya jika tidak ada filter aktif
    use_cache = not cari and not tahun and not filter_status

    if use_cache and not current_user.is_authenticated:
        cache_key = f'dokumen_publik_{sub_kamar_id}_page{page}'
        cached = cache.get(cache_key)
        if cached:
            return cached

    # Base query
    query = Dokumen.query.filter_by(sub_kamar_id=sub_kamar_id)

    if not current_user.is_authenticated:
        query = query.filter_by(visibilitas='publik')

    if cari:
        query = query.filter(
            db.or_(
                Dokumen.judul.ilike(f'%{cari}%'),
                Dokumen.nomor_dokumen.ilike(f'%{cari}%')
            )
        )
    if tahun:
        try:
            query = query.filter(db.extract('year', Dokumen.created_at) == int(tahun))
        except ValueError:
            pass
    if filter_status in ('aktif', 'arsip'):
        query = query.filter_by(status=filter_status)

    # Pagination — 20 dokumen per halaman
    pagination   = query.order_by(Dokumen.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    dokumen_list = pagination.items

    # Tahun unik untuk dropdown
    tahun_query = db.session.query(
        db.distinct(db.extract('year', Dokumen.created_at))
    ).filter(Dokumen.sub_kamar_id == sub_kamar_id)
    if not current_user.is_authenticated:
        tahun_query = tahun_query.filter(Dokumen.visibilitas == 'publik')
    tahun_list = sorted(
        [int(t[0]) for t in tahun_query.all() if t[0]], reverse=True
    )

    response = render_template('public/dokumen.html',
        kamar         = kamar,
        sub_kamar     = sub_kamar,
        dokumen_list  = dokumen_list,
        pagination    = pagination,
        tahun_list    = tahun_list,
        cari          = cari,
        tahun         = tahun,
        filter_status = filter_status,
    )

    # Simpan ke cache kalau tidak ada filter
    if use_cache and not current_user.is_authenticated:
        cache.set(cache_key, response, timeout=180)

    return response

@public_bp.route('/uploads/<path:filename>')
def serve_pdf(filename):
    """Serve PDF inline di browser."""
    response = make_response(send_from_directory(
        current_app.config['UPLOAD_FOLDER'], filename
    ))
    response.headers['Content-Disposition'] = 'inline'
    response.headers['Content-Type'] = 'application/pdf'
    return response

@public_bp.route('/download/<path:filename>')
def download_pdf(filename):
    """Force download PDF."""
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'], filename,
        as_attachment=True
    )

def clear_dokumen_cache(sub_kamar_id=None, kamar_id=None):
    """
    Clear cache yang relevan setelah ada perubahan dokumen.
    Dipanggil dari admin routes setelah upload/hapus/edit.
    """
    cache.delete('statistik_beranda')
    if sub_kamar_id:
        for page in range(1, 10):
            cache.delete(f'dokumen_publik_{sub_kamar_id}_page{page}')
    if kamar_id:
        cache.delete(f'sub_kamar_{kamar_id}')
    cache.delete('kamar_list')

@public_bp.route('/share/<token>')
def akses_share_link(token):
    """Akses dokumen internal via temporary share link."""
    from models import ShareLink
    from datetime import datetime

    share = ShareLink.query.filter_by(token=token).first()

    # Validasi link
    if not share:
        return render_template('public/share_invalid.html',
            pesan="Link tidak ditemukan atau sudah tidak valid.")

    if not share.is_valid:
        if share.is_expired:
            pesan = "Link ini sudah kedaluwarsa."
        elif not share.is_aktif:
            pesan = "Link ini telah dicabut oleh administrator."
        else:
            pesan = "Link ini sudah mencapai batas akses."
        return render_template('public/share_invalid.html', pesan=pesan)

    # Tambah counter akses
    share.jumlah_akses += 1
    from models import db
    db.session.commit()

    dok = share.dokumen
    return render_template('public/share.html',
        dok   = dok,
        share = share,
    )
