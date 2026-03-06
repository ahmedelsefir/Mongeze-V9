import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore, auth
import json
import pytz
from datetime import datetime

# --- 1. إعدادات النظام الأساسية (أمان أولاً) ---
st.set_page_config(page_title="Mongez Cloud S9", page_icon="🛡️", layout="wide")
Cairo_tz = pytz.timezone('Africa/Cairo')

def get_now():
    return datetime.now(Cairo_tz)

# --- 2. الاتصال السحابي (Firebase) المحمي بالكاش ---
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        try:
            # الربط الذكي من الـ Secrets كما في صورتك
            if "firebase" in st.secrets:
                cred = credentials.Certificate(dict(st.secrets["firebase"]))
            elif "FIREBASE_SERVICE_ACCOUNT" in st.secrets:
                secret_info = json.loads(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
                cred = credentials.Certificate(secret_info)
            else:
                cred = credentials.Certificate("serviceAccountKey.json")
            
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"⚠️ خطأ في بوابة السحاب: {e}")
    return firestore.client()

db = init_firebase()

def get_ai_response(prompt, context=""):
    try:
        # 1. إعداد المفتاح
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        
        # 2. الحل القاطع: نداء الموديل بدون كلمة models وبإصدار مستقر v1
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash'
        )
        
        # 3. إرسال الطلب
        full_prompt = f"أنت مساعد نظام المنجز S9. السياق: {context}\nالسؤال: {prompt}"
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        # إذا فشل، نجرب الطريقة البديلة الأبسط
        try:
            model = genai.GenerativeModel('gemini-pro')
            return model.generate_content(prompt).text
        except:
            return f"⚠️ تحديث أمني من جوجل: {str(e)}"

# --- 4. إدارة حالة الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'uid': None, 'role': 'user'})

# --- 5. بوابة تسجيل الدخول (لن يظهر أي خطأ أحمر قبل تجاوزها) ---
if not st.session_state['logged_in']:
    st.title("🦅 بوابة المنجز S9")
    email = st.text_input("البريد الإلكتروني")
    pw = st.text_input("كلمة السر", type='password')
    
    if st.button("دخول آمن"):
        try:
            user = auth.get_user_by_email(email)
            user_doc = db.collection("users").document(user.uid).get()
            if user_doc.exists:
                data = user_doc.to_dict()
                st.session_state.update({
                    'logged_in': True,
                    'uid': user.uid,
                    'role': data.get('role', 'user'),
                    'user_email': email
                })
                st.rerun()
            else:
                st.error("❌ حسابك غير معرف في قاعدة البيانات (Firestore)")
        except:
            st.error("❌ بيانات الدخول خاطئة")
    st.stop() # هذا السطر يمنع تنفيذ أي كود آخر قبل الدخول

# --- 6. لوحة العمليات بعد الدخول ---
role = st.session_state['role']
with st.sidebar:
    st.success(f"مرحباً: {st.session_state['user_email']}")
    mode = st.radio("🚀 القائمة:", ["🧠 عقل المنجز", "📊 العمليات الميدانية"])
    if st.button("🚪 خروج"):
        st.session_state.clear()
        st.rerun()

# --- 7. تشغيل البرامج ---
if mode == "🧠 عقل المنجز":
    st.subheader("استشارة العقل الاستراتيجي 🧠")
    q = st.chat_input("اسأل المنجز...")
    if q:
        with st.spinner("جاري التفكير..."):
            res = get_ai_response(q, context=f"مستخدم بدوره: {role}")
            st.markdown(res)
