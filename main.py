import streamlit as st

# إعدادات الصفحة الأساسية
st.set_page_config(
    page_title="منصة مُنجز الذكية",
    page_icon="🚀",
    layout="wide"
)

# عنوان الواجهة الرئيسية
st.markdown("<h1 style='text-align: center; color: #FF6B35;'>🚀 مرحباً بكم في منصة مُنجز</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2rem;'>نظام الإدارة والخدمات اللوجستية المتكامل لعام 2026</p>", unsafe_allow_html=True)
st.markdown("---")

# تقسيم الشاشة لأزرار دخول سريعة
if st.button("🛒 دخول العميل", use_container_width=True):
    st.switch_page("pages/1_Client.py")

if st.button("🚖 دخول السائق", use_container_width=True):
    st.switch_page("pages/2_Driver.py")

if st.button("📊 بوابة المسؤول", use_container_width=True):
    st.switch_page("pages/3_Admin.py")

st.markdown("---")
st.caption("تم التصميم بواسطة فريق مُنجز التقني")
