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

# تهيئة الصفحة وحمايتها من التشنج الميكانيكي أثناء التنقل
st.set_page_config(page_title="منصة منجز الذكية", page_icon="🤖", layout="wide")

# ========================================================
# 🔒 معالج حقن وتطهير مفتاح Firebase الـ JSON
# ========================================================
if "firebase_init_success" not in st.session_state:
    st.session_state["firebase_init_success"] = False

try:
    FIREBASE_URL = st.secrets.get("FIREBASE_URL", "https://gen-lang-client-03099029-937be-default-rtdb.firebaseio.com").strip()
    
    # جلب وتنظيف نص المفتاح الحساس لتفادي مشاكل الـ PEM والـ Invalid Key
    raw_json_str = st.secrets["textkey"].strip()
    firebase_credentials = json.loads(raw_json_str)
    
    if "private_key" in firebase_credentials:
        # إصلاح شامل لرموز السطور الجديدة المخفية داخل سيرفرات الاستضافة
        key_block = firebase_credentials["private_key"]
        key_block = key_block.replace("\\\\n", "\n").replace("\\n", "\n").strip()
        firebase_credentials["private_key"] = key_block

    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_credentials)
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_URL})
    st.session_state["firebase_init_success"] = True
except Exception as e:
    st.sidebar.error(f"⚠️ تنبيه نظام الاتصال: {e}")

# ========================================================
# ☁️ محرك الإرسال السحابي الفوري والمباشر (Direct Database HTTP POST)
# ========================================================
def send_data_to_firebase(node, payload_data):
    try:
        base_url = FIREBASE_URL.rstrip('/')
        clean_url = f"{base_url}/{node}.json"
        response = requests.post(clean_url, json=payload_data, timeout=15)
        return response.ok
    except Exception as e:
        st.error(f"❌ عطل في شبكة النقل السحابي: {e}")
        return False

# ========================================================
# 📱 نظام التنقل وإدارة قنوات المنصة
# ========================================================
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "الرئيسية"

def navigate_to(page_name):
    st.session_state["current_page"] = page_name

st.title("🤖 غرفة العمليات المركزية لـ مُنجز")
st.write("نظام إدارة الرحلات والمزايدات الفورية الحية والتحكم المركزي.")

# أزرار شريط التنقل العلوية المستقرة
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

# 1️⃣ الشاشة الرئيسية للسيستم
if st.session_state["current_page"] == "الرئيسية":
    st.markdown("<h3 style='color: #FF5733;'>📡 حالة الاتصال الحالية</h3>", unsafe_allow_html=True)
    if st.session_state["firebase_init_success"]:
        st.success("🔒 الخادم السحابي مربوط بنجاح وجاهز تماماً لاستلام ورفع الطلبات لايف!")
    else:
        st.error("❌ السيستم غير متصل بـ Firebase حالياً. يرجى مراجعة صلاحيات المفتاح الحساس.")

