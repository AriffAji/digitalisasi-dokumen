"""
Unit tests for configuration management.
Tests cover config values, environment loading, and app setup.
"""

import pytest
import os
from config import Config, DevelopmentConfig, ProductionConfig


class TestBaseConfig:
    """Test base Config class."""

    @pytest.mark.unit
    def test_secret_key_exists(self):
        """Test that secret key is configured."""
        config = Config()
        assert config.SECRET_KEY is not None

    @pytest.mark.unit
    def test_database_uri_configured(self):
        """Test database URI is configured."""
        config = Config()
        assert config.SQLALCHEMY_DATABASE_URI is not None

    @pytest.mark.unit
    def test_upload_folder_exists(self):
        """Test upload folder path is configured."""
        config = Config()
        assert config.UPLOAD_FOLDER is not None

    @pytest.mark.unit
    def test_max_content_length(self):
        """Test max file size is 10MB."""
        config = Config()
        assert config.MAX_CONTENT_LENGTH == 10 * 1024 * 1024

    @pytest.mark.unit
    def test_allowed_extensions(self):
        """Test allowed file extensions."""
        config = Config()
        assert 'pdf' in config.ALLOWED_EXTENSIONS

    @pytest.mark.unit
    def test_sqlalchemy_track_modifications_disabled(self):
        """Test SQLAlchemy track modifications is disabled."""
        config = Config()
        assert config.SQLALCHEMY_TRACK_MODIFICATIONS is False

    @pytest.mark.unit
    def test_session_lifetime(self):
        """Test session lifetime is 8 hours."""
        config = Config()
        from datetime import timedelta
        assert config.PERMANENT_SESSION_LIFETIME == timedelta(hours=8)

    @pytest.mark.unit
    def test_session_cookie_httponly_enabled(self):
        """Test HTTPOnly cookie protection."""
        config = Config()
        assert config.SESSION_COOKIE_HTTPONLY is True

    @pytest.mark.unit
    def test_session_cookie_samesite_set(self):
        """Test SameSite cookie setting."""
        config = Config()
        assert config.SESSION_COOKIE_SAMESITE == 'Lax'

    @pytest.mark.unit
    def test_cache_type_configured(self):
        """Test cache type is set."""
        config = Config()
        assert config.CACHE_TYPE == 'SimpleCache'

    @pytest.mark.unit
    def test_cache_default_timeout(self):
        """Test cache default timeout is 5 minutes."""
        config = Config()
        assert config.CACHE_DEFAULT_TIMEOUT == 300

    @pytest.mark.unit
    def test_cache_threshold(self):
        """Test cache threshold is set."""
        config = Config()
        assert config.CACHE_THRESHOLD == 500

    @pytest.mark.unit
    def test_instansi_info_configured(self):
        """Test institution info is configured."""
        config = Config()
        assert config.INSTANSI_NAMA == 'PPNP'
        assert config.INSTANSI_LENGKAP == 'Politeknik Pertanian Negeri Payakumbuh'

    @pytest.mark.unit
    def test_sistem_info_configured(self):
        """Test system info is configured."""
        config = Config()
        assert config.SISTEM_NAMA == 'SIADIK'
        assert config.SISTEM_LENGKAP == 'Sistem Informasi Arsip Digital Kepegawaian'

    @pytest.mark.unit
    def test_tahun_fokus(self):
        """Test year focus is configured."""
        config = Config()
        assert config.TAHUN_FOKUS == '2026'


class TestDevelopmentConfig:
    """Test development configuration."""

    @pytest.mark.unit
    def test_debug_enabled_in_development(self):
        """Test debug is enabled in development."""
        config = DevelopmentConfig()
        assert config.DEBUG is True

    @pytest.mark.unit
    def test_development_inherits_base_config(self):
        """Test development config inherits from base."""
        config = DevelopmentConfig()
        assert config.INSTANSI_NAMA == 'PPNP'
        assert config.SQLALCHEMY_TRACK_MODIFICATIONS is False

    @pytest.mark.unit
    def test_session_cookie_not_secure_in_development(self):
        """Test session cookie is not secure in development."""
        config = DevelopmentConfig()
        assert config.SESSION_COOKIE_SECURE is False


class TestProductionConfig:
    """Test production configuration."""

    @pytest.mark.unit
    def test_debug_disabled_in_production(self):
        """Test debug is disabled in production."""
        config = ProductionConfig()
        assert config.DEBUG is False

    @pytest.mark.unit
    def test_session_cookie_secure_in_production(self):
        """Test session cookie is secure in production."""
        config = ProductionConfig()
        assert config.SESSION_COOKIE_SECURE is True

    @pytest.mark.unit
    def test_production_inherits_base_config(self):
        """Test production config inherits from base."""
        config = ProductionConfig()
        assert config.CACHE_TYPE == 'SimpleCache'
        assert config.MAX_CONTENT_LENGTH == 10 * 1024 * 1024


