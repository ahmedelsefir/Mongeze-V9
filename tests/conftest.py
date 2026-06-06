"""
Shared fixtures for Mongeze-V9 test suite.

We mock heavy external dependencies (streamlit, firebase_admin) at import time
so that the application modules can be imported in a plain pytest environment
without a running Streamlit server or Firebase credentials.
"""

import sys
import types
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Streamlit stub – lightweight mock so `import streamlit as st` works
# ---------------------------------------------------------------------------

class _SecretsMock(dict):
    """A dict subclass that also supports attribute-style access like st.secrets."""
    pass


def _build_streamlit_stub():
    """Return a module-like object that satisfies common st.* usage."""
    st = MagicMock()
    st.secrets = _SecretsMock()
    st.session_state = {}
    return st


@pytest.fixture(autouse=True)
def _patch_streamlit(monkeypatch):
    """Ensure every test gets a fresh streamlit stub."""
    stub = _build_streamlit_stub()
    monkeypatch.setitem(sys.modules, "streamlit", stub)
    monkeypatch.setitem(sys.modules, "streamlit_js_eval", MagicMock())
    yield stub


@pytest.fixture(autouse=True)
def _patch_firebase(monkeypatch):
    """Stub firebase_admin so imports don't need real credentials."""
    fb = types.ModuleType("firebase_admin")
    fb._apps = {}
    fb.initialize_app = MagicMock()
    fb.credentials = MagicMock()
    fb.auth = MagicMock()
    fb.firestore = MagicMock()
    monkeypatch.setitem(sys.modules, "firebase_admin", fb)
    monkeypatch.setitem(sys.modules, "firebase_admin.credentials", fb.credentials)
    monkeypatch.setitem(sys.modules, "firebase_admin.auth", fb.auth)
    monkeypatch.setitem(sys.modules, "firebase_admin.firestore", fb.firestore)
    yield fb
