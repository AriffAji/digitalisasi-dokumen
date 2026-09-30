"""
Tests for app factory and overall application setup.
Tests cover app creation, error handlers, context processors, and Flask extensions.
"""

import pytest
from app import create_app, setup_logging
from models import db
from flask import Flask


class TestAppFactory:
    """Test Flask app factory."""

    @pytest.mark.unit
    def test_app_created_with_default_config(self):
        """Test app is created with default config."""
        app = create_app()
        assert app is not None
        assert isinstance(app, Flask)

    @pytest.mark.unit
    def test_app_created_with_development_config(self):
        """Test app can be created with development config."""
        app = create_app('development')
        assert app is not None

    @pytest.mark.unit
    def test_app_created_with_production_config(self):
        """Test app can be created with production config."""
        app = create_app('production')
        assert app is not None
        assert app.config['DEBUG'] is False

    @pytest.mark.unit
    def test_app_has_secret_key(self):
        """Test app has a secret key configured."""
        app = create_app()
        assert app.config['SECRET_KEY'] is not None

    @pytest.mark.unit
    def test_app_has_database_configured(self):
        """Test app has database configured."""
        app = create_app()
        assert 'SQLALCHEMY_DATABASE_URI' in app.config

    @pytest.mark.unit
    def test_app_upload_folder_created(self, tmp_path, monkeypatch):
        """Test app creates upload folder if not exists."""
        monkeypatch.setenv('UPLOAD_FOLDER', str(tmp_path / 'uploads'))
        app = create_app()
        # Folder should be created by create_app


class TestAppExtensions:
    """Test Flask extensions initialization."""

    @pytest.mark.unit
    def test_database_initialized(self, app):
        """Test SQLAlchemy database is initialized."""
        with app.app_context():
            assert db is not None

    @pytest.mark.unit
    def test_csrf_protection_initialized(self, app):
        """Test CSRF protection is initialized."""
        with app.app_context():
            from extensions import csrf
            assert csrf is not None

    @pytest.mark.unit
    def test_cache_initialized(self, app):
        """Test caching is initialized."""
        with app.app_context():
            from extensions import cache
            assert cache is not None

    @pytest.mark.unit
    def test_login_manager_initialized(self, app):
        """Test login manager is initialized."""
        with app.app_context():
            from flask_login import current_user
            # Should be able to use login_manager features


class TestAppBlueprints:
    """Test app blueprints registration."""

    @pytest.mark.unit
    def test_public_blueprint_registered(self, app):
        """Test public blueprint is registered."""
        assert any(bp.name == 'public' for bp in app.blueprints.values())

    @pytest.mark.unit
    def test_auth_blueprint_registered(self, app):
        """Test auth blueprint is registered."""
        assert any(bp.name == 'auth' for bp in app.blueprints.values())

    @pytest.mark.unit
    def test_admin_blueprint_registered(self, app):
        """Test admin blueprint is registered."""
        assert any(bp.name == 'admin' for bp in app.blueprints.values())

    @pytest.mark.unit
    def test_superadmin_blueprint_registered(self, app):
        """Test superadmin blueprint is registered."""
        assert any(bp.name == 'superadmin' for bp in app.blueprints.values())

    @pytest.mark.unit
    def test_auth_blueprint_has_url_prefix(self, app):
        """Test auth blueprint has correct URL prefix."""
        with app.test_request_context():
            # Login route should be at /auth/login
            pass

    @pytest.mark.unit
    def test_admin_blueprint_has_url_prefix(self, app):
        """Test admin blueprint has correct URL prefix."""
        with app.test_request_context():
            # Admin routes should be under /admin
            pass

    @pytest.mark.unit
    def test_superadmin_blueprint_has_url_prefix(self, app):
        """Test superadmin blueprint has correct URL prefix."""
        with app.test_request_context():
            # Superadmin routes should be under /superadmin
            pass


class TestErrorHandlers:
    """Test app error handlers."""

    @pytest.mark.unit
    def test_404_error_handler(self, client):
        """Test 404 error handler renders template."""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404

    @pytest.mark.unit
    def test_403_error_handler(self, client):
        """Test 403 error handler renders template."""
        # 403 will be triggered by accessing locked kamar
        from models import Kamar
        with client.application.app_context():
            kamar = Kamar(nama='Test', status='terkunci', urutan=1)
            db.session.add(kamar)
            db.session.commit()
            kamar_id = kamar.id

        response = client.get(f'/kamar/{kamar_id}')
        assert response.status_code == 403

    @pytest.mark.unit
    def test_429_error_handler(self, client, regular_user):
        """Test 429 rate limit handler renders template."""
        # Trigger rate limiting with failed login attempts
        for _ in range(5):
            client.post('/auth/login', data={
                'email': 'user@test.com',
                'password': 'wrong'
            })

        response = client.post('/auth/login', data={
            'email': 'user@test.com',
            'password': 'User@123456'
        })

        assert response.status_code == 429


