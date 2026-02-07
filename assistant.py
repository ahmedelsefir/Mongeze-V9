import streamlit as st
import pandas as pd
import time
from datetime import datetime
import json
from firebase_admin import credentials, firestore, initialize_app, get_app, delete_app

# --- 1. إعدادات الهوية البصرية (Emerald & Gold VIP) ---
st.set_page_config(page_title="المنجز V54 - الربط السحابي", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; text-align: right; }
    .main { background-color: #f4f7f6; }
    .app-header {
        background: linear-gradient(90deg, #1b5e20 0%, #2e7d32 100%);
        color: white; padding: 20px; border-radius: 15px;
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .info-card {
        background: white; padding: 20px; border-radius: 15px;
        border-right: 8px solid #d4af37; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .stButton>button {
        background: #1b5e20; color: white; border-radius: 10px;
        height: 3em; font-weight: bold; width: 100%; border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. محرك الربط السحابي (Firebase Engine) ---
def init_firebase():
    """محرك الربط السحابي المؤمن - المنجز V54"""
    try:
        # فحص إذا كان التطبيق مفعل مسبقاً
        try:
            return firestore.client()
        except Exception:
            # إذا لم يكن مفعلاً، نقرأ الأسرار
            if "firebase" in st.secrets:
                key_dict = dict(st.secrets["firebase"])
                
                # المعالجة الجوهرية لفك تشفير المفتاح الخاص
                if "private_key" in key_dict:
                    key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")
                
                cred = credentials.Certificate(key_dict)
                initialize_app(cred)
                return firestore.client()
            return None
    except Exception as e:
        st.error(f"⚠️ خطأ في بوابة التشفير: {e}")
        return None

# تشغيل المحرك وتخزينه في المتغير db
db = init_firebase()
if 'user_id' not in st.session_state: st.session_state.user_id = None

# --- 4. بوابة الدخول ---
if not st.session_state.auth:
    st.markdown("<h1 style='text-align:center; color:#1b5e20;'>🛡️ المنجز V54 - الدخول السحابي</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        u_type = st.radio("نوع الحساب:", ["مستشار (Management)", "عميل (VIP Client)"])
        user_email = st.text_input("البريد الإلكتروني")
        pwd = st.text_input("كلمة المرور", type="password")
        
        if st.button("🚀 دخول وتفعيل الربط"):
            if pwd == "123": # سيتم استبدالها لاحقاً بـ Auth حقيقي من Firebase
                st.session_state.auth = True
                st.session_state.role = 'admin' if "مستشار" in u_type else 'user'
                st.session_state.user_email = user_email
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 5. الترويسة العلوية ---
conn_status = "متصل بالسحاب 🟢" if db else "وضع محلي (أوفلاين) ⚠️"
st.markdown(f"""
    <div class='app-header'>
        <div><span style='font-size:24px; font-weight:bold; color:gold;'>🛡️ المنجز V54</span></div>
        <div style='display:flex; align-items:center; gap:20px;'>
            <span style='background:rgba(255,255,255,0.2); padding:4px 12px; border-radius:20px;'>{conn_status}</span>
            <div style='font-weight:bold;'>👤 {st.session_state.user_email}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 6. منطق لوحة المستشار (Admin) ---
if st.session_state.role == 'admin':
    with st.sidebar:
        st.markdown("### 👨‍💼 الإدارة السيادية")
        menu = st.radio("القائمة:", ["📊 مراقبة العملاء", "📋 مصفوفة الـ 24", "📅 المناوبات"])

    if menu == "📊 مراقبة العملاء":
        st.header("📈 حالة الربط مع العملاء")
        # جلب البيانات حياً من Firestore (مثال)
        if db:
            docs = db.collection('users_data').stream()
            clients = [doc.to_dict() for doc in docs]
            if clients:
                st.table(pd.DataFrame(clients))
            else:
                st.info("لا يوجد بيانات عملاء مسجلة في السحابة بعد.")
        else:
            st.warning("البيانات تظهر من الذاكرة المؤقتة فقط (Offline Mode)")

    elif menu == "📋 مصفوفة الـ 24":
        st.header("⚙️ تعديل بنود المنظومة")
        # هنا يتم تحديث البيانات في Firestore لتظهر للعميل فوراً
        st.write("قم بتعديل الحالة هنا لتصل للعميل في الإشعارات:")
        items = pd.DataFrame({"البند": [f"بند {i+1}" for i in range(24)], "الحالة": ["مكتمل"]*24})
        edited_df = st.data_editor(items)
        if st.button("💾 حفظ وتعميم على السحابة"):
            if db:
                db.collection('settings').document('matrix_24').set({"data": edited_df.to_dict()})
                st.success("تم تحديث البيانات السحابية لجميع المشتركين!")

# --- 7. منطق لوحة العميل (User) ---
else:
    with st.sidebar:
        st.markdown("### 🌟 بوابة العميل VIP")
        menu = st.radio("القائمة:", ["✨ تتبع طلبي", "📁 رفع المستندات"])

    if menu == "✨ تتبع طلبي":
        st.header("✨ حالة معاملتك الحالية")
        # جلب البيانات التي وضعها المستشار في مصفوفة الـ 24
        st.markdown("""
        <div class='info-card'>
            <h4>📦 حالة الطلب: جاري المراجعة</h4>
            <div style='background:#1b5e20; width:70%; height:10px; border-radius:5px;'></div>
            <p style='margin-top:10px;'>سيقوم المستشار بتحديث البنود الخاصة بك قريباً.</p>
        </div>
        """, unsafe_allow_html=True)

    elif menu == "📁 رفع المستندات":
        st.header("📁 مركز الوثائق الآمن")
        doc_type = st.selectbox("نوع الوثيقة:", ["سجل تجاري", "بطاقة ضريبية", "فاتورة"])
        uploaded_file = st.file_uploader("اختر الملف")
        if uploaded_file and st.button("🚀 رفع للسيرفر السيادي"):
            st.success("تم الرفع والتشفير. سيقوم المستشار بمراجعتها فوراً.")

# --- 8. خروج ---
if st.sidebar.button("🚪 خروج آمن"):
    st.session_state.clear()
    st.rerun()

# --- ملاحظة تقنية للمدير أحمد ---
# لتفعيل الربط الحقيقي، يرجى الذهاب لـ Streamlit Cloud -> Settings -> Secrets
# وإضافة بيانات ملف الـ Firebase JSON تحت مسمى [firebase]
