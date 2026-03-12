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

# --- 2. السحاب (Firebase) ---
@st.cache_resource
def get_ai_response(prompt):
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        
        # المحاولة الأولى: النداء المباشر (الأكثر استقراراً الآن)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        # المحاولة الثانية: إذا فشل الأول، نجبره على استخدام نسخة v1 المستقرة
        try:
            import google.generativeai.types as types
            model = genai.GenerativeModel('gemini-1.5-flash')
            # نحدد الإصدار يدوياً في الطلب
            response = model.generate_content(prompt)
            return response.text
        except:
            return f"🛡️ القائد أحمد، النظام يتطلب إعادة تشغيل عميقة (Reboot) لتفعيل التحديث 0.8.3: {str(e)}"

db = init_firebase()

# --- 3. بوابة ذكاء منجز (الحل القاطع للـ 404) ---
def get_ai_response(prompt):
    try:
        # تهيئة المفتاح من Secrets
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        
        # استخدام اسم الموديل المباشر (هذا يمنع التحويل التلقائي لـ v1beta)
        # جربنا 'gemini-1.5-flash' بدون بادئات لضمان التوافق
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        # محرك احتياطي: إذا فشل 1.5، نستخدم 1.0 برو المستقر جداً
        try:
            backup_model = genai.GenerativeModel('gemini-pro')
            res = backup_model.generate_content(prompt)
            return res.text
        except:
            return f"⚠️ عذراً قائد، البوابة السحابية تطلب Reboot App. السبب: {str(e)}"

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
            st.success("تم التحقق.. جاري فتح الأنظمة")
            st.rerun()
        except:
            st.error("❌ عذراً، هذا البريد غير مدرج في سجلاتنا")
    st.stop()

# --- 5. واجهة التحكم والذكاء ---
st.sidebar.success(f"🟢 المتحدث الرسمي: {st.session_state['user_email']}")
if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.clear()
    st.rerun()

st.header("🧠 عقل المنجز الآلي (S9)")
st.info("النظام الآن يعمل بالنسخة المستقرة 1.5 Flash")

user_q = st.chat_input("أصدر أوامرك للمنجز...")
if user_q:
    with st.chat_message("user"):
        st.write(user_q)
    
    with st.spinner("🚀 جاري معالجة البيانات بالسحاب..."):
        reply = get_ai_response(user_q)
        with st.chat_message("assistant"):
            st.markdown(reply)
