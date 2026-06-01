# 📁 SIADIK

### Sistem Informasi Arsip Digital Kepegawaian

**Politeknik Pertanian Negeri Payakumbuh (PPNP)**

---

## 🌟 Tentang Sistem

SIADIK adalah platform digital terpusat untuk mengelola arsip dokumen kepegawaian PPNP. Dokumen disimpan dalam format PDF, dikelompokkan dalam struktur kamar dan sub-kamar, serta dapat diakses sesuai level pengguna.

---

## ⚡ Teknologi

![Python](https://img.shields.io/badge/Python-3.14-blue?style=flat-square&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0.3-black?style=flat-square&logo=flask)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.x-38bdf8?style=flat-square&logo=tailwindcss)
![SQLite](https://img.shields.io/badge/SQLite-Development-lightgrey?style=flat-square&logo=sqlite)
![Flowbite](https://img.shields.io/badge/Flowbite-2.3.0-blue?style=flat-square)

| Layer | Teknologi |
|---|---|
| Backend | Flask + SQLAlchemy |
| Database | SQLite (dev) → MariaDB (production) |
| Frontend | Tailwind CSS + Flowbite |
| Icons | Google Material Icons |
| Auth | Flask-Login (session-based) |

---

## 👥 Level Akses

| Role | Akses |
|---|---|
| 🌐 **Publik** | Lihat & unduh dokumen publik tanpa login |
| 👤 **User** | Lihat semua dokumen termasuk internal |
| 🔑 **Admin** | Kelola dokumen & sub-kamar di kamarnya sendiri |
| 👑 **Superadmin** | Akses penuh ke seluruh sistem |

---

## 📁 Struktur Kamar Arsip

```
📦 SIADIK
├── 🟢 Kepegawaian & Tatalaksana   (Aktif - Fokus 2026)
├── 🔒 Perencanaan                  (Segera Hadir)
├── 🔒 Keuangan                     (Segera Hadir)
├── 🔒 Barang Milik Negara          (Segera Hadir)
└── 🔒 Kasubag Umum                 (Segera Hadir)
```

---

## 🚀 Instalasi

### 1. Clone repository

```bash
git clone https://github.com/AriffAji/digitalisasi-dokumen.git
cd digitalisasi-dokumen
```

### 2. Buat virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup environment

```bash
# Salin file contoh
cp .env.example .env

# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# Isi .env dengan SECRET_KEY hasil generate
```

### 5. Jalankan aplikasi

```bash
python app.py
```

Buka browser → `http://127.0.0.1:5000`

---

## 🔑 Akun Default

Akun superadmin dibuat otomatis saat pertama jalan:

| Email | Password |
|---|---|
| <superadmin@ppnp.ac.id> | *[Hubungi administrator]* |

> > ⚠️ **Password diatur langsung oleh administrator. Tidak dipublikasikan.**

---

## 📂 Struktur Folder

```
siadik/
├── app.py                  # Entry point
├── config.py               # Konfigurasi
├── models.py               # Database models
├── decorators.py           # Role-based access
├── requirements.txt
├── .env.example
├── blueprints/
│   ├── public/             # Route publik
│   ├── auth/               # Login & logout
│   ├── admin/              # Panel admin
│   └── superadmin/         # Panel superadmin
├── templates/
│   ├── base.html           # Template induk
│   ├── public/             # Halaman publik
│   ├── auth/               # Halaman login
│   ├── admin/              # Dashboard admin
│   └── superadmin/         # Dashboard superadmin
├── static/
│   ├── css/
│   ├── js/
│   └── img/
└── uploads/                # File PDF (tidak di-commit)
```

---

## 🗄️ Database Schema

```
users        → id, nama, email, password_hash, role, kamar_id
kamar        → id, nama, deskripsi, status, urutan
sub_kamar    → id, kamar_id, nama, deskripsi
dokumen      → id, sub_kamar_id, nomor_dokumen, judul, file_path,
               status, visibilitas, uploaded_by, created_at
```

---

## 🗺️ Roadmap

- [x] Phase 1 — Fondasi & struktur project
- [x] Phase 2 — Sistem autentikasi multi-role
- [x] Phase 3 — Halaman publik + filter dokumen
- [x] Phase 4 — Panel admin (upload, sub-kamar, user)
- [x] Phase 5 — Panel superadmin (kamar, admin)
- [x] Phase 6 — Keamanan (.env + SECRET_KEY)
- [ ] Migrasi SQLite → MariaDB (Agustus 2026)
- [ ] Deploy ke VPS Hostinger (Agustus 2026)
- [ ] Aktivasi kamar Perencanaan, Keuangan, BMN, Kasubag Umum

---

## 👨‍💻 Developer

Dikembangkan oleh Tim Kepegawaian **PPNP** — Politeknik Pertanian Negeri Payakumbuh
© 2026 SIADIK. Hak cipta dilindungi.
