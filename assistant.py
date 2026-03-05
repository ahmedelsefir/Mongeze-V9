import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import google.generativeai as genai

# --- 1. التأسيس والربط السحابي (الإعدادات المخفية) ---
st.set_page_config(page_title="منظومة المنجز S9", page_icon="🦅", layout="wide")

if not firebase_admin._apps:
    try:
        # الربط ببيانات Firebase من الـ Secrets
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"⚠️ خطأ في اتصال السيرفر: {e}")

db = firestore.client()

# تفعيل عقل المنجز (حل مشكلة 404 نهائياً)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # استخدام الموديل المستقر والسريع
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.warning("⚠️ محرك الذكاء في وضع الاستعداد")

# --- 2. إدارة الجلسة (Session Management) ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'uid': None})

# --- 3. واجهة الدخول واستعادة الحساب (نظام الـ SMTP) ---
if not st.session_state.logged_in:
    st.title("🦅 بوابة المنجز S9")
    t1, t2 = st.tabs(["🔐 دخول المحترفين", "🔑 استعادة الوصول"])
    
    with t1:
        email = st.text_input("البريد الإلكتروني")
        pwd = st.text_input("كلمة السر", type="password")
        if st.button("دخول النظام"):
            try:
                user = auth.get_user_by_email(email)
                st.session_state.update({'logged_in': True, 'uid': user.uid})
                st.rerun()
            except: st.error("❌ بيانات الدخول غير صحيحة")
            
    with t2:
        st.info("سيصلك رابط التغيير عبر إيميلك الرسمي المتصل بـ SMTP")
        re_mail = st.text_input("أدخل بريدك المسجل:")
        if st.button("إرسال رابط الاستعادة"):
            try:
                # يستخدم الـ 16 حرف المبرمجة في Firebase SMTP
                auth.generate_password_reset_link(re_mail)
                st.success(f"✅ تم الإرسال لـ {re_mail} بنجاح!")
            except: st.error("⚠️ تأكد من البريد المكتوب")
    st.stop()

# --- 4. جلب بيانات المستخدم "الخاصة" من Firestore ---
user_ref = db.collection("users").document(st.session_state.uid)
user_data = user_ref.get().to_dict() or {"name": "قائد جديد", "balance": 0, "role": "agent"}

# --- 5. القائمة الجانبية (Sidebar) ---
with st.sidebar:
    st.header(f"🦅 القائد: {user_data.get('name')}")
    st.metric("💰 الرصيد الحالي", f"{user_data.get('balance', 0):,.2f} EGP")
    st.divider()
    app_mode = st.radio("🛰️ البرامج النشطة:", ["📊 لوحة العمليات", "🧠 عقل المنجز (AI)", "🚀 لوحة المدير العام"])
    if st.button("🚪 خروج آمن"):
        st.session_state.clear()
        st.rerun()

# --- 6. لوحة العمليات والمحاسبة الآلية (دالة الـ 14%) ---
if app_mode == "📊 لوحة العمليات":
    st.subheader("📦 إدارة الطلبات الميدانية")
    # جلب طلبات المندوب الحالي فقط
    orders = db.collection("orders").where("assigned_to", "==", st.session_state.uid).where("status", "==", "processing").stream()
    
    found = False
    for order in orders:
        found = True
        d = order.to_dict()
        with st.expander(f"طلب جديد: {d.get('customer_email')}"):
            st.write(f"التفاصيل: {d.get('order_details')}")
            if st.button("✅ تم التوصيل (إضافة الربح)", key=order.id):
                # المحاسبة الآلية (14% عمولة)
                profit = d.get('price', 0) * 0.14
                db.collection("orders").document(order.id).update({"status": "delivered"})
                user_ref.update({"balance": firestore.Increment(profit)})
                st.toast(f"✅ مبروك! أضيفت {profit} EGP لمحفظتك.", icon='💰')
                st.rerun()
    if not found: st.info("لا توجد طلبات جارية لك حالياً.")

# --- 7. عقل المنجز (الربط المباشر ببيانات المستخدم) ---
elif app_mode == "🧠 عقل المنجز (AI)":
    st.subheader("🧠 استشارة العقل الاستراتيجي")
    q = st.chat_input("اسأل المنجز عن حسابك أو العمليات...")
    if q:
        # تغذية الموديل ببيانات حقيقية من Firestore
        context = f"الاسم: {user_data.get('name')}, الرصيد: {user_data.get('balance')}."
        try:
            full_p = f"بناءً على بياناتك {context}. أجب على سؤال القائد: {q}"
            res = model.generate_content(full_p)
            st.markdown(res.text)
        except Exception as e: st.error(f"⚠️ خطأ في المحرك: {e}")

# --- 8. لوحة المدير العام (إضافة الطلبات وتوزيع المهام) ---
elif app_mode == "🚀 لوحة المدير العام":
    if user_data.get('role') == 'admin':
        st.subheader("➕ إضافة وتعيين طلب جديد")
        with st.form("admin_form"):
            c1, c2 = st.columns(2)
            with c1:
                c_mail = st.text_input("بريد العميل")
                c_desc = st.text_area("وصف الشحنة")
            with c2:
                c_price = st.number_input("القيمة الإجمالية", min_value=1.0)
                # جلب المناديب من Firestore آلياً
                agents = db.collection("users").where("role", "==", "agent").stream()
                agent_map = {a.to_dict().get('name'): a.id for a in agents}
                selected = st.selectbox("تعيين للمندوب:", list(agent_map.keys())) if agent_map else None
            
            if st.form_submit_button("إرسال الطلب للميدان"):
                if selected:
                    db.collection("orders").add({
                        "customer_email": c_mail,
                        "order_details": c_desc,
                        "price": c_price,
                        "assigned_to": agent_map[selected],
                        "status": "processing",
                        "timestamp": firestore.SERVER_TIMESTAMP
                    })
                    st.success(f"✅ تم توجيه الطلب إلى {selected}")
    else:
        st.error("⚠️ عذراً، هذه الصلاحية للمدير العام فقط.")
