"""
Shared Firebase utilities for the Mongeze platform.

Consolidates duplicated Firebase REST API calls, initialization logic,
username sanitization, and timestamp formatting used across main.py
and Streamlit page files.
"""

import json
import logging
import re
import base64

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
    url = st.secrets.get("FIREBASE_URL", "").strip()
    if not url:
        logger.error("Missing FIREBASE_URL in Streamlit secrets")
    return url


def _sanitize_firebase_path(node):
    """Sanitize Firebase node path to prevent path traversal."""
    sanitized = node.strip("/")
    sanitized = re.sub(r'[\[\]#$]', '', sanitized)
    sanitized = re.sub(r'\.{2,}', '.', sanitized)
    return sanitized


def _build_url(node):
    """Build a fully-qualified Firebase REST endpoint for *node*."""
    base = _get_firebase_url()
    sanitized = _sanitize_firebase_path(node)
    return f"{base.rstrip('/')}/{sanitized}.json"


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


def _normalize_private_key(private_key):
    """
    Normalize and sanitize a Firebase private key string.

    Handles:
      1. Double-escaped newlines (\\\\n) → single-escaped (\\n)
      2. Escaped newlines (\\n) → actual newlines (\n)
      3. Leading/trailing whitespace
      4. Malformed base64 padding (trailing '=' symbols)
      5. Multi-line string formatting

    Args:
        private_key: str — raw private key from secrets (may be escaped, multi-line, etc.)

    Returns:
        str: Cleaned, normalized private key ready for PEM parsing, or None on failure.
    """
    if not isinstance(private_key, str):
        logger.error("private_key is not a string: %s", type(private_key))
        return None

    try:
        # Step 1: Strip leading/trailing whitespace
        pk = private_key.strip()

        # Step 2: Handle double-escaped newlines first (order matters)
        # Convert "\\\\n" (two backslashes + n in string) to "\\n" (escaped newline)
        pk = pk.replace("\\\\n", "\\n")

        # Step 3: Convert escaped newlines to actual newlines
        # Convert "\\n" (backslash-n in string) to "\n" (actual newline)
        pk = pk.replace("\\n", "\n")

        # Step 4: Strip whitespace again after newline normalization
        pk = pk.strip()

        # Step 5: Validate PEM structure
        if not pk.startswith("-----BEGIN"):
            logger.error("private_key does not start with PEM header (-----BEGIN)")
            return None

        if not pk.endswith("-----END"):
            # Some keys may have trailing newlines; this is OK
            if not ("\n-----END" in pk or "\r\n-----END" in pk):
                logger.error("private_key does not end with PEM footer (-----END)")
                return None

        # Step 6: Attempt to validate base64 content (between PEM headers)
        # Extract the base64 body (between header and footer)
        lines = pk.split("\n")
        base64_lines = []
        in_body = False

        for line in lines:
            if line.startswith("-----BEGIN"):
                in_body = True
                continue
            elif line.startswith("-----END"):
                in_body = False
                continue
            elif in_body:
                stripped = line.strip()
                if stripped:
                    base64_lines.append(stripped)

        # Attempt to decode base64 to validate structure
        if base64_lines:
            base64_body = "".join(base64_lines)
            try:
                # Validate base64 by attempting decode
                # Add padding if needed (base64 padding is always 0-3 '=' chars)
                missing_padding = len(base64_body) % 4
                if missing_padding:
                    base64_body += "=" * (4 - missing_padding)
                
                base64.b64decode(base64_body, validate=True)
                logger.debug("private_key base64 validation passed")
            except Exception as b64_error:
                logger.warning("private_key base64 validation failed: %s (continuing anyway)", b64_error)
                # Don't fail here; some valid keys may have non-standard base64

        logger.info("private_key normalization successful")
        return pk

    except Exception as e:
        logger.error("Error normalizing private_key: %s", e)
        return None


