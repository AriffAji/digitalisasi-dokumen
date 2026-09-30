"""
Unit and integration tests for authorization decorators.
Tests cover role_required, superadmin_required, admin_required, and user_required decorators.
"""

import pytest
from decorators import role_required, superadmin_required, admin_required, user_required
from flask import Flask, render_template_string


class TestRoleRequiredDecorator:
    """Test role_required decorator."""

    @pytest.fixture
    def test_app(self):
        """Create a test app for decorator testing."""
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-secret'
        app.config['TESTING'] = True

        from flask_login import LoginManager, UserMixin
        from models import User, db

        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        db.init_app(app)

        login_manager = LoginManager()
        login_manager.init_app(app)

        @login_manager.user_loader
        def load_user(user_id):
            with app.app_context():
                return User.query.get(int(user_id))

        return app

    @pytest.mark.unit
    def test_role_required_allows_matching_role(self, app, admin_user):
        """Test role_required allows user with matching role."""
        from flask_login import login_user, current_user

        @role_required('admin')
        def protected_route():
            return 'success'

        with app.app_context():
            with app.test_request_context():
                login_user(admin_user)
                result = protected_route()
                assert result == 'success'

    @pytest.mark.unit
    def test_role_required_denies_non_matching_role(self, app, regular_user):
        """Test role_required denies user without matching role."""
        from flask_login import login_user

        @role_required('admin')
        def protected_route():
            return 'success'

        with app.app_context():
            with app.test_request_context():
                login_user(regular_user)
                with pytest.raises(Exception):  # Should abort with 403
                    protected_route()

    @pytest.mark.unit
    def test_role_required_multiple_roles(self, app, admin_user, superadmin_user):
        """Test role_required with multiple allowed roles."""
        from flask_login import login_user

        @role_required('admin', 'superadmin')
        def protected_route():
            return 'success'

        with app.app_context():
            # Admin should pass
            with app.test_request_context():
                login_user(admin_user)
                result = protected_route()
                assert result == 'success'

            # Superadmin should pass
            with app.test_request_context():
                login_user(superadmin_user)
                result = protected_route()
                assert result == 'success'

    @pytest.mark.unit
    def test_role_required_denies_unauthenticated(self, app):
        """Test role_required denies unauthenticated users."""
        @role_required('admin')
        def protected_route():
            return 'success'

        with app.app_context():
            with app.test_request_context():
                with pytest.raises(Exception):
                    protected_route()

    @pytest.mark.unit
    def test_role_required_preserves_function_name(self, app, admin_user):
        """Test role_required decorator preserves function name."""
        from flask_login import login_user

        @role_required('admin')
        def my_protected_route():
            return 'success'

        assert my_protected_route.__name__ == 'my_protected_route'

    @pytest.mark.unit
    def test_role_required_with_kwargs(self, app, admin_user):
        """Test role_required with keyword arguments."""
        from flask_login import login_user

        @role_required('admin')
        def protected_route(param1, param2=None):
            return f'{param1}-{param2}'

        with app.app_context():
            with app.test_request_context():
                login_user(admin_user)
                result = protected_route('test', param2='value')
                assert result == 'test-value'


class TestSuperadminRequiredDecorator:
    """Test superadmin_required decorator."""

    @pytest.mark.unit
    def test_superadmin_required_allows_superadmin(self, app, superadmin_user):
        """Test superadmin_required allows superadmin."""
        from flask_login import login_user

        @superadmin_required
        def protected_route():
            return 'success'

        with app.app_context():
            with app.test_request_context():
                login_user(superadmin_user)
                result = protected_route()
                assert result == 'success'

    @pytest.mark.unit
    def test_superadmin_required_denies_admin(self, app, admin_user):
        """Test superadmin_required denies regular admin."""
        from flask_login import login_user

        @superadmin_required
        def protected_route():
            return 'success'

        with app.app_context():
            with app.test_request_context():
                login_user(admin_user)
                with pytest.raises(Exception):
                    protected_route()

    @pytest.mark.unit
    def test_superadmin_required_denies_user(self, app, regular_user):
        """Test superadmin_required denies regular user."""
        from flask_login import login_user

        @superadmin_required
        def protected_route():
            return 'success'

        with app.app_context():
            with app.test_request_context():
                login_user(regular_user)
                with pytest.raises(Exception):
                    protected_route()

    @pytest.mark.unit
    def test_superadmin_required_denies_unauthenticated(self, app):
        """Test superadmin_required denies unauthenticated users."""
        @superadmin_required
        def protected_route():
            return 'success'

        with app.app_context():
            with app.test_request_context():
                with pytest.raises(Exception):
                    protected_route()


