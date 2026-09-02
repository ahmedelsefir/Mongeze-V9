import streamlit as st
import logging
from datetime import datetime
import re
from functools import wraps
import time
import random
from typing import Any, Dict, Optional, Callable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _retry(retries: int = 3, backoff_factor: float = 0.4, allowed_exceptions: tuple = (Exception,)):
    """Decorator to retry a function with exponential backoff.

    Usage:
      @_retry(retries=3, backoff_factor=0.5)
      def fn(...):
          ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < retries:
                try:
                    return func(*args, **kwargs)
                except allowed_exceptions as e:
                    attempt += 1
                    if attempt >= retries:
                        logger.error("Function %s failed after %d attempts: %s", func.__name__, retries, e)
                        raise
                    sleep_time = backoff_factor * (2 ** (attempt - 1)) + random.uniform(0, backoff_factor)
                    logger.warning("Function %s attempt %d/%d failed: %s. Retrying in %.2f seconds...", func.__name__, attempt, retries, e, sleep_time)
                    time.sleep(sleep_time)
        return wrapper
    return decorator


@_retry(retries=3, backoff_factor=0.5)
def initialize_firebase(notify: bool = True) -> bool:
    """Initialize Firebase Admin SDK lazily and safely.

    Reads credentials from st.secrets['firebase'] and handles private_key newline normalization.
    """
    try:
        import firebase_admin
        from firebase_admin import credentials

        if firebase_admin._apps:
            logger.debug("Firebase already initialized")
            return True

        if "firebase" in st.secrets:
            secret_dict = dict(st.secrets["firebase"])
            if "private_key" in secret_dict and isinstance(secret_dict["private_key"], str):
                secret_dict["private_key"] = secret_dict["private_key"].replace("\\n", "\n")

            cred = credentials.Certificate(secret_dict)

            app_opts: Dict[str, Any] = {}
            db_url = secret_dict.get("databaseURL") or st.secrets["firebase"].get("databaseURL")
            if db_url:
                app_opts["databaseURL"] = db_url

            # initialize_app may fail transiently; let decorator handle retries
            firebase_admin.initialize_app(cred, app_opts)
            logger.info("Firebase Admin initialized")
            if notify:
                st.success("تم الاتصال بقاعدة البيانات بنجاح 🟢")
            return True
        else:
            msg = "Firebase credentials not found in Streamlit secrets."
            logger.warning(msg)
            if notify:
                st.error(msg)
            return False

    except Exception as e:
        logger.exception("Failed to initialize Firebase: %s", e)
        if notify:
            st.error(f"فشل الاتصال بقاعدة البيانات: {e}")
        return False


def init_firebase(notify: bool = True) -> bool:
    """Compatibility wrapper for initialize_firebase"""
    return initialize_firebase(notify=notify)


def init_firestore(notify: bool = True):
    """Compatibility wrapper to initialize and return a Firestore client."""
    initialize_firebase(notify=notify)
    try:
        from firebase_admin import firestore
        return firestore.client()
    except Exception as e:
        logger.error(f"Init Firestore Error: {e}")
        if notify:
            st.error(f"فشل تهيئة Firestore: {e}")
        return None


# ---------------- Realtime Database helpers ----------------

@_retry(retries=4, backoff_factor=0.5)
def push_realtime_data(path: str, data: Dict[str, Any], notify: bool = False) -> Optional[str]:
    initialize_firebase(notify=False)
    try:
        from firebase_admin import db
        ref = db.reference(path)
        new_ref = ref.push(data)
        return new_ref.key
    except Exception as e:
        logger.exception("Realtime Push Error: %s", e)
        if notify:
            st.error(f"فشل الإرسال: {e}")
        raise


@_retry(retries=3, backoff_factor=0.4)
def get_realtime_data(path: str, notify: bool = False) -> Optional[Dict[str, Any]]:
    initialize_firebase(notify=False)
    try:
        from firebase_admin import db
        ref = db.reference(path)
        return ref.get()
    except Exception as e:
        logger.exception("Realtime Get Error: %s", e)
        if notify:
            st.error(f"فشل جلب البيانات: {e}")
        raise


@_retry(retries=3, backoff_factor=0.4)
def update_realtime_data(path: str, data: Dict[str, Any], notify: bool = False) -> bool:
    initialize_firebase(notify=False)
    try:
        from firebase_admin import db
        ref = db.reference(path)
        ref.update(data)
        return True
    except Exception as e:
        logger.exception("Realtime Update Error: %s", e)
        if notify:
            st.error(f"فشل التحديث: {e}")
        raise


def update_firebase_node(path: str, data: Dict[str, Any], notify: bool = False) -> bool:
    """Compatibility alias used by pages like 2_Taxi_Driver.py"""
    try:
        return update_realtime_data(path, data, notify=notify)
    except Exception:
        return False


@_retry(retries=3, backoff_factor=0.4)
def delete_firebase_node(path: str, notify: bool = False) -> bool:
    initialize_firebase(notify=False)
    try:
        from firebase_admin import db
        ref = db.reference(path)
        ref.delete()
        return True
    except Exception as e:
        logger.exception("Realtime Delete Error: %s", e)
        if notify:
            st.error(f"فشل الحذف: {e}")
        raise


def fetch_from_firebase(path: str, notify: bool = False) -> Optional[Dict[str, Any]]:
    try:
        return get_realtime_data(path, notify=notify)
    except Exception:
        return None


def fetch_firebase_dict(path: str, notify: bool = False) -> Dict[str, Any]:
    try:
        res = get_realtime_data(path, notify=notify)
        if isinstance(res, dict):
            return res
        return {}
    except Exception:
        return {}


# ---------------- Firestore helpers ----------------

@_retry(retries=3, backoff_factor=0.4)
def set_firestore_doc(collection: str, doc_id: str, data: Dict[str, Any], notify: bool = False) -> bool:
    initialize_firebase(notify=False)
    try:
        from firebase_admin import firestore
        client = firestore.client()
        client.collection(collection).document(doc_id).set(data)
        return True
    except Exception as e:
        logger.exception("Firestore Set Error: %s", e)
        if notify:
            st.error(f"فشل حفظ المستند: {e}")
        raise


@_retry(retries=3, backoff_factor=0.4)
def get_firestore_doc(collection: str, doc_id: str, notify: bool = False) -> Optional[Dict[str, Any]]:
    initialize_firebase(notify=False)
    try:
        from firebase_admin import firestore
        client = firestore.client()
        doc = client.collection(collection).document(doc_id).get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        logger.exception("Firestore Get Error: %s", e)
        if notify:
            st.error(f"فشل جلب المستند: {e}")
        raise


# ---------------- Utility helpers ----------------

def sanitize_username(username: str) -> str:
    """Clean username to be safe for Firebase paths (keeps Arabic letters, numbers, underscore)."""
    if not username:
        return ""
    return re.sub(r"[^a-zA-Z0-9_\u0600-\u06FF]", "_", str(username)).strip()


def get_current_timestamp() -> str:
    """Return a consistent timestamp string for records."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
