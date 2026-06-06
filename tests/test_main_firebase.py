"""
Tests for the Firebase helper functions in main.py.

These functions wrap HTTP calls to the Firebase REST API.
We mock `requests` to verify correct URL construction, payload handling,
and error-path behavior.
"""

import ast
import textwrap
from unittest.mock import MagicMock, patch, call

import pytest
import requests


# ---------------------------------------------------------------------------
# Extract the Firebase helper functions from main.py
# ---------------------------------------------------------------------------

def _import_firebase_helpers():
    with open("main.py", "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)

    target_funcs = {
        "send_to_firebase",
        "update_firebase_node",
        "fetch_from_firebase",
        "fetch_user_settings",
        "save_user_settings",
        "fetch_driver_account",
        "save_driver_account",
        "delete_user_from_firebase",
    }

    func_sources = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in target_funcs:
            func_sources.append(ast.get_source_segment(source, node))

    import_block = textwrap.dedent("""\
        import json
        import logging
        import requests
        from datetime import datetime
        logger = logging.getLogger("test_firebase_helpers")
        FIREBASE_URL = "https://test-db.firebaseio.com/"
    """)
    combined = import_block + "\n\n" + "\n\n".join(func_sources)

    ns = {}
    exec(compile(combined, "<test_firebase_helpers>", "exec"), ns)
    return ns


@pytest.fixture(scope="module")
def funcs():
    return _import_firebase_helpers()


# ===================================================================
# send_to_firebase
# ===================================================================

class TestSendToFirebase:

    def test_success(self, funcs):
        mock_resp = MagicMock()
        mock_resp.ok = True
        with patch.object(requests, "post", return_value=mock_resp) as mock_post:
            result = funcs["send_to_firebase"]("orders", {"key": "value"})
        assert result is True
        mock_post.assert_called_once()
        url = mock_post.call_args[0][0]
        assert url == "https://test-db.firebaseio.com/orders.json"

    def test_failure_response(self, funcs):
        mock_resp = MagicMock()
        mock_resp.ok = False
        with patch.object(requests, "post", return_value=mock_resp):
            assert funcs["send_to_firebase"]("orders", {}) is False

    def test_timeout_returns_false(self, funcs):
        with patch.object(requests, "post", side_effect=requests.exceptions.Timeout):
            assert funcs["send_to_firebase"]("orders", {}) is False

    def test_connection_error_returns_false(self, funcs):
        with patch.object(requests, "post", side_effect=requests.exceptions.ConnectionError):
            assert funcs["send_to_firebase"]("orders", {}) is False

    def test_strips_slashes_from_node(self, funcs):
        mock_resp = MagicMock(ok=True)
        with patch.object(requests, "post", return_value=mock_resp) as mock_post:
            funcs["send_to_firebase"]("/orders/", {"k": "v"})
        url = mock_post.call_args[0][0]
        assert url == "https://test-db.firebaseio.com/orders.json"


# ===================================================================
# update_firebase_node
# ===================================================================

class TestUpdateFirebaseNode:

    def test_success(self, funcs):
        mock_resp = MagicMock(ok=True)
        with patch.object(requests, "patch", return_value=mock_resp) as mock_patch:
            result = funcs["update_firebase_node"]("orders/123", {"status": "done"})
        assert result is True
        url = mock_patch.call_args[0][0]
        assert "orders/123.json" in url

    def test_failure(self, funcs):
        mock_resp = MagicMock(ok=False)
        with patch.object(requests, "patch", return_value=mock_resp):
            assert funcs["update_firebase_node"]("orders/123", {}) is False

    def test_timeout(self, funcs):
        with patch.object(requests, "patch", side_effect=requests.exceptions.Timeout):
            assert funcs["update_firebase_node"]("orders/123", {}) is False


# ===================================================================
# fetch_from_firebase
# ===================================================================

class TestFetchFromFirebase:

    def test_returns_list_of_items(self, funcs):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "abc": {"order_id": "O1", "status": "pending"},
            "def": {"order_id": "O2", "status": "done"},
        }
        with patch.object(requests, "get", return_value=mock_resp):
            result = funcs["fetch_from_firebase"]("orders")
        assert len(result) == 2
        assert result[0]["db_id"] in ("abc", "def")

    def test_returns_empty_list_on_no_data(self, funcs):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = None
        with patch.object(requests, "get", return_value=mock_resp):
            assert funcs["fetch_from_firebase"]("orders") == []

    def test_returns_empty_list_on_failed_response(self, funcs):
        mock_resp = MagicMock()
        mock_resp.ok = False
        with patch.object(requests, "get", return_value=mock_resp):
            assert funcs["fetch_from_firebase"]("orders") == []

    def test_returns_empty_list_on_timeout(self, funcs):
        with patch.object(requests, "get", side_effect=requests.exceptions.Timeout):
            assert funcs["fetch_from_firebase"]("orders") == []

    def test_skips_non_dict_values(self, funcs):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "abc": {"order_id": "O1"},
            "xyz": "not a dict",
        }
        with patch.object(requests, "get", return_value=mock_resp):
            result = funcs["fetch_from_firebase"]("orders")
        assert len(result) == 1

    def test_json_decode_error_returns_empty(self, funcs):
        import json as _json
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.side_effect = _json.JSONDecodeError("err", "", 0)
        with patch.object(requests, "get", return_value=mock_resp):
            assert funcs["fetch_from_firebase"]("orders") == []


