"""Existing feature tests run with an explicitly authenticated admin."""

from app.core.admin_auth import AuthenticatedAdmin, get_current_admin


def enable_admin_for_unit_tests(app) -> None:
    app.dependency_overrides[get_current_admin] = lambda: AuthenticatedAdmin(
        id=1, username="test-admin")
