import streamlit as st
import logging
import time
import random
from typing import Any, Dict, Optional, Callable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _retry(func: Callable[[], Any], retries: int = 3, backoff_factor: float = 0.5, allowed_exceptions: tuple = (Exception,)) -> Any:
    """Run func with retries and exponential backoff.

    Args:
        func: zero-argument callable to execute.
        retries: total attempts (including first).
        backoff_factor: base wait time in seconds; wait = backoff_factor * 2**(attempt-1) + jitter
        allowed_exceptions: tuple of exception classes to catch and retry.

    Raises the last exception if all attempts fail.
    Returns the callable's result on success.
    """
    attempt = 0
    while attempt < retries:
        try:
            return func()
        except allowed_exceptions as e:
            attempt += 1
            if attempt >= retries:
                logger.exception("Operation failed after %d attempts: %s", attempt, e)
                raise
            sleep_time = backoff_factor * (2 ** (attempt - 1)) + random.uniform(0, backoff_factor)
            logger.warning("Operation attempt %d/%d failed: %s. Retrying in %.2f seconds...", attempt, retries, e, sleep_time)
            time.sleep(sleep_time)


def initialize_firebase(notify: bool = True) -> bool:
    """Lazy initialize Firebase Admin SDK when needed.

    This function does not run at import time and reads st.secrets only when called.
    Returns True on successful initialization or when already initialized, False otherwise.
    """
    try:
        # Local import to avoid ImportError at module import time when package isn't installed
        import firebase_admin
        from firebase_admin import credentials

        if firebase_admin._apps:
            logger.debug("Firebase already initialized")
            return True

        if "firebase" in st.secrets:
            secret_dict = dict(st.secrets["firebase"])
            if "private_key" in secret_dict and isinstance(secret_dict["private_key"], str):
                # Convert escaped newlines to real newlines
                secret_dict["private_key"] = secret_dict["private_key"].replace("\\n", "\n")

            cred = credentials.Certificate(secret_dict)

            app_opts: Dict[str, Any] = {}
            db_url = secret_dict.get("databaseURL") or st.secrets["firebase"].get("databaseURL")
            if db_url:
                app_opts["databaseURL"] = db_url

            # initialize_app can fail for transient reasons; wrap with retry
            def _init():
                firebase_admin.initialize_app(cred, app_opts)
                return True

            try:
                return _retry(_init, retries=3, backoff_factor=0.5)
            except Exception as e:
                logger.exception("Failed to initialize Firebase after retries: %s", e)
                if notify:
                    st.error(f"فشل الاتصال بقاعدة البيانات: {e}")
                return False
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


# ---------------- Realtime Database helpers (lazy imports + retry) ----------------


def push_realtime_data(path: str, data: Dict[str, Any], notify: bool = False) -> Optional[str]:
    """Push data to Realtime Database and return generated key or None."""
    try:
        if not initialize_firebase(notify=False):
            if notify:
                st.error("Firebase غير مهيأ. تحقق من الإعدادات.")
            return None

        from firebase_admin import db

        def _op():
            ref = db.reference(path)
            new_ref = ref.push(data)
            return new_ref.key

        key = _retry(_op, retries=4, backoff_factor=0.5)
        logger.info("Pushed data to %s, key=%s", path, key)
        if notify:
            st.success("تم إرسال البيانات بنجاح")
        return key
    except Exception as e:
        logger.exception("Realtime Push Error: %s", e)
        if notify:
            st.error(f"فشل الإرسال: {e}")
        return None


def get_realtime_data(path: str, notify: bool = False) -> Optional[Dict[str, Any]]:
    """Get data from Realtime Database path."""
    try:
        if not initialize_firebase(notify=False):
            return None
        from firebase_admin import db

        def _op():
            ref = db.reference(path)
            return ref.get()

        return _retry(_op, retries=3, backoff_factor=0.4)
    except Exception as e:
        logger.exception("Realtime Get Error: %s", e)
        if notify:
            st.error(f"فشل جلب البيانات: {e}")
        return None


def update_realtime_data(path: str, data: Dict[str, Any], notify: bool = False) -> bool:
    """Partially update data at a Realtime Database path."""
    try:
        if not initialize_firebase(notify=False):
            return False
        from firebase_admin import db

        def _op():
            ref = db.reference(path)
            ref.update(data)
            return True

        return bool(_retry(_op, retries=3, backoff_factor=0.4))
    except Exception as e:
        logger.exception("Realtime Update Error: %s", e)
        if notify:
            st.error(f"فشل التحديث: {e}")
        return False


def delete_firebase_node(path: str, notify: bool = False) -> bool:
    """Delete a node/path in Realtime Database."""
    try:
        if not initialize_firebase(notify=False):
            return False
        from firebase_admin import db

        def _op():
            ref = db.reference(path)
            ref.delete()
            return True

        return bool(_retry(_op, retries=3, backoff_factor=0.4))
    except Exception as e:
        logger.exception("Realtime Delete Error: %s", e)
        if notify:
            st.error(f"فشل الحذف: {e}")
        return False


def fetch_from_firebase(path: str, notify: bool = False) -> Optional[Dict[str, Any]]:
    """Alias to get_realtime_data for compatibility with existing main.py."""
    return get_realtime_data(path, notify)


def fetch_firebase_dict(path: str, notify: bool = False) -> Dict[str, Any]:
    """Return Realtime DB data as a dict or empty dict."""
    res = get_realtime_data(path, notify)
    if isinstance(res, dict):
        return res
    return {}


# ---------------- Firestore helpers (lazy imports + retry) ----------------


def set_firestore_doc(collection: str, doc_id: str, data: Dict[str, Any], notify: bool = False) -> bool:
    """Create or overwrite a Firestore document."""
    try:
        if not initialize_firebase(notify=False):
            return False
        from firebase_admin import firestore

        def _op():
            client = firestore.client()
            client.collection(collection).document(doc_id).set(data)
            return True

        return bool(_retry(_op, retries=3, backoff_factor=0.4))
    except Exception as e:
        logger.exception("Firestore Set Error: %s", e)
        if notify:
            st.error(f"فشل حفظ المستند: {e}")
        return False


def get_firestore_doc(collection: str, doc_id: str, notify: bool = False) -> Optional[Dict[str, Any]]:
    """Retrieve a Firestore document as a dict or None if not found."""
    try:
        if not initialize_firebase(notify=False):
            return None
        from firebase_admin import firestore

        def _op():
            client = firestore.client()
            doc = client.collection(collection).document(doc_id).get()
            return doc.to_dict() if doc.exists else None

        return _retry(_op, retries=3, backoff_factor=0.4)
    except Exception as e:
        logger.exception("Firestore Get Error: %s", e)
        if notify:
            st.error(f"فشل جلب المستند: {e}")
        return None


# ---------------- Compatibility wrappers ----------------

def init_firestore(notify: bool = True):
    """دالة توافقية لتهيئة واسترجاع عميل Firestore"""
    # Ensure Firebase is initialized first
    initialize_firebase(notify=notify)
    try:
        from firebase_admin import firestore
        return firestore.client()
    except Exception as e:
        logger.error(f"Init Firestore Error: {e}")
        if notify:
            st.error(f"فشل تهيئة Firestore: {e}")
        return None


def init_firebase(notify: bool = True):
    """دالة توافقية للتهيئة العامة"""
    return initialize_firebase(notify=notify)