# ===================================================================
# fetch_user_settings
# ===================================================================

class TestFetchUserSettings:

    def test_returns_settings_dict(self, funcs):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"language": "ar", "theme": "dark"}
        with patch.object(requests, "get", return_value=mock_resp):
            result = funcs["fetch_user_settings"]("أحمد مصطفى")
        assert result == {"language": "ar", "theme": "dark"}

    def test_returns_empty_on_no_data(self, funcs):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = None
        with patch.object(requests, "get", return_value=mock_resp):
            assert funcs["fetch_user_settings"]("user1") == {}

    def test_returns_empty_on_error(self, funcs):
        with patch.object(requests, "get", side_effect=Exception("network")):
            assert funcs["fetch_user_settings"]("user1") == {}

    def test_url_encodes_spaces(self, funcs):
        mock_resp = MagicMock(ok=True)
        mock_resp.json.return_value = {}
        with patch.object(requests, "get", return_value=mock_resp) as mock_get:
            funcs["fetch_user_settings"]("ahmed mostafa")
        url = mock_get.call_args[0][0]
        assert "ahmed_mostafa" in url


# ===================================================================
# save_user_settings
# ===================================================================

class TestSaveUserSettings:

    def test_success(self, funcs):
        mock_resp = MagicMock(ok=True)
        with patch.object(requests, "patch", return_value=mock_resp):
            assert funcs["save_user_settings"]("user1", {"theme": "dark"}) is True

    def test_sanitizes_username(self, funcs):
        mock_resp = MagicMock(ok=True)
        with patch.object(requests, "patch", return_value=mock_resp) as mock_patch:
            funcs["save_user_settings"]("ahmed.mostafa user", {"k": "v"})
        url = mock_patch.call_args[0][0]
        assert "ahmed_mostafa_user" in url

    def test_failure(self, funcs):
        with patch.object(requests, "patch", side_effect=Exception("err")):
            assert funcs["save_user_settings"]("user1", {}) is False


# ===================================================================
# fetch_driver_account
# ===================================================================

class TestFetchDriverAccount:

    def test_returns_account_data(self, funcs):
        mock_resp = MagicMock(ok=True)
        mock_resp.json.return_value = {"payment_method": "instapay", "account_number": "123"}
        with patch.object(requests, "get", return_value=mock_resp):
            result = funcs["fetch_driver_account"]("driver1")
        assert result["payment_method"] == "instapay"

    def test_returns_defaults_on_no_data(self, funcs):
        mock_resp = MagicMock(ok=True)
        mock_resp.json.return_value = None
        with patch.object(requests, "get", return_value=mock_resp):
            result = funcs["fetch_driver_account"]("driver1")
        assert result["payment_method"] is None
        assert result["account_number"] is None

    def test_returns_defaults_on_error(self, funcs):
        with patch.object(requests, "get", side_effect=Exception("err")):
            result = funcs["fetch_driver_account"]("driver1")
        assert result["payment_method"] is None


# ===================================================================
# save_driver_account
# ===================================================================

class TestSaveDriverAccount:

    def test_success_adds_timestamp(self, funcs):
        mock_resp = MagicMock(ok=True)
        data = {"payment_method": "instapay"}
        with patch.object(requests, "patch", return_value=mock_resp) as mock_patch:
            assert funcs["save_driver_account"]("driver1", data) is True
        payload = mock_patch.call_args[1]["json"]
        assert "last_updated" in payload

    def test_failure(self, funcs):
        with patch.object(requests, "patch", side_effect=Exception("err")):
            assert funcs["save_driver_account"]("driver1", {}) is False


# ===================================================================
# delete_user_from_firebase
# ===================================================================

class TestDeleteUserFromFirebase:

    def test_success_cascading_delete(self, funcs):
        mock_delete = MagicMock(ok=True)
        mock_get = MagicMock(ok=True)
        mock_get.json.return_value = {"chat_ahmed_room": {"msg": "hi"}}

        with patch.object(requests, "delete", return_value=mock_delete) as del_mock, \
             patch.object(requests, "get", return_value=mock_get):
            result = funcs["delete_user_from_firebase"]("ahmed")
        assert result is True
        # Should have called delete for users, drivers_accounts, and any matching chats
        assert del_mock.call_count >= 2

    def test_returns_true_even_if_no_chats(self, funcs):
        mock_delete = MagicMock(ok=True)
        mock_get = MagicMock(ok=True)
        mock_get.json.return_value = None

        with patch.object(requests, "delete", return_value=mock_delete), \
             patch.object(requests, "get", return_value=mock_get):
            assert funcs["delete_user_from_firebase"]("user1") is True

    def test_returns_false_on_error(self, funcs):
        with patch.object(requests, "delete", side_effect=Exception("err")), \
             patch.object(requests, "get", side_effect=Exception("err")):
            assert funcs["delete_user_from_firebase"]("user1") is False