# 2️⃣ بوابة طلبات الطرود (شحن وتوصيل البضائع)
elif st.session_state["current_page"] == "الطرود":
    st.markdown("<h2 style='color: #1E88E5;'>📦 بث شحن الطرود والطلبات التجارية</h2>", unsafe_allow_html=True)
    
    # بناء الاستمارة الميكانيكية المغلقة لضمان عدم تصفير البيانات أثناء النقر
    with st.form(key="parcel_submission_form"):
        customer_name = st.text_input("اسم العميل أو التاجر:", value="أحمد مصطفى")
        item_details = st.text_area("تفاصيل محتوى الطرد والعنوان بدقة:")
        suggested_price = st.number_input("الميزانية المقترحة للتوصيل (ج.م):", min_value=10.0, value=80.0, step=5.0)
        
        # زر الإرسال المدمج داخل الاستمارة إجبارياً
        submit_parcel = st.form_submit_button("🚀 نشر طلب الطرد سحابياً", use_container_width=True)
        
        if submit_parcel:
            if not item_details.strip():
                st.error("⚠️ خطأ ميكانيكي: من فضلك اكتب تفاصيل الطرد أولاً في الخانة المخصصة!")
            else:
                payload = {
                    "service_type": "Parcel",
                    "customer": customer_name,
                    "details": item_details.strip(),
                    "price": suggested_price,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                with st.spinner("جاري الحقن والبث الفوري لقاعدة البيانات..."):
                    if send_data_to_firebase("orders", payload):
                        st.success("🎉 الله ينور يا هندسة! تم إرسال وبث طلب الطرد بنجاح ووصل للـ Firebase حياً!")
                    else:
                        st.error("❌ فشل الإرسال، تحقق من إعدادات الشبكة ومفتاح السيرفر.")

# 3️⃣ بوابة توصيل تاكسي (توصيل الأفراد الفوري 🚕)
elif st.session_state["current_page"] == "التاكسي":
    st.markdown("<h2 style='color: #F1C40F;'>🚕 خدمة طلب تاكسي وتوصيل الأفراد الفوري</h2>", unsafe_allow_html=True)
    
    with st.form(key="taxi_submission_form"):
        passenger_name = st.text_input("اسم الراكب:", value="عميل منجز")
        pickup_location = st.text_input("نقطة الانطلاق (منين؟):")
        dropoff_location = st.text_input("وجهة الوصول (على فين؟):")
        fare_offer = st.number_input("عرض السعر المقترح للرحلة (ج.م):", min_value=20.0, value=230.0, step=10.0)
        
        submit_taxi = st.form_submit_button("🚕 اطلب التاكسي الآن وبث المزايدة", use_container_width=True)
        
        if submit_taxi:
            if not pickup_location.strip() or not dropoff_location.strip():
                st.error("⚠️ خطأ ميكانيكي: من فضلك حدد مكان ومسار الرحلة (الانطلاق والوصول) أولاً!")
            else:
                payload = {
                    "service_type": "Taxi",
                    "customer": passenger_name,
                    "from": pickup_location.strip(),
                    "to": dropoff_location.strip(),
                    "price": fare_offer,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                with st.spinner("جاري بث رحلة التاكسي الحية..."):
                    if send_data_to_firebase("orders", payload):
                        st.success("🎉 ممتاز جداً! تم بث رحلة التاكسي حياً لجميع السائقين في الميدان!")
                    else:
                        st.error("❌ فشل بث الرحلة السحابية.")

# 4️⃣ مركز التنبيهات المركزي للشركة 📢
elif st.session_state["current_page"] == "التنبيهات":
    st.markdown("<h2 style='color: #E67E22;'>📢 مركز إرسال الإشعارات والتعميمات المركزية</h2>", unsafe_allow_html=True)
    
    with st.form(key="alert_submission_form"):
        sender_staff = st.text_input("المسؤول عن البث الإداري:", value="إدارة العمليات")
        notif_target = st.selectbox("الفئة المستهدفة بالتنبيه الفوري:", ["الجميع", "العملاء فقط", "الكباتن فقط"])
        notif_text = st.text_area("نص التنبيه أو التعميم المراد بثه للهواتف:")
        
        submit_alert = st.form_submit_button("📡 بث التنبيه الفوري الآن", use_container_width=True)
        
        if submit_alert:
            if not notif_text.strip():
                st.error("⚠️ لا يمكن بث تنبيه فارغ، برجاء كتابة نص الإشعار أولاً!")
            else:
                notif_payload = {
                    "sender": sender_staff,
                    "target": notif_target,
                    "message": notif_text.strip(),
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                with st.spinner("جاري تعميم البث الإداري..."):
                    if send_data_to_firebase("system_alerts", notif_payload):
                        st.success("📡 تم بث وتعميم التنبيه الإداري بنجاح تام وحفظه في السجل!")
                    else:
                        st.error("❌ فشل في إرسال التنبيه السحابي.")
