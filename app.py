import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, session
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = 'ganti_dengan_rahasia_anda_nanti' 

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password123'

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def init_db():
    conn = sqlite3.connect('sop.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            judul TEXT NOT NULL,
            filename TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    conn = sqlite3.connect('sop.db')
    conn.row_factory = sqlite3.Row
    sops = conn.execute('SELECT * FROM sops ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('index.html', sops=sops)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = "Username atau Password salah!"
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        judul = request.form['judul']
        file = request.files['file']
        if file and file.filename.endswith('.pdf'):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            conn = sqlite3.connect('sop.db')
            conn.execute('INSERT INTO sops (judul, filename) VALUES (?, ?)', (judul, filename))
            conn.commit()
            conn.close()
            return redirect(url_for('admin'))
            
    conn = sqlite3.connect('sop.db')
    conn.row_factory = sqlite3.Row
    sops = conn.execute('SELECT * FROM sops ORDER BY id DESC').fetchall()
    conn.close()
    total_sop = len(sops)
    return render_template('admin.html', sops=sops, total_sop=total_sop)

@app.route('/delete/<int:id>')
def delete_sop(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = sqlite3.connect('sop.db')
    conn.row_factory = sqlite3.Row
    sop = conn.execute('SELECT * FROM sops WHERE id = ?', (id,)).fetchone()
    if sop:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], sop['filename'])
        if os.path.exists(filepath):
            os.remove(filepath)
        conn.execute('DELETE FROM sops WHERE id = ?', (id,))
        conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_sop(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = sqlite3.connect('sop.db')
    conn.row_factory = sqlite3.Row
    if request.method == 'POST':
        judul_baru = request.form['judul']
        file_baru = request.files['file']
        if file_baru and file_baru.filename.endswith('.pdf'):
            sop_lama = conn.execute('SELECT * FROM sops WHERE id = ?', (id,)).fetchone()
            filepath_lama = os.path.join(app.config['UPLOAD_FOLDER'], sop_lama['filename'])
            if os.path.exists(filepath_lama):
                os.remove(filepath_lama)
            filename_baru = secure_filename(file_baru.filename)
            file_baru.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_baru))
            conn.execute('UPDATE sops SET judul = ?, filename = ? WHERE id = ?', (judul_baru, filename_baru, id))
        else:
            conn.execute('UPDATE sops SET judul = ? WHERE id = ?', (judul_baru, id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin'))
    sop = conn.execute('SELECT * FROM sops WHERE id = ?', (id,)).fetchone()
    conn.close()
    return render_template('edit.html', sop=sop)

@app.route('/uploads/<filename>')
def serve_pdf(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
