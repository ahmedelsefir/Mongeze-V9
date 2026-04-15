import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

def connect_to_firebase():
    # 1. التأكد إن التطبيق مش مفتوح قبل كدة لمنع أخطاء التكرار
    if not firebase_admin._apps:
        try:
            # 2. سحب البيانات من "أسرار" ستريم ليت
            # المفترض إنك وضعت البيانات تحت عنوان [firebase] في الإعدادات
            fb_creds = dict(st.secrets["firebase"])
            
            # 3. حل سحري لمشكلة الـ PEM: استبدال الـ \n النصية بسطور حقيقية
            # هذا السطر هو اللي هيشيل الخطأ اللي في الصورة عندك
            if "private_key" in fb_creds:
                fb_creds["private_key"] = fb_creds["private_key"].replace("\\n", "\n")
            
            # 4. تفعيل المفتاح
            cred = credentials.Certificate(fb_creds)
            firebase_admin.initialize_app(cred)
            
        except Exception as e:
            st.error(f"حدث خطأ أثناء الربط: {e}")
            return None
            
    return firestore.client()

# نداء الدالة لتشغيل قاعدة البيانات
db = connect_to_firebase()

if db:
    st.success("تم فتح مركز تحكم منجز بنجاح! 🚀")
