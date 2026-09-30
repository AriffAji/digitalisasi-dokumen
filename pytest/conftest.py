"""
Pytest configuration and fixtures for SIADIK application.
Centralized setup for all test modules.
"""

import os
import sys
import pytest
from datetime import datetime, timedelta
from io import BytesIO

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Kamar, SubKamar, Dokumen, ShareLink
from config import Config


# ===== PYTEST CONFIGURATION =====
def pytest_configure(config):
    """Configure pytest before running tests."""
    config.addinivalue_line(
        "markers", "unit: Mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: Mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "auth: Mark test as authentication test"
    )
    config.addinivalue_line(
        "markers", "slow: Mark test as slow"
    )


# ===== APP FIXTURE =====
@pytest.fixture(scope='function')
def app():
    """Create and configure a Flask app for testing."""
    class TestingConfig(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
        WTF_CSRF_ENABLED = False
        SESSION_COOKIE_SECURE = False
        CACHE_TYPE = 'SimpleCache'
        SECRET_KEY = 'test-secret-key-12345'
        UPLOAD_FOLDER = '/tmp/test_uploads'

    app = create_app('default')
    app.config.from_object(TestingConfig)

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Create tables
    with app.app_context():
        db.create_all()

    yield app

    # Cleanup
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def app_context(app):
    """Push app context for tests that need it."""
    with app.app_context():
        yield
        db.session.remove()


# ===== USER FIXTURES =====
@pytest.fixture
def superadmin_user(app):
    """Create a superadmin user."""
    with app.app_context():
        user = User(
            nama='Super Admin',
            email='superadmin@test.com',
            role='superadmin',
            is_active=True
        )
        user.set_password('SuperAdmin@123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def admin_user(app):
    """Create an admin user."""
    with app.app_context():
        user = User(
            nama='Admin User',
            email='admin@test.com',
            role='admin',
            is_active=True
        )
        user.set_password('Admin@12345')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def regular_user(app):
    """Create a regular user."""
    with app.app_context():
        user = User(
            nama='Regular User',
            email='user@test.com',
            role='user',
            is_active=True
        )
        user.set_password('User@123456')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def inactive_user(app):
    """Create an inactive user."""
    with app.app_context():
        user = User(
            nama='Inactive User',
            email='inactive@test.com',
            role='user',
            is_active=False
        )
        user.set_password('Inactive@12')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def multiple_users(app):
    """Create multiple users for testing."""
    with app.app_context():
        users_data = [
            {'nama': 'User One', 'email': 'user1@test.com', 'role': 'user', 'password': 'User1@12345'},
            {'nama': 'User Two', 'email': 'user2@test.com', 'role': 'user', 'password': 'User2@12345'},
            {'nama': 'User Three', 'email': 'user3@test.com', 'role': 'admin', 'password': 'User3@12345'},
            {'nama': 'User Four', 'email': 'user4@test.com', 'role': 'admin', 'password': 'User4@12345'},
        ]
        users = []
        for data in users_data:
            pwd = data.pop('password')
            user = User(**data, is_active=True)
            user.set_password(pwd)
            db.session.add(user)
            users.append(user)
        db.session.commit()
        return users


# ===== KAMAR FIXTURES =====
@pytest.fixture
def kamar_aktif(app):
    """Create an active kamar."""
    with app.app_context():
        kamar = Kamar(
            nama='Kepegawaian & Tatalaksana',
            deskripsi='Test kamar aktif',
            status='aktif',
            urutan=1
        )
        db.session.add(kamar)
        db.session.commit()
        return kamar


@pytest.fixture
def kamar_terkunci(app):
    """Create a locked kamar."""
    with app.app_context():
        kamar = Kamar(
            nama='Perencanaan',
            deskripsi='Test kamar terkunci',
            status='terkunci',
            urutan=2
        )
        db.session.add(kamar)
        db.session.commit()
        return kamar


@pytest.fixture
def multiple_kamar(app):
    """Create multiple kamar."""
    with app.app_context():
        kamar_data = [
            {'nama': 'Kamar 1', 'deskripsi': 'Description 1', 'status': 'aktif', 'urutan': 1},
            {'nama': 'Kamar 2', 'deskripsi': 'Description 2', 'status': 'aktif', 'urutan': 2},
            {'nama': 'Kamar 3', 'deskripsi': 'Description 3', 'status': 'terkunci', 'urutan': 3},
            {'nama': 'Kamar 4', 'deskripsi': 'Description 4', 'status': 'aktif', 'urutan': 4},
            {'nama': 'Kamar 5', 'deskripsi': 'Description 5', 'status': 'terkunci', 'urutan': 5},
        ]
        kamar_list = []
        for data in kamar_data:
            kamar = Kamar(**data)
            db.session.add(kamar)
            kamar_list.append(kamar)
        db.session.commit()
        return kamar_list


# ===== SUB_KAMAR FIXTURES =====
@pytest.fixture
def sub_kamar(app, kamar_aktif):
    """Create a sub_kamar."""
    with app.app_context():
        sub_kamar = SubKamar(
            kamar_id=kamar_aktif.id,
            nama='Sub Kamar Test',
            deskripsi='Test sub kamar'
        )
        db.session.add(sub_kamar)
        db.session.commit()
        return sub_kamar


@pytest.fixture
def multiple_sub_kamar(app, kamar_aktif):
    """Create multiple sub_kamar."""
    with app.app_context():
        sub_kamar_data = [
            {'nama': 'Sub Kamar 1', 'deskripsi': 'Description 1'},
            {'nama': 'Sub Kamar 2', 'deskripsi': 'Description 2'},
            {'nama': 'Sub Kamar 3', 'deskripsi': 'Description 3'},
        ]
        sub_kamar_list = []
        for data in sub_kamar_data:
            sk = SubKamar(kamar_id=kamar_aktif.id, **data)
            db.session.add(sk)
            sub_kamar_list.append(sk)
        db.session.commit()
        return sub_kamar_list


# ===== DOKUMEN FIXTURES =====
@pytest.fixture
def sample_pdf():
    """Create a sample PDF file in memory."""
    pdf_content = b'%PDF-1.4\n%fake pdf content for testing'
    return BytesIO(pdf_content)


@pytest.fixture
def dokumen(app, sub_kamar, regular_user):
    """Create a sample dokumen."""
    with app.app_context():
        dokumen = Dokumen(
            sub_kamar_id=sub_kamar.id,
            nomor_dokumen='DOK/2026/001',
            judul='Test Dokumen',
            file_path='/uploads/test_dokumen.pdf',
            status='aktif',
            visibilitas='internal',
            uploaded_by=regular_user.id
        )
        db.session.add(dokumen)
        db.session.commit()
        return dokumen


@pytest.fixture
def multiple_dokumen(app, sub_kamar, regular_user):
    """Create multiple dokumen."""
    with app.app_context():
        dokumen_list = []
        for i in range(10):
            dok = Dokumen(
                sub_kamar_id=sub_kamar.id,
                nomor_dokumen=f'DOK/2026/{i:03d}',
                judul=f'Test Dokumen {i+1}',
                file_path=f'/uploads/dokumen_{i}.pdf',
                status='aktif' if i % 2 == 0 else 'arsip',
                visibilitas='publik' if i % 3 == 0 else 'internal',
                uploaded_by=regular_user.id
            )
            db.session.add(dok)
            dokumen_list.append(dok)
        db.session.commit()
        return dokumen_list


# ===== SHARE_LINK FIXTURES =====
@pytest.fixture
def share_link(app, dokumen, regular_user):
    """Create a share link."""
    with app.app_context():
        expired_at = datetime.utcnow() + timedelta(days=7)
        link = ShareLink(
            dokumen_id=dokumen.id,
            token='test_token_abc123xyz',
            created_by=regular_user.id,
            expired_at=expired_at,
            max_akses=5,
            is_aktif=True
        )
        db.session.add(link)
        db.session.commit()
        return link


@pytest.fixture
def expired_share_link(app, dokumen, regular_user):
    """Create an expired share link."""
    with app.app_context():
        expired_at = datetime.utcnow() - timedelta(days=1)
        link = ShareLink(
            dokumen_id=dokumen.id,
            token='expired_token_old123',
            created_by=regular_user.id,
            expired_at=expired_at,
            max_akses=10,
            is_aktif=True
        )
        db.session.add(link)
        db.session.commit()
        return link


# ===== HELPER FIXTURES =====
@pytest.fixture
def auth_client(client, regular_user):
    """Create an authenticated test client."""
    client.post('/auth/login', data={
        'email': regular_user.email,
        'password': 'User@123456'
    })
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Create an authenticated admin test client."""
    client.post('/auth/login', data={
        'email': admin_user.email,
        'password': 'Admin@12345'
    })
    return client


@pytest.fixture
def superadmin_client(client, superadmin_user):
    """Create an authenticated superadmin test client."""
    client.post('/auth/login', data={
        'email': superadmin_user.email,
        'password': 'SuperAdmin@123'
    })
    return client


@pytest.fixture
def db_session(app):
    """Provide database session for tests."""
    with app.app_context():
        yield db.session
