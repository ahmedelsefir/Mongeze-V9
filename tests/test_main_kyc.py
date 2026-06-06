"""
Tests for the KYC (Know Your Driver) verification functions in main.py.
"""

import ast
import textwrap
from unittest.mock import MagicMock, patch
from io import BytesIO

import pytest
import requests


def _import_kyc_functions():
    with open("main.py", "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)

    target_funcs = {
        "upload_document_to_firebase",
        "fetch_driver_kyc_documents",
        "create_driver_kyc_record",
        "update_driver_verification_status",
        "save_user_settings",
    }

    func_sources = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in target_funcs:
            func_sources.append(ast.get_source_segment(source, node))

    import_block = textwrap.dedent("""\
        import base64
        import json
        import logging
        import requests
        from datetime import datetime
        logger = logging.getLogger("test_kyc")
        FIREBASE_URL = "https://test-db.firebaseio.com/"
    """)
    combined = import_block + "\n\n" + "\n\n".join(func_sources)

    ns = {}
    exec(compile(combined, "<test_kyc>", "exec"), ns)
    return ns


@pytest.fixture(scope="module")
def funcs():
    return _import_kyc_functions()


class TestUploadDocumentToFirebase:

    def test_success(self, funcs):
        file_data = MagicMock()
        file_data.read.return_value = b"fake image data"
        file_data.name = "id_card.jpg"

        mock_resp = MagicMock(ok=True)
        with patch.object(requests, "patch", return_value=mock_resp) as mock_patch:
            result = funcs["upload_document_to_firebase"]("ahmed", "national_id", file_data)
        assert result is True
        url = mock_patch.call_args[0][0]
        assert "driver_kyc/ahmed/national_id.json" in url

    def test_empty_file_data_returns_false(self, funcs):
        assert funcs["upload_document_to_firebase"]("ahmed", "national_id", None) is False

    def test_empty_file_bytes_returns_false(self, funcs):
        file_data = MagicMock()
        file_data.read.return_value = b""
        result = funcs["upload_document_to_firebase"]("ahmed", "national_id", file_data)
        assert result is False

    def test_firebase_error_returns_false(self, funcs):
        file_data = MagicMock()
        file_data.read.return_value = b"data"
        file_data.name = "license.jpg"

        mock_resp = MagicMock(ok=False, status_code=500)
        with patch.object(requests, "patch", return_value=mock_resp):
            result = funcs["upload_document_to_firebase"]("ahmed", "driving_license", file_data)
        assert result is False

    def test_sanitizes_username(self, funcs):
        file_data = MagicMock()
        file_data.read.return_value = b"data"
        file_data.name = "doc.pdf"

        mock_resp = MagicMock(ok=True)
        with patch.object(requests, "patch", return_value=mock_resp) as mock_patch:
            funcs["upload_document_to_firebase"]("ahmed mostafa", "national_id", file_data)
        url = mock_patch.call_args[0][0]
        assert "ahmed_mostafa" in url


class TestFetchDriverKycDocuments:

    def test_returns_documents(self, funcs):
        mock_resp = MagicMock(ok=True)
        mock_resp.json.return_value = {"national_id": {"verified": True}}
        with patch.object(requests, "get", return_value=mock_resp):
            result = funcs["fetch_driver_kyc_documents"]("ahmed")
        assert result["national_id"]["verified"] is True

    def test_returns_empty_on_no_data(self, funcs):
        mock_resp = MagicMock(ok=True)
        mock_resp.json.return_value = None
        with patch.object(requests, "get", return_value=mock_resp):
            assert funcs["fetch_driver_kyc_documents"]("ahmed") == {}

    def test_returns_empty_on_error(self, funcs):
        with patch.object(requests, "get", side_effect=Exception("err")):
            assert funcs["fetch_driver_kyc_documents"]("ahmed") == {}


class TestCreateDriverKycRecord:

    def test_success(self, funcs):
        mock_patch = MagicMock(ok=True)
        with patch.object(requests, "patch", return_value=mock_patch) as rp:
            result = funcs["create_driver_kyc_record"]("ahmed", "مندوب / كابتن", "sedan")
        assert result is True
        # First call is to driver_kyc metadata, second is save_user_settings
        first_call_payload = rp.call_args_list[0][1]["json"]
        assert first_call_payload["driver_name"] == "ahmed"
        assert first_call_payload["car_type"] == "sedan"
        assert first_call_payload["verification_status"] == "Pending Approval"

    def test_default_car_type(self, funcs):
        mock_patch = MagicMock(ok=True)
        with patch.object(requests, "patch", return_value=mock_patch) as rp:
            funcs["create_driver_kyc_record"]("ahmed", "مندوب / كابتن")
        first_call_payload = rp.call_args_list[0][1]["json"]
        assert first_call_payload["car_type"] == "Personal"

    def test_failure(self, funcs):
        mock_patch = MagicMock(ok=False)
        with patch.object(requests, "patch", return_value=mock_patch):
            assert funcs["create_driver_kyc_record"]("ahmed", "role") is False


class TestUpdateDriverVerificationStatus:

    def test_approve_driver(self, funcs):
        mock_resp = MagicMock(ok=True)
        with patch.object(requests, "patch", return_value=mock_resp) as rp:
            result = funcs["update_driver_verification_status"]("ahmed", "Active")
        assert result is True
        # First call is to driver_kyc metadata, second is save_user_settings
        first_call_payload = rp.call_args_list[0][1]["json"]
        assert first_call_payload["verification_status"] == "Active"
        assert "approved_at" in first_call_payload

    def test_reject_driver_with_reason(self, funcs):
        mock_resp = MagicMock(ok=True)
        with patch.object(requests, "patch", return_value=mock_resp) as rp:
            result = funcs["update_driver_verification_status"]("ahmed", "Rejected", "Invalid documents")
        assert result is True
        first_call_payload = rp.call_args_list[0][1]["json"]
        assert first_call_payload["verification_status"] == "Rejected"
        assert first_call_payload["rejection_reason"] == "Invalid documents"
        assert "rejected_at" in first_call_payload

    def test_pending_status(self, funcs):
        mock_resp = MagicMock(ok=True)
        with patch.object(requests, "patch", return_value=mock_resp) as rp:
            funcs["update_driver_verification_status"]("ahmed", "Pending Approval")
        payload = rp.call_args[1]["json"]
        assert "approved_at" not in payload
        assert "rejected_at" not in payload

    def test_failure(self, funcs):
        with patch.object(requests, "patch", side_effect=Exception("err")):
            assert funcs["update_driver_verification_status"]("ahmed", "Active") is False
