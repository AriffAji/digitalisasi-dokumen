"""
Unit tests for database models.
Tests cover User, Kamar, SubKamar, Dokumen, and ShareLink models.
"""

import pytest
from datetime import datetime, timedelta
from models import db, User, Kamar, SubKamar, Dokumen, ShareLink


class TestUserModel:
    """Test User model and methods."""

    @pytest.mark.unit
    def test_user_creation(self, app):
        """Test creating a user."""
        with app.app_context():
            user = User(
                nama='Test User',
                email='test@example.com',
                role='user',
                is_active=True
            )
            user.set_password('TestPassword123')
            db.session.add(user)
            db.session.commit()

            found_user = User.query.filter_by(email='test@example.com').first()
            assert found_user is not None
            assert found_user.nama == 'Test User'
            assert found_user.role == 'user'

    @pytest.mark.unit
    def test_user_password_hashing(self, app):
        """Test password hashing."""
        with app.app_context():
            user = User(
                nama='Test User',
                email='hash_test@example.com',
                role='user'
            )
            password = 'SecurePassword123'
            user.set_password(password)

            assert user.password_hash != password
            assert user.check_password(password) is True
            assert user.check_password('WrongPassword') is False

    @pytest.mark.unit
    def test_password_validation(self, app):
        """Test password check returns correct boolean."""
        with app.app_context():
            user = User(
                nama='Test User',
                email='pwd_test@example.com',
                role='user'
            )
            correct_pwd = 'CorrectPassword123'
            user.set_password(correct_pwd)

            assert user.check_password(correct_pwd) is True
            assert user.check_password('IncorrectPassword123') is False
            assert user.check_password('') is False

    @pytest.mark.unit
    def test_user_roles(self, app):
        """Test role checking methods."""
        with app.app_context():
            superadmin = User(
                nama='Super Admin',
                email='superadmin@example.com',
                role='superadmin'
            )
            admin = User(
                nama='Admin',
                email='admin@example.com',
                role='admin'
            )
            user = User(
                nama='Regular User',
                email='user@example.com',
                role='user'
            )

            assert superadmin.is_superadmin() is True
            assert superadmin.is_admin() is False
            assert superadmin.is_user() is False

            assert admin.is_superadmin() is False
            assert admin.is_admin() is True
            assert admin.is_user() is False

            assert user.is_superadmin() is False
            assert user.is_admin() is False
            assert user.is_user() is True

    @pytest.mark.unit
    def test_user_unique_email(self, app):
        """Test that user emails must be unique."""
        with app.app_context():
            user1 = User(
                nama='User 1',
                email='duplicate@example.com',
                role='user'
            )
            user1.set_password('Password123')
            db.session.add(user1)
            db.session.commit()

            user2 = User(
                nama='User 2',
                email='duplicate@example.com',
                role='user'
            )
            user2.set_password('Password123')
            db.session.add(user2)

            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()

    @pytest.mark.unit
    def test_user_default_values(self, app):
        """Test user model default values."""
        with app.app_context():
            user = User(
                nama='Test User',
                email='defaults@example.com'
            )
            db.session.add(user)
            db.session.commit()

            found = User.query.filter_by(email='defaults@example.com').first()
            assert found.role == 'user'  # default role
            assert found.is_active is True  # default is_active
            assert found.created_at is not None

    @pytest.mark.unit
    def test_user_repr(self, app):
        """Test user string representation."""
        with app.app_context():
            user = User(
                nama='Test User',
                email='repr@example.com',
                role='admin'
            )
            repr_str = repr(user)
            assert 'repr@example.com' in repr_str
            assert 'admin' in repr_str


