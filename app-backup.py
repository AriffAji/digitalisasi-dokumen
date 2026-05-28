import os
import sqlite3
from flask import (
    Flask, render_template, request,
    redirect, url_for, send_from_directory, session, flash
)
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# ─── Konfigurasi ────────────────────────────────────────────────────────────
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback_key')

ADMIN_USERNAME  = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD  = os.environ.get('ADMIN_PASSWORD', 'admin123')
UPLOAD_FOLDER   = 'uploads'
ALLOWED_EXT     = {'pdf'}
DB_PATH         = 'sop.db'

app.config['UPLOAD_FOLDER']      = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ─── Helper ─────────────────────────────────────────────────────────────────
def get_db():
    """Buka koneksi database dan set row_factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def allowed_file(filename: str) -> bool:
    """Cek apakah ekstensi file diizinkan."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


def login_required(f):
    """Decorator: redirect ke login jika belum login."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ─── Inisialisasi Database ───────────────────────────────────────────────────
def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sops (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                judul    TEXT NOT NULL,
                filename TEXT NOT NULL
            )
        ''')

init_db()


# ─── Routes: Publik ──────────────────────────────────────────────────────────
@app.route('/')
def index():
    with get_db() as conn:
        sops = conn.execute('SELECT * FROM sops ORDER BY id DESC').fetchall()
    return render_template('index.html', sops=sops)


@app.route('/uploads/<filename>')
def serve_pdf(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ─── Routes: Auth ────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('admin'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        error = 'Username atau Password salah!'

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ─── Routes: Admin ───────────────────────────────────────────────────────────
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if request.method == 'POST':
        judul = request.form.get('judul', '').strip()
        file  = request.files.get('file')

        if not judul:
            flash('Judul tidak boleh kosong.', 'error')
        elif not file or not allowed_file(file.filename):
            flash('File harus berformat PDF.', 'error')
        else:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            with get_db() as conn:
                conn.execute(
                    'INSERT INTO sops (judul, filename) VALUES (?, ?)',
                    (judul, filename)
                )
            flash('SOP berhasil ditambahkan.', 'success')
            return redirect(url_for('admin'))

    with get_db() as conn:
        sops = conn.execute('SELECT * FROM sops ORDER BY id DESC').fetchall()

    return render_template('admin.html', sops=sops, total_sop=len(sops))


@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_sop(id):
    with get_db() as conn:
        sop = conn.execute('SELECT * FROM sops WHERE id = ?', (id,)).fetchone()
        if sop:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], sop['filename'])
            if os.path.exists(filepath):
                os.remove(filepath)
            conn.execute('DELETE FROM sops WHERE id = ?', (id,))
            flash('SOP berhasil dihapus.', 'success')
        else:
            flash('SOP tidak ditemukan.', 'error')

    return redirect(url_for('admin'))


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_sop(id):
    with get_db() as conn:
        sop = conn.execute('SELECT * FROM sops WHERE id = ?', (id,)).fetchone()

    if not sop:
        flash('SOP tidak ditemukan.', 'error')
        return redirect(url_for('admin'))

    if request.method == 'POST':
        judul_baru = request.form.get('judul', '').strip()
        file_baru  = request.files.get('file')

        if not judul_baru:
            flash('Judul tidak boleh kosong.', 'error')
            return render_template('edit.html', sop=sop)

        with get_db() as conn:
            if file_baru and allowed_file(file_baru.filename):
                # Hapus file lama, simpan file baru
                filepath_lama = os.path.join(app.config['UPLOAD_FOLDER'], sop['filename'])
                if os.path.exists(filepath_lama):
                    os.remove(filepath_lama)
                filename_baru = secure_filename(file_baru.filename)
                file_baru.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_baru))
                conn.execute(
                    'UPDATE sops SET judul = ?, filename = ? WHERE id = ?',
                    (judul_baru, filename_baru, id)
                )
            else:
                conn.execute(
                    'UPDATE sops SET judul = ? WHERE id = ?',
                    (judul_baru, id)
                )

        flash('SOP berhasil diperbarui.', 'success')
        return redirect(url_for('admin'))

    return render_template('edit.html', sop=sop)


# ─── Entry Point ─────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=False)