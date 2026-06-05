from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    nama          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role          = db.Column(db.String(20), nullable=False, default='user', index=True)
    kamar_id      = db.Column(db.Integer, db.ForeignKey('kamar.id'), nullable=True, index=True)
    is_active     = db.Column(db.Boolean, default=True, index=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi
    kamar   = db.relationship('Kamar', backref='admins')
    dokumen = db.relationship('Dokumen', backref='uploader', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_superadmin(self):
        return self.role == 'superadmin'

    def is_admin(self):
        return self.role == 'admin'

    def is_user(self):
        return self.role == 'user'

    def __repr__(self):
        return f'<User {self.email} [{self.role}]>'


class Kamar(db.Model):
    __tablename__ = 'kamar'

    id         = db.Column(db.Integer, primary_key=True)
    nama       = db.Column(db.String(100), nullable=False)
    deskripsi  = db.Column(db.Text, nullable=True)
    status     = db.Column(db.String(20), nullable=False, default='terkunci', index=True)
    urutan     = db.Column(db.Integer, default=0, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi
    sub_kamar = db.relationship('SubKamar', backref='kamar', lazy='dynamic',
                                 cascade='all, delete-orphan')

    @property
    def total_dokumen(self):
        total = 0
        for sk in self.sub_kamar:
            total += sk.dokumen.count()
        return total

    def __repr__(self):
        return f'<Kamar {self.nama}>'


class SubKamar(db.Model):
    __tablename__ = 'sub_kamar'

    id         = db.Column(db.Integer, primary_key=True)
    kamar_id   = db.Column(db.Integer, db.ForeignKey('kamar.id'), nullable=False, index=True)
    nama       = db.Column(db.String(100), nullable=False)
    deskripsi  = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi
    dokumen = db.relationship('Dokumen', backref='sub_kamar', lazy='dynamic',
                               cascade='all, delete-orphan')

    @property
    def total_dokumen(self):
        return self.dokumen.count()

    def __repr__(self):
        return f'<SubKamar {self.nama}>'


class Dokumen(db.Model):
    __tablename__ = 'dokumen'

    id            = db.Column(db.Integer, primary_key=True)
    sub_kamar_id  = db.Column(db.Integer, db.ForeignKey('sub_kamar.id'), nullable=False, index=True)
    nomor_dokumen = db.Column(db.String(100), nullable=True)
    judul         = db.Column(db.String(255), nullable=False, index=True)
    file_path     = db.Column(db.String(255), nullable=False)
    status        = db.Column(db.String(20), nullable=False, default='aktif', index=True)
    visibilitas   = db.Column(db.String(20), nullable=False, default='internal', index=True)
    uploaded_by   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Composite index untuk query yang sering dipakai bersamaan
    __table_args__ = (
        db.Index('idx_dokumen_sub_status',      'sub_kamar_id', 'status'),
        db.Index('idx_dokumen_sub_visibilitas',  'sub_kamar_id', 'visibilitas'),
        db.Index('idx_dokumen_sub_tahun',        'sub_kamar_id', 'created_at'),
    )

    def __repr__(self):
        return f'<Dokumen {self.judul}>'


class ShareLink(db.Model):
    __tablename__ = 'share_links'

    id          = db.Column(db.Integer, primary_key=True)
    dokumen_id  = db.Column(db.Integer, db.ForeignKey('dokumen.id'), nullable=False, index=True)
    token       = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_by  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    expired_at  = db.Column(db.DateTime, nullable=False)
    max_akses   = db.Column(db.Integer, default=0)  # 0 = unlimited
    jumlah_akses= db.Column(db.Integer, default=0)
    is_aktif    = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    # Relasi
    dokumen     = db.relationship('Dokumen', backref='share_links')
    pembuat     = db.relationship('User', backref='share_links')

    @property
    def is_expired(self):
        return datetime.utcnow() > self.expired_at

    @property
    def is_valid(self):
        if not self.is_aktif:
            return False
        if self.is_expired:
            return False
        if self.max_akses > 0 and self.jumlah_akses >= self.max_akses:
            return False
        return True

    def __repr__(self):
        return f'<ShareLink {self.token}>'


def init_db(app):
    """Inisialisasi database dan buat data awal jika belum ada."""
    db.init_app(app)

    with app.app_context():
        db.create_all()
        _seed_data()


def _seed_data():
    """Buat data awal: superadmin + 5 kamar default."""

    if not User.query.filter_by(role='superadmin').first():
        superadmin = User(
            nama  = 'Super Admin',
            email = 'superadmin@ppnp.ac.id',
            role  = 'superadmin'
        )
        superadmin.set_password('SuperAdmin@2026')
        db.session.add(superadmin)
        print('[SEED] Superadmin dibuat')

    if Kamar.query.count() == 0:
        kamar_default = [
            {'nama': 'Kepegawaian & Tatalaksana', 'deskripsi': 'Arsip dokumen kepegawaian dan tatalaksana instansi', 'status': 'aktif',    'urutan': 1},
            {'nama': 'Perencanaan',                'deskripsi': 'Arsip dokumen perencanaan program dan anggaran',    'status': 'terkunci', 'urutan': 2},
            {'nama': 'Keuangan',                   'deskripsi': 'Arsip dokumen keuangan dan laporan fiskal',         'status': 'terkunci', 'urutan': 3},
            {'nama': 'Barang Milik Negara',        'deskripsi': 'Arsip dokumen inventaris dan aset negara',          'status': 'terkunci', 'urutan': 4},
            {'nama': 'Kasubag Umum',               'deskripsi': 'Arsip dokumen ketatausahaan dan umum',              'status': 'terkunci', 'urutan': 5},
        ]
        for k in kamar_default:
            kamar = Kamar(**k)
            db.session.add(kamar)
        print('[SEED] 5 kamar default dibuat.')

    db.session.commit()
