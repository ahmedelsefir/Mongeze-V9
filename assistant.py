import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

REQUIRED_FIELDS = [
    "type",
    "project_id",
    "private_key_id",
    "private_key",
    "client_email",
    "client_id",
    "auth_uri",
    "token_uri",
    "auth_provider_x509_cert_url",
    "client_x509_cert_url",
]

def validate_service_account(info: dict):
    missing = [key for key in REQUIRED_FIELDS if not info.get(key)]
    if missing:
        raise ValueError(f"حقول ناقصة في secrets.toml: {', '.join(missing)}")

    private_key = info["private_key"].strip()

    if "-----BEGIN PRIVATE KEY-----" not in private_key:
        raise ValueError("بداية private_key غير صحيحة")

    if "-----END PRIVATE KEY-----" not in private_key:
        raise ValueError("نهاية private_key غير صحيحة")

    return True

def init_firebase():
    if "gcp_service_account" not in st.secrets:
        raise ValueError("القسم gcp_service_account غير موجود في secrets.toml")

    service_account_info = dict(st.secrets["gcp_service_account"])
    validate_service_account(service_account_info)

    if not firebase_admin._apps:
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred)

    return firestore.client()

st.title("فحص اتصال Firebase")

try:
    db = init_firebase()
    st.success("تم التعرف على المفتاح والاتصال بـ Firebase بنجاح")
except Exception as e:
    st.error(f"حدث خطأ: {e}")