class TestKamarModel:
    """Test Kamar model."""

    @pytest.mark.unit
    def test_kamar_creation(self, app):
        """Test creating a kamar."""
        with app.app_context():
            kamar = Kamar(
                nama='Kepegawaian',
                deskripsi='Test kamar',
                status='aktif',
                urutan=1
            )
            db.session.add(kamar)
            db.session.commit()

            found = Kamar.query.filter_by(nama='Kepegawaian').first()
            assert found is not None
            assert found.status == 'aktif'

    @pytest.mark.unit
    def test_kamar_status_values(self, app):
        """Test kamar status can be aktif or terkunci."""
        with app.app_context():
            kamar_aktif = Kamar(
                nama='Aktif Kamar',
                status='aktif',
                urutan=1
            )
            kamar_terkunci = Kamar(
                nama='Terkunci Kamar',
                status='terkunci',
                urutan=2
            )
            db.session.add(kamar_aktif)
            db.session.add(kamar_terkunci)
            db.session.commit()

            assert Kamar.query.filter_by(status='aktif').count() == 1
            assert Kamar.query.filter_by(status='terkunci').count() == 1

    @pytest.mark.unit
    def test_kamar_urutan_ordering(self, app):
        """Test kamar can be ordered by urutan."""
        with app.app_context():
            for i in range(1, 6):
                kamar = Kamar(
                    nama=f'Kamar {i}',
                    urutan=i
                )
                db.session.add(kamar)
            db.session.commit()

            kamar_list = Kamar.query.order_by(Kamar.urutan).all()
            for i, kamar in enumerate(kamar_list, 1):
                assert kamar.urutan == i

    @pytest.mark.unit
    def test_kamar_total_dokumen_property(self, app, kamar_aktif, sub_kamar, regular_user):
        """Test kamar total_dokumen property."""
        with app.app_context():
            # Add some documents
            for i in range(5):
                dok = Dokumen(
                    sub_kamar_id=sub_kamar.id,
                    judul=f'Dokumen {i}',
                    file_path=f'/uploads/dok{i}.pdf',
                    uploaded_by=regular_user.id
                )
                db.session.add(dok)
            db.session.commit()

            kamar = Kamar.query.get(kamar_aktif.id)
            assert kamar.total_dokumen == 5

    @pytest.mark.unit
    def test_kamar_repr(self, app):
        """Test kamar string representation."""
        with app.app_context():
            kamar = Kamar(nama='Test Kamar')
            repr_str = repr(kamar)
            assert 'Test Kamar' in repr_str


class TestSubKamarModel:
    """Test SubKamar model."""

    @pytest.mark.unit
    def test_sub_kamar_creation(self, app, kamar_aktif):
        """Test creating a sub kamar."""
        with app.app_context():
            sub_kamar = SubKamar(
                kamar_id=kamar_aktif.id,
                nama='Sub Kamar Test',
                deskripsi='Test sub kamar'
            )
            db.session.add(sub_kamar)
            db.session.commit()

            found = SubKamar.query.filter_by(nama='Sub Kamar Test').first()
            assert found is not None
            assert found.kamar_id == kamar_aktif.id

    @pytest.mark.unit
    def test_sub_kamar_relationship_with_kamar(self, app, kamar_aktif):
        """Test sub kamar relationship with kamar."""
        with app.app_context():
            sub1 = SubKamar(kamar_id=kamar_aktif.id, nama='Sub 1')
            sub2 = SubKamar(kamar_id=kamar_aktif.id, nama='Sub 2')
            db.session.add(sub1)
            db.session.add(sub2)
            db.session.commit()

            kamar = Kamar.query.get(kamar_aktif.id)
            assert kamar.sub_kamar.count() == 2

    @pytest.mark.unit
    def test_sub_kamar_total_dokumen_property(self, app, kamar_aktif, regular_user):
        """Test sub_kamar total_dokumen property."""
        with app.app_context():
            sub_kamar = SubKamar(kamar_id=kamar_aktif.id, nama='Sub Test')
            db.session.add(sub_kamar)
            db.session.commit()

            for i in range(3):
                dok = Dokumen(
                    sub_kamar_id=sub_kamar.id,
                    judul=f'Dok {i}',
                    file_path=f'/up/d{i}.pdf',
                    uploaded_by=regular_user.id
                )
                db.session.add(dok)
            db.session.commit()

            sub = SubKamar.query.get(sub_kamar.id)
            assert sub.total_dokumen == 3

    @pytest.mark.unit
    def test_sub_kamar_repr(self, app, kamar_aktif):
        """Test sub kamar string representation."""
        with app.app_context():
            sub_kamar = SubKamar(kamar_id=kamar_aktif.id, nama='Test Sub')
            repr_str = repr(sub_kamar)
            assert 'Test Sub' in repr_str


