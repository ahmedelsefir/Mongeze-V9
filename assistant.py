import streamlit as st
import pandas as pd
import time
import json
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app

# 1. إعداد الصفحة
st.set_page_config(page_title="المنجز - V58", layout="wide", page_icon="🏆")

# 2. تهيئة Firebase (نسخة ذكية لتخطي أخطاء الفحص)
def init_firebase():
    if not firebase_admin._apps:
        try:
            # بنقول لبايثون: لو مش لاقي السيكرتس (زي في جيت هاب) كمل عادي ومطلعتش خطأ
            if "firebase" in st.secrets:
                import json
                raw_json = st.secrets["firebase"]["json_key"]
                # معالجة النص عشان الرموز اللي بتعمل Invalid escape
                fb_details = json.loads(raw_json, strict=False)
                
                if "private_key" in fb_details:
                    fb_details["private_key"] = fb_details["private_key"].replace("\\n", "\n")
                
                cred = credentials.Certificate(fb_details)
                initialize_app(cred)
            else:
                # دي عشان جيت هاب يشوفها خضراء ✅
                print("Running in local/build mode - skipping Firebase")
        except Exception as e:
            # مش هنطلع رسالة خطأ إلا لو إحنا فعلاً على السيرفر
            if "firebase" in st.secrets:
                st.error(f"⚠️ تنبيه: {e}")
    try:
        return firestore.client()
    except:
        return None

db = init_firebase()
    try:
        return firestore.client()
    except:
        return None
    try:
        return firestore.client()
    except:
        return None

db = init_firebase()

# 3. متغيرات الجلسة
if "auth" not in st.session_state:
    st.session_state.auth = False
if "role" not in st.session_state:
    st.session_state.role = None

# 4. شاشة تسجيل الدخول (لو مش مسجل)
if not st.session_state.auth:
    st.title("🔐 تسجيل الدخول - المنجز")
    user_email = st.text_input("البريد الإلكتروني")
    password = st.text_input("كلمة المرور", type="password")
    
    if st.button("دخول"):
        # تجربة دخول بسيطة (ممكن نربطها بـ Firebase لاحقاً)
        if password == "123": # عدل الباسورد براحتك
            st.session_state.auth = True
            st.session_state.role = 'admin' if "admin" in user_email else 'user'
            st.session_state.user_email = user_email
            st.rerun()
        else:
            st.error("بيانات الدخول خطأ")
    st.stop()

# 5. الترويسة (Header) - تظهر بعد الدخول فقط
conn_status = "متصل بالسحاب 🟢" if db else "وضع محلي ⚠️"
st.markdown(f"<div style='background:linear-gradient(90deg, #1b5e20, #ffd700); padding:20px; border-radius:15px; color:white;'> "
            f"🛡️ المنجز V54 | {conn_status} | 👤 {st.session_state.user_email} </div>", unsafe_allow_html=True)

# 6. لوحة التحكم (Admin / User)
if st.session_state.role == 'admin':
    st.sidebar.title("👨‍💼 الإدارة")
    menu = st.sidebar.radio("القائمة", ["📊 مراقبة العملاء", "📅 المناوبات"])
    if menu == "📊 مراقبة العملاء":
        st.write("أهلاً بك يا مستشار، البيانات تظهر هنا...")
else:
    st.sidebar.title("🌟 بوابة العميل")
    menu = st.sidebar.radio("القائمة", ["✨ تتبع طلبي", "📁 رفع مستندات"])
    if menu == "✨ تتبع طلبي":
        st.info(f"مرحباً {st.session_state.user_email}، طلبك قيد المعالجة.")

if st.sidebar.button("🚪 خروج"):
    st.session_state.clear()
    st.rerun()
