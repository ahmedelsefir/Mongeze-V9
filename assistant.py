import streamlit as st
import google.generativeai as genai

# 1. التأسيس الآلي للنظام [cite: 2026-01-13]
st.set_page_config(page_title="منظومة مُنجز الذكية", layout="wide", page_icon="🚀")

# الربط التلقائي بمفتاح API من Secrets لضمان رضا العميل [cite: 2026-01-18]
try:
    if "GOOGLE_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    else:
        st.error("⚠️ مفتاح الاتصال غير موجود في Secrets!")
except Exception as e:
    st.error(f"❌ فشل الاتصال الآلي: {e}")

# 2. إدارة جلسة الدخول
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# 3. بوابة العبور (الدخول المباشر للمطور)
if not st.session_state['logged_in']:
    st.title("🔐 بوابة دخول مُنجز")
    col1, col2 = st.columns(2)
    with col1:
        user = st.text_input("اسم المستخدم")
    with col2:
        pw = st.text_input("كلمة المرور", type='password')
    
    if st.button("دخول للنظام"):
        # المفتاح الموحد للدخول
        if user == "ahmedelsefir" and pw == "123":
            st.session_state['logged_in'] = True
            st.success("تم الاتصال بنجاح.. جاري التحميل")
            st.rerun()
        else:
            st.error("بيانات الدخول غير صحيحة")
else:
    # 4. لوحة التحكم المرنة (سهولة إضافة أي برنامج) [cite: 2026-01-13]
    st.sidebar.title("🎮 لوحة التحكم")
    # لإضافة برنامج جديد، فقط أضف اسمه في القائمة أدناه
    menu = ["🤖 المساعد الذكي", "📊 المحاسب الذكي", "⚙️ الإعدادات"]
    choice = st.sidebar.selectbox("اختر البرنامج المطلوب:", menu)

    # --- موديول المساعد الذكي (Gemini 1.5 Flash - الأكثر استقراراً) ---
    if choice == "🤖 المساعد الذكي":
        st.header("🤖 عقل مُنجز (Gemini V9)")
        st.info("المساعد جاهز للعمل بـ دقة متناهية.")
        
        prompt = st.chat_input("تحدث مع مُنجز...")
        if prompt:
            try:
                # استخدام الموديل الأحدث لتجنب أخطاء NotFound
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                with st.chat_message("assistant"):
                    st.markdown(response.text)
            except Exception as e:
                st.error(f"حدث خطأ في الاتصال بالذكاء الاصطناعي: {e}")

    # --- موديول المحاسب الذكي (قيد التأسيس) ---
    elif choice == "📊 المحاسب الذكي":
        st.header("📊 المحاسب الذكي")
        st.write("سيتم تفعيل معادلات (1.14) و (0.90) هنا بكل دقة.")

    # --- نظام الإعدادات والخروج ---
    elif choice == "⚙️ الإعدادات":
        if st.sidebar.button("تسجيل الخروج"):
            st.session_state['logged_in'] = False
            st.rerun()