def _parse_firebase_credentials():
    """Parse Firebase service-account JSON from Streamlit secrets.

    Accepts:
      - a JSON string stored in st.secrets["textkey"] (or firebase.service_account / textkey)
      - OR a dict already stored under st.secrets["firebase"]["service_account"]

    Safely handles private_key normalization to prevent PEM parsing errors.

    Returns the credentials dict or None on failure.
    """
    try:
        firebase_secret = st.secrets.get("firebase")
        raw = None

        # Prefer a structured `firebase` secret if present (service_account may be dict or JSON string)
        if firebase_secret and isinstance(firebase_secret, dict):
            raw = (
                firebase_secret.get("service_account")
                or firebase_secret.get("serviceAccount")
                or firebase_secret.get("textkey")
                or firebase_secret.get("textKey")
            )

        # Fallback to top-level textkey or legacy names
        if not raw:
            raw = st.secrets.get("textkey") or st.secrets.get("FIREBASE_SERVICE_ACCOUNT")

        if not raw:
            try:
                st.sidebar.warning(
                    "Firebase credentials not found in Streamlit secrets. Firestore/Realtime DB features are disabled."
                )
            except Exception:
                logger.warning("Firebase credentials missing; running in offline mode.")
            logger.warning("Firebase credentials missing from secrets")
            return None

        # If raw is already a dict (service account provided as structured secret), use it directly
        if isinstance(raw, dict):
            creds = raw
        else:
            raw_str = str(raw).strip()
            # Try to parse JSON first
            try:
                creds = json.loads(raw_str)
            except json.JSONDecodeError:
                # As a fallback, try ast.literal_eval to handle Python-style dict strings
                import ast

                try:
                    creds = ast.literal_eval(raw_str)
                except Exception as ex:
                    logger.error("Failed to parse Firebase credentials string: %s", ex)
                    try:
                        st.sidebar.error("Firebase credentials are malformed in Streamlit secrets.")
                    except Exception:
                        pass
                    return None

        # ========================================================
        # ENHANCED: Normalize private_key with full error handling
        # ========================================================
        pk = creds.get("private_key")
        if pk and isinstance(pk, str):
            normalized_pk = _normalize_private_key(pk)
            if normalized_pk:
                creds["private_key"] = normalized_pk
            else:
                logger.error("Failed to normalize private_key — credentials may be invalid")
                try:
                    st.sidebar.error(
                        "Firebase private key is malformed. Check your secrets configuration."
                    )
                except Exception:
                    pass
                return None

        return creds

    except Exception as e:
        logger.exception("Unexpected error while reading Firebase credentials: %s", e)
        try:
            st.sidebar.error("Unexpected error reading Firebase credentials. Check logs.")
        except Exception:
            pass
        return None


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
        if not creds:
            logger.warning("Not initialising Firebase Admin because credentials are unavailable.")
            return False
        
        try:
            cred = fb_credentials.Certificate(creds)
            firebase_admin.initialize_app(cred, {"databaseURL": _get_firebase_url()})
            logger.info("Firebase Admin SDK initialized successfully")
            return True
        except ValueError as ve:
            logger.error("Firebase certificate credential error (PEM parsing failed): %s", ve)
            try:
                st.sidebar.error(
                    "Failed to initialize Firebase: Invalid certificate. Check private key format."
                )
            except Exception:
                pass
            return False
            
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
        creds = _parse_firebase_credentials()
        if not creds:
            logger.warning("Firestore client not created because credentials are unavailable.")
            return None

        try:
            if not firebase_admin._apps:
                cred = fb_credentials.Certificate(creds)
                firebase_admin.initialize_app(cred)
            return firestore.client()
        except ValueError as ve:
            logger.error("Firestore certificate credential error (PEM parsing failed): %s", ve)
            try:
                st.sidebar.error(
                    "Failed to initialize Firestore: Invalid certificate. Check private key format."
                )
            except Exception:
                pass
            return None
            
    except Exception as e:
        logger.error("Firestore initialisation error: %s", e)
        try:
            st.sidebar.error("Failed to initialise Firestore. Check application logs.")
        except Exception:
            pass
        return None
