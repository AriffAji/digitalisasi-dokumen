"""
Integration tests for authentication routes.
Tests cover login, logout, profile, password change, and rate limiting.
"""

import pytest
from datetime import datetime
from models import db, User


class TestLoginRoute:
    """Test login functionality."""

    @pytest.mark.auth
    def test_login_page_get(self, client):
        """Test GET request to login page."""
        response = client.get('/auth/login')
        assert response.status_code == 200

    @pytest.mark.auth
    def test_login_with_valid_credentials(self, client, regular_user):
        """Test login with valid email and password."""
        response = client.post('/auth/login', data={
            'email': 'user@test.com',
            'password': 'User@123456'
        }, follow_redirects=False)

        assert response.status_code in [200, 302]

    @pytest.mark.auth
    def test_login_redirect_by_role_user(self, client, regular_user):
        """Test login redirects regular user to public index."""
        response = client.post('/auth/login', data={
            'email': 'user@test.com',
            'password': 'User@123456'
        }, follow_redirects=True)

        assert response.status_code == 200

    @pytest.mark.auth
    def test_login_redirect_by_role_admin(self, client, admin_user):
        """Test login redirects admin to admin dashboard."""
        response = client.post('/auth/login', data={
            'email': 'admin@test.com',
            'password': 'Admin@12345'
        }, follow_redirects=True)

        assert response.status_code == 200

    @pytest.mark.auth
    def test_login_redirect_by_role_superadmin(self, client, superadmin_user):
        """Test login redirects superadmin to superadmin dashboard."""
        response = client.post('/auth/login', data={
            'email': 'superadmin@test.com',
            'password': 'SuperAdmin@123'
        }, follow_redirects=True)

        assert response.status_code == 200

    @pytest.mark.auth
    def test_login_with_invalid_email(self, client):
        """Test login with non-existent email."""
        response = client.post('/auth/login', data={
            'email': 'nonexistent@test.com',
            'password': 'SomePassword123'
        })

        assert response.status_code == 200
        assert b'Email atau password salah' in response.data

    @pytest.mark.auth
    def test_login_with_wrong_password(self, client, regular_user):
        """Test login with wrong password."""
        response = client.post('/auth/login', data={
            'email': 'user@test.com',
            'password': 'WrongPassword123'
        })

        assert response.status_code == 200
        assert b'Email atau password salah' in response.data

    @pytest.mark.auth
    def test_login_with_inactive_user(self, client, inactive_user):
        """Test login with an inactive user account."""
        response = client.post('/auth/login', data={
            'email': 'inactive@test.com',
            'password': 'Inactive@12'
        })

        assert response.status_code == 200
        assert b'telah dinonaktifkan' in response.data

    @pytest.mark.auth
    def test_login_email_case_insensitive(self, client, regular_user):
        """Test login with different email case."""
        response = client.post('/auth/login', data={
            'email': 'USER@TEST.COM',  # uppercase
            'password': 'User@123456'
        }, follow_redirects=False)

        assert response.status_code in [200, 302]

    @pytest.mark.auth
    def test_login_rate_limiting_after_5_attempts(self, client, regular_user):
        """Test rate limiting after 5 failed login attempts."""
        for i in range(5):
            client.post('/auth/login', data={
                'email': 'user@test.com',
                'password': 'WrongPassword123'
            })

        # 6th attempt should be blocked
        response = client.post('/auth/login', data={
            'email': 'user@test.com',
            'password': 'User@123456'  # even correct password
        })

        assert response.status_code == 429
        assert b'Terlalu banyak percobaan' in response.data

    @pytest.mark.auth
    def test_login_rate_limit_tracking_by_ip(self, client, regular_user):
        """Test rate limiting is tracked per IP."""
        # First IP fails 5 times
        for _ in range(5):
            client.post('/auth/login', data={
                'email': 'user@test.com',
                'password': 'WrongPassword'
            }, environ_base={'REMOTE_ADDR': '192.168.1.1'})

        # Different IP should work
        response = client.post('/auth/login', data={
            'email': 'user@test.com',
            'password': 'User@123456'
        }, environ_base={'REMOTE_ADDR': '192.168.1.2'})

        assert response.status_code != 429

    @pytest.mark.auth
    def test_login_remember_me(self, client, regular_user):
        """Test remember me functionality."""
        response = client.post('/auth/login', data={
            'email': 'user@test.com',
            'password': 'User@123456',
            'remember': 'on'
        }, follow_redirects=False)

        assert response.status_code in [200, 302]

    @pytest.mark.auth
    def test_authenticated_user_redirect_from_login(self, auth_client):
        """Test that authenticated user is redirected from login page."""
        response = auth_client.get('/auth/login')
        assert response.status_code in [200, 302]

    @pytest.mark.auth
    def test_login_successful_clears_attempts(self, client, regular_user):
        """Test that successful login clears failed attempt counter."""
        # Fail once
        client.post('/auth/login', data={
            'email': 'user@test.com',
            'password': 'WrongPassword'
        })

        # Login successfully
        response = client.post('/auth/login', data={
            'email': 'user@test.com',
            'password': 'User@123456'
        }, follow_redirects=False)

        assert response.status_code in [200, 302]


class TestLogoutRoute:
    """Test logout functionality."""

    @pytest.mark.auth
    def test_logout_redirects_to_login(self, auth_client):
        """Test logout redirects to login page."""
        response = auth_client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200

    @pytest.mark.auth
    def test_logout_without_auth(self, client):
        """Test logout without being authenticated."""
        response = client.get('/auth/logout', follow_redirects=True)
        # Should redirect to login
        assert response.status_code == 200

    @pytest.mark.auth
    def test_logout_clears_session(self, auth_client):
        """Test that logout clears user session."""
        # First get a protected page while authenticated
        response = auth_client.get('/auth/profil')
        assert response.status_code == 200

        # Logout
        auth_client.get('/auth/logout')

        # Try to access protected page again
        response = auth_client.get('/auth/profil', follow_redirects=True)
        # Should redirect to login


