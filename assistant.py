import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore, auth
import json
import pytz
from datetime import datetime

# --- 1. الإعدادات ---
st.set_page_config(page_title="Mongez S9 Pro", page_icon="🛡️", layout="wide")
Cairo_tz = pytz.timezone('Africa/Cairo')
def get_now(): return datetime.now(Cairo_tz)

# --- 2. السحاب (Firebase) - وضعنا التعريف أولاً ---
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
    return firestore.client()

# الآن نستدعي الدالة بعد تعريفها مباشرة
db = init_firebase()

# --- 3. بوابة ذكاء منجز (الحل النهائي للـ 404) ---
def get_ai_response(prompt):
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # استخدام الاسم المباشر للموديل لضمان تخطي v1beta
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # محرك احتياطي 1.0 برو في حال تعثر فلاش
        try:
            backup_model = genai.GenerativeModel('gemini-pro')
            return backup_model.generate_content(prompt).text
        except:
            return f"⚠️ بوابة الذكاء تتطلب Reboot App لتفعيل التحديث 0.8.3: {str(e)}"

# --- 4. إدارة الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user_email': ""})

if not st.session_state['logged_in']:
    st.title("🦅 بوابة دخول المنجز S9")
    email = st.text_input("البريد الإلكتروني المعتمد")
    if st.button("تفعيل الدخول الآمن"):
        try:
            user = auth.get_user_by_email(email)
            st.session_state.update({'logged_in': True, 'user_email': email})
            st.rerun()
        except:
            st.error("❌ عذراً، هذا البريد غير مدرج")
    st.stop()

# --- 5. واجهة التحكم والذكاء ---
st.sidebar.success(f"🟢 المتحدث الرسمي: {st.session_state['user_email']}")
if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.clear()
    st.rerun()

st.header("🧠 عقل المنجز الآلي (S9)")
user_q = st.chat_input("أصدر أوامرك للمنجز...")
if user_q:
    with st.spinner("🚀 جاري المعالجة..."):
        st.markdown(get_ai_response(user_q))
