import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

def initialize_firebase():
    # التحقق مما إذا كان التطبيق قد تم تهيئته مسبقاً لمنع التكرار
    if not firebase_admin._apps:
        try:
            # 1. جلب البيانات من secrets الخاصة بـ Streamlit
            # تأكد أنك وضعت البيانات تحت اسم [firebase] في الإعدادات
            firebase_secrets = dict(st.secrets["firebase"])
            
            # 2. معالجة مشكلة الـ Private Key والسطور الجديدة
            # هذا السطر هو الحل لخطأ PEM الموضح في الصورة
            if "private_key" in firebase_secrets:
                firebase_secrets["private_key"] = firebase_secrets["private_key"].replace("\\n", "\n")
            
            # 3. تهيئة الاعتمادات
            cred = credentials.Certificate(firebase_secrets)
            firebase_admin.initialize_app(cred)
            
        except Exception as e:
            st.error(f"خطأ في تهيئة النظام: {e}")
            return None
            
    return firestore.client()

# تشغيل النظام
db = initialize_firebase()

if db:
    st.success("تم الاتصال بمركز تحكم مونجيز بنجاح! ✅")
