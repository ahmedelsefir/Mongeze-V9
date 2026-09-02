"""firebase_helpers.py

Helper utilities to initialize and interact safely with Firebase Realtime Database and Firestore
for the Mongeze-V9 Streamlit app.

Conventions followed:
- Secure secrets via st.secrets
- All DB operations wrapped in try/except
- Use Python logging (no print)
- Streamlit notifications are optional (notify=True) to avoid UI noise
- Compatible with firebase_admin SDK

Functions:
- initialize_firebase(notify: bool = True) -> bool
- push_realtime_data(path: str, data: dict, notify: bool = False) -> Optional[str]
- get_realtime_data(path: str) -> Optional[dict]
- update_realtime_data(path: str, data: dict) -> bool
- set_realtime_data(path: str, data: dict) -> bool
- delete_realtime_data(path: str) -> bool
- get_firestore_doc(collection: str, doc_id: str) -> Optional[dict]
- set_firestore_doc(collection: str, doc_id: str, data: dict) -> bool
- update_firestore_doc(collection: str, doc_id: str, data: dict) -> bool
- query_firestore_collection(collection: str, filters: list[tuple] | None = None, limit: int | None = None) -> list[dict]
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional, List, Tuple

import streamlit as st
import firebase_admin
from firebase_admin import credentials, db, firestore

# Configure module logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def _get_firebase_secret() -> Optional[Dict[str, Any]]:
    """Load firebase credentials dictionary from st.secrets or environment.

    Returns None if not found or invalid.
    """
    try:
        if "firebase" in st.secrets:
            # st.secrets["firebase"] can be a toml table or JSON string depending on how it's stored
            secret_obj = st.secrets["firebase"]
            # If someone put the whole JSON as a single string under a key like "serviceAccount",
            # try to parse it.
            if isinstance(secret_obj, dict):
                secret_dict = dict(secret_obj)
            else:
                try:
                    secret_dict = json.loads(secret_obj)
                except Exception:
                    logger.error("Unable to parse st.secrets['firebase'] as JSON/dict")
                    return None

            # Fix private_key line breaks when stored as a single-line string
            if "private_key" in secret_dict and isinstance(secret_dict["private_key"], str):
                secret_dict["private_key"] = secret_dict["private_key"].replace("\\n", "\n")

            return secret_dict
        else:
            logger.warning("st.secrets does not contain 'firebase' table")
            return None
    except Exception as e:
        logger.exception("Error reading firebase secrets: %s", e)
        return None


def initialize_firebase(notify: bool = True) -> bool:
    """Initialize Firebase Admin SDK for both Realtime Database and Firestore.

    Parameters:
    - notify: If True, show Streamlit success/error messages. Set to False in background tasks.

    Returns True on success, False on failure.
    """
    try:
        if firebase_admin._apps:
            # Already initialized
            logger.debug("Firebase already initialized (cached app present)")
            return True

        secret_dict = _get_firebase_secret()
        if not secret_dict:
            msg = "Firebase credentials not found in st.secrets['firebase']"
            logger.error(msg)
            if notify:
                st.error(msg)
            return False

        cred = credentials.Certificate(secret_dict)

        app_opts: Dict[str, Any] = {}
        # Allow the toml/secret to provide databaseURL
        db_url = None
        try:
            db_url = secret_dict.get("databaseURL") or st.secrets["firebase"].get("databaseURL")
        except Exception:
            db_url = None

        if db_url:
            app_opts["databaseURL"] = db_url

        firebase_admin.initialize_app(cred, app_opts)
        logger.info("Initialized Firebase Admin SDK")
        if notify:
            st.success("تم الاتصال بقاعدة البيانات بنجاح 🟢")
        return True
    except Exception as e:
        logger.exception("Failed to initialize Firebase: %s", e)
        if notify:
            st.error(f"خطأ في تهيئة قاعدة البيانات: {e}")
        return False


# ------------------------- Realtime Database helpers -------------------------

def push_realtime_data(path: str, data: Dict[str, Any], notify: bool = False) -> Optional[str]:
    """Push a new child under `path` in the Realtime Database. Returns the generated key on success."""
    try:
        if not initialize_firebase(notify=False):
            logger.error("Cannot push data: Firebase not initialized")
            if notify:
                st.error("Firebase غير مهيأ. تحقق من الإعدادات.")
            return None

        ref = db.reference(path)
        new_ref = ref.push(data)
        key = new_ref.key
        logger.info("Pushed realtime data to %s, key=%s", path, key)
        if notify:
            st.success("تم إرسال البيانات بنجاح")
        return key
    except Exception as e:
        logger.exception("Failed to push realtime data to %s: %s", path, e)
        if notify:
            st.error(f"فشل إرسال البيانات: {e}")
        return None


def get_realtime_data(path: str) -> Optional[Dict[str, Any]]:
    """Get data at `path` from Realtime Database. Returns a dict (or None)."""
    try:
        if not initialize_firebase(notify=False):
            logger.error("Cannot read data: Firebase not initialized")
            return None

        ref = db.reference(path)
        data = ref.get()
        logger.debug("Fetched realtime data from %s", path)
        return data
    except Exception as e:
        logger.exception("Failed to read realtime data from %s: %s", path, e)
        return None


def set_realtime_data(path: str, data: Dict[str, Any]) -> bool:
    """Set (overwrite) the data at `path` in Realtime Database."""
    try:
        if not initialize_firebase(notify=False):
            logger.error("Cannot set data: Firebase not initialized")
            return False

        ref = db.reference(path)
        ref.set(data)
        logger.info("Set realtime data at %s", path)
        return True
    except Exception as e:
        logger.exception("Failed to set realtime data at %s: %s", path, e)
        return False


def update_realtime_data(path: str, data: Dict[str, Any]) -> bool:
    """Update keys at `path` in Realtime Database (partial update)."""
    try:
        if not initialize_firebase(notify=False):
            logger.error("Cannot update data: Firebase not initialized")
            return False

        ref = db.reference(path)
        ref.update(data)
        logger.info("Updated realtime data at %s", path)
        return True
    except Exception as e:
        logger.exception("Failed to update realtime data at %s: %s", path, e)
        return False


def delete_realtime_data(path: str) -> bool:
    """Delete value at `path` in Realtime Database."""
    try:
        if not initialize_firebase(notify=False):
            logger.error("Cannot delete data: Firebase not initialized")
            return False

        ref = db.reference(path)
        ref.delete()
        logger.info("Deleted realtime data at %s", path)
        return True
    except Exception as e:
        logger.exception("Failed to delete realtime data at %s: %s", path, e)
        return False


# ------------------------- Firestore helpers -------------------------

def _get_firestore_client() -> Optional[firestore.Client]:
    try:
        if not initialize_firebase(notify=False):
            logger.error("Cannot get Firestore client: Firebase not initialized")
            return None
        client = firestore.client()
        return client
    except Exception as e:
        logger.exception("Failed to obtain Firestore client: %s", e)
        return None


def set_firestore_doc(collection: str, doc_id: str, data: Dict[str, Any]) -> bool:
    """Create or overwrite a Firestore document."""
    try:
        client = _get_firestore_client()
        if client is None:
            return False
        doc_ref = client.collection(collection).document(doc_id)
        doc_ref.set(data)
        logger.info("Set Firestore doc %s/%s", collection, doc_id)
        return True
    except Exception as e:
        logger.exception("Failed to set Firestore doc %s/%s: %s", collection, doc_id, e)
        return False


def get_firestore_doc(collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
    try:
        client = _get_firestore_client()
        if client is None:
            return None
        doc = client.collection(collection).document(doc_id).get()
        if not doc.exists:
            logger.debug("Firestore doc %s/%s does not exist", collection, doc_id)
            return None
        data = doc.to_dict()
        logger.debug("Fetched Firestore doc %s/%s", collection, doc_id)
        return data
    except Exception as e:
        logger.exception("Failed to get Firestore doc %s/%s: %s", collection, doc_id, e)
        return None


def update_firestore_doc(collection: str, doc_id: str, data: Dict[str, Any]) -> bool:
    try:
        client = _get_firestore_client()
        if client is None:
            return False
        doc_ref = client.collection(collection).document(doc_id)
        doc_ref.update(data)
        logger.info("Updated Firestore doc %s/%s", collection, doc_id)
        return True
    except Exception as e:
        logger.exception("Failed to update Firestore doc %s/%s: %s", collection, doc_id, e)
        return False


def query_firestore_collection(collection: str, filters: Optional[List[Tuple[str, str, Any]]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Run a simple query on a collection.

    filters: list of (field, op, value) e.g. [("status", "==", "pending")]
    """
    try:
        client = _get_firestore_client()
        if client is None:
            return []
        coll = client.collection(collection)
        q = coll
        if filters:
            for field, op, value in filters:
                q = q.where(field, op, value)
        if limit:
            q = q.limit(limit)
        docs = q.stream()
        results = []
        for d in docs:
            doc = d.to_dict()
            doc["_id"] = d.id
            results.append(doc)
        logger.debug("Queried Firestore collection %s, returned %d docs", collection, len(results))
        return results
    except Exception as e:
        logger.exception("Failed to query Firestore collection %s: %s", collection, e)
        return []


# ------------------------- Small helpers -------------------------

def safe_timestamp_str(ts) -> str:
    """Return a string representation of a timestamp-like object for safe writes."""
    try:
        return str(ts)
    except Exception:
        return ""
