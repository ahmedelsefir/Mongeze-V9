import streamlit as st
import firebase_admin
from firebase_admin import credentials, db, firestore
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_firebase(notify=True):
    """تهيئة اتصال فايربيس بشكل آمن ليدعم Realtime DB و Firestore"""
    try:
        if not firebase_admin._apps:
            if "firebase" in st.secrets:
                secret_dict = dict(st.secrets["firebase"])
                
                # تصحيح الـ private_key لتعامل سليماً مع الأسطر الجديدة
                if "private_key" in secret_dict:
                    secret_dict["private_key"] = secret_dict["private_key"].replace("\\n", "\n")
                
                cred = credentials.Certificate(secret_dict)
                db_url = st.secrets["firebase"].get("databaseURL", "")
                
                initialize_args = {}
                if db_url:
                    initialize_args['databaseURL'] = db_url
                
                firebase_admin.initialize_app(cred, initialize_args)
                if notify:
                    st.success("تم الاتصال بقاعدة البيانات بنجاح 🟢")
            else:
                if notify:
                    st.error("Firebase credentials not found in Streamlit secrets.")
                return False
        return True
    except Exception as e:
        logger.error(f"Firebase Init Error: {e}")
        if notify:
            st.error(f"فشل الاتصال بقاعدة البيانات: {e}")
        return False


def push_realtime_data(path, data, notify=False):
    """إرسال بيانات جديدة في الوقت الحقيقي إلى Realtime Database"""
    try:
        if initialize_firebase(notify=False):
            ref = db.reference(path)
            new_ref = ref.push(data)
            return new_ref.key
    except Exception as e:
        logger.error(f"Realtime Push Error: {e}")
        if notify:
            st.error(f"فشل الإرسال: {e}")
    return None


def get_realtime_data(path, notify=False):
    """جلب البيانات في الوقت الحقيقي من Realtime Database"""
    try:
        if initialize_firebase(notify=False):
            ref = db.reference(path)
            return ref.get()
    except Exception as e:
        logger.error(f"Realtime Get Error: {e}")
        if notify:
            st.error(f"فشل جلب البيانات: {e}")
    return None


def update_realtime_data(path, data, notify=False):
    """تحديث بيانات في الوقت الحقيقي"""
    try:
        if initialize_firebase(notify=False):
            ref = db.reference(path)
            ref.update(data)
            return True
    except Exception as e:
        logger.error(f"Realtime Update Error: {e}")
        if notify:
            st.error(f"فشل التحديث: {e}")
    return False


def set_firestore_doc(collection, doc_id, data, notify=False):
    """حفظ مستند في Firestore"""
    try:
        if initialize_firebase(notify=False):
            fs_db = firestore.client()
            fs_db.collection(collection).document(doc_id).set(data)
            return True
    except Exception as e:
        logger.error(f"Firestore Set Error: {e}")
        if notify:
            st.error(f"فشل حفظ المستند: {e}")
    return False


def get_firestore_doc(collection, doc_id, notify=False):
    """جلب مستند من Firestore"""
    try:
        if initialize_firebase(notify=False):
            fs_db = firestore.client()
            doc = fs_db.collection(collection).document(doc_id).get()
            if doc.exists:
                return doc.to_dict()
    except Exception as e:
        logger.error(f"Firestore Get Error: {e}")
        if notify:
            st.error(f"فشل جلب المستند: {e}")
    return None
