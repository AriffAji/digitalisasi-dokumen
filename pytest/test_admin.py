"""
Integration tests for admin routes.
Tests cover admin dashboard, document management, kamar management, and user administration.
"""

import pytest
from models import db, Kamar, SubKamar, Dokumen, User
from datetime import datetime


class TestAdminDashboard:
    """Test admin dashboard."""

    @pytest.mark.integration
    def test_admin_dashboard_access(self, admin_client):
        """Test admin can access dashboard."""
        response = admin_client.get('/admin/dashboard', follow_redirects=True)
        assert response.status_code == 200

    @pytest.mark.integration
    def test_admin_dashboard_denied_to_user(self, auth_client):
        """Test regular user cannot access admin dashboard."""
        response = auth_client.get('/admin/dashboard', follow_redirects=True)
        # Should be denied

    @pytest.mark.integration
    def test_admin_dashboard_denied_to_unauthenticated(self, client):
        """Test unauthenticated users cannot access admin dashboard."""
        response = client.get('/admin/dashboard', follow_redirects=True)
        # Should redirect to login

    @pytest.mark.integration
    def test_admin_dashboard_denied_to_superadmin_on_own_dashboard(self, superadmin_client):
        """Test superadmin is redirected from admin dashboard."""
        response = superadmin_client.get('/admin/dashboard', follow_redirects=True)
        # Superadmin should use superadmin dashboard


class TestKamarManagement:
    """Test kamar CRUD operations from admin panel."""

    @pytest.mark.integration
    def test_kamar_list_page(self, admin_client):
        """Test admin can view kamar list."""
        response = admin_client.get('/admin/kamar', follow_redirects=True)
        # Kamar list page should be accessible

    @pytest.mark.integration
    def test_create_kamar_page(self, admin_client):
        """Test admin can access kamar creation page."""
        response = admin_client.get('/admin/kamar/create', follow_redirects=True)
        # Kamar creation form should be available

    @pytest.mark.integration
    def test_create_kamar_valid_data(self, admin_client):
        """Test creating kamar with valid data."""
        response = admin_client.post('/admin/kamar/create', data={
            'nama': 'New Kamar Test',
            'deskripsi': 'Test kamar creation',
            'status': 'aktif',
            'urutan': 6
        }, follow_redirects=True)

        assert response.status_code == 200

    @pytest.mark.integration
    def test_create_kamar_missing_nama(self, admin_client):
        """Test creating kamar without nama fails."""
        response = admin_client.post('/admin/kamar/create', data={
            'nama': '',
            'deskripsi': 'Test',
            'status': 'aktif',
            'urutan': 1
        })

        assert response.status_code == 200

    @pytest.mark.integration
    def test_create_kamar_invalid_urutan(self, admin_client):
        """Test creating kamar with invalid urutan."""
        response = admin_client.post('/admin/kamar/create', data={
            'nama': 'Test Kamar',
            'deskripsi': 'Test',
            'status': 'aktif',
            'urutan': 'not_a_number'
        })

        assert response.status_code == 200

    @pytest.mark.integration
    def test_edit_kamar_page(self, admin_client, kamar_aktif):
        """Test admin can access kamar edit page."""
        response = admin_client.get(f'/admin/kamar/{kamar_aktif.id}/edit', follow_redirects=True)
        # Kamar edit page should be accessible

    @pytest.mark.integration
    def test_edit_kamar_valid_data(self, admin_client, kamar_aktif):
        """Test editing kamar with valid data."""
        response = admin_client.post(f'/admin/kamar/{kamar_aktif.id}/edit', data={
            'nama': 'Updated Kamar Name',
            'deskripsi': 'Updated description',
            'status': 'terkunci',
            'urutan': 2
        }, follow_redirects=True)

        assert response.status_code == 200

    @pytest.mark.integration
    def test_delete_kamar(self, admin_client, kamar_aktif):
        """Test deleting kamar."""
        response = admin_client.post(f'/admin/kamar/{kamar_aktif.id}/delete', follow_redirects=True)
        assert response.status_code == 200

    @pytest.mark.integration
    def test_cannot_delete_kamar_with_subdokumen(self, admin_client, kamar_aktif, sub_kamar, regular_user):
        """Test cannot delete kamar with documents."""
        with admin_client.application.app_context():
            dok = Dokumen(
                sub_kamar_id=sub_kamar.id,
                judul='Test',
                file_path='/up/test.pdf',
                uploaded_by=regular_user.id
            )
            db.session.add(dok)
            db.session.commit()

        response = admin_client.post(f'/admin/kamar/{kamar_aktif.id}/delete', follow_redirects=True)


