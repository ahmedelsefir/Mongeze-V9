import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
import google.generativeai as genai

# --- 🛡️ 1. التأسيس والربط السحابي الآمن ---
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate(dict(st.secrets["firebase"]))
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"⚠️ خطأ في اتصال Firebase: {e}")

db = firestore.client()

# تفعيل محرك الذكاء (Flash سريع ومستقر)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.warning("⚠️ محرك الذكاء في وضع الاستعداد.")

# --- 👤 2. إدارة الجلسة والهوية ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'uid': None})

def login_gate():
    st.markdown("<h1 style='text-align: center;'>🦅 منظومة المنجز S9</h1>", unsafe_allow_html=True)
    email = st.text_input("البريد الإلكتروني")
    password = st.text_input("كلمة السر الاستراتيجية", type="password")
    
    if st.button("دخول للمنظومة", use_container_width=True):
        try:
            user = auth.get_user_by_email(email)
            st.session_state.update({'logged_in': True, 'uid': user.uid})
            st.rerun()
        except:
            st.error("❌ بيانات الدخول غير صحيحة.")
    st.stop()

if not st.session_state.logged_in:
    login_gate()

# --- 📱 3. جلب بيانات المستخدم الحية من Firestore ---
user_ref = db.collection("users").document(st.session_state.uid)
user_data = user_ref.get().to_dict() or {}
role = user_data.get('role', 'user')

# --- Sidebar: واجهة التحكم الجانبية ---
with st.sidebar:
    st.image(user_data.get('profile_pic', "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"), width=90)
    st.title(f"القائد: {user_data.get('name', 'مستخدم جديد')}")
    st.markdown(f"🔱 **الرتبة:** `{role.upper()}`")
    st.success(f"💰 **المحفظة:** {user_data.get('balance', 0)} EGP")
    st.divider()
    
    app_mode = st.radio("🛰️ البرامج التشغيلية:", 
                        ["لوحة البيانات", "مركز الذكاء", "إدارة العمليات"])
    
    if st.button("خروج آمن"):
        st.session_state.clear()
        st.rerun()

# --- 🚀 4. تنفيذ البرامج (Logic) ---

# البرنامج الأول: لوحة البيانات الشخصية
if app_mode == "لوحة البيانات":
    st.header("👤 ملف المستخدم الاستراتيجي")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("الاسم المعتمد", value=user_data.get('name', ''))
            new_phone = st.text_input("رقم الموبايل", value=user_data.get('phone', ''))
        with col2:
            new_pic = st.text_input("رابط الصورة الشخصية", value=user_data.get('profile_pic', ''))
        
        if st.button("حفظ التعديلات"):
            user_ref.update({"name": new_name, "phone": new_phone, "profile_pic": new_pic})
            st.success("✅ تم التحديث في السحابة!")

# البرنامج الثاني: مركز الذكاء والتحليل
elif app_mode == "مركز الذكاء":
    st.header("🧠 عقل المنجز (AI)")
    prompt = st.chat_input("تحدث مع المساعد الذكي...")
    if prompt:
        with st.chat_message("assistant"):
            try:
                context = f"أنا القائد {user_data.get('name')} برتبة {role}. سؤالي: {prompt}"
                response = model.generate_content(context)
                st.markdown(response.text)
            except Exception as e:
                st.error(f"حدث خطأ في محرك الذكاء: {e}")

# البرنامج الثالث: إدارة العمليات والأرباح
elif app_mode == "إدارة العمليات":
    st.header("📦 مركز العمليات والعمولات")
    orders = db.collection("orders").where("status", "==", "pending").stream()
    
    for o in orders:
        d = o.to_dict()
        with st.expander(f"طلب: {d.get('customer_email', 'بدون إيميل')}"):
            price = d.get('price', 100)
            st.write(f"التفاصيل: {d.get('order_details', 'لا توجد تفاصيل')}")
            st.write(f"القيمة المادية: {price} EGP")
            
            if st.button("إتمام المهمة وقبض العمولة", key=o.id):
                # تحديث حالة الطلب
                db.collection("orders").document(o.id).update({"status": "delivered"})
                # إضافة عمولة (14%) للمحفظة
                commission = price * 0.14
                new_balance = user_data.get('balance', 0) + commission
                user_ref.update({"balance": new_balance})
                st.success(f"🎊 مبروك! أضيفت عمولة قدرها {commission} EGP لرصيدك.")
                st.balloons()
                st.rerun()

# --- 🏗️ 5. إضافة موديول جديد ---
st.divider()
with st.expander("➕ توسيع النظام"):
    new_app = st.text_input("أدخل اسم البرنامج المراد توليده:")
    if st.button("توليد الهيكل"):
        st.info(f"جاري تحضير موديول {new_app}..")
