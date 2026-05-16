import streamlit as st
import os

# 1. إعدادات الصفحة الأساسية
st.set_page_config(
    page_title="منصة مُنجز الذكية",
    page_icon="🚀",
    layout="wide"
)

# 2. العنوان الرئيسي
st.markdown("<h1 style='text-align: center; color: #FF6B35;'>🚀 مرحباً بكم في منصة مُنجز</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #555555;'>نظام الإدارة والخدمات اللوجستية المتكامل لعام 2026</p>", unsafe_allow_html=True)
st.markdown("---")

# 🔍 نظام فحص المسارات التلقائي (لو هناك مشكلة في اسم الملف سيظهر لك هنا فوراً)
st.sidebar.header("📁 فحص ملفات النظام")
pages_dir = os.path.join(os.path.dirname(__file__), "pages")

if os.path.exists(pages_dir):
    st.sidebar.success("✅ مجلد pages موجود")
    st.sidebar.write("الملفات المتاحة حالياً:")
    st.sidebar.json(os.listdir(pages_dir))
else:
    st.sidebar.error("❌ السيرفر لا يرى مجلد pages! تأكد من وجوده في GitHub")

# 3. أزرار الانتقال بأسماء المسارات الصريحة كاملة
st.markdown("<h3 style='text-align: center; color: #1E3A8A;'>اختر القسم الذي تود الدخول إليه:</h3>", unsafe_allow_html=True)
st.write("\n")

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
st.caption("<p style='text-align: center; color: #888888;'>تم التصميم بمنتهى الدقة بواسطة فريق مُنجز التقني</p>", unsafe_allow_html=True)
