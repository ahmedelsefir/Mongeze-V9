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

# إعداد الصفحة وتأمين واجهة الاستخدام من التشنج الميكانيكي
st.set_page_config(page_title="منصة منجز الذكية", page_icon="🤖", layout="wide")

# ========================================================
# 🔒 معالج حقن مفتاح JSON وتطهيره تلقائياً
# ========================================================
if "firebase_init_success" not in st.session_state:
    st.session_state["firebase_init_success"] = False

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
    st.session_state["firebase_init_success"] = True
except Exception as e:
    st.sidebar.error(f"⚠️ اتصال محلي مؤقت: {e}")

# ========================================================
# ☁️ محرك الإرسال المباشر لمنع تجمد السيرفر (Direct HTTP POST)
# ========================================================
def send_data_to_firebase(node, payload_data):
    try:
        # إرسال مباشر عبر بروتوكول HTTP لتفادي مشاكل الـ inotify watch
        clean_url = f"{FIREBASE_URL.rstrip('/')}/{node}.json"
        response = requests.post(clean_url, json=payload_data, timeout=10)
        return response.ok
    except Exception as e:
        st.error(f"❌ عطل في شبكة النقل السحابي: {e}")
        return False

# ========================================================
# 📱 إدارة غرف التحكم والصفحات
# ========================================================
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "الرئيسية"

def navigate_to(page_name):
    st.session_state["current_page"] = page_name

st.title("🤖 غرفة العمليات المركزية لـ مُنجز")
st.write("نظام إدارة الرحلات والمزايدات الفورية الحية.")

# أزرار التنقل العلوية المستقرة
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🏠 القائمة الرئيسية", use_container_width=True): navigate_to("الرئيسية")
with col2:
    if st.button("📦 طلبات الطرود", use_container_width=True): navigate_to("الطرود")
with col3:
    if st.button("🚕 توصيل تاكسي", use_container_width=True): navigate_to("التاكسي")
with col4:
    if st.button("📢 مركز التنبيهات", use_container_width=True): navigate_to("التنبيهات")

st.write("---")

# 1️⃣ القائمة الرئيسية
if st.session_state["current_page"] == "الرئيسية":
    st.markdown("<h3 style='color: #FF5733;'>🧪 حالة الاتصال الحالية</h3>", unsafe_allow_html=True)
    if st.session_state["firebase_init_success"]:
        st.success("🔒 الخادم السحابي مربوط وجاهز تماماً لاستلام الطلبات الآن!")
    else:
        st.warning("⚠️ النظام يعمل في بيئة النقل المباشر لتجنب أحمال السيرفر.")

# 2️⃣ بوابة طلبات الطرود
elif st.session_state["current_page"] == "الطرود":
    st.markdown("<h2 style='color: #1E88E5;'>📦 بث شحن الطرود والطلبات التجارية</h2>", unsafe_allow_html=True)
    
    with st.form(key="parcel_form", clear_on_submit=True):
        customer_name = st.text_input("اسم العميل أو التاجر:", value="أحمد مصطفى")
        item_details = st.text_area("تفاصيل محتوى الطرد والعنوان بدقة:")
        suggested_price = st.number_input("الميزانية المقترحة للتوصيل (ج.م):", min_value=10.0, value=80.0)
        submit_parcel = st.form_submit_with_repr = st.form_submit_button("🚀 نشر طلب الطرد سحابياً", use_container_width=True)
        
        if submit_parcel:
            if item_details.strip() == "":
                st.error("⚠️ من فضلك اكتب تفاصيل الطرد أولاً!")
            else:
                payload = {
                    "service_type": "Parcel",
                    "customer": customer_name,
                    "details": item_details,
                    "price": suggested_price,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                with st.spinner("جاري الحقن والبث الفوري..."):
                    if send_data_to_firebase("orders", payload):
                        st.success("🎉 ممتاز يا هندسة! تم إرسال وبث طلب الطرد بنجاح إلى Firebase!")
                    else:
                        st.error("❌ فشل الإرسال، تحقق من اتصال السيرفر.")

# 3️⃣ بوابة توصيل تاكسي
elif st.session_state["current_page"] == "التاكسي":
    st.markdown("<h2 style='color: #F1C40F;'>🚕 طلب تاكسي وتوصيل الأفراد الفوري</h2>", unsafe_allow_html=True)
    
    with st.form(key="taxi_form", clear_on_submit=True):
        passenger_name = st.text_input("اسم الراكب:", value="عميل منجز")
        pickup_location = st.text_input("نقطة الانطلاق (منين؟):")
        dropoff_location = st.text_input("وجهة الوصول (على فين؟):")
        fare_offer = st.number_input("عرض السعر المقترح للرحلة (ج.م):", min_value=20.0, value=230.0)
        submit_taxi = st.form_submit_button("🚕 اطلب التاكسي الآن وبث المزايدة", use_container_width=True)
        
        if submit_taxi:
            if pickup_location.strip() == "" or dropoff_location.strip() == "":
                st.error("⚠️ من فضلك حدد مكان الانطلاق والوصول أولاً!")
            else:
                payload = {
                    "service_type": "Taxi",
                    "customer": passenger_name,
                    "from": pickup_location,
                    "to": dropoff_location,
                    "price": fare_offer,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                with st.spinner("جاري بث رحلة التاكسي..."):
                    if send_data_to_firebase("orders", payload):
                        st.success("🎉 الله ينور! تم بث رحلة التاكسي حياً ووصلت لقاعدة البيانات فوراً!")
                    else:
                        st.error("❌ فشل بث الرحلة.")

# 4️⃣ مركز التنبيهات
elif st.session_state["current_page"] == "التنبيهات":
    st.markdown("<h2 style='color: #E67E22;'>📢 مركز إرسال الإشعارات المركزية</h2>", unsafe_allow_html=True)
    with st.form(key="alert_form", clear_on_submit=True):
        sender_staff = st.text_input("المسؤول عن البث:", value="إدارة العمليات")
        notif_target = st.selectbox("الفئة المستهدفة:", ["الجميع", "العملاء فقط", "الكباتن فقط"])
        notif_text = st.text_area("نص التنبيه الإداري:")
        submit_alert = st.form_submit_button("📡 بث التنبيه الفوري", use_container_width=True)
        
        if submit_alert:
            if notif_text.strip() == "":
                st.error("⚠️ لا يمكن بث تنبيه فارغ!")
            else:
                notif_payload = {
                    "sender": sender_staff,
                    "target": notif_target,
                    "message": notif_text,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                if send_data_to_firebase("system_alerts", notif_payload):
                    st.success("📡 تم بث وتعميم التنبيه بنجاح!")
