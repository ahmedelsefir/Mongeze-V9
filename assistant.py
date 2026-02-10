import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import time

# --- 1. فحص الاتصال السحابي (The Bridge) ---
def connect_to_the_cloud():
    # التحقق إذا كان التطبيق مسبقاً لمنع خطأ التكرار
    if not firebase_admin._apps:
        try:
            # التأكد من وجود الخزنة (Secrets)
            if "firebase" in st.secrets:
                fb_data = dict(st.secrets["firebase"])
                # السطر الحاسم لتشغيل المفتاح الخاص
                fb_data["private_key"] = fb_data["private_key"].replace("\\n", "\n")
                
                cred = credentials.Certificate(fb_data)
                firebase_admin.initialize_app(cred)
                return firestore.client()
            else:
                st.error("❌ الخزنة (Secrets) فارغة! يرجى إضافة مفتاح Firebase.")
                return None
        except Exception as e:
            st.error(f"⚠️ فشل الربط التقني: {e}")
            return None
    return firestore.client()

# تفعيل قاعدة البيانات
db = connect_to_the_cloud()

# --- 2. واجهة المستخدم الفاخرة ---
st.set_page_config(page_title="المنجز V58 - القوة السحابية", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f9fbf9; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #1b5e20; color: gold; }
    .vip-card { padding: 20px; border-radius: 15px; background: white; border-right: 8px solid #1b5e20; box-shadow: 2px 2px 15px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 3. نظام الدخول والحماية ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🛡️ بوابة المنجز V58")
    user_mail = st.text_input("إيميل العميل الـ VIP")
    if st.button("فتح البوابة"):
        if "@" in user_mail:
            st.session_state.auth = True
            st.session_state.email = user_mail
            st.rerun()
    st.stop()

# --- 4. لوحة التحكم الرئيسية ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/1055/1055672.png", width=100)
st.sidebar.title(f"القائد: {st.session_state.email.split('@')[0]}")

# عرض حالة الاتصال الحية
if db:
    st.sidebar.success("✅ متصل سحابياً (Firebase Active)")
else:
    st.sidebar.error("❌ غير متصل (Offline Mode)")

tabs = st.tabs(["🏠 الرئيسية", "📊 إدارة المناوبات", "⚙️ الإعدادات"])

with tabs[0]:
    st.markdown("<div class='vip-card'><h1>🌿 مرحباً بك في عصر السحاب</h1><p>الآن يمكنك البدء في تخزين بيانات العملاء وضمان رضاهم التام.</p></div>", unsafe_allow_html=True)
    
    if st.button("🚀 اختبار إرسال أول نبضة للسحابة"):
        if db:
            with st.spinner("جاري الكتابة في السحابة..."):
                db.collection("test").add({"msg": "Hello Cloud", "time": str(time.ctime())})
                st.balloons()
                st.success("تم الاتصال والحفظ بنجاح مبهر!")
        else:
            st.error("لا يمكن الإرسال.. تأكد من إعدادات Secrets")

with tabs[1]:
    st.header("📅 إدارة المناوبات الذكية")
    # سيتم ربط هذا الجزء مباشرة بـ Firestore لاحقاً
    st.write("الجدول السحابي قيد المزامنة...")

with tabs[2]:
    st.header("⚙️ تفاصيل الربط")
    if "firebase" in st.secrets:
        st.write(f"المشروع المرتبط: `{st.secrets['firebase']['project_id']}`")
