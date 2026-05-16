import streamlit as st
import os

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

# الحصول على المسار الحالي للمشروع لضمان التوجيه الصحيح بنسبة 100%
current_dir = os.path.dirname(__file__)

# 3. أزرار الانتقال الذكية باستخدام المسار المباشر المستقر
if st.button("🛒 دخول بوابة العميل", use_container_width=True):
    target_page = os.path.join(current_dir, "pages", "1_العميل.py")
    st.switch_page(target_page)

st.write("\n")

if st.button("🚖 دخول بوابة السائق", use_container_width=True):
    target_page = os.path.join(current_dir, "pages", "2_السائق.py")
    st.switch_page(target_page)

st.write("\n")

if st.button("📊 دخول بوابة المسؤول", use_container_width=True):
    target_page = os.path.join(current_dir, "pages", "3_المسؤول.py")
    st.switch_page(target_page)

# 4. تذييل الصفحة
st.markdown("---")
st.markdown("<p style='text-align: center; color: #888888; font-size: 0.9rem;'>تم التصميم بمنتهى الدقة بواسطة فريق مُنجز التقني</p>", unsafe_allow_html=True)
