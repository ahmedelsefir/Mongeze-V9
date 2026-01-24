import streamlit as st
import google.generativeai as genai

# 1. إعدادات الأمان والذكاء الاصطناعي [cite: 2026-01-13]
st.set_page_config(page_title="منظومة مُنجز الذكية", layout="wide")

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("فشل في قراءة مفتاح الـ API. تأكد من إعداده في Secrets.")

# 2. نظام إدارة الجلسة (Session State)
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# 3. بوابة الدخول
if not st.session_state['logged_in']:
    st.title("🔐 بوابة دخول مُنجز")
    user = st.text_input("اسم المستخدم")
    pw = st.text_input("كلمة المرور", type='password')
    if st.button("دخول للنظام"):
        if user == "ahmedelsefir" and pw == "123":
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("بيانات الدخول غير صحيحة")
else:
    # 4. القائمة الجانبية (هنا نضيف البرامج الجديدة بكل سهولة) [cite: 2026-01-18]
    st.sidebar.header("🕹️ لوحة التحكم")
    apps = ["🤖 المساعد الذكي", "📊 المحاسب الذكي", "⚙️ الإعدادات"]
    # ملاحظة: يمكنك مستقبلاً إضافة "📦 إدارة المخازن" أو "👥 شؤون الموظفين" للقائمة أعلاه
    
    choice = st.sidebar.selectbox("اختر البرنامج:", apps)

    # --- موديول المساعد الذكي ---
    if choice == "🤖 المساعد الذكي":
        st.subheader("عقل مُنجز الاصطناعي")
        prompt = st.chat_input("اسأل مُنجز...")
        if prompt:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            st.write(response.text)

    # --- موديول المحاسب الذكي ---
    elif choice == "📊 المحاسب الذكي":
        st.subheader("النظام المحاسبي الدقيق")
        st.write("هنا سنقوم ببرمجة معادلات الـ 1.14 والـ 0.90 التي طلبتها.")

    # --- موديول الإعدادات (أو أي برنامج جديد) ---
    elif choice == "⚙️ الإعدادات":
        st.subheader("إعدادات المنظومة")
        if st.sidebar.button("تسجيل الخروج"):
            st.session_state['logged_in'] = False
            st.rerun()
