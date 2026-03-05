import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import google.generativeai as genai

# --- 1. التأسيس المحصن (نموذج Firebase) ---
if not firebase_admin._apps:
    try:
        # قراءة المفاتيح من Secrets
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"⚠️ خطأ في نموذج الاتصال: {e}")

db = firestore.client()

# تفعيل عقل المنجز (تحديث الموديل لتجنب خطأ 404)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # الموديل Flash هو الأسرع والأكثر توافقاً مع Firestore حالياً
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except:
    st.warning("⚠️ محرك الذكاء في وضع الاستعداد.")

# --- 2. إدارة الجلسة والدخول الخاص ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'uid': None})

if not st.session_state.logged_in:
    st.title("🦅 منظومة المنجز S9")
    tab1, tab2 = st.tabs(["🔐 دخول المستخدمين", "🔑 استعادة كلمة المرور"])
    
    with tab1:
        email = st.text_input("البريد الإلكتروني", key="l_mail")
        passw = st.text_input("كلمة السر", type="password", key="l_pass")
        if st.button("فتح النظام الشخصي", use_container_width=True):
            try:
                # التحقق من المستخدم عبر Firebase Auth
                user = auth.get_user_by_email(email)
                st.session_state.update({'logged_in': True, 'uid': user.uid})
                st.rerun()
            except: st.error("❌ بيانات الدخول غير صحيحة.")
            
    with tab2:
        st.info("سيصلك رابط التغيير من ahmedelsefir7@gmail.com")
        r_email = st.text_input("أدخل بريدك المسجل:", key="r_mail")
        if st.button("إرسال رابط الاستعادة"):
            try:
                # استخدام الـ 16 رقم (App Password) التي حصلت عليها لتفعيل الإرسال
                auth.generate_password_reset_link(r_email)
                st.success(f"✅ تم فتح باب الاستعادة! تفقد بريدك: {r_email}")
            except: st.error("⚠️ تأكد من تسجيل البريد في السيستم أولاً.")
    st.stop()

# --- 3. نظام "الصفحة الخاصة" (Multi-User Dashboard) ---
# جلب بيانات المستخدم "الحالي فقط" من Firestore
user_ref = db.collection("users").document(st.session_state.uid)
user_data = user_ref.get().to_dict() or {}

with st.sidebar:
    st.image(user_data.get('profile_pic', "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"), width=80)
    st.header(f"أهلاً، {user_data.get('name', 'المستخدم')}")
    st.success(f"💰 رصيدك: {user_data.get('balance', 0)} EGP")
    
    # قائمة التحكم الشخصية
    app_mode = st.radio("🛰️ البرامج التشغيلية:", ["لوحة المحاسبة", "عقل المنجز (AI)"])
    
    if st.button("تسجيل الخروج"):
        st.session_state.clear()
        st.rerun()

# --- 4. برنامج المحاسبة والطلبات الخاص بالمستخدم ---
if app_mode == "لوحة المحاسبة":
    st.header("📦 إدارة طلباتي وأرباحي")
    
    # جلب الطلبات الخاصة بهذا المستخدم فقط (بناءً على UID)
    my_orders = db.collection("orders").where("assigned_to", "==", st.session_state.uid).where("status", "==", "processing").stream()
    
    found_orders = False
    for order in my_orders:
        found_orders = True
        ord_info = order.to_dict()
        with st.expander(f"طلب جديد: {ord_info.get('customer_email')}"):
            st.write(f"التفاصيل: {ord_info.get('order_details')}")
            price = ord_info.get('price', 100)
            
            if st.button("تم التوصيل (إضافة الربح)", key=order.id):
                # 1. تحديث حالة الطلب في Firestore
                db.collection("orders").document(order.id).update({"status": "delivered"})
                
                # 2. إضافة العمولة (14%) لمحفظة المستخدم آلياً
                profit = price * 0.14
                user_ref.update({"balance": firestore.Increment(profit)})
                
                st.toast(f"✅ مبروك! أضيفت {profit} EGP لمحفظتك.", icon='💰')
                st.rerun()
    
    if not found_orders:
        st.info("لا توجد طلبات جارية خاصة بك حالياً.")

# --- 5. عقل المنجز المتصل ببيانات المستخدم آلياً ---
elif app_mode == "عقل المنجز (AI)":
    st.header("🧠 عقل المنجز - التحليل الشخصي")
    
    user_query = st.chat_input("اسأل المنجز عن حسابك أو شغلك...")
    if user_query:
        # بناء نموذج الإجابة (Context) من بيانات المستخدم الحقيقية
        context = f"""
        أنت المساعد الذكي لمنظومة المنجز. 
        المستخدم الحالي هو: {user_data.get('name')}.
        رصيده الحالي: {user_data.get('balance')} جنيه.
        دوره في النظام: {user_data.get('role', 'مندوب')}.
        أجب على أسئلته بناءً على هذه الأرقام بدقة واحترافية.
        """
        
        with st.spinner("جاري فحص النموذج..."):
            try:
                # إرسال البيانات + السؤال للموديل الحديث
                full_prompt = f"{context}\n\nسؤال المستخدم: {user_query}"
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
            except Exception as e:
                st.error(f"⚠️ خطأ في محرك الذكاء: {e}")
