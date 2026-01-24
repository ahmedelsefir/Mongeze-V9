import streamlit as st
import google.generativeai as genai
import pandas as pd

# 1. الإعدادات الأساسية والربط الآلي
st.set_page_config(page_title="منظومة مُنجز الشاملة", layout="wide", page_icon="🏛️")

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("⚠️ خطأ في مفتاح الاتصال بـ API")

# 2. إدارة جلسة الدخول (بدون تعقيد قاعدة البيانات)
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 بوابة دخول مُنجز الذكية")
    user = st.text_input("اسم المستخدم")
    pw = st.text_input("كلمة المرور", type='password')
    if st.button("دخول للنظام"):
        if user == "ahmedelsefir" and pw == "123":
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("بيانات الدخول غير صحيحة")
else:
    # 3. لوحة التحكم الجانبية (سهولة إضافة برامج أخرى)
    st.sidebar.title("🎮 لوحة تحكم مُنجز")
    menu = ["🤖 المساعد الذكي", "📊 المحاسب الذكي", "📦 إدارة المخازن (قريباً)", "⚙️ الإعدادات"]
    choice = st.sidebar.selectbox("اختر الأداة:", menu)

    # --- أداة 1: المساعد الذكي (اتصال آلي) ---
    if choice == "🤖 المساعد الذكي":
        st.header("🤖 عقل مُنجز الاصطناعي")
        prompt = st.chat_input("اسأل مُنجز عن أي شيء في عملك...")
        if prompt:
            # البحث الآلي عن الموديل الشغال
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            model = genai.GenerativeModel(models[0] if models else 'gemini-1.5-flash')
            response = model.generate_content(prompt)
            with st.chat_message("assistant"):
                st.markdown(response.text)

    # --- أداة 2: المحاسب الذكي (المعادلات الدقيقة) ---
    elif choice == "📊 المحاسب الذكي":
        st.header("📊 المحاسب الذكي (دقة 100%)")
        st.write("أدخل المبلغ لحساب الضريبة (1.14) والخصم (0.90) تلقائياً")
        
        amount = st.number_input("أدخل المبلغ الأساسي:", min_value=0.0, step=1.0)
        
        col1, col2 = st.columns(2)
        with col1:
            taxed = amount * 1.14
            st.metric("المبلغ + الضريبة (1.14)", f"{taxed:,.2f}")
        with col2:
            discounted = amount * 0.90
            st.metric("المبلغ بعد الخصم (0.90)", f"{discounted:,.2f}")

    # --- أداة 3: إدارة المخازن (هيكل جاهز للإضافة) ---
    elif choice == "📦 إدارة المخازن (قريباً)":
        st.info("هذا القسم جاهز لاستقبال بيانات مخازنك وتتبع الجرد آلياً.")

    # --- أداة 4: الإعدادات والخروج ---
    elif choice == "⚙️ الإعدادات":
        st.subheader("إعدادات النظام")
        if st.sidebar.button("تسجيل الخروج"):
            st.session_state['logged_in'] = False
            st.rerun()
