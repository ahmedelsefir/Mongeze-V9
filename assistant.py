import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore, auth
import json
import pytz
from datetime import datetime

# --- 1. الإعدادات ---
st.set_page_config(page_title="Mongez S9", page_icon="🛡️")
Cairo_tz = pytz.timezone('Africa/Cairo')
def get_now(): return datetime.now(Cairo_tz)

# --- 2. السحاب (Firebase) ---
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        try:
            if "firebase" in st.secrets:
                cred = credentials.Certificate(dict(st.secrets["firebase"]))
            else:
                cred = credentials.Certificate(json.loads(st.secrets["FIREBASE_SERVICE_ACCOUNT"]))
            firebase_admin.initialize_app(cred)
        except: pass
    return firestore.client()
db = init_firebase()

# --- 3. بوابة ذكاء منجز (الحل القاطع للـ 404) ---
def get_ai_response(prompt):
    try:
        # التأكد من تهيئة المفتاح في كل طلب لضمان الاتصال
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        
        # التعديل الذهبي: استخدام المسار الكامل والمستقر للموديل
        model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
        
        # إرسال المحتوى
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # إضافة تفاصيل أكثر للخطأ لنعرف السبب إذا فشل
        return f"⚠️ تحديث أمني من جوجل: {str(e)}"

# --- 4. واجهة المستخدم ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'user_email': ""})

if not st.session_state['logged_in']:
    st.title("🦅 دخول المنجز S9")
    email = st.text_input("البريد")
    if st.button("دخول"):
        try:
            user = auth.get_user_by_email(email)
            st.session_state.update({'logged_in': True, 'user_email': email})
            st.rerun()
        except: st.error("❌ غير مسجل")
    st.stop()

# --- 5. تشغيل العقل الآلي ---
st.sidebar.success(f"متصل: {st.session_state['user_email']}")
if st.sidebar.button("🚪 خروج"):
    st.session_state.clear()
    st.rerun()

st.header("🧠 عقل المنجز الآلي")
user_q = st.chat_input("تحدث مع المنجز...")
if user_q:
    with st.spinner("جاري الاتصال بالسحاب..."):
        st.markdown(get_ai_response(user_q))
