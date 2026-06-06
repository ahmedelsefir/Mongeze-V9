"""
Tests for firebase_setup.py – user management functions.

Now that the syntax error in display_users() is fixed, we can test all functions.
"""

import ast
import textwrap
from unittest.mock import MagicMock, patch, call

import pytest


def _load_firebase_setup_funcs():
    with open("firebase_setup.py", "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)

    target_funcs = {"add_user", "update_user_role", "display_users"}
    func_sources = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in target_funcs:
            func_sources.append(ast.get_source_segment(source, node))

    import_block = textwrap.dedent("""\
        from unittest.mock import MagicMock
        auth = MagicMock()
    """)
    combined = import_block + "\n\n" + "\n\n".join(func_sources)

    ns = {}
    exec(compile(combined, "<test_firebase_setup>", "exec"), ns)
    return ns


@pytest.fixture(scope="module")
def ns():
    return _load_firebase_setup_funcs()


class TestAddUser:

    def test_adds_user_with_admin_role(self, ns):
        mock_user = MagicMock()
        mock_user.uid = "uid-123"
        ns["auth"].create_user.return_value = mock_user

        ns["add_user"]("admin@test.com", "pass123", "admin")
        ns["auth"].create_user.assert_called_once_with(email="admin@test.com", password="pass123")
        ns["auth"].set_custom_user_claims.assert_called_once_with("uid-123", {"role": "admin"})

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

    def test_updates_client_role(self, ns):
        ns["auth"].reset_mock()
        result = ns["update_user_role"]("uid-123", "client")
        ns["auth"].set_custom_user_claims.assert_called_once_with("uid-123", {"role": "client"})

    def test_rejects_invalid_role(self, ns):
        ns["auth"].reset_mock()
        ns["update_user_role"]("uid-123", "superadmin")
        ns["auth"].set_custom_user_claims.assert_not_called()


class TestDisplayUsers:

    def test_lists_users(self, ns, capsys):
        mock_user1 = MagicMock()
        mock_user1.email = "admin@test.com"
        mock_user1.uid = "uid-111"
        mock_user2 = MagicMock()
        mock_user2.email = "client@test.com"
        mock_user2.uid = "uid-222"

        mock_page = MagicMock()
        mock_page.users = [mock_user1, mock_user2]
        ns["auth"].list_users.return_value = mock_page

        ns["display_users"]()
        captured = capsys.readouterr()
        assert "admin@test.com" in captured.out
        assert "uid-111" in captured.out
        assert "client@test.com" in captured.out
        assert "uid-222" in captured.out

    def test_empty_user_list(self, ns, capsys):
        mock_page = MagicMock()
        mock_page.users = []
        ns["auth"].list_users.return_value = mock_page

        ns["display_users"]()
        captured = capsys.readouterr()
        assert captured.out == ""
