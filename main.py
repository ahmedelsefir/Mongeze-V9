import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
import requests
import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials
from datetime import datetime

st.set_page_config(page_title="منصة منجز الذكية", page_icon="🤖", layout="wide")

# ========================================================
# 🔒 المعالج الميكانيكي المطور لتثبيت وحقن مفتاح JSON
# ========================================================
try:
    FIREBASE_URL = st.secrets.get("FIREBASE_URL", "https://gen-lang-client-03099029-937be-default-rtdb.firebaseio.com")
    raw_json_str = st.secrets["textkey"].strip()
    firebase_credentials = json.loads(raw_json_str)
    
    if "private_key" in firebase_credentials:
        key_block = firebase_credentials["private_key"]
        key_block = key_block.replace("\\\\n", "\n").replace("\\n", "\n").strip()
        firebase_credentials["private_key"] = key_block

    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_credentials)
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_URL})
    st.sidebar.success("⚡ تم التفعيل السحابي بنجاح ميكانيكي كامل!")
except Exception as e:
    st.sidebar.error(f"⚠️ خطأ الارتباط المؤقت بقاعدة البيانات: {e}")

# جلب إعدادات السيرفر
try:
    ZOHO_WEBHOOK_URL = st.secrets["zoho"]["ZOHO_WEBHOOK_URL"]
    SYSTEM_SMTP_SERVER = st.secrets["smtp"]["server"]
    SYSTEM_SMTP_PORT = int(st.secrets["smtp"]["port"])
    SYSTEM_SMTP_USER = st.secrets["smtp"]["user"]
    SYSTEM_SMTP_PASS = st.secrets["smtp"]["pass"].strip()
except Exception:
    ZOHO_WEBHOOK_URL = ""
    SYSTEM_SMTP_SERVER = "smtp.gmail.com"
    SYSTEM_SMTP_PORT = 587
    SYSTEM_SMTP_USER = ""
    SYSTEM_SMTP_PASS = ""

# ========================================================
# ☁️ دوال المزامنة السحابية للطلبات والإشعارات
# ========================================================
def save_to_firebase(node, data):
    try:
        response = requests.post(f"{FIREBASE_URL}/{node}.json", json=data)
        return response.ok
    except Exception:
        return False

def load_from_firebase(node):
    try:
        response = requests.get(f"{FIREBASE_URL}/{node}.json")
        if response.ok and response.json():
            raw_data = response.json()
            if isinstance(raw_data, dict):
                return list(raw_data.values())
            elif isinstance(raw_data, list):
                return [item for item in raw_data if item is not None]
        return []
    except Exception:
        return []

# ========================================================
# 📱 إدارة التحكم المركزي والتنقل بين قنوات المنصة
# ========================================================
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "الرئيسية"

def navigate_to(page_name):
    st.session_state["current_page"] = page_name

st.title("🤖 مركز الرقابة وغرفة العمليات المركزية لـ مُنجز")
st.write("نظام إدارة الرحلات، الأتمتة المالية، والإشعارات الموجهة.")

# شريط التنقل العلوي الموسع
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    if st.button("🏠 الشاشة الرئيسية", use_container_width=True): navigate_to("الرئيسية")
with col2:
    if st.button("📦 طلبات الطرود", use_container_width=True): navigate_to("الطرود")
with col3:
    if st.button("🚕 توصيل تاكسي", use_container_width=True): navigate_to("التاكسي")
with col4:
    if st.button("📢 مركز التنبيهات", use_container_width=True): navigate_to("التنبيهات")
with col5:
    if st.button("📊 النظام المالي", use_container_width=True): navigate_to("المالي")

st.write("---")

# 1️⃣ الشاشة الرئيسية
if st.session_state["current_page"] == "الرئيسية":
    st.markdown("<h3 style='color: #FF5733;'>🧪 حالة قنوات الاتصال الفورية</h3>", unsafe_allow_html=True)
    st.info("جميع الأنظمة متصلة ومستقرة تماماً وجاهزة لاستقبال البيانات الحية وضبط المزايدات.")

