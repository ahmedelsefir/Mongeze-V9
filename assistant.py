import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore, auth
import json
import pytz
from datetime import datetime

# --- 1. الإعدادات الأساسية ---
st.set_page_config(page_title="Mongez S9 Pro", page_icon="🛡️", layout="wide")
Cairo_tz = pytz.timezone('Africa/Cairo')
def get_now(): return datetime.now(Cairo_tz)

# --- 2. تعريف وظائف السحاب (Firebase) أولاً ---
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        try:
            if "firebase" in st.secrets:
                cred = credentials.Certificate(dict(st.secrets["firebase"]))
            else:
                cred = credentials.Certificate(json.loads(st.secrets["FIREBASE_SERVICE_ACCOUNT"]))
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"خطأ في ربط Firebase: {e}")
            return None
    return firestore.client()

# --- 3. استدعاء Firebase بعد التعريف لضمان عدم وجود NameError ---
db = init_firebase()

# --- 4. بوابة ذكاء منجز (مُصلحة) ---
def get_ai_response(prompt):
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        
        # ✅ نماذج تعمل في 2025
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        try:
            # ✅ نموذج احتياطي يعمل
            backup_model = genai.GenerativeModel('gemini-2.0-flash-lite')
            return backup_model.generate_content(prompt).text
        except Exception as e2:
            return f"⚠️ عذراً قائد، خطأ في الاتصال: {str(e2)}"

# --- 5. نظام إدارة الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user_email': ""})

if not st.session_state['logged_in']:
    st.title("🦅 بوابة دخول المنجز S9")
    email = st.text_input("البريد الإلكتروني")
    if st.button("تفعيل الدخول"):
        try:
            user = auth.get_user_by_email(email)
            st.session_state.update({'logged_in': True, 'user_email': email})
            st.rerun()
        except:
            st.error("❌ البريد غير مسجل")
    st.stop()

# --- 6. واجهة المستخدم النهائية ---
st.sidebar.success(f"🟢 المتحدث: {st.session_state['user_email']}")
if st.sidebar.button("🚪 خروج"):
    st.session_state.clear()
    st.rerun()

st.header("🧠 عقل المنجز الآلي (S9)")
user_q = st.chat_input("أصدر أوامرك...")
if user_q:
    with st.spinner("🚀 جاري الاتصال..."):
        st.markdown(get_ai_response(user_q))
