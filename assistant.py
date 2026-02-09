import streamlit as st
import pandas as pd
import time
import json
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app

# 1. إعداد الصفحة
st.set_page_config(page_title="المنجز - V58", layout="wide", page_icon="🏆")

# 2. تهيئة Firebase
def init_firebase():
    if not firebase_admin._apps:
        try:
            # التأكد من وجود المفتاح في السيكرتس
            if "firebase" in st.secrets:
                raw_json = st.secrets["firebase"]["json_key"]
                fb_details = json.loads(raw_json, strict=False)
                
                # تصليح الـ private_key
                if "private_key" in fb_details:
                    fb_details["private_key"] = fb_details["private_key"].replace("\\n", "\n")
                
                cred = credentials.Certificate(fb_details)
                initialize_app(cred)
            else:
                print("Firebase secrets not found - skipping...")
        except Exception as e:
            if "firebase" in st.secrets:
                st.error(f"❌ Firebase Error: {e}")
    
    try:
        return firestore.client()
    except:
        return None

db = init_firebase()

# 3. متغيرات الجلسة
if "auth" not in st.session_state:
    st.session_state.auth = False

# 4. شاشة تسجيل الدخول
if not st.session_state.auth:
    st.title("🔐 تسجيل الدخول - المنجز")
    user_email = st.text_input("البريد الإلكتروني")
    password = st.text_input("كلمة المرور", type="password")
    
    if st.button("دخول"):
        if password == "123":
            st.session_state.auth = True
            st.session_state.user_email = user_email
            st.rerun()
        else:
            st.error("بيانات الدخول خطأ")
    st.stop()

# 5. الترويسة (Header)
conn_status = "✅ متصل بالسحاب" if db else "⚠️ وضع محلي"
st.markdown(f"<div style='background:linear-gradient(90deg, #1b5e20, #ffd700); padding:10px; border-radius:10px; color:white;'>🏆 المنجز V58 | {conn_status} | 👤 {st.session_state.user_email}</div>", unsafe_allow_html=True)

st.write("### أهلاً بك في نظام المنجز")