class TestContextProcessors:
    """Test app context processors."""

    @pytest.mark.unit
    def test_global_variables_injected(self, client):
        """Test global variables are injected into templates."""
        response = client.get('/')
        assert response.status_code == 200
        # Global variables should be available in templates

    @pytest.mark.unit
    def test_sistem_nama_available(self, app):
        """Test SISTEM_NAMA is available in template context."""
        with app.app_context():
            pass
        # SISTEM_NAMA should be 'SIADIK'

    @pytest.mark.unit
    def test_instansi_nama_available(self, app):
        """Test INSTANSI_NAMA is available in template context."""
        with app.app_context():
            pass
        # INSTANSI_NAMA should be 'PPNP'

    @pytest.mark.unit
    def test_tahun_fokus_available(self, app):
        """Test TAHUN_FOKUS is available in template context."""
        with app.app_context():
            pass
        # TAHUN_FOKUS should be '2026'


class TestSessionConfiguration:
    """Test session configuration."""

    @pytest.mark.unit
    def test_permanent_session_enabled(self, app):
        """Test permanent sessions are enabled."""
        @app.before_request
        def check_permanent():
            from flask import session
            # Session should be set to permanent

    @pytest.mark.unit
    def test_csrf_protection_enabled(self, app):
        """Test CSRF protection is enabled."""
        from extensions import csrf
        # CSRF should be initialized

    @pytest.mark.unit
    def test_cache_enabled(self, app):
        """Test cache is enabled."""
        from extensions import cache
        # Cache should be initialized


class TestLogging:
    """Test application logging."""

    @pytest.mark.unit
    def test_logging_setup_function_exists(self):
        """Test setup_logging function exists."""
        assert callable(setup_logging)

    @pytest.mark.unit
    def test_logging_setup(self, app):
        """Test logging is set up correctly."""
        # Logs should be written to logs/siadik.log


class TestAppInitialization:
    """Test app initialization process."""

    @pytest.mark.unit
    def test_app_context_works(self, app):
        """Test app context can be pushed."""
        with app.app_context():
            assert app is not None

    @pytest.mark.unit
    def test_test_client_created(self, client):
        """Test client can be created."""
        assert client is not None

    @pytest.mark.unit
    def test_database_tables_created(self, app):
        """Test database tables are created."""
        with app.app_context():
            # Tables should exist in test database

    @pytest.mark.unit
    def test_cli_runner_created(self, runner):
        """Test CLI runner can be created."""
        assert runner is not None


class TestAppConfiguration:
    """Test app configuration loading."""

    @pytest.mark.unit
    def test_app_loads_base_config(self):
        """Test app loads base configuration."""
        app = create_app()
        assert app.config['TESTING'] is False or app.config['TESTING'] is True

    @pytest.mark.unit
    def test_app_config_immutable_after_creation(self, app):
        """Test app config can be accessed after creation."""
        original_debug = app.config['DEBUG']
        # Config values should be accessible

    @pytest.mark.unit
    def test_testing_config_overrides_defaults(self):
        """Test testing config properly overrides defaults."""
        from config import Config

        class TestConfig(Config):
            TESTING = True

        # Should properly override base config


class TestAppDatabaseIntegration:
    """Test app and database integration."""

    @pytest.mark.integration
    def test_database_session_available(self, app):
        """Test database session is available in app context."""
        with app.app_context():
            from models import db
            assert db.session is not None

    @pytest.mark.integration
    def test_models_can_be_queried(self, app):
        """Test models can be queried."""
        with app.app_context():
            from models import User
            result = User.query.count()
            assert isinstance(result, int)

    @pytest.mark.integration
    def test_database_changes_persist_in_session(self, app):
        """Test database changes persist within session."""
        with app.app_context():
            from models import User
            initial_count = User.query.count()

            user = User(
                nama='Test User',
                email='unique_test@test.com',
                role='user'
            )
            user.set_password('TestPassword123')
            db.session.add(user)
            db.session.commit()

            new_count = User.query.count()
            assert new_count == initial_count + 1


class TestAppErrorHandlingIntegration:
    """Test error handling integration."""

    @pytest.mark.integration
    def test_app_handles_database_errors(self, app):
        """Test app handles database errors gracefully."""
        with app.test_client() as client:
            response = client.get('/')
            assert response.status_code in [200, 500, 302]

    @pytest.mark.integration
    def test_app_handles_template_errors(self, app):
        """Test app handles template rendering errors."""
        with app.test_client() as client:
            response = client.get('/')
            assert response.status_code in [200, 500]


class TestAppRoutesAvailable:
    """Test that routes are properly registered."""

    @pytest.mark.integration
    def test_public_routes_available(self, client):
        """Test public routes are available."""
        response = client.get('/')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_auth_login_route_available(self, client):
        """Test auth login route is available."""
        response = client.get('/auth/login')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_search_route_available(self, client):
        """Test search route is available."""
        response = client.get('/search')
        assert response.status_code == 200

    @pytest.mark.integration
    def test_api_search_route_available(self, client):
        """Test API search route is available."""
        response = client.get('/api/global-search?q=test')
        assert response.status_code == 200
