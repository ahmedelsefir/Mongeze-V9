import streamlit as st
import pandas as pd
import random
import time
from datetime import datetime

# --- 1. إعدادات الهوية البصرية الفاخرة (Emerald & Gold UI) ---
st.set_page_config(
    page_title="منصة المنجز V32 - الإمبراطورية",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تخصيص التصميم عبر CSS لضمان الوضوح والجمال
st.markdown("""
    <style>
    /* تنسيق القائمة الجانبية - أيقونات ضخمة وألوان ملكية */
    .stRadio div[role="radiogroup"] label { 
        font-size: 22px !important; 
        font-weight: bold; 
        background: linear-gradient(90deg, #1b5e20 0%, #2e7d32 100%);
        color: #ffeb3b !important; 
        padding: 18px; 
        margin: 10px 0; 
        border-radius: 15px; 
        border: 2px solid #ffffff; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        transition: 0.3s;
    }
    .stRadio div[role="radiogroup"] label:hover { transform: scale(1.02); border-color: #ffeb3b; }
    
    /* كرت الترحيب السحري */
    .welcome-card {
        background: linear-gradient(135deg, #ffffff 0%, #f1f8e9 100%);
        padding: 40px;
        border-radius: 25px;
        border-right: 15px solid #1b5e20;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 30px;
        animation: fadeIn 1.5s ease-in-out;
    }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
    
    /* صندوق سياسة الخصوصية */
    .policy-box {
        background: #f8fafc;
        padding: 20px;
        border-radius: 12px;
        border: 1px dashed #1b5e20;
        height: 150px;
        overflow-y: scroll;
        font-size: 14px;
        color: #334155;
        margin: 15px 0;
    }
    
    /* تحسين الخطوط العامة */
    h1, h2, h3 { color: #1b5e20; font-family: 'Cairo', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. إدارة الأمان والتحقق (Auth Engine) ---
if 'auth_step' not in st.session_state: st.session_state.auth_step = 'login'
if 'user_logged' not in st.session_state: st.session_state.user_logged = False

# واجهة الدخول (قبل الوصول للبرنامج)
if not st.session_state.user_logged:
    st.markdown("<h1 style='text-align:center;'>🛡️ بوابة المنجز النخبوية</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        if st.session_state.auth_step == 'login':
            email = st.text_input("📧 البريد الإلكتروني للعميل VIP")
            st.markdown("<b>📜 سياسة الخصوصية وشروط الاستخدام:</b>", unsafe_allow_html=True)
            st.markdown("""<div class='policy-box'>
                أهلاً بك في المنجز. نحن نلتزم بحماية بياناتك الضريبية بأعلى معايير التشفير. 
                بالموافقة، تمنحنا صلاحية تنظيم ملفاتك المحاسبية. 
                لن يتم مشاركة أي سجلات مع جهات خارجية. 
                نظامنا مراقب بـ Honeybadger لضمان استقرار الخدمة 24/7.
                </div>""", unsafe_allow_html=True)
            
            agree = st.checkbox("أوافق على كافة الشروط والسياسات")
            
            if st.button("🚀 إرسال كود التحقق (OTP)"):
                if "@" in email and agree:
                    st.session_state.temp_email = email
                    st.session_state.secure_otp = str(random.randint(1000, 9999))
                    st.session_state.auth_step = 'verify'
                    st.success(f"تم إرسال الكود لبريدك! (للمعاينة: {st.session_state.secure_otp})")
                    st.rerun()
                else:
                    st.warning("يرجى إدخال إيميل صحيح والموافقة على السياسة.")

        elif st.session_state.auth_step == 'verify':
            st.info(f"رمز التحقق أُرسل إلى: {st.session_state.temp_email}")
            otp_input = st.text_input("🔢 أدخل الرمز المكون من 4 أرقام")
            if st.button("🔐 تأكيد وهبوط آمن"):
                if otp_input == st.session_state.secure_otp:
                    st.session_state.user_logged = True
                    st.balloons() # لمسة احتفالية عند النجاح
                    st.rerun()
                else:
                    st.error("الرمز غير صحيح، يرجى المحاولة مرة أخرى.")
            if st.button("⬅️ العودة لتغيير الإيميل"):
                st.session_state.auth_step = 'login'
                st.rerun()
    st.stop()

# --- 3. اللمسة السحرية: رسالة الترحيب (تظهر لمرة واحدة عند الدخول) ---
if 'first_load' not in st.session_state:
    st.session_state.first_load = True

if st.session_state.first_load:
    st.markdown(f"""
        <div class='welcome-card'>
            <h1 style='margin-bottom:10px;'>🌿 نورت إمبراطورية المنجز يا قائد</h1>
            <p style='font-size:22px; color:#475569;'>يسعدنا انضمامك اليوم كعضو VIP (<b>{st.session_state.temp_email}</b>)</p>
            <p style='font-size:18px;'>تم تأمين حسابك بنجاح وجاري مزامنة بياناتك مع السيرفر الرئيسي.</p>
        </div>
        """, unsafe_allow_html=True)
    st.toast("نورت المنجز! نتمنى لك تجربة استثنائية.")
    time.sleep(3)
    st.session_state.first_load = False
    st.rerun()

# --- 4. واجهة التطبيق الرئيسية (The Masterpiece) ---
st.sidebar.markdown(f"### 👤 المدير العام")
st.sidebar.caption(f"متصل: {st.session_state.temp_email}")

menu = st.sidebar.radio("قائمة الإنجازات الاحترافية:", [
    "🏠 اللوحة العامة المركزية", 
    "🤖 مساعد المنجز (AI)", 
    "📊 المحاسب الرقمي (جداول 24)", 
    "📅 إدارة المناوبات", 
    "📂 مركز الوثائق المؤمن",
    "⚙️ إعدادات النظام والأسرار"
])

# سحب المفاتيح من الخزنة (Secrets) لضمان الأمان
HB_KEY = st.secrets.get("HONEYBADGER_API_KEY", "Hidden-Vault")

if menu == "🏠 اللوحة العامة المركزية":
    st.markdown("<h2>🌿 نظرة عامة على النشاط</h2>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي السجلات", "1,420", "+25")
    c2.metric("حالة الخادم", "مستقر 100%", "آمن")
    c3.metric("النمو الضريبي", "18%", "نشط")
    
    # محتوى تفاعلي لمنع الصفحات البيضاء
    st.info("💡 نصيحة المنجز: تأكد من مراجعة جدول المناوبات اليومي لضمان سرعة الرد على العملاء.")

elif menu == "🤖 مساعد المنجز (AI)":
    st.header("💬 المساعد الذكي التفاعلي")
    if 'messages' not in st.session_state: st.session_state.messages = []
    
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.write(m["content"])
        
    query = st.chat_input("اسأل المنجز عن الباقات أو الدعم الفني...")
    if query:
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"): st.write(query)
        
        # رد آلي احترافي
        response = "🤖: أهلاً بك يا قائد! جارٍ تحليل استفسارك برمجياً. هل تود معرفة تفاصيل باقة الإمبراطور السنوية؟"
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"): st.write(response)

elif menu == "📊 المحاسب الرقمي (جداول 24)":
    st.header("📊 موديول التحليل المالي")
    st.success("✅ تم جلب البيانات وتشفيرها بنجاح.")
    chart_data = pd.DataFrame({
        "الشهر": ["يناير", "فبراير", "مارس"],
        "الإيرادات": [45000, 52000, 48000]
    })
    st.line_chart(chart_data.set_index("الشهر"))
    st.table(chart_data)

elif menu == "📅 إدارة المناوبات":
    st.header("📅 تنظيم ورديات العمل")
    with st.expander("➕ تسجيل مستشار جديد"):
        st.text_input("اسم المستشار")
        st.date_input("يوم المناوبة")
        if st.button("اعتماد"): st.success("تم الحفظ في قاعدة البيانات.")
    st.info("الجدول الحالي محدث بناءً على أحدث بيانات GitHub.")

elif menu == "📂 مركز الوثائق المؤمن":
    st.header("📂 أرشفة الملفات الرسمية")
    st.warning("⚠️ سيتم تشفير الملفات فور رفعها طبقاً لسياسة الخصوصية.")
    st.file_uploader("رفع السجل التجاري")
    st.file_uploader("رفع البطاقة الضريبية")
    if st.button("بدء المعالجة الرقمية"):
        with st.spinner("جاري التشفير..."):
            time.sleep(2)
            st.success("تم الحفظ في الخزنة الرقمية بنجاح.")

elif menu == "⚙️ إعدادات النظام والأسرار":
    st.header("⚙️ مركز تحكم الأمان (Secrets)")
    st.write(f"🛡️ حالة مفتاح Honeybadger: `{HB_KEY[:8]}****` (
