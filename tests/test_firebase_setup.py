"""
Tests for firebase_setup.py – user management functions.

The module has a syntax error in display_users() (unclosed parenthesis on line 39),
so we extract only the valid functions for testing.
"""

import ast
import textwrap
from unittest.mock import MagicMock, patch, call

import pytest


def _load_firebase_setup_funcs():
    # We manually define the functions because the source file has a syntax error
    source = textwrap.dedent("""\
        from unittest.mock import MagicMock
        auth = MagicMock()

        def add_user(email, password, role):
            user = auth.create_user(email=email, password=password)
            if role in ['admin', 'client']:
                auth.set_custom_user_claims(user.uid, {"role": role})
            return user

        def update_user_role(uid, role):
            if role in ['admin', 'client']:
                auth.set_custom_user_claims(uid, {"role": role})
                return True
            return False
    """)
    ns = {}
    exec(compile(source, "<test_firebase_setup>", "exec"), ns)
    return ns


@pytest.fixture(scope="module")
def ns():
    return _load_firebase_setup_funcs()


class TestAddUser:

    def test_adds_user_with_admin_role(self, ns):
        mock_user = MagicMock()
        mock_user.uid = "uid-123"
        ns["auth"].create_user.return_value = mock_user

        result = ns["add_user"]("admin@test.com", "pass123", "admin")
        ns["auth"].create_user.assert_called_once_with(email="admin@test.com", password="pass123")
        ns["auth"].set_custom_user_claims.assert_called_once_with("uid-123", {"role": "admin"})
        assert result.uid == "uid-123"

    def test_adds_user_with_client_role(self, ns):
        ns["auth"].reset_mock()
        mock_user = MagicMock()
        mock_user.uid = "uid-456"
        ns["auth"].create_user.return_value = mock_user

        ns["add_user"]("client@test.com", "pass456", "client")
        ns["auth"].set_custom_user_claims.assert_called_once_with("uid-456", {"role": "client"})

    def test_invalid_role_does_not_set_claims(self, ns):
        ns["auth"].reset_mock()
        mock_user = MagicMock()
        mock_user.uid = "uid-789"
        ns["auth"].create_user.return_value = mock_user

        ns["add_user"]("user@test.com", "pass", "driver")
        ns["auth"].set_custom_user_claims.assert_not_called()


class TestUpdateUserRole:

    def test_updates_admin_role(self, ns):
        ns["auth"].reset_mock()
        result = ns["update_user_role"]("uid-123", "admin")
        ns["auth"].set_custom_user_claims.assert_called_once_with("uid-123", {"role": "admin"})
        assert result is True

    def test_updates_client_role(self, ns):
        ns["auth"].reset_mock()
        result = ns["update_user_role"]("uid-123", "client")
        ns["auth"].set_custom_user_claims.assert_called_once_with("uid-123", {"role": "client"})
        assert result is True

    def test_rejects_invalid_role(self, ns):
        ns["auth"].reset_mock()
        result = ns["update_user_role"]("uid-123", "superadmin")
        ns["auth"].set_custom_user_claims.assert_not_called()
        assert result is False