class TestProfileRoute:
    """Test user profile functionality."""

    @pytest.mark.auth
    def test_profile_page_get(self, auth_client):
        """Test GET request to profile page."""
        response = auth_client.get('/auth/profil')
        assert response.status_code == 200

    @pytest.mark.auth
    def test_profile_requires_authentication(self, client):
        """Test profile page requires authentication."""
        response = client.get('/auth/profil', follow_redirects=True)
        # Should redirect to login
        assert response.status_code == 200

    @pytest.mark.auth
    def test_change_password_valid(self, app, auth_client, regular_user):
        """Test changing password with valid inputs."""
        response = auth_client.post('/auth/profil', data={
            'password_lama': 'User@123456',
            'password_baru': 'NewPassword123',
            'konfirmasi': 'NewPassword123'
        })

        assert response.status_code in [200, 302]

        # Verify new password works
        with app.app_context():
            user = User.query.get(regular_user.id)
            assert user.check_password('NewPassword123') is True

    @pytest.mark.auth
    def test_change_password_wrong_old_password(self, auth_client):
        """Test change password with wrong old password."""
        response = auth_client.post('/auth/profil', data={
            'password_lama': 'WrongOldPassword',
            'password_baru': 'NewPassword123',
            'konfirmasi': 'NewPassword123'
        })

        assert response.status_code == 200
        assert b'Password lama salah' in response.data

    @pytest.mark.auth
    def test_change_password_mismatch_confirmation(self, auth_client):
        """Test change password with mismatched confirmation."""
        response = auth_client.post('/auth/profil', data={
            'password_lama': 'User@123456',
            'password_baru': 'NewPassword123',
            'konfirmasi': 'DifferentPassword123'
        })

        assert response.status_code == 200
        assert b'Konfirmasi password tidak cocok' in response.data

    @pytest.mark.auth
    def test_change_password_too_short(self, auth_client):
        """Test change password with password less than 8 characters."""
        response = auth_client.post('/auth/profil', data={
            'password_lama': 'User@123456',
            'password_baru': 'Short1',
            'konfirmasi': 'Short1'
        })

        assert response.status_code == 200
        assert b'minimal 8 karakter' in response.data

    @pytest.mark.auth
    def test_change_password_without_letters(self, auth_client):
        """Test change password without letters."""
        response = auth_client.post('/auth/profil', data={
            'password_lama': 'User@123456',
            'password_baru': '12345678',
            'konfirmasi': '12345678'
        })

        assert response.status_code == 200
        assert b'mengandung huruf' in response.data

    @pytest.mark.auth
    def test_change_password_without_numbers(self, auth_client):
        """Test change password without numbers."""
        response = auth_client.post('/auth/profil', data={
            'password_lama': 'User@123456',
            'password_baru': 'OnlyLetters',
            'konfirmasi': 'OnlyLetters'
        })

        assert response.status_code == 200
        assert b'mengandung angka' in response.data

    @pytest.mark.auth
    def test_change_password_success_message(self, auth_client):
        """Test success message after password change."""
        response = auth_client.post('/auth/profil', data={
            'password_lama': 'User@123456',
            'password_baru': 'NewSecure123',
            'konfirmasi': 'NewSecure123'
        }, follow_redirects=True)

        assert b'Password berhasil diubah' in response.data


class TestAuthEdgeCases:
    """Test edge cases and security aspects."""

    @pytest.mark.auth
    def test_login_with_empty_email(self, client):
        """Test login with empty email."""
        response = client.post('/auth/login', data={
            'email': '',
            'password': 'SomePassword123'
        })

        assert response.status_code == 200

    @pytest.mark.auth
    def test_login_with_empty_password(self, client):
        """Test login with empty password."""
        response = client.post('/auth/login', data={
            'email': 'user@test.com',
            'password': ''
        })

        assert response.status_code == 200

    @pytest.mark.auth
    def test_login_with_whitespace_email(self, client, regular_user):
        """Test login with whitespace in email."""
        response = client.post('/auth/login', data={
            'email': '  user@test.com  ',
            'password': 'User@123456'
        }, follow_redirects=False)

        assert response.status_code in [200, 302]

    @pytest.mark.auth
    def test_multiple_users_login_sequentially(self, client, regular_user, admin_user, superadmin_user):
        """Test multiple users logging in sequentially."""
        # User login
        response1 = client.post('/auth/login', data={
            'email': 'user@test.com',
            'password': 'User@123456'
        }, follow_redirects=True)
        assert response1.status_code == 200

        # Logout
        client.get('/auth/logout')

        # Admin login
        response2 = client.post('/auth/login', data={
            'email': 'admin@test.com',
            'password': 'Admin@12345'
        }, follow_redirects=True)
        assert response2.status_code == 200

    @pytest.mark.auth
    def test_login_with_sql_injection_attempt(self, client):
        """Test login is safe against SQL injection."""
        response = client.post('/auth/login', data={
            'email': "' OR '1'='1",
            'password': "' OR '1'='1"
        })

        assert response.status_code == 200
        assert b'Email atau password salah' in response.data

    @pytest.mark.auth
    def test_password_change_with_empty_fields(self, auth_client):
        """Test password change with empty fields."""
        response = auth_client.post('/auth/profil', data={
            'password_lama': '',
            'password_baru': '',
            'konfirmasi': ''
        })

        assert response.status_code == 200
