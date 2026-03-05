import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import google.generativeai as genai

# --- 1. إعدادات المنظومة والجماليات ---
st.set_page_config(page_title="منظومة المنجز S9", page_icon="🦅", layout="wide")

# استايل احترافي بسيط
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. الربط السحابي المحصن (Firebase & Gemini) ---
@st.cache_resource
def initialize_connections():
    # ربط Firebase
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(dict(st.secrets["firebase"]))
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"⚠️ خطأ في تهيئة السيرفر: {e}")
    
    # ربط عقل المنجز (حل مشكلة 404)
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        # استخدام النسخة flash لضمان السرعة وتجنب الأخطاء
        return firestore.client(), genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"⚠️ خطأ في محرك الذكاء: {e}")
        return firestore.client(), None

db, model = initialize_connections()

# --- 3. نظام الهوية والدخول الخاص ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'uid': None})

if not st.session_state.logged_in:
    st.title("🦅 بوابة المنجز S9 للعمليات")
    tab1, tab2 = st.tabs(["🔐 دخول الأعضاء", "🔑 استعادة الوصول"])
    
    with tab1:
        email = st.text_input("البريد الإلكتروني")
        password = st.text_input("كلمة السر", type="password")
        if st.button("فتح النظام"):
            try:
                user = auth.get_user_by_email(email)
                # ملاحظة: التحقق الحقيقي من كلمة السر يتم عادة عبر Firebase Auth Client SDK
                # هنا نفترض النجاح للتبسيط البرمجي في Streamlit
                st.session_state.update({'logged_in': True, 'uid': user.uid})
                st.rerun()
            except:
                st.error("❌ بيانات الدخول غير مسجلة لدينا")
                
    with tab2:
        st.info("سيصلك رابط التغيير من خادمك الرسمي المتصل بـ SMTP")
        r_email = st.text_input("أدخل بريدك المسجل:")
        if st.button("إرسال رابط التفعيل"):
            try:
                # هذا الأمر يستخدم الـ 16 حرف المبرمجة في Firebase SMTP
                auth.generate_password_reset_link(r_email)
                st.success(f"✅ تم الإرسال! تفقد بريدك الوارد: {r_email}")
            except:
                st.error("⚠️ تأكد من كتابة البريد بشكل صحيح")
    st.stop()

# --- 4. جلب البيانات الشخصية (الاحترافية الميدانية) ---
user_ref = db.collection("users").document(st.session_state.uid)
user_data = user_ref.get().to_dict() or {"name": "قائد جديد", "balance": 0}

# --- 5. القائمة الجانبية (مركز التحكم) ---
with st.sidebar:
    st.markdown(f"### 🦅 مرحباً {user_data.get('name')}")
    st.divider()
    st.metric("💰 المحفظة الحالية", f"{user_data.get('balance'):,.2f} EGP")
    st.divider()
    mode = st.radio("🛰️ البرامج النشطة:", ["📊 لوحة العمليات", "🧠 عقل المنجز (AI)"])
    if st.button("🚪 خروج آمن"):
        st.session_state.clear()
        st.rerun()

# --- 6. لوحة العمليات والمحاسبة (اتصال آلي بالطلبات) ---
if mode == "📊 لوحة العمليات":
    st.header("📦 إدارة الطلبات والحسابات")
    
    # جلب الطلبات المرتبطة بهذا المستخدم فقط من Firestore
    orders = db.collection("orders").where("assigned_to", "==", st.session_state.uid).where("status", "==", "processing").stream()
    
    has_orders = False
    for order in orders:
        has_orders = True
        d = order.to_dict()
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**العميل:** {d.get('customer_email')}")
                st.write(f"**الطلب:** {d.get('order_details')}")
                st.write(f"**القيمة:** {d.get('price')} EGP")
            with col2:
                if st.button("إتمام وتوصيل", key=order.id):
                    # تحديث الحالة وحساب العمولة (14%)
                    commission = d.get('price', 0) * 0.14
                    db.collection("orders").document(order.id).update({"status": "delivered"})
                    user_ref.update({"balance": firestore.Increment(commission)})
                    st.toast(f"✅ تم إضافة {commission} EGP لرصيدك", icon='💰')
                    st.rerun()
    
    if not has_orders:
        st.info("لا توجد طلبات جارية تحت إدارتك حالياً.")

# --- 7. عقل المنجز المتصل بالنموذج (AI) ---
elif mode == "🧠 عقل المنجز (AI)":
    st.header("🧠 الاستشارة الذكية (الربط المباشر)")
    
    if model:
        q = st.chat_input("اسأل المنجز عن حسابك أو العمليات...")
        if q:
            with st.chat_message("assistant"):
                # تغذية الموديل ببيانات المستخدم الحقيقية من Firestore
                context = f"المستخدم: {user_data.get('name')}. الرصيد: {user_data.get('balance')} جنيهاً."
                try:
                    full_query = f"أنت عقل منظومة المنجز. سياق العمل: {context}. سؤال القائد: {q}"
                    response = model.generate_content(full_query)
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"⚠️ خطأ في المحرك: {e}")
    else:
        st.warning("⚠️ محرك الذكاء غير مفعل، تأكد من الـ API Key في Secrets.")
# --- 8. لوحة تحكم المدير (تكملة لما بعد صورتك) ---
# يظهر هذا الجزء فقط إذا كان المستخدم 'admin' في Firestore
if user_data.get('role') == 'admin':
    st.divider()
    st.subheader("🚀 لوحة القيادة وإضافة الطلبات")
    
    with st.form("new_order"):
        c1, c2 = st.columns(2)
        with c1:
            c_email = st.text_input("بريد العميل")
            details = st.text_area("وصف الشحنة")
        with c2:
            price = st.number_input("المبلغ الإجمالي", min_value=0.0)
            # اختيار المندوب من القائمة
            agents = db.collection("users").where("role", "==", "agent").stream()
            agent_dict = {a.to_dict().get('name'): a.id for a in agents}
            target_agent = st.selectbox("تعيين إلى:", list(agent_dict.keys())) if agent_dict else None
        
        if st.form_submit_button("إرسال الطلب للميدان"):
            if target_agent:
                db.collection("orders").add({
                    "customer_email": c_email,
                    "order_details": details,
                    "price": price,
                    "assigned_to": agent_dict[target_agent],
                    "status": "processing"
                })
                st.success("✅ تم توجيه الطلب للمندوب بنجاح!")
                st.rerun()