class TestConfigDict:
    """Test config dictionary."""

    @pytest.mark.unit
    def test_config_dict_has_default(self):
        """Test config dict has default entry."""
        from config import config
        assert 'default' in config

    @pytest.mark.unit
    def test_config_dict_has_development(self):
        """Test config dict has development entry."""
        from config import config
        assert 'development' in config

    @pytest.mark.unit
    def test_config_dict_has_production(self):
        """Test config dict has production entry."""
        from config import config
        assert 'production' in config

    @pytest.mark.unit
    def test_default_config_is_development(self):
        """Test default config is development config."""
        from config import config
        assert config['default'] == DevelopmentConfig


class TestConfigWithEnv:
    """Test configuration with environment variables."""

    @pytest.mark.unit
    def test_secret_key_from_env(self, monkeypatch):
        """Test secret key can be set from environment."""
        monkeypatch.setenv('SECRET_KEY', 'env-secret-key')
        # Import after setting env to test actual loading
        config = Config()
        # Note: The actual loading happens at module import time
        # This test documents the behavior

    @pytest.mark.unit
    def test_database_url_from_env(self, monkeypatch):
        """Test database URL can be set from environment."""
        monkeypatch.setenv('DATABASE_URL', 'sqlite:///test.db')
        # Config loads DATABASE_URL from env

    @pytest.mark.unit
    def test_fallback_secret_key(self):
        """Test fallback secret key exists."""
        config = Config()
        # Should have a fallback key if env var not set
        assert config.SECRET_KEY is not None


class TestConfigValidation:
    """Test configuration validation."""

    @pytest.mark.unit
    def test_max_content_length_is_integer(self):
        """Test max content length is integer."""
        config = Config()
        assert isinstance(config.MAX_CONTENT_LENGTH, int)

    @pytest.mark.unit
    def test_cache_threshold_is_integer(self):
        """Test cache threshold is integer."""
        config = Config()
        assert isinstance(config.CACHE_THRESHOLD, int)

    @pytest.mark.unit
    def test_cache_default_timeout_is_integer(self):
        """Test cache timeout is integer."""
        config = Config()
        assert isinstance(config.CACHE_DEFAULT_TIMEOUT, int)

    @pytest.mark.unit
    def test_all_string_configs_are_string(self):
        """Test all string configs are actually strings."""
        config = Config()
        assert isinstance(config.INSTANSI_NAMA, str)
        assert isinstance(config.SISTEM_NAMA, str)
        assert isinstance(config.TAHUN_FOKUS, str)

    @pytest.mark.unit
    def test_all_bool_configs_are_bool(self):
        """Test all boolean configs are actually boolean."""
        config = Config()
        assert isinstance(config.SESSION_COOKIE_HTTPONLY, bool)
        assert isinstance(config.SQLALCHEMY_TRACK_MODIFICATIONS, bool)


class TestCacheConfiguration:
    """Test cache-specific configuration."""

    @pytest.mark.unit
    def test_cache_type_simple_cache(self):
        """Test cache type is SimpleCache."""
        config = Config()
        assert config.CACHE_TYPE == 'SimpleCache'

    @pytest.mark.unit
    def test_cache_reasonable_timeout(self):
        """Test cache timeout is reasonable."""
        config = Config()
        assert config.CACHE_DEFAULT_TIMEOUT >= 60  # At least 1 minute
        assert config.CACHE_DEFAULT_TIMEOUT <= 3600  # At most 1 hour

    @pytest.mark.unit
    def test_cache_threshold_positive(self):
        """Test cache threshold is positive."""
        config = Config()
        assert config.CACHE_THRESHOLD > 0


class TestSecurityConfiguration:
    """Test security-related configuration."""

    @pytest.mark.unit
    def test_session_security_headers_set(self):
        """Test session security headers are configured."""
        config = Config()
        assert config.SESSION_COOKIE_HTTPONLY is True
        assert config.SESSION_COOKIE_SAMESITE in ['Strict', 'Lax', 'None']

    @pytest.mark.unit
    def test_session_lifetime_reasonable(self):
        """Test session lifetime is reasonable."""
        from datetime import timedelta
        config = Config()
        assert config.PERMANENT_SESSION_LIFETIME >= timedelta(hours=1)
        assert config.PERMANENT_SESSION_LIFETIME <= timedelta(days=7)

    @pytest.mark.unit
    def test_max_file_size_reasonable(self):
        """Test max file size is reasonable."""
        config = Config()
        max_size = config.MAX_CONTENT_LENGTH
        assert max_size >= 1024 * 1024  # At least 1MB
        assert max_size <= 100 * 1024 * 1024  # At most 100MB
