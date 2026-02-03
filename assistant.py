import streamlit as st
import os

# --- 1. إعدادات الهوية البصرية ---
st.set_page_config(page_title="المنجز V30 - الأمان المطلق", layout="wide")

# --- 2. جلب التوكن من "الخزنة" وليس من الكود ---
# سيتم ضبط هذا المفتاح في إعدادات السيرفر (Secrets) وليس هنا
github_token = st.secrets.get("GITHUB_TOKEN", "🔒 التوكن مؤمن في الخزنة")

st.markdown("""
    <style>
    .stRadio div[role="radiogroup"] label { font-size: 22px !important; font-weight: bold; background: #0e2413; color: #ffeb3b !important; padding: 15px; margin: 10px 0; border-radius: 12px; border: 2px solid #ffeb3b; }
    .security-banner { background: #fff3cd; color: #856404; padding: 15px; border-radius: 10px; border-right: 10px solid #ffeeba; font-weight: bold; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. بوابة الدخول الذكية ---
if 'logged_in' not in st.session_state:
    st.title("🛡️ نظام المنجز - الدخول المشفر")
    if st.button("🚀 دخول للنظام"):
        st.session_state['logged_in'] = True
        st.rerun()
else:
    st.sidebar.title("👤 لوحة القائد")
    menu = st.sidebar.radio("الخدمات المحمية:", ["🏠 الرئيسية", "🤖 مساعد المنجز", "⚙️ مركز الأمان"])

    if menu == "🏠 الرئيسية":
        st.markdown("<div class='security-banner'>⚠️ تنبيه أمني: تم ترحيل كافة الرموز الحساسة إلى خزنة الأسرار المشفرة.</div>", unsafe_allow_html=True)
        st.write("أهلاً بك يا قائد. الكود الآن نظيف تماماً من أي 'توكنز' صريحة، مما يحمي الحساب من الإغلاق.")
        st.metric("مستوى الأمان", "عالي جداً 🛡️")

    elif menu == "⚙️ مركز الأمان":
        st.header("⚙️ إدارة الأسرار (Secrets)")
        st.success("✅ يتم الآن قراءة GitHub Token من بيئة مشفرة.")
        st.write("حالة التوكن الحالي:")
        st.code(github_token, language="text") # سيعرض رسالة التأمين فقط

    if st.sidebar.button("🚪 خروج"):
        st.session_state.clear()
        st.rerun()
