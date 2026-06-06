"""
Tests for utils.py – the Zoho email sending utility.
"""

import smtplib
from unittest.mock import MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Import helper – load send_monjez_email without triggering Streamlit
# ---------------------------------------------------------------------------

def _load_send_monjez_email():
    import ast, textwrap

    with open("utils.py", "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "send_monjez_email":
            func_source = ast.get_source_segment(source, node)
            break
    else:
        raise RuntimeError("send_monjez_email not found")

    import_block = textwrap.dedent("""\
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from unittest.mock import MagicMock
        st = MagicMock()
    """)
    ns = {}
    exec(compile(import_block + "\n\n" + func_source, "<test_utils>", "exec"), ns)
    return ns


@pytest.fixture(scope="module")
def ns():
    return _load_send_monjez_email()


class TestSendMonjezEmail:

    def test_success(self, ns):
        ns["st"].secrets = {"zoho": {"sender_email": "test@zoho.com", "app_password": "pass123"}}

        mock_server = MagicMock()
        with patch("smtplib.SMTP_SSL", return_value=mock_server):
            result = ns["send_monjez_email"]("user@example.com", "Test Subject", "<h1>Hello</h1>")
        assert result is True
        mock_server.__enter__().login.assert_called_once_with("test@zoho.com", "pass123")
        mock_server.__enter__().sendmail.assert_called_once()

    def test_missing_secrets_returns_false(self, ns):
        ns["st"].secrets = {}
        result = ns["send_monjez_email"]("user@example.com", "Sub", "<p>body</p>")
        assert result is False

    def test_smtp_failure_returns_false(self, ns):
        ns["st"].secrets = {"zoho": {"sender_email": "test@zoho.com", "app_password": "pass123"}}

        with patch("smtplib.SMTP_SSL", side_effect=smtplib.SMTPException("failed")):
            result = ns["send_monjez_email"]("user@example.com", "Sub", "<p>body</p>")
        assert result is False