class TestDokumenModel:
    """Test Dokumen model."""

    @pytest.mark.unit
    def test_dokumen_creation(self, app, sub_kamar, regular_user):
        """Test creating a dokumen."""
        with app.app_context():
            dokumen = Dokumen(
                sub_kamar_id=sub_kamar.id,
                nomor_dokumen='DOK/2026/001',
                judul='Test Dokumen',
                file_path='/uploads/test.pdf',
                uploaded_by=regular_user.id
            )
            db.session.add(dokumen)
            db.session.commit()

            found = Dokumen.query.filter_by(judul='Test Dokumen').first()
            assert found is not None
            assert found.status == 'aktif'  # default status
            assert found.visibilitas == 'internal'  # default visibilitas

    @pytest.mark.unit
    def test_dokumen_status_values(self, app, sub_kamar, regular_user):
        """Test dokumen status values."""
        with app.app_context():
            dok1 = Dokumen(
                sub_kamar_id=sub_kamar.id,
                judul='Aktif Dokumen',
                file_path='/up/aktif.pdf',
                status='aktif',
                uploaded_by=regular_user.id
            )
            dok2 = Dokumen(
                sub_kamar_id=sub_kamar.id,
                judul='Arsip Dokumen',
                file_path='/up/arsip.pdf',
                status='arsip',
                uploaded_by=regular_user.id
            )
            db.session.add(dok1)
            db.session.add(dok2)
            db.session.commit()

            assert Dokumen.query.filter_by(status='aktif').count() == 1
            assert Dokumen.query.filter_by(status='arsip').count() == 1

    @pytest.mark.unit
    def test_dokumen_visibilitas_values(self, app, sub_kamar, regular_user):
        """Test dokumen visibilitas values."""
        with app.app_context():
            dok1 = Dokumen(
                sub_kamar_id=sub_kamar.id,
                judul='Public Dokumen',
                file_path='/up/pub.pdf',
                visibilitas='publik',
                uploaded_by=regular_user.id
            )
            dok2 = Dokumen(
                sub_kamar_id=sub_kamar.id,
                judul='Internal Dokumen',
                file_path='/up/int.pdf',
                visibilitas='internal',
                uploaded_by=regular_user.id
            )
            db.session.add(dok1)
            db.session.add(dok2)
            db.session.commit()

            assert Dokumen.query.filter_by(visibilitas='publik').count() == 1
            assert Dokumen.query.filter_by(visibilitas='internal').count() == 1

    @pytest.mark.unit
    def test_dokumen_timestamps(self, app, sub_kamar, regular_user):
        """Test dokumen created_at and updated_at timestamps."""
        with app.app_context():
            before = datetime.utcnow()
            dokumen = Dokumen(
                sub_kamar_id=sub_kamar.id,
                judul='Timestamp Test',
                file_path='/up/time.pdf',
                uploaded_by=regular_user.id
            )
            db.session.add(dokumen)
            db.session.commit()
            after = datetime.utcnow()

            found = Dokumen.query.filter_by(judul='Timestamp Test').first()
            assert before <= found.created_at <= after
            assert before <= found.updated_at <= after

    @pytest.mark.unit
    def test_dokumen_repr(self, app, sub_kamar, regular_user):
        """Test dokumen string representation."""
        with app.app_context():
            dokumen = Dokumen(
                sub_kamar_id=sub_kamar.id,
                judul='Repr Test',
                file_path='/up/repr.pdf',
                uploaded_by=regular_user.id
            )
            repr_str = repr(dokumen)
            assert 'Repr Test' in repr_str