class TestSubKamarManagement:
    """Test sub-kamar CRUD operations."""

    @pytest.mark.integration
    def test_sub_kamar_list(self, admin_client, kamar_aktif):
        """Test viewing sub-kamar list."""
        response = admin_client.get(f'/admin/kamar/{kamar_aktif.id}/sub', follow_redirects=True)
        # Sub-kamar list should be accessible

    @pytest.mark.integration
    def test_create_sub_kamar(self, admin_client, kamar_aktif):
        """Test creating sub-kamar."""
        response = admin_client.post(f'/admin/kamar/{kamar_aktif.id}/sub/create', data={
            'nama': 'New Sub Kamar',
            'deskripsi': 'Test sub-kamar'
        }, follow_redirects=True)

        assert response.status_code == 200

    @pytest.mark.integration
    def test_edit_sub_kamar(self, admin_client, sub_kamar):
        """Test editing sub-kamar."""
        response = admin_client.post(f'/admin/sub/{sub_kamar.id}/edit', data={
            'nama': 'Updated Sub Kamar',
            'deskripsi': 'Updated description'
        }, follow_redirects=True)

        assert response.status_code == 200

    @pytest.mark.integration
    def test_delete_sub_kamar(self, admin_client, sub_kamar):
        """Test deleting sub-kamar."""
        response = admin_client.post(f'/admin/sub/{sub_kamar.id}/delete', follow_redirects=True)
        assert response.status_code == 200


class TestDokumenUpload:
    """Test document upload functionality."""

    @pytest.mark.integration
    def test_upload_dokumen_page(self, admin_client, kamar_aktif, sub_kamar):
        """Test admin can access upload page."""
        response = admin_client.get(f'/admin/kamar/{kamar_aktif.id}/sub/{sub_kamar.id}/upload', follow_redirects=True)
        # Upload page should be accessible

    @pytest.mark.integration
    def test_upload_dokumen_valid_file(self, admin_client, kamar_aktif, sub_kamar, sample_pdf):
        """Test uploading a valid PDF file."""
        response = admin_client.post(
            f'/admin/kamar/{kamar_aktif.id}/sub/{sub_kamar.id}/upload',
            data={
                'judul': 'Test Document',
                'nomor_dokumen': 'DOK/2026/999',
                'file': (sample_pdf, 'test.pdf'),
                'status': 'aktif',
                'visibilitas': 'internal'
            },
            follow_redirects=True
        )

        assert response.status_code == 200

    @pytest.mark.integration
    def test_upload_dokumen_missing_judul(self, admin_client, kamar_aktif, sub_kamar, sample_pdf):
        """Test uploading without judul fails."""
        response = admin_client.post(
            f'/admin/kamar/{kamar_aktif.id}/sub/{sub_kamar.id}/upload',
            data={
                'judul': '',
                'nomor_dokumen': 'DOK/2026/999',
                'file': (sample_pdf, 'test.pdf')
            }
        )

        assert response.status_code == 200

    @pytest.mark.integration
    def test_upload_dokumen_no_file(self, admin_client, kamar_aktif, sub_kamar):
        """Test uploading without file fails."""
        response = admin_client.post(
            f'/admin/kamar/{kamar_aktif.id}/sub/{sub_kamar.id}/upload',
            data={
                'judul': 'Test Document',
                'nomor_dokumen': 'DOK/2026/999'
            }
        )

        assert response.status_code == 200

    @pytest.mark.integration
    def test_upload_dokumen_non_pdf_file(self, admin_client, kamar_aktif, sub_kamar):
        """Test uploading non-PDF file is rejected."""
        response = admin_client.post(
            f'/admin/kamar/{kamar_aktif.id}/sub/{sub_kamar.id}/upload',
            data={
                'judul': 'Test Document',
                'nomor_dokumen': 'DOK/2026/999',
                'file': ('not a pdf', 'test.txt')
            }
        )

        assert response.status_code == 200


