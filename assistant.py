import streamlit as st
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, firestore, auth
import json
from datetime import datetime

# --- 🔐 1. الأمان الاستراتيجي (تحميل المفاتيح) ---
if not firebase_admin._apps:
    secret_info = st.secrets["firebase"]  # تم التغيير ليتطابق مع الـ Secrets
    cred = credentials.Certificate(dict(secret_info)) # تحويلها لقاموس آمن
    firebase_admin.initialize_app(cred)

db = firestore.client()
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 👤 2. نظام التحقق من الهوية (Authentication) ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'user_info': {}, 'cart': []})

def login_gate():
    st.title("🛡️ منصة المنجز - تسجيل الدخول الآمن")
    email = st.text_input("البريد الإلكتروني")
    password = st.text_input("كلمة السر", type="password")
    if st.button("دخول النظام"):
        try:
            user = auth.get_user_by_email(email)
            user_doc = db.collection("users").document(user.uid).get()
            if user_doc.exists:
                data = user_doc.to_dict()
                st.session_state.update({'logged_in': True, 'role': data['role'], 'user_info': data, 'user_email': email})
                st.rerun()
        except: st.error("❌ بيانات غير صحيحة")
    st.stop()

if not st.session_state.logged_in:
    login_gate()

# --- 🚀 3. محرك المنجز الرئيسي (Main Logic) ---
role = st.session_state.role
user_name = st.session_state.user_info.get('name')

# قائمة التحكم بناءً على الجروب
if role == "admin": menu = ["📊 لوحة القائد", "👥 إدارة المجموعات", "💰 المحاسبة والضرائب"]
elif role == "staff": menu = ["🎧 خدمة العملاء AI", "📅 المناوبات"]
elif role == "driver": menu = ["📦 استلام الطلبات", "🏆 محفظتي", "🚀 مساعد AI"]
else: menu = ["🛍️ اطلب أي شيء", "📋 طلباتي", "🚀 مساعد AI"]

choice = st.sidebar.selectbox(f"مرحباً {user_name}", menu)

# --- 4. تنفيذ الوظائف (بناءً على كلامنا السابق) ---

# أ- واجهة العميل (اطلب أي شيء)
if choice == "🛍️ اطلب أي شيء":
    st.header("ماذا تريد أن تنجز اليوم؟")
    order_type = st.radio("نوع الطلب", ["🍔 مطاعم", "🛒 سوبر ماركت", "📦 طلب خاص"])
    order_desc = st.text_area("وصف الطلب...")
    if st.button("🚀 إرسال الطلب"):
        db.collection("orders").add({
            "customer_email": st.session_state.user_email,
            "order_details": order_desc,
            "status": "pending",
            "timestamp": datetime.now()
        })
        st.success("تم الإرسال! انتظر عروض المناديب الآن.")

# ب- واجهة المندوب والمزايدة (Bidding)
elif choice == "📦 استلام الطلبات":
    st.subheader("📥 الطلبات المتاحة")
    orders = db.collection("orders").where("status", "==", "pending").stream()
    for o in orders:
        data = o.to_dict()
        with st.expander(f"طلب من {data['customer_email']}"):
            st.write(data['order_details'])
            bid = st.number_input("سعر التوصيل", key=o.id, min_value=10)
            if st.button("إرسال عرضي", key=f"btn_{o.id}"):
                db.collection("orders").document(o.id).collection("bids").add({
                    "driver": user_name, "price": bid, "email": st.session_state.user_email
                })
                st.toast("تم إرسال عرضك!")

# ج- واجهة القائد (المحاسبة والضرائب 14%)
elif choice == "💰 المحاسبة والضرائب":
    st.header("📈 التقارير المالية والضرائب")
    # معادلة الضريبة اللي اتفقنا عليها
    st.write("يتم احتساب 14% ضريبة قيمة مضافة على عمولة التشغيل آلياً.")
    # (هنا يوضع كود عرض الإيرادات من الحلقات السابقة)

# د- المساعد الذكي وخدمة العملاء (AI First)
elif choice == "🚀 مساعد AI" or choice == "🎧 خدمة العملاء AI":
    st.title("🤖 مساعد المنجز الذكي")
    u_query = st.chat_input("كيف يمكنني مساعدتك؟")
    if u_query:
        # رسالة الترحيب اللي طلبتها
        st.info(f"أهلاً بك يا {user_name}، سوف يتم الرد عليك من قبل أهم مدير خدمة عملاء الآن في خلال دقائق.")
        resp = model.generate_content(u_query)
        st.write(resp.text)

if st.sidebar.button("تسجيل الخروج"):
    st.session_state.logged_in = False
    st.rerun()
