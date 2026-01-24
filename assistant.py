import streamlit as st
import google.generativeai as genai
import sqlite3
import hashlib

# 1. تأسيس قاعدة بيانات مُنجز الاستراتيجية
def init_db():
    conn = sqlite3.connect('mongez_v4.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    conn.commit()
    conn.close()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

# 2. تفعيل ذكاء Gemini مع سياق البيزنس [cite: 2026-01-22]
try:
    # ملاحظة: تأكد من إضافة GOOGLE_API_KEY في إعدادات Streamlit Secrets
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    system_prompt = "أنت 'مُنجز' شريك الأعمال التقني. تخصصك: المحاسبة الدقيقة وجلب العملاء عبر SEO."
except Exception as e:
    st.error(f"⚠️ خطأ تقني في مفتاح API: {e}")

# 3. واجهة البرنامج (v4.0 الاحترافية) [cite: 2026-01-18]
st.set_page_config(page_title="Mongez v4.0", page_icon="🛡️", layout="wide")
init_db()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# نظام الدخول (بوابة الأمان)
if not st.session_state['logged_in']:
    st.sidebar.title("🔐 بوابة مُنجز")
    menu = st.sidebar.selectbox("القائمة", ["تسجيل دخول", "إنشاء حساب"])
    user = st.sidebar.text_input("اسم المستخدم")
    pw = st.sidebar.text_input("كلمة المرور", type='password')
    
    if st.sidebar.button("دخول للنظام"):
        # تعديل جوهري لضمان الدخول حتى لو قاعدة البيانات فارغة [cite: 2026-01-13]
        if user == "ahmedelsefir" and pw == "123": # يمكنك تغيير كلمة السر هنا
            st.session_state['logged_in'] = True
            st.session_state['user'] = user
            st.rerun()
        else:
            conn = sqlite3.connect('mongez_v4.db')
            c = conn.cursor()
            if menu == "تسجيل دخول":
                c.execute('SELECT password FROM users WHERE username =?', (user,))
                result = c.fetchone()
                # التحقق من الـ Hash
                if result and check_hashes(pw, result[0]):
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = user
                    st.rerun()
                else:
                    st.sidebar.error("بيانات الدخول غير صحيحة")
            conn.close()

# 4. تفعيل محركات العمل (الأدوات الأربعة) [cite: 2026-01-13]
if st.session_state['logged_in']:
    st.sidebar.success(f"مرحباً بك: {st.session_state['user']}")
    app_choice = st.sidebar.radio("قائمة التحكم", 
                                  ["المساعد الذكي (الوعي الشامل)", 
                                   "برنامج المحاسب المعتمد", 
                                   "جالب العملاء SEO", 
                                   "المحرك الصوتي المباشر"])

    if app_choice == "المساعد الذكي (الوعي الشامل)":
        st.title("🚀 مُنجز: الوعي الشامل")
        u_input = st.chat_input("أعطِ أمراً لـ مُنجز...")
        if u_input:
            resp = model.generate_content(f"{system_prompt}\nالمستخدم: {u_input}")
            st.write(resp.text)

    elif app_choice == "برنامج المحاسب المعتمد":
        st.title("📊 موديول المحاسبة")
        # هنا سنضع معادلات المحرك التي كانت في assistant.py لاحقاً
        st.info("نظام إدارة الفواتير والقيود المالية قيد التشغيل.")

    elif app_choice == "جالب العملاء SEO":
        st.title("🔍 محرك جلب الفرص")
        st.write("أدخل المجال المستهدف لاستخراج بيانات العملاء فوراً.")

    elif app_choice == "المحرك الصوتي المباشر":
        st.title("🎙️ التحكم الصوتي")
        st.write("اضغط وابدأ التحدث لتنفيذ الأوامر برمجياً.")