# 2️⃣ بوابة طلبات الطرود (شحن البضائع)
elif st.session_state["current_page"] == "الطرود":
    st.markdown("<h2 style='color: #1E88E5;'>📦 بوابة شحن الطرود والطلبات التجارية</h2>", unsafe_allow_html=True)
    customer_name = st.text_input("اسم العميل أو التاجر:", value="أحمد مصطفى")
    item_details = st.text_input("تفاصيل محتوى الطرد (مثلاً: ملابس، إلكترونيات):")
    suggested_price = st.number_input("الميزانية المقترحة للتوصيل (ج.م):", min_value=10.0, value=40.0)
    
    if st.button("🚀 نشر طلب الطرد سحابياً", use_container_width=True):
        payload = {
            "service_type": "Parcel",
            "customer": customer_name,
            "details": item_details,
            "price": suggested_price,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        if save_to_firebase("orders", payload):
            st.success("🔒 تم نشر طلب الشحن بنجاح وجاري إخطار مناديب الشحن!")

# 3️⃣ بوابة توصيل تاكسي (توصيل الأفراد الجديد 🚕)
elif st.session_state["current_page"] == "التاكسي":
    st.markdown("<h2 style='color: #F1C40F;'>🚕 خدمة طلب تاكسي وتوصيل الأفراد الفوري</h2>", unsafe_allow_html=True)
    passenger_name = st.text_input("اسم الراكب:", value="عميل منجز")
    pickup_location = st.text_input("نقطة الانطلاق (منين؟):")
    dropoff_location = st.text_input("وجهة الوصول (على فين؟):")
    fare_offer = st.number_input("عرض السعر المقترح للرحلة (ج.م):", min_value=20.0, value=50.0)
    
    if st.button("🚀 اطلب التاكسي الآن وبث المزايدة", use_container_width=True):
        payload = {
            "service_type": "Taxi",
            "customer": passenger_name,
            "from": pickup_location,
            "to": dropoff_location,
            "price": fare_offer,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        if save_to_firebase("orders", payload):
            st.success("🚕 تم بث رحلة التاكسي حياً لجميع السائقين القريبين منك!")

# 4️⃣ مركز التنبيهات المطور (الذي يشرف عليه الموظفون 📢)
elif st.session_state["current_page"] == "التنبيهات":
    st.markdown("<h2 style='color: #E67E22;'>📢 غُرفة التحكم وإرسال الإشعارات المركزية</h2>", unsafe_allow_html=True)
    
    # نموذج لإرسال تنبيه جديد بواسطة موظفي الشركة
    st.markdown("### ✍️ بث تنبيه عام جديد للمنصة")
    sender_staff = st.text_input("اسم الموظف المسؤول عن البث:", value="إدارة العمليات")
    notif_target = st.selectbox("الفئة المستهدفة بالتنبيه:", ["الجميع", "العملاء فقط", "الكباتن والسائقين فقط"])
    notif_text = st.text_area("نص التنبيه أو التعميم الإداري:")
    
    if st.button("📡 بث التنبيه الفوري لكل الهواتف والقنوات", use_container_width=True):
        notif_payload = {
            "sender": sender_staff,
            "target": notif_target,
            "message": notif_text,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        if save_to_firebase("system_alerts", notif_payload):
            st.success(f"🎉 تم بث التنبيه بنجاح إلى فئة: ({notif_target}) وتم حفظه في السجل الرسمي.")
            
    st.write("---")
    st.markdown("### 📜 السجل التاريخي للتنبيهات الصادرة")
    all_alerts = load_from_firebase("system_alerts")
    if all_alerts:
        for alert in reversed(all_alerts):
            st.info(f"🔔 **[{alert.get('target')}]** من: {alert.get('sender')} ({alert.get('time')})\n\n{alert.get('message')}")
    else:
        st.write("لا توجد تنبيهات صادرة حتى الآن.")

# 5️⃣ النظام المالي
elif st.session_state["current_page"] == "الالمالي" or st.session_state["current_page"] == "المالي":
    st.markdown("<h2 style='color: #9C27B0;'>📊 الهيكل المحاسبي المركزي</h2>", unsafe_allow_html=True)
    st.write("التقارير المالية والتحصيلات الضريبية تعمل بأتمتة كاملة ومربوطة بالخادم الحركي لـ Firebase.")