class TestShareLinkModel:
    """Test ShareLink model."""

    @pytest.mark.unit
    def test_share_link_creation(self, app, dokumen, regular_user):
        """Test creating a share link."""
        with app.app_context():
            expired_at = datetime.utcnow() + timedelta(days=7)
            link = ShareLink(
                dokumen_id=dokumen.id,
                token='test_token_123',
                created_by=regular_user.id,
                expired_at=expired_at,
                max_akses=5
            )
            db.session.add(link)
            db.session.commit()

            found = ShareLink.query.filter_by(token='test_token_123').first()
            assert found is not None
            assert found.is_aktif is True  # default value

    @pytest.mark.unit
    def test_share_link_is_expired_property(self, app, dokumen, regular_user):
        """Test is_expired property."""
        with app.app_context():
            # Not expired
            future = datetime.utcnow() + timedelta(days=1)
            link1 = ShareLink(
                dokumen_id=dokumen.id,
                token='future_token',
                created_by=regular_user.id,
                expired_at=future
            )

            # Expired
            past = datetime.utcnow() - timedelta(days=1)
            link2 = ShareLink(
                dokumen_id=dokumen.id,
                token='past_token',
                created_by=regular_user.id,
                expired_at=past
            )

            db.session.add(link1)
            db.session.add(link2)
            db.session.commit()

            link1_found = ShareLink.query.filter_by(token='future_token').first()
            link2_found = ShareLink.query.filter_by(token='past_token').first()

            assert link1_found.is_expired is False
            assert link2_found.is_expired is True

    @pytest.mark.unit
    def test_share_link_is_valid_property(self, app, dokumen, regular_user):
        """Test is_valid property with various conditions."""
        with app.app_context():
            # Valid link
            valid_link = ShareLink(
                dokumen_id=dokumen.id,
                token='valid_token',
                created_by=regular_user.id,
                expired_at=datetime.utcnow() + timedelta(days=1),
                max_akses=5,
                jumlah_akses=2,
                is_aktif=True
            )

            # Inactive link
            inactive_link = ShareLink(
                dokumen_id=dokumen.id,
                token='inactive_token',
                created_by=regular_user.id,
                expired_at=datetime.utcnow() + timedelta(days=1),
                is_aktif=False
            )

            # Exceeded max_akses
            exceeded_link = ShareLink(
                dokumen_id=dokumen.id,
                token='exceeded_token',
                created_by=regular_user.id,
                expired_at=datetime.utcnow() + timedelta(days=1),
                max_akses=5,
                jumlah_akses=5,
                is_aktif=True
            )

            db.session.add_all([valid_link, inactive_link, exceeded_link])
            db.session.commit()

            assert ShareLink.query.filter_by(token='valid_token').first().is_valid is True
            assert ShareLink.query.filter_by(token='inactive_token').first().is_valid is False
            assert ShareLink.query.filter_by(token='exceeded_token').first().is_valid is False

    @pytest.mark.unit
    def test_share_link_unlimited_access(self, app, dokumen, regular_user):
        """Test share link with unlimited access (max_akses=0)."""
        with app.app_context():
            link = ShareLink(
                dokumen_id=dokumen.id,
                token='unlimited_token',
                created_by=regular_user.id,
                expired_at=datetime.utcnow() + timedelta(days=1),
                max_akses=0,  # Unlimited
                jumlah_akses=100  # Even with high count, should be valid
            )
            db.session.add(link)
            db.session.commit()

            found = ShareLink.query.filter_by(token='unlimited_token').first()
            assert found.is_valid is True

    @pytest.mark.unit
    def test_share_link_repr(self, app, dokumen, regular_user):
        """Test share link string representation."""
        with app.app_context():
            link = ShareLink(
                dokumen_id=dokumen.id,
                token='repr_token_xyz',
                created_by=regular_user.id,
                expired_at=datetime.utcnow() + timedelta(days=1)
            )
            repr_str = repr(link)
            assert 'repr_token_xyz' in repr_str
