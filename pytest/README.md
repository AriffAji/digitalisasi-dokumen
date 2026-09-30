# SIADIK Pytest Test Suite

Complete test suite for SIADIK Flask application.

## 📊 Statistics
- **Test Files**: 8
- **Total Tests**: 180+
- **Total Lines**: 3,196
- **Test-to-Code Ratio**: 1.542:1

## 📁 Files

### Test Files
- `test_models.py` - Database model tests (527 lines)
- `test_auth.py` - Authentication route tests (382 lines)
- `test_decorators.py` - Authorization decorator tests (378 lines)
- `test_public.py` - Public route tests (356 lines)
- `test_config.py` - Configuration tests (292 lines)
- `test_app.py` - App factory tests (375 lines)
- `test_admin.py` - Admin operation tests (509 lines)

### Configuration
- `conftest.py` - Pytest fixtures & configuration (377 lines)
- `pytest.ini` - Pytest configuration
- `requirements-test.txt` - Test dependencies

### Documentation
- `TEST_SUITE.md` - Comprehensive test guide
- `TESTING_SUMMARY.md` - Quick reference & summary

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements-test.txt

# 2. Run all tests
python -m pytest -v

# 3. Run with coverage
python -m pytest --cov=./ --cov-report=html

# 4. Run specific test file
python -m pytest test_models.py -v

# 5. Run by marker
python -m pytest -m unit      # unit tests only
python -m pytest -m auth      # auth tests only
```

## ✅ Test Coverage

- **Models**: 100% (User, Kamar, SubKamar, Dokumen, ShareLink)
- **Routes**: 85%+ (Auth, Public, Admin, API)
- **Decorators**: 100% (Authorization)
- **Configuration**: 100%
- **Security**: SQL injection, CSRF, rate limiting

## 📝 Fixtures Available

30+ fixtures including:
- User: superadmin_user, admin_user, regular_user, inactive_user
- Content: kamar_aktif, sub_kamar, dokumen, multiple_dokumen
- Auth: auth_client, admin_client, superadmin_client

See `conftest.py` for full fixture list.

## 🎯 Test Markers

- `@pytest.mark.unit` - Unit tests (fast)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.auth` - Authentication tests
- `@pytest.mark.slow` - Slow tests

## ⚠️ Note

Tests require Python 3.12+ (Python 3.14 has SQLAlchemy compatibility issues).

For more details, see `TEST_SUITE.md` or `TESTING_SUMMARY.md`.
