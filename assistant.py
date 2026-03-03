import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import google.generativeai as genai
from streamlit_js_eval import streamlit_js_eval
import pandas as pd

# --- 🛡️ 1. التأسيس الأمني (قاعدة البيانات والذكاء) ---
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"⚠️ فشل الاتصال بالسحابة: {e}")

db = firestore.client()

# تفعيل الموديل الخارق (Gemini 1.5 Pro)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-pro')
except:
    st.warning("⚠️ محرك الذكاء الاصطناعي في وضع الاستعداد.")

# --- 👤 2. إدارة الجلسة والهوية ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_info': {}, 'apps': []})

def login_gate():
    st.markdown("<h1 style='text-align: center;'>🦅 منصة المنجز - الدخول الذكي</h1>", unsafe_allow_html=True)
    email = st.text_input("البريد الوارد (ahmedelsefir9@...)")
    password = st.text_input("كلمة المرور الاستراتيجية", type="password")
    
    if st.button("فتح النظام", use_container_width=True):
        try:
            user = auth.get_user_by_email(email)
            user_doc = db.collection("users").document(user.uid).get()
            if user_doc.exists:
                data = user_doc.to_dict()
                st.session_state.update({
                    'logged_in': True, 'role': data.get('role', 'user'),
                    'user_info': data, 'user_email': email
                })
                st.rerun()
        except: st.error("❌ وصول مرفوض: تأكد من البيانات")
    st.stop()

if not st.session_state.logged_in:
    login_gate()

# --- 📱 3. واجهة القائد والبرامج (Sidebar) ---
user_info = st.session_state.user_info
role = st.session_state.role

with st.sidebar:
    st.image(user_info.get('profile_pic', "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"), width=80)
    st.title(f"القائد: {user_info.get('name')}")
    st.caption(f"الرتبة: {role.upper()}")
    st.divider()
    
    # بوابة البرامج الجديدة (Dynamic App Switcher)
    app_mode = st.radio("🛰️ اختر البرنامج التشغيلي:", 
                        ["المنجز الأساسي", "مركز الذكاء التطويري", "إدارة القبول والسيستم"])
    
    if st.button("خروج آمن"):
        st.session_state.clear()
        st.rerun()

# --- 🚀 4. تنفيذ البرامج (Logic) ---

# البرنامج الأول: المنجز الأساسي (العمليات اليومية)
if app_mode == "المنجز الأساسي":
    st.header("📦 إدارة العمليات الميدانية")
    tabs = st.tabs(["🛒 الطلبات النشطة", "💰 المحفظة المالية", "📋 سجل الإنجاز"])
    
    with tabs[0]:
        if role in ["admin", "driver"]:
            orders = db.collection("orders").where("status", "==", "pending").stream()
            for o in orders:
                d = o.to_dict()
                with st.expander(f"طلب جديد: {d.get('customer_email')}"):
                    st.write(d.get('order_details'))
                    if st.button("قبول المهمة", key=o.id):
                        db.collection("orders").document(o.id).update({"status": "processing", "driver": user_info.get('name')})
                        st.success("تم تأكيد المهمة!")

# البرنامج الثاني: مركز الذكاء التطويري (العقل المدبر)
elif app_mode == "مركز الذكاء التطويري":
    st.header("🧠 مساعد المنجز الخارق (Gemini 1.5 Pro)")
    st.info("هذا الموديل مخصص لتحليل البيانات المعقدة وحل مشكلات السيستم.")
    
    u_input = st.chat_input("تحدث مع عقل المنجز...")
    if u_input:
        with st.chat_message("assistant"):
            st.write(f"أهلاً بك يا {user_info.get('name')}.. جاري التحليل الاستراتيجي...")
            try:
                # ربط الذكاء ببيانات السيستم الحقيقية
                context = f"المستخدم الحالي هو {role}. المهام المتاحة: توصيل، محاسبة، ضرائب 14%. السؤال: {u_input}"
                response = model.generate_content(context)
                st.markdown(response.text)
            except Exception as e:
                st.error(f"عذراً قائد، هناك ضغط على المحرك: {e}")

# البرنامج الثالث: إدارة القبول والسيستم (فتح البرامج الجديدة)
elif app_mode == "إدارة القبول والسيستم":
    st.header("⚙️ مركز التحكم والقبول")
    
    if role == "admin":
        col1, col2 = st.columns(2)
        with col1:
            st.metric("المناديب النشطين", "12") # يمكن ربطها بـ Firestore count
        with col2:
            st.metric("الضرائب المحصلة (14%)", "1,450 EGP")
            
        st.subheader("🆕 طلبات القبول والتسجيل")
        pendings = db.collection("users").where("status", "==", "pending").stream()
        for p in pendings:
            p_data = p.to_dict()
            with st.container(border=True):
                st.write(f"إيميل: {p_data.get('email')} | الرتبة المطلوبة: {p_data.get('role')}")
                if st.button("تفعيل البرنامج لهذا المستخدم", key=p.id):
                    db.collection("users").document(p.id).update({"status": "active"})
                    st.balloons()
    else:
        st.warning("⚠️ هذه المنطقة مخصصة للقادة فقط.")

# --- 🚀 5. بوابة "فتح البرامج الجديدة" (Future Expansion) ---
st.divider()
with st.expander("➕ إضافة موديول جديد للسيستم"):
    st.write("يمكنك الآن طلب إضافة برنامج (مخازن، شحن دولي، إدارة عقارات) وسيقوم الذكاء بتوليده.")
    new_app_idea = st.text_input("اسم البرنامج الجديد المراد فتحه داخل المنجز:")
    if st.button("توليد هيكل البرنامج"):
        st.write(f"جاري تحضير موديول {new_app_idea} في بيئة IDX...")
