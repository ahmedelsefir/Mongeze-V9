import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore, auth
import json
import pytz
from datetime import datetime

# --- 1. الإعدادات الأساسية ---
st.set_page_config(page_title="Mongez Cloud S9", page_icon="🛡️", layout="wide")
Cairo_tz = pytz.timezone('Africa/Cairo')
def get_now(): return datetime.now(Cairo_tz)

# --- 2. ربط السحاب (Firebase) ---
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

# --- 3. بوابة ذكاء منجز (الاتصال الإجباري) ---
def get_ai_response(prompt, context=""):
    try:
        # الربط بالمفتاح الجديد من الخزنة
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        
        # التعديل المفصلي: استخدام الطريقة المباشرة لطلب الموديل دون v1beta
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # إرسال المحتوى بشكل خام لتجاوز مشاكل التنسيق
        response = model.generate_content(
            f"أنت العقل المدبر لنظام المنجز S9. السياق: {context}\nالأمر: {prompt}"
        )
        return response.text
    except Exception as e:
        # إذا فشل، نحاول الاتصال بأقدم نسخة مستقرة لضمان الرد
        try:
            model = genai.GenerativeModel('gemini-pro')
            return model.generate_content(prompt).text
        except:
            return f"⚠️ بوابة الذكاء تطلب إعادة تشغيل (Reboot): {str(e)}"

# --- 4. إدارة الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'uid': None, 'role': 'صاحب عمل'})

if not st.session_state['logged_in']:
    st.title("🦅 بوابة المنجز S9")
    email = st.text_input("البريد الإلكتروني")
    pw = st.text_input("كلمة السر", type='password')
    if st.button("دخول آمن"):
        try:
            user = auth.get_user_by_email(email)
            st.session_state.update({'logged_in': True, 'uid': user.uid, 'user_email': email})
            st.rerun()
        except: st.error("❌ بيانات الدخول غير صحيحة")
    st.stop()

# --- 5. واجهة التحكم ---
with st.sidebar:
    st.success(f"المسؤول: {st.session_state['user_email']}")
    mode = st.radio("🚀 القائمة:", ["🧠 عقل المنجز الآلي", "📊 العمليات الميدانية"])
    if st.button("🚪 خروج"):
        st.session_state.clear()
        st.rerun()

if mode == "🧠 عقل المنجز الآلي":
    st.subheader("تواصل مباشر مع ذكاء منجز 🧠")
    q = st.chat_input("أعطِ أمراً للمنجز...")
    if q:
        with st.spinner("جاري كسر حاجز الاتصال..."):
            reply = get_ai_response(q, context=f"المسؤول: {st.session_state['user_email']}")
            st.markdown(reply)

elif mode == "📊 العمليات الميدانية":
    st.header("⏱️ المتابعة الحية")
    # تم الإبقاء على ساعة الإيقاف والعمليات كما هي لضمان استقرار المهام
    tasks = db.collection("tasks").where("status", "==", "active").stream()
    for task in tasks:
        t = task.to_dict()
        elapsed = get_now() - t['start'].astimezone(Cairo_tz)
        st.warning(f"📍 {t['desc']} | ⏱️ {elapsed.seconds // 60} دقيقة")
        if st.button("إتمام", key=task.id):
            db.collection("tasks").document(task.id).update({"status": "done"})
            st.rerun()
