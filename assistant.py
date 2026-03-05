import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import google.generativeai as genai

# --- 1. الربط السحابي المحصن ---
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        firebase_admin.initialize_app(cred)
    except: st.error("⚠️ خطأ في اتصال السيرفر")

db = firestore.client()

# حل مشكلة الـ 404 الظاهرة في صورتك
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # تأكد من كتابة الاسم هكذا بالضبط لتجنب خطأ 404
    model = genai.GenerativeModel('gemini-1.5-flash') 
except: model = None

# --- 2. إدارة الهوية (بناءً على بياناتك في الصورة) ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'uid': None})

# (هنا كود الدخول واستعادة الحساب المرتبط بـ SMTP في الـ Secrets)

# --- 3. جلب بيانات "القائد الأعلى" ---
user_ref = db.collection("users").document(st.session_state.uid)
user_data = user_ref.get().to_dict() or {"name": "القائد الأعلى", "balance": 0, "role": "admin"}

# --- 4. مركز القيادة (القائمة الجانبية) ---
with st.sidebar:
    st.markdown(f"### 🦅 {user_data.get('name')}") # يظهر اسمك كما في الصورة
    st.metric("💰 الرصيد الحالي", f"{user_data.get('balance'):,.2f} EGP")
    st.divider()
    mode = st.radio("🛰️ البرامج النشطة:", ["📊 لوحة العمليات", "🧠 عقل المنجز (AI)", "🚀 لوحة المدير العام"])
    if st.button("🚪 خروج آمن"):
        st.session_state.clear()
        st.rerun()

# --- 5. وظيفة عقل المنجز (بعد حل الـ 404) ---
if mode == "🧠 عقل المنجز (AI)":
    st.header("🧠 استشارة العقل الاستراتيجي")
    if model:
        q = st.chat_input("اسأل المنجز عن حسابك أو العمليات...")
        if q:
            with st.spinner("جاري التحليل..."):
                context = f"المستخدم: {user_data.get('name')}. الرصيد: {user_data.get('balance')}."
                res = model.generate_content(f"سياق: {context}. سؤال: {q}")
                st.markdown(res.text)
    else:
        st.error("⚠️ تأكد من الـ API Key في إعدادات التطبيق.")

# --- 6. لوحة المدير العام (كما تظهر في صورتك) ---
elif mode == "🚀 لوحة المدير العام":
    st.title("➕ إضافة وتعيين طلب جديد")
    with st.form("admin_form"):
        col1, col2 = st.columns(2)
        with col1:
            c_mail = st.text_input("بريد العميل")
            details = st.text_area("وصف الشحنة")
        with col2:
            price = st.number_input("القيمة الإجمالية", min_value=1.0)
            # جلب المناديب النشطين من قاعدة البيانات
            agents = db.collection("users").where("role", "==", "agent").stream()
            agent_map = {a.to_dict().get('name'): a.id for a in agents}
            selected = st.selectbox("تعيين للمندوب:", list(agent_map.keys())) if agent_map else None
        
        if st.form_submit_button("إرسال الطلب للميدان"):
            db.collection("orders").add({
                "customer_email": c_mail,
                "order_details": details,
                "price": price,
                "assigned_to": agent_map[selected] if selected else st.session_state.uid,
                "status": "processing"
            })
            st.success("✅ تم الإرسال للميدان بنجاح!")