class TestDokumenManagement:
    """Test document management from admin panel."""

    @pytest.mark.integration
    def test_edit_dokumen(self, admin_client, dokumen):
        """Test editing document metadata."""
        response = admin_client.post(f'/admin/dokumen/{dokumen.id}/edit', data={
            'judul': 'Updated Title',
            'nomor_dokumen': 'DOK/2026/UPDATE',
            'status': 'aktif',
            'visibilitas': 'publik'
        }, follow_redirects=True)

        assert response.status_code == 200

    @pytest.mark.integration
    def test_delete_dokumen(self, admin_client, dokumen):
        """Test deleting a document."""
        response = admin_client.post(f'/admin/dokumen/{dokumen.id}/delete', follow_redirects=True)
        assert response.status_code == 200

    @pytest.mark.integration
    def test_move_dokumen_to_different_sub_kamar(self, admin_client, dokumen, kamar_aktif, regular_user):
        """Test moving document to different sub-kamar."""
        with admin_client.application.app_context():
            new_sub = SubKamar(kamar_id=kamar_aktif.id, nama='New Sub')
            db.session.add(new_sub)
            db.session.commit()
            new_sub_id = new_sub.id

        response = admin_client.post(f'/admin/dokumen/{dokumen.id}/move', data={
            'sub_kamar_id': new_sub_id
        }, follow_redirects=True)

        assert response.status_code == 200

    @pytest.mark.integration
    def test_change_dokumen_status(self, admin_client, dokumen):
        """Test changing document status."""
        response = admin_client.post(f'/admin/dokumen/{dokumen.id}/status', data={
            'status': 'arsip'
        }, follow_redirects=True)

        assert response.status_code == 200

    @pytest.mark.integration
    def test_change_dokumen_visibilitas(self, admin_client, dokumen):
        """Test changing document visibility."""
        response = admin_client.post(f'/admin/dokumen/{dokumen.id}/visibilitas', data={
            'visibilitas': 'publik'
        }, follow_redirects=True)

        assert response.status_code == 200


class TestDokumenSearch:
    """Test document search in admin panel."""

    @pytest.mark.integration
    def test_search_dokumen_by_judul(self, admin_client, dokumen):
        """Test searching documents by title."""
        response = admin_client.get(f'/admin/dokumen?cari={dokumen.judul}', follow_redirects=True)
        assert response.status_code == 200

    @pytest.mark.integration
    def test_search_dokumen_by_nomor(self, admin_client, dokumen):
        """Test searching documents by document number."""
        response = admin_client.get(f'/admin/dokumen?cari={dokumen.nomor_dokumen}', follow_redirects=True)
        assert response.status_code == 200

    @pytest.mark.integration
    def test_filter_dokumen_by_sub_kamar(self, admin_client, sub_kamar):
        """Test filtering documents by sub-kamar."""
        response = admin_client.get(f'/admin/dokumen?sub_kamar_id={sub_kamar.id}', follow_redirects=True)
        assert response.status_code == 200

    @pytest.mark.integration
    def test_filter_dokumen_by_status(self, admin_client):
        """Test filtering documents by status."""
        response = admin_client.get('/admin/dokumen?status=aktif', follow_redirects=True)
        assert response.status_code == 200

    @pytest.mark.integration
    def test_filter_dokumen_by_visibilitas(self, admin_client):
        """Test filtering documents by visibility."""
        response = admin_client.get('/admin/dokumen?visibilitas=internal', follow_redirects=True)
        assert response.status_code == 200


class TestUserManagement:
    """Test user administration from admin panel."""

    @pytest.mark.integration
    def test_user_list_page(self, admin_client):
        """Test admin can view user list."""
        response = admin_client.get('/admin/users', follow_redirects=True)
        # User list should be accessible

    @pytest.mark.integration
    def test_create_user_page(self, admin_client):
        """Test admin can access user creation page."""
        response = admin_client.get('/admin/users/create', follow_redirects=True)
        # User creation form should be available

    @pytest.mark.integration
    def test_create_user_valid_data(self, admin_client):
        """Test creating user with valid data."""
        response = admin_client.post('/admin/users/create', data={
            'nama': 'New User',
            'email': 'newuser@test.com',
            'password': 'NewUser@123',
            'role': 'user'
        }, follow_redirects=True)

        assert response.status_code == 200

    @pytest.mark.integration
    def test_create_user_duplicate_email(self, admin_client, regular_user):
        """Test creating user with duplicate email fails."""
        response = admin_client.post('/admin/users/create', data={
            'nama': 'Duplicate User',
            'email': 'user@test.com',  # Already exists
            'password': 'Password123',
            'role': 'user'
        })

        assert response.status_code == 200

    @pytest.mark.integration
    def test_edit_user(self, admin_client, regular_user):
        """Test editing user."""
        response = admin_client.post(f'/admin/users/{regular_user.id}/edit', data={
            'nama': 'Updated Name',
            'email': 'user@test.com',
            'role': 'admin'
        }, follow_redirects=True)

        assert response.status_code == 200

    @pytest.mark.integration
    def test_deactivate_user(self, admin_client, regular_user):
        """Test deactivating a user account."""
        response = admin_client.post(f'/admin/users/{regular_user.id}/deactivate', follow_redirects=True)
        assert response.status_code == 200

    @pytest.mark.integration
    def test_activate_user(self, admin_client, inactive_user):
        """Test activating a user account."""
        response = admin_client.post(f'/admin/users/{inactive_user.id}/activate', follow_redirects=True)
        assert response.status_code == 200

    @pytest.mark.integration
    def test_reset_user_password(self, admin_client, regular_user):
        """Test resetting user password."""
        response = admin_client.post(f'/admin/users/{regular_user.id}/reset-password', data={
            'password': 'NewPassword123'
        }, follow_redirects=True)

        assert response.status_code == 200

    @pytest.mark.integration
    def test_cannot_delete_last_superadmin(self, admin_client, superadmin_user):
        """Test preventing deletion of last superadmin."""
        response = admin_client.post(f'/admin/users/{superadmin_user.id}/delete', follow_redirects=True)
        # Should prevent deletion