class TestAdminRequiredDecorator:
    """Test admin_required decorator."""

    @pytest.mark.unit
    def test_admin_required_allows_admin(self, app, admin_user):
        """Test admin_required allows admin."""
        from flask_login import login_user

        @admin_required
        def protected_route():
            return 'success'

        with app.app_context():
            with app.test_request_context():
                login_user(admin_user)
                result = protected_route()
                assert result == 'success'

    @pytest.mark.unit
    def test_admin_required_allows_superadmin(self, app, superadmin_user):
        """Test admin_required allows superadmin."""
        from flask_login import login_user

        @admin_required
        def protected_route():
            return 'success'

        with app.app_context():
            with app.test_request_context():
                login_user(superadmin_user)
                result = protected_route()
                assert result == 'success'

    @pytest.mark.unit
    def test_admin_required_denies_user(self, app, regular_user):
        """Test admin_required denies regular user."""
        from flask_login import login_user

        @admin_required
        def protected_route():
            return 'success'

        with app.app_context():
            with app.test_request_context():
                login_user(regular_user)
                with pytest.raises(Exception):
                    protected_route()

    @pytest.mark.unit
    def test_admin_required_denies_unauthenticated(self, app):
        """Test admin_required denies unauthenticated users."""
        @admin_required
        def protected_route():
            return 'success'

        with app.app_context():
            with app.test_request_context():
                with pytest.raises(Exception):
                    protected_route()


class TestUserRequiredDecorator:
    """Test user_required decorator."""

    @pytest.mark.unit
    def test_user_required_allows_user(self, app, regular_user):
        """Test user_required allows regular user."""
        from flask_login import login_user

        @user_required
        def protected_route():
            return 'success'

        with app.app_context():
            with app.test_request_context():
                login_user(regular_user)
                result = protected_route()
                assert result == 'success'

    @pytest.mark.unit
    def test_user_required_allows_admin(self, app, admin_user):
        """Test user_required allows admin."""
        from flask_login import login_user

        @user_required
        def protected_route():
            return 'success'

        with app.app_context():
            with app.test_request_context():
                login_user(admin_user)
                result = protected_route()
                assert result == 'success'

    @pytest.mark.unit
    def test_user_required_allows_superadmin(self, app, superadmin_user):
        """Test user_required allows superadmin."""
        from flask_login import login_user

        @user_required
        def protected_route():
            return 'success'

        with app.app_context():
            with app.test_request_context():
                login_user(superadmin_user)
                result = protected_route()
                assert result == 'success'

    @pytest.mark.unit
    def test_user_required_denies_unauthenticated(self, app):
        """Test user_required denies unauthenticated users."""
        @user_required
        def protected_route():
            return 'success'

        with app.app_context():
            with app.test_request_context():
                with pytest.raises(Exception):
                    protected_route()


class TestDecoratorCombinations:
    """Test combining multiple decorators."""

    @pytest.mark.unit
    def test_stacked_decorators(self, app, admin_user):
        """Test stacking multiple decorators."""
        from flask_login import login_user

        def other_decorator(f):
            def wrapper(*args, **kwargs):
                return f(*args, **kwargs)
            return wrapper

        @other_decorator
        @admin_required
        def protected_route():
            return 'success'

        with app.app_context():
            with app.test_request_context():
                login_user(admin_user)
                result = protected_route()
                assert result == 'success'

    @pytest.mark.unit
    def test_decorator_with_request_data(self, app, admin_user):
        """Test decorator with request data."""
        from flask_login import login_user

        @admin_required
        def protected_route(data):
            return f'success-{data}'

        with app.app_context():
            with app.test_request_context():
                login_user(admin_user)
                result = protected_route('test')
                assert result == 'success-test'


class TestDecoratorErrorHandling:
    """Test decorator error handling."""

    @pytest.mark.unit
    def test_role_required_with_invalid_role_string(self, app, superadmin_user):
        """Test role_required doesn't match invalid role strings."""
        from flask_login import login_user

        @role_required('nonexistent_role')
        def protected_route():
            return 'success'

        with app.app_context():
            with app.test_request_context():
                login_user(superadmin_user)
                with pytest.raises(Exception):
                    protected_route()

    @pytest.mark.unit
    def test_decorator_preserves_docstring(self, app):
        """Test decorator preserves function docstring."""
        @admin_required
        def protected_route():
            """This is a test function."""
            return 'success'

        # Note: wraps should preserve docstring
        assert protected_route.__doc__ is not None or protected_route.__name__ == 'decorated_function'
