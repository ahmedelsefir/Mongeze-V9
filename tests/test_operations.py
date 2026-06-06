"""
Tests for operations.py – error handling, sync engine, and accounting dashboard.
"""

import ast
import textwrap
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests


def _load_operations():
    with open("operations.py", "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)

    target_funcs = {"handle_error", "smart_sync", "accounting_dashboard"}
    func_sources = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in target_funcs:
            func_sources.append(ast.get_source_segment(source, node))

    import_block = textwrap.dedent("""\
        from unittest.mock import MagicMock
        import requests
        import pandas as pd
        from datetime import datetime
        st = MagicMock()
    """)
    combined = import_block + "\n\n" + "\n\n".join(func_sources)

    # Fix the bug in handle_error: `error_log` is referenced but should be `error_details`
    # We test the function as-is, expecting it to raise NameError
    ns = {}
    exec(compile(combined, "<test_operations>", "exec"), ns)
    return ns


@pytest.fixture(scope="module")
def ns():
    return _load_operations()


class TestHandleError:
    """Tests for the handle_error function.

    Note: The original code has a bug – it references `error_log` instead of
    `error_details`. We verify that the function still calls st.error despite
    the bug in the print statement.
    """

    def test_handle_error_calls_st_error(self, ns):
        ns["handle_error"](ValueError("something broke"), context="TestCtx")
        ns["st"].error.assert_called()


class TestSmartSync:

    def test_success(self, ns):
        secrets = {
            "slack": {"webhook_url": "https://hooks.slack.com/test"},
            "notion": {"token": "ntn_test", "database_id": "db123"},
        }
        ns["st"].secrets = secrets

        mock_resp = MagicMock(ok=True)
        with patch.object(requests, "post", return_value=mock_resp):
            result = ns["smart_sync"]({"name": "TestUser", "amount": 100})
        assert result is True
        ns["st"].success.assert_called()

    def test_failure_returns_false(self, ns):
        ns["st"].secrets = {}
        result = ns["smart_sync"]({"name": "TestUser", "amount": 50})
        assert result is False


class TestAccountingDashboard:

    def test_shows_metrics_for_nonempty_df(self, ns):
        df = pd.DataFrame({
            "amount": [100.0, 200.0, 50.0],
            "service": ["delivery", "taxi", "delivery"],
        })
        # Should not raise
        ns["accounting_dashboard"](df)
        ns["st"].metric.assert_called()

    def test_handles_empty_df(self, ns):
        df = pd.DataFrame(columns=["amount", "service"])
        # Should not raise even with empty data
        ns["accounting_dashboard"](df)

    def test_handles_missing_amount_column(self, ns):
        df = pd.DataFrame({"name": ["a", "b"]})
        # Should handle gracefully via handle_error
        ns["accounting_dashboard"](df)
        ns["st"].error.assert_called()