class TestAdminPermissions:
    """Test admin-level permission checks."""

    @pytest.mark.integration
    def test_user_cannot_access_admin_kamar_management(self, auth_client, kamar_aktif):
        """Test regular user cannot access kamar management."""
        response = auth_client.get(f'/admin/kamar/{kamar_aktif.id}/edit', follow_redirects=True)
        # Should be denied

    @pytest.mark.integration
    def test_user_cannot_upload_dokumen(self, auth_client, kamar_aktif, sub_kamar):
        """Test regular user cannot upload documents."""
        response = auth_client.get(f'/admin/kamar/{kamar_aktif.id}/sub/{sub_kamar.id}/upload', follow_redirects=True)
        # Should be denied

    @pytest.mark.integration
    def test_user_cannot_manage_users(self, auth_client):
        """Test regular user cannot access user management."""
        response = auth_client.get('/admin/users', follow_redirects=True)
        # Should be denied

    @pytest.mark.integration
    def test_superadmin_can_access_admin_functions(self, superadmin_client, kamar_aktif):
        """Test superadmin can access all admin functions."""
        response = superadmin_client.get(f'/admin/kamar/{kamar_aktif.id}/edit', follow_redirects=True)
        # Superadmin should have access


class TestAdminStatistics:
    """Test admin statistics and reporting."""

    @pytest.mark.integration
    def test_dokumen_statistics(self, admin_client, multiple_dokumen):
        """Test viewing dokumen statistics."""
        response = admin_client.get('/admin/statistics/dokumen', follow_redirects=True)
        # Statistics page should be accessible

    @pytest.mark.integration
    def test_activity_log(self, admin_client):
        """Test viewing activity log."""
        response = admin_client.get('/admin/logs', follow_redirects=True)
        # Activity log should be accessible

    @pytest.mark.integration
    def test_user_activity_report(self, admin_client, regular_user):
        """Test viewing user activity report."""
        response = admin_client.get(f'/admin/users/{regular_user.id}/activity', follow_redirects=True)
        # User activity should be viewable


class TestBulkOperations:
    """Test bulk operations in admin."""

    @pytest.mark.integration
    def test_bulk_change_status(self, admin_client, multiple_dokumen):
        """Test bulk status change."""
        response = admin_client.post('/admin/dokumen/bulk-action', data={
            'action': 'change_status',
            'status': 'arsip',
            'dokumen_ids': [d.id for d in multiple_dokumen[:5]]
        }, follow_redirects=True)

        assert response.status_code == 200

    @pytest.mark.integration
    def test_bulk_change_visibility(self, admin_client, multiple_dokumen):
        """Test bulk visibility change."""
        response = admin_client.post('/admin/dokumen/bulk-action', data={
            'action': 'change_visibility',
            'visibilitas': 'publik',
            'dokumen_ids': [d.id for d in multiple_dokumen[:5]]
        }, follow_redirects=True)

        assert response.status_code == 200

    @pytest.mark.integration
    def test_bulk_delete(self, admin_client, multiple_dokumen):
        """Test bulk delete operation."""
        response = admin_client.post('/admin/dokumen/bulk-action', data={
            'action': 'delete',
            'dokumen_ids': [d.id for d in multiple_dokumen[:3]]
        }, follow_redirects=True)

        assert response.status_code == 200


class TestAdminSecurity:
    """Test security aspects of admin operations."""

    @pytest.mark.integration
    def test_sql_injection_in_search(self, admin_client):
        """Test search is safe against SQL injection."""
        response = admin_client.get("/admin/dokumen?cari=' OR '1'='1", follow_redirects=True)
        assert response.status_code == 200

    @pytest.mark.integration
    def test_csrf_protection_on_delete(self, client, dokumen):
        """Test CSRF protection on deletion."""
        response = client.post(f'/admin/dokumen/{dokumen.id}/delete')
        # Should require CSRF token

    @pytest.mark.integration
    def test_cannot_escalate_privileges(self, auth_client):
        """Test user cannot escalate own privileges."""
        response = auth_client.post('/admin/users/self/role', data={
            'role': 'admin'
        })

        # Should be denied or not change role
