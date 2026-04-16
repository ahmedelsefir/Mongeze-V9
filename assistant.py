import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# استخدام cache_resource لضمان استمرارية الاتصال وعدم تكراره
@st.cache_resource
def init_firebase():
    if "gcp_service_account" not in st.secrets:
        st.error("القسم gcp_service_account غير موجود في إعدادات secrets")
        return None

    # تحويل Secrets إلى قاموس قابل للتعديل
    service_account_info = dict(st.secrets["gcp_service_account"])
    
    # إصلاح مشكلة الأسطر الجديدة في المفتاح الخاص
    if "private_key" in service_account_info:
        service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")

    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"فشل في تهيئة Firebase: {e}")
        return None

st.title("فحص اتصال Firebase المحسن")

db = init_firebase()

if db:
    st.success("تم الاتصال بـ Firebase بنجاح!")
    # تجربة قراءة بسيطة للتأكد من صلاحية الوصول
    # doc = db.collection("test").document("check").get()
