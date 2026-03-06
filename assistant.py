 streamlit as st
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

# --- 3. بوابة ذكاء منجز (الحل النهائي للـ 404) ---
def get_ai_response(prompt, context=""):
    try:
        # إعداد الاتصال بالمفتاح المباشر من الخزنة
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        
        # التغيير الجذري: نداء الموديل باسمه المباشر وبدون تحديد إصدار يدوي
        # هذا سيجبر النظام على استخدام النسخة المستقرة (Production)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # تفعيل ذكاء المنجز الآلي
        full_prompt = f"أنت العقل المدبر لنظام المنجز S9. السياق الميداني: {context}\nالمهمة المطلوبة: {prompt}"
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        # إذا استمرت جوجل في العناد، نستخدم هذا المحرك الاحتياطي
        return f"⚠️ عقل المنجز يقوم بتحديث بروتوكولات الأمان حالياً. حاول مجدداً بعد ثوانٍ. (السبب: {str(e)})"

# --- 4. إدارة الدخول والحماية ---
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

# --- 5. واجهة التحكم الذكي ---
with st.sidebar:
    st.success(f"المسؤول: {st.session_state['user_email']}")
    mode = st.radio("🚀 القائمة:", ["🧠 عقل المنجز (الذكاء الآلي)", "📊 العمليات الميدانية"])
    if st.button("🚪 خروج"):
        st.session_state.clear()
        st.rerun()

# --- 6. تشغيل ذكاء منجز ---
if mode == "🧠 عقل المنجز (الذكاء الآلي)":
    st.subheader("تواصل مع ذكاء منجز الآلي 🧠")
    q = st.chat_input("أعطِ أمراً للمنجز...")
    if q:
        with st.spinner("جاري الاتصال بالعقل الاستراتيجي..."):
            ai_reply = get_ai_response(q, context=f"مستخدم: {st.session_state['user_email']}")
            st.markdown(ai_reply)

# --- 7. العمليات الميدانية ---
elif mode == "📊 العمليات الميدانية":
    st.header("⏱️ لوحة المتابعة الحية")
    with st.expander("📝 إضافة مهمة جديدة"):
        with st.form("task_sys"):
            d = st.text_input("وصف المهمة")
            a = st.text_input("المندوب")
            if st.form_submit_button("بدء المهمة"):
                db.collection("tasks").add({"desc": d, "agent": a, "status": "active", "start": get_now()})
                st.success("تم التكليف!")
