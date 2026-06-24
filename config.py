import os
from datetime import timedelta
from dotenv import load_dotenv

# Load .env otomatis
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Secret key — wajib dari .env di production
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-key-ganti-di-env'

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'siadik.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'pdf'}

    # ===== SESSION SECURITY =====
    # Session otomatis expire setelah 8 jam tidak aktif
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    # Cegah JavaScript akses cookie (proteksi XSS)
    SESSION_COOKIE_HTTPONLY = True
    # Proteksi CSRF tambahan via SameSite
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Set True jika sudah pakai HTTPS (aktifkan saat deploy Agustus)
    SESSION_COOKIE_SECURE = False

    # ===== CACHING =====
    CACHE_TYPE           = 'SimpleCache'  # In-memory cache, tidak perlu Redis
    CACHE_DEFAULT_TIMEOUT = 300           # Default 5 menit
    CACHE_THRESHOLD      = 500            # Max 500 item di cache

    # Info instansi
    INSTANSI_NAMA     = 'PPNP'
    INSTANSI_LENGKAP  = 'Politeknik Pertanian Negeri Payakumbuh'
    SISTEM_NAMA       = 'SIADIK'
    SISTEM_LENGKAP    = 'Sistem Informasi Arsip Digital Kepegawaian'
    TAHUN_FOKUS       = '2026'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    # Aktifkan saat deploy dengan HTTPS (Agustus)
    SESSION_COOKIE_SECURE = True
    # Uncomment ini nanti saat migrasi ke MariaDB (Agustus):
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://siadik_user:SiadikPPNP@2026@localhost/siadik'

config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig
}
