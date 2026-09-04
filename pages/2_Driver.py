import html as html_mod
import requests
import time
from datetime import datetime

# 1️⃣ استيراد Streamlit وتنفيذ تهيئة الصفحة فوراً كأول أمر Streamlit
import streamlit as st

st.set_page_config(
    page_title="منصة مُنجز - بوابة الميدان",
    page_icon="🚚",
    layout="wide",
    initialsidebar_state="expanded"
)

# 2️⃣ الاستيرادات والموديولات الفرعية
import streamlit.components.v1 as components

try:
    from firebase_admin import firestore
except ImportError:
    firestore = None

try:
    from firebase_helpers import init_firestore
except ImportError:
    def init_firestore():
        return None

try:
    from utils import send_monjez_email
except ImportError:
    def send_monjez_email(*args, **kwargs):
        pass

# استيراد آمن لبوابة الدفع لتفادي التعارض أو الأخطاء
try:
    from pages.Payment_Hub import render_payment_hub
except Exception:
    try:
        from Payment_Hub import render_payment_hub  # type: ignore
    except Exception:
        def render_payment_hub(*args, **kwargs):
            st.warning("بوابة الدفع غير متاحة حالياً — يرجى تفعيل صفحة Payment_Hub أو إعداد الأسرار.")
            return None


# --- 3️⃣ الاتصال الآمن بـ Firebase ---
db = init_firestore()
if db is None:
    st.error("❌ فشل اتصال السيرفر مع قاعدة البيانات. يرجى التحقق من إعدادات المفاتيح و Firebase.")


# --- 4️⃣ إدارة حالة الجلسة (Session State) ---
if "user_authenticated" not in st.session_state:
    st.session_state.user_authenticated = False

if "driver_data" not in st.session_state:
    st.session_state.driver_data = {}


# --- 5️⃣ الواجهة الرئيسية لبوابة الميدان ---
def main():
    st.title("🚚 منصة مُنجز - بوابة الميدان")
    st.markdown("---")

    # الشريط الجانبي
    with st.sidebar:
        st.header("📋 القائمة الرئيسية")
        page = st.radio(
            "اختر القسم:",
            ["الرئيسية والمهام", "المحفظة والدفع", "تحديث البيانات", "الدعم الفني"]
        )

    # عرض الصفحات حسب الاختيار
    if page == "الرئيسية والمهام":
        st.subheader("📌 المهام والطلبات الحالية")
        st.info("مرحباً بك في بوابة الميدان! يمكنك متابعة واستلام الطلبات المتاحة حالياً.")
        
        # مؤشرات سريعة
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="الطلبات النشطة", value="0")
        with col2:
            st.metric(label="الطلبات المكتملة اليوم", value="0")
        with col3:
            st.metric(label="إجمالي الأرباح اليوم", value="0 ر.س")

    elif page == "المحفظة والدفع":
        st.subheader("💳 المحفظة والعمليات المالية")
        render_payment_hub()

    elif page == "تحديث البيانات":
        st.subheader("⚙️ إعدادات الحساب والبيانات الشخصية")
        st.write("يمكنك تحديث بيانات المندوب ورقم التواصل هنا.")

    elif page == "الدعم الفني":
        st.subheader("📞 الدعم الفني والمساعدة")
        st.write("إذا واجهتك أي مشكلة، يمكنك التواصل مع فريق دعم منصة مُنجز.")


if __name__ == "__main__":
    main()
