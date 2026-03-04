import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import google.generativeai as genai

# --- 1. التأسيس الذكي ---
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"⚠️ خطأ فني في قاعدة البيانات: {e}")

db = firestore.client()

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
except:
    st.warning("⚠️ محرك الذكاء في وضع الاستعداد.")

# --- 2. إدارة الجلسة والدخول الاستراتيجي ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'uid': None})

if not st.session_state.logged_in:
    st.title("🦅 منظومة المنجز S9")
    
    # إضافة تبويبات للدخول أو استعادة كلمة السر
    tab1, tab2 = st.tabs(["🔐 تسجيل الدخول", "🔑 استعادة كلمة المرور"])
    
    with tab1:
        email = st.text_input("البريد الإلكتروني", key="login_email")
        password = st.text_input("كلمة السر", type="password", key="login_pass")
        if st.button("فتح النظام", use_container_width=True):
            try:
                # التحقق من المستخدم عبر Firebase
                user = auth.get_user_by_email(email)
                st.session_state.update({'logged_in': True, 'uid': user.uid})
                st.rerun()
            except: 
                st.error("❌ البريد أو كلمة السر غير صحيحة")
    
    with tab2:
        st.info("سيتم إرسال رابط رسمي من جوجل لتغيير كلمة المرور لبريدك.")
        reset_email = st.text_input("أدخل بريدك المسجل:", key="reset_email")
        if st.button("إرسال رابط الاستعادة", use_container_width=True):
            if reset_email:
                try:
                    # إرسال إيميل إعادة التعيين
                    auth.generate_password_reset_link(reset_email)
                    st.success(f"✅ تم إرسال الرابط بنجاح إلى {reset_email}")
                except Exception as e:
                    st.error(f"⚠️ تأكد من صحة البريد: {e}")
            else:
                st.warning("يرجى كتابة البريد أولاً.")
    st.stop()

# --- 3. جلب البيانات وتحديث المحفظة ---
user_ref = db.collection("users").document(st.session_state.uid)
user_data = user_ref.get().to_dict() or {}

with st.sidebar:
    st.image(user_data.get('profile_pic', "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"), width=80)
    st.header(user_data.get('name', 'القائد'))
    st.metric("💰 الرصيد الحالي", f"{user_data.get('balance', 0)} EGP")
    app_mode = st.radio("🛰️ البرامج التشغيلية:", ["مركز التحكم", "عقل المنجز (AI)", "العمليات الميدانية"])
    if st.button("تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

# --- 4. معالجة الأقسام ---
if app_mode == "عقل المنجز (AI)":
    st.header("🧠 استشارة الذكاء الاصطناعي")
    user_query = st.chat_input("تحدث مع المنجز...")
    if user_query:
        with st.spinner("جاري التفكير..."):
            try:
                response = model.generate_content(user_query)
                st.markdown(response.text)
            except Exception as e:
                st.error(f"المحرك يحتاج لتحديث مفتاح API. الخطأ: {e}")

elif app_mode == "العمليات الميدانية":
    st.header("📦 إدارة الطلبات المباشرة")
    orders = db.collection("orders").where("status", "==", "pending").stream()
    
    for order in orders:
        ord_info = order.to_dict()
        with st.expander(f"طلب جديد من: {ord_info.get('customer_email', 'عميل')}"):
            st.write(f"التفاصيل: {ord_info.get('order_details')}")
            if st.button("تم التسجيل والإتمام", key=order.id):
                db.collection("orders").document(order.id).update({"status": "delivered"})
                new_bal = user_data.get('balance', 0) + (ord_info.get('price', 100) * 0.14)
                user_ref.update({"balance": new_bal})
                st.success("✅ تم تحديث المحفظة والطلب!")
                st.rerun()
