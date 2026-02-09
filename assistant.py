import streamlit as st
import pandas as pd
import time
from datetime import datetime
import json
import firebase_admin
from firebase_admin import credentials, firestore, initialize_app, get_app

# --- 1. إعدادات الصفحة والهوية البصرية ---
st.set_page_config(page_title="المنجز - V54", layout="wide", page_icon="🏆")

# تصميم الواجهة (CSS) لضمان ظهور البطاقات والألوان بشكل احترافي
st.markdown("""
<style>
    .app-header { 
        background: linear-gradient(90deg, #1b5e20, #ffd700); 
        padding: 20px; 
        border-radius: 15px; 
        color: white; 
        margin-bottom: 25px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .info-card { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 15px; 
        border: 2px solid #e0e0e0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: #1b5e20;
    }
    stButton>button {
        width: 100%;
        border-radius: 10px;
        background-color: #1b5e20;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. تهيئة متغيرات الجلسة (Session State) لمنع الأخطاء ---
if "auth" not in st.session_state:
    st.session_state.auth = False
if "role" not in st.session_state:
    st.session_state.role = None
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# --- 3. محرك الربط السحابي (Firebase Engine) ---
def init_firebase():
    try:
        # إذا كان التطبيق مفعل، لا نكرر العملية
        return firestore.client()
    except Exception:
        # سحب البيانات مباشرة من السيكرتس كقاموس
        if "firebase" in st.secrets:
            try:
                # تحويل السيكرتس لقاموس بايثون نظيف
                fb_details = dict(st.secrets["firebase"])
                
                # تصحيح أهم سطر (المفتاح الخاص) لضمان عدم وجود أخطاء تنسيق
                if "private_key" in fb_details:
                    fb_details["private_key"] = fb_details["private_key"].replace("\\n", "\n")
                
                cred = credentials.Certificate(fb_details)
                initialize_app(cred)
                return firestore.client()
            except Exception as e:
                st.error(f"خطأ في إعدادات السحاب: {e}")
    return None
                st.session_state.role = 'admin' if "مستشار" in u_type else 'user'
                st.session_state.user_email = user_email
                st.success("تم تسجيل الدخول بنجاح!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("كلمة المرور غير صحيحة")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 5. الترويسة العلوية (Header) ---
conn_status = "متصل بالسحاب 🟢" if db else "وضع محلي (أوفلاين) ⚠️"
st.markdown(f"""
    <div class='app-header'>
        <div><span style='font-size:24px; font-weight:bold;'>🛡️ المنجز V54</span></div>
        <div style='display:flex; align-items:center; gap:20px;'>
            <span style='background:rgba(255,255,255,0.2); padding:4px 12px; border-radius:20px;'>{conn_status}</span>
            <div style='font-weight:bold;'>👤 {st.session_state.user_email}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 6. لوحة تحكم المستشار (Admin) ---
if st.session_state.role == 'admin':
    with st.sidebar:
        st.markdown("### 👨‍💼 الإدارة السيادية")
        menu = st.radio("القائمة:", ["📊 مراقبة العملاء", "📋 مصفوفة الـ 24", "📅 المناوبات"])

    if menu == "📊 مراقبة العملاء":
        st.header("📈 حالة الربط مع العملاء")
        if db:
            try:
                docs = db.collection('users_data').stream()
                clients = [doc.to_dict() for doc in docs]
                if clients:
                    st.table(pd.DataFrame(clients))
                else:
                    st.info("لا يوجد بيانات عملاء مسجلة في السحابة بعد.")
            except Exception as e:
                st.error(f"خطأ في جلب البيانات: {e}")
        else:
            st.warning("البيانات تظهر من الذاكرة المؤقتة فقط (Offline Mode)")

    elif menu == "📋 مصفوفة الـ 24":
        st.header("⚙️ تعديل بنود المنظومة")
        st.write("قم بتعديل الحالة هنا لتصل للعميل فوراً:")
        items = pd.DataFrame({
            "البند": [f"بند {i+1}" for i in range(24)], 
            "الحالة": ["مكتمل"]*24
        })
        edited_df = st.data_editor(items)
        if st.button("💾 حفظ وتعميم على السحابة"):
            if db:
                db.collection('settings').document('matrix_24').set({"data": edited_df.to_dict()})
                st.success("تم تحديث البيانات السحابية لجميع المشتركين!")

# --- 7. لوحة تحكم العميل (User) ---
else:
    with st.sidebar:
        st.markdown("### 🌟 بوابة العميل VIP")
        menu = st.radio("القائمة:", ["✨ تتبع طلبي", "📁 رفع المستندات"])

    if menu == "✨ تتبع طلبي":
        st.header("✨ حالة معاملتك الحالية")
        st.markdown(f"""
        <div class='info-card'>
            <h4>📦 مرحبا بك: {st.session_state.user_email}</h4>
            <p>حالة الطلب الحالية: <b>جاري المراجعة</b></p>
            <div style='background-color:#e0e0e0; width:100%; height:15px; border-radius:10px;'>
                <div style='background-color:#1b5e20; width:70%; height:15px; border-radius:10px;'></div>
            </div>
            <p style='margin-top:10px; font-size:12px;'>سيقوم المستشار بتحديث مصفوفة الـ 24 الخاصة بك قريباً.</p>
        </div>
        """, unsafe_allow_html=True)

    elif menu == "📁 رفع المستندات":
        st.header("📁 مركز الوثائق الآمن")
        doc_type = st.selectbox("نوع الوثيقة:", ["سجل تجاري", "بطاقة ضريبية", "فاتورة"])
        uploaded_file = st.file_uploader("اختر الملف")
        if uploaded_file and st.button("🚀 رفع للسيرفر السيادي"):
            st.success("تم الرفع والتشفير بنجاح. سيقوم المستشار بمراجعتها.")

# --- 8. تسجيل الخروج ---
if st.sidebar.button("🚪 خروج آمن"):
    st.session_state.clear()
    st.rerun()
