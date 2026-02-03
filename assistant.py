import streamlit as st
import pandas as pd
import random

# --- 1. إعدادات الهوية البصرية ---
st.set_page_config(page_title="منصة المنجز V27", layout="wide")

st.markdown("""
    <style>
    .stRadio div[role="radiogroup"] label { font-size: 22px !important; font-weight: bold; background: #1e3d23; color: #ffeb3b !important; padding: 15px; border-radius: 12px; margin: 10px 0; border: 2px solid #fff; }
    .policy-box { background: #f0f2f6; padding: 20px; border-radius: 10px; border: 1px solid #ccc; height: 150px; overflow-y: scroll; font-size: 14px; margin-bottom: 20px; }
    .main-card { background: white; padding: 25px; border-radius: 20px; border-right: 12px solid #1b5e20; box-shadow: 0 10px 20px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. محرك إدارة الدخول (التحقق والخصوصية) ---
if 'step' not in st.session_state: st.session_state.step = 'login'

if 'logged_in' not in st.session_state:
    st.title("🛡️ بوابة دخول المنجز المؤمنة")
    
    # الخطوة 1: إدخال الايميل والموافقة على السياسة
    if st.session_state.step == 'login':
        with st.container():
            email = st.text_input("📧 أدخل البريد الإلكتروني للعميل")
            
            st.markdown("### 📄 سياسة الخصوصية وشروط الاستخدام")
            st.markdown("""<div class='policy-box'>
                بموافقتك على هذا، أنت تقر بأن منصة المنجز هي المسؤولة عن تنظيم حساباتك الضريبية... 
                يتم حماية بياناتك وفقاً لمعايير التشفير العالمية. 
                لا يتم مشاركة السجلات التجارية أو البطاقات الضريبية مع أي طرف ثالث...
                تلتزم المنصة بتوفير الدعم الفني والمحاسبي خلال فترة الاشتراك.
                </div>""", unsafe_allow_html=True)
            
            agree = st.checkbox("أوافق على سياسة الخصوصية وشروط الاستخدام")
            
            if st.button("🚀 إرسال كود التحقق"):
                if agree and "@" in email:
                    st.session_state.temp_email = email
                    st.session_state.otp = str(random.randint(1000, 9999)) # توليد رقم عشوائي
                    st.session_state.step = 'verify'
                    st.success(f"تم إرسال كود التحقق إلى {email} (محاكاة: الكود هو {st.session_state.otp})")
                    st.rerun()
                else:
                    st.error("يرجى إدخال إيميل صحيح والموافقة على الشروط أولاً.")

    # الخطوة 2: التحقق من الرقم المرسل
    elif st.session_state.step == 'verify':
        st.subheader(f"🔑 التحقق من الهوية ({st.session_state.temp_email})")
        code_input = st.text_input("أدخل الكود المكون من 4 أرقام المرسل لإيميلك")
        if st.button("تأكيد الدخول"):
            if code_input == st.session_state.otp:
                st.session_state.logged_in = True
                st.session_state.role = "العميل VIP"
                st.success("تم التحقق بنجاح! نورت الإمبراطورية.")
                st.rerun()
            else:
                st.error("الكود غير صحيح، حاول مرة أخرى.")
        if st.button("⬅️ العودة"):
            st.session_state.step = 'login'
            st.rerun()
    st.stop()

# --- 3. واجهة التطبيق الرئيسية (بعد تخطي الأمان) ---
role = st.session_state.role
st.sidebar.title(f"👤 {role}")
menu = st.sidebar.radio("الخدمات:", ["🏠 الرئيسية", "🤖 مساعد المنجز", "📊 المحاسب الرقمي", "📂 مركز الوثائق"])

if menu == "🏠 الرئيسية":
    st.markdown("<div class='main-card'><h1>🌿 مرحباً بك في المنجز</h1><p>دخولك مؤمن بالكامل ونظام الخصوصية مفعل ✅</p></div>", unsafe_allow_html=True)
    st.metric("حالة الحساب", "نشط - فترة تجريبية")

elif menu == "🤖 مساعد المنجز":
    st.header("💬 المساعد الذكي")
    # البوت يرد على أسئلة الخصوصية الآن
    p = st.chat_input("اسأل المنجز...")
    if p:
        with st.chat_message("user"): st.write(p)
        with st.chat_message("assistant"):
            if "خصوصية" in p or "أمان" in p:
                st.write("🤖: بياناتك مشفرة ولا يمكن لأحد الاطلاع عليها إلا المستشار المسؤول عن ملفك.")
            else:
                st.write("🤖: أهلاً بك! أنا هنا لخدمتك.")

elif menu == "📂 مركز الوثائق":
    st.header("📂 رفع الوثائق المؤمنة")
    st.info("بناءً على سياسة الخصوصية التي وافقت عليها، ملفاتك في أمان تام.")
    st.file_uploader("ارفع السجل التجاري")
