import streamlit as st

# 1. إعدادات الصفحة الأساسية للمنصة
st.set_page_config(
    page_title="منصة مُنجز الذكية",
    page_icon="🚀",
    layout="wide"
)

# 2. تصميم واجهة العنوان الرئيسية والألوان الاحترافية
st.markdown("<h1 style='text-align: center; color: #FF6B35;'>🚀 مرحباً بكم في منصة مُنجز</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #555555;'>نظام الإدارة والخدمات اللوجستية المتكامل لعام 2026</p>", unsafe_allow_html=True)
st.markdown("---")

st.markdown("<h3 style='text-align: center; color: #1E3A8A;'>اختر القسم الذي تود الدخول إليه:</h3>", unsafe_allow_html=True)
st.write("\n")

# 3. أزرار الانتقال القياسية (الآن السيرفر سيتعرف عليها تلقائياً فوراً)
if st.button("🛒 دخول بوابة العميل", use_container_width=True):
    st.switch_page("pages/1_Client.py")

st.write("\n")

if st.button("🚖 دخول بوابة السائق", use_container_width=True):
    st.switch_page("pages/2_Driver.py")

st.write("\n")

if st.button("📊 دخول بوابة المسؤول", use_container_width=True):
    st.switch_page("pages/3_Admin.py")

# 4. تذييل الصفحة
st.markdown("---")
st.markdown("<p style='text-align: center; color: #888888; font-size: 0.9rem;'>تم التصميم بمنتهى الدقة بواسطة فريق مُنجز التقني</p>", unsafe_allow_html=True)
