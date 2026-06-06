"""
Shared Firebase utilities for the Mongeze platform.

Consolidates duplicated Firebase REST API calls, initialization logic,
username sanitization, and timestamp formatting used across main.py
and Streamlit page files.
"""

import json
import logging

import firebase_admin
import requests
import streamlit as st
from datetime import datetime
from firebase_admin import credentials as fb_credentials

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------

def get_current_timestamp():
    """Return the current datetime as a formatted string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def sanitize_username(username):
    """Sanitize a username for use as a Firebase node key."""
    return username.replace(" ", "_").replace(".", "_")


# ---------------------------------------------------------------------------
# Firebase Realtime Database – REST helpers
# ---------------------------------------------------------------------------

def _get_firebase_url():
    """Read the Firebase Realtime Database URL from Streamlit secrets."""
    return st.secrets.get(
        "FIREBASE_URL",
        "https://gen-lang-client-03099029-937be-default-rtdb.firebaseio.com/",
    ).strip()


def _build_url(node):
    """Build a fully-qualified Firebase REST endpoint for *node*."""
    base = _get_firebase_url()
    return f"{base.rstrip('/')}/{node.strip('/')}.json"


def firebase_request(method, node, data=None, timeout=10):
    """
    Execute a Firebase REST API request with standardised error handling.

    Args:
        method: HTTP verb as a lowercase string ('get', 'post', 'patch', 'delete').
        node: Firebase node path (e.g. ``"orders"``).
        data: Optional JSON-serialisable payload for POST / PATCH.
        timeout: Request timeout in seconds.

    Returns:
        A :class:`requests.Response` on success, or ``None`` on failure.
    """
    try:
        url = _build_url(node)
        request_fn = getattr(requests, method)
        if data is not None:
            response = request_fn(url, json=data, timeout=timeout)
        else:
            response = request_fn(url, timeout=timeout)
        return response
    except requests.exceptions.Timeout:
        logger.error("Timeout during %s to Firebase node: %s", method.upper(), node)
        return None
    except requests.exceptions.RequestException as e:
        logger.error("Request error during %s to Firebase: %s", method.upper(), e)
        return None
    except Exception as e:
        logger.error("Unexpected error during %s to Firebase: %s", method.upper(), e)
        return None


def send_to_firebase(node, data):
    """POST *data* to a Firebase node. Returns ``True`` on success."""
    response = firebase_request("post", node, data)
    return response is not None and response.ok


def update_firebase_node(node, data):
    """PATCH *data* onto an existing Firebase node. Returns ``True`` on success."""
    response = firebase_request("patch", node, data)
    return response is not None and response.ok


def fetch_from_firebase(node):
    """
    GET all children of a Firebase node.

    Returns a list of dicts, each augmented with a ``"db_id"`` key holding
    the Firebase key.  Returns ``[]`` on any error.
    """
    response = firebase_request("get", node)
    if response is None or not response.ok:
        return []
    try:
        data = response.json()
        if data and isinstance(data, dict):
            items = []
            for k, v in data.items():
                try:
                    if isinstance(v, dict):
                        item = {"db_id": k}
                        item.update(v)
                        items.append(item)
                except Exception as item_error:
                    logger.warning("Error processing item %s: %s", k, item_error)
                    continue
            return items
        return []
    except json.JSONDecodeError as e:
        logger.error("JSON decode error from Firebase: %s", e)
        return []


def fetch_firebase_dict(node):
    """GET a single Firebase node and return the raw dict (or ``{}``)."""
    response = firebase_request("get", node)
    if response is None or not response.ok:
        return {}
    try:
        data = response.json()
        return data if data else {}
    except Exception as e:
        logger.error("Error fetching dict from Firebase node %s: %s", node, e)
        return {}


def delete_firebase_node(node):
    """DELETE a Firebase node. Returns ``True`` on success."""
    response = firebase_request("delete", node)
    return response is not None and response.ok


# ---------------------------------------------------------------------------
# Firebase Admin SDK initialisation
# ---------------------------------------------------------------------------

def _parse_firebase_credentials():
    """Parse Firebase service-account JSON from Streamlit secrets."""
    raw = st.secrets["textkey"].strip()
    creds = json.loads(raw)
    if "private_key" in creds:
        creds["private_key"] = (
            creds["private_key"]
            .replace("\\\\n", "\n")
            .replace("\\n", "\n")
            .strip()
        )
    return creds


def init_firebase_admin():
    """
    Initialise the Firebase Admin SDK (Realtime Database mode).

    Safe to call multiple times – skips if already initialised.
    Returns ``True`` on success, ``False`` on failure.
    """
    try:
        if firebase_admin._apps:
            return True
        creds = _parse_firebase_credentials()
        cred = fb_credentials.Certificate(creds)
        firebase_admin.initialize_app(cred, {"databaseURL": _get_firebase_url()})
        return True
    except Exception as e:
        logger.error("Firebase Admin initialisation error: %s", e)
        return False


def init_firestore():
    """
    Initialise Firebase and return a Firestore client.

    Used by Streamlit page files that talk to Firestore rather than the
    Realtime Database.  Returns ``None`` on failure.
    """
    from firebase_admin import firestore

    try:
        if not firebase_admin._apps:
            creds = _parse_firebase_credentials()
            cred = fb_credentials.Certificate(creds)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        logger.error("Firestore initialisation error: %s", e)
        return None
