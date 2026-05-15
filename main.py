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
st.subheader("اختر القسم الذي تود الدخول إليه:")
col1, col2, col3 = st.columns(3)

with col1:
    st.info("### 🛒 بوابة العميل")
    if st.button("دخول العميل"):
        st.switch_page("pages/1_العميل.py")

with col2:
    st.success("### 🚕 بوابة السائق")
    if st.button("دخول السائق"):
        st.switch_page("pages/2_السائق.py")

with col3:
    st.warning("### 🏛️ لوحة المسؤول")
    if st.button("دخول المسؤول"):
        st.switch_page("pages/3_المسؤول.py")

st.markdown("---")
st.caption("تم التصميم بواسطة فريق مُنجز التقني")
