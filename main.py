import base64
import html
import json
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from math import asin, cos, radians, sin, sqrt

import pandas as pd
import streamlit as st

# ========================================================
# ⚡ CRITICAL: set_page_config() MUST be the first Streamlit call
# ========================================================
st.set_page_config(page_title="منصة منجز الذكية", page_icon="🤖", layout="wide")

# ========================================================
# 🤖 استيراد عقل مُنجز (AI Agent) مع حماية الدفاع
# ========================================================
try:
    from assistant import ask_mongeze_ai, get_gemini_api_key
except Exception:
    def ask_mongeze_ai(prompt, *args, **kwargs):
        return "⚠️ عقل مُنجز (AI Agent) غير متصل حالياً."

    def get_gemini_api_key():
        return ""

# ========================================================
# 📦 استيراد آمن ومباشر للموديولات من مجلد pages
# ========================================================
try:
    from pages.Client import (
        render_chat_page,
        render_customer_tracking,
        render_parcels_page,
        render_taxi_page,
    )
except Exception:
    def render_chat_page(*args, **kwargs):
        st.info("صفحة الشات غير محملة.")
    def render_customer_tracking(*args, **kwargs):
        pass
    def render_parcels_page(*args, **kwargs):
        st.info("بوابة الطرود غير محملة.")
    def render_taxi_page(*args, **kwargs):
        st.info("خدمة التاكسي غير محملة.")

import firebase_admin
from firebase_admin import credentials, initialize_app, firestore

# ========================================================
# 🌐 قاموس الترجمة الموحد لمنصة منجز الذكية
# ========================================================
LANG_TEXTS = {
    "العربية": {
        "app_title": "🤖 غرفة العمليات المركزية لـ منجز الذكية",
        "btn_monitor": "🏠 شاشة المراقبة",
        "btn_parcels": "📦 بوابة الطرود",
        "btn_taxi": "🚕 توصيل تاكسي",
        "btn_settings": "⚙️ إعدادات التطبيق والملف الشخصي",
    },
    "English": {
        "app_title": "🤖 Mongeze Smart Central Operations Room",
        "btn_monitor": "🏠 Operations Monitor",
        "btn_parcels": "📦 Parcels Portal",
        "btn_taxi": "🚕 Taxi Delivery",
        "btn_settings": "⚙️ Settings & Profile",
    },
}

# ========================================================
# 🤖 إعداد واجهة منصة منجز الذكية وحماية الجلسة
# ========================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SESSION_GUARD_VERSION = "monjez-mobile-session-guard-v5"

def initialize_session_guard():
    protected_keys = {
        "current_page",
        "my_active_order_id",
        "user_name",
        "audio_notifications_enabled",
        "language",
        "driver_verification_status",
        "_session_guard_version",
    }

    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "الرئيسية"
    if "my_active_order_id" not in st.session_state:
        st.session_state["my_active_order_id"] = ""
    if "user_name" not in st.session_state:
        st.session_state["user_name"] = "أحمد مصطفى"
    if "audio_notifications_enabled" not in st.session_state:
        st.session_state["audio_notifications_enabled"] = False
    if "language" not in st.session_state:
        st.session_state["language"] = "العربية"
    if "driver_verification_status" not in st.session_state:
        st.session_state["driver_verification_status"] = "Pending"

    if st.session_state.get("_session_guard_version") != SESSION_GUARD_VERSION:
        for key in list(st.session_state.keys()):
            if key not in protected_keys:
                st.session_state.pop(key, None)
        st.session_state["_session_guard_version"] = SESSION_GUARD_VERSION

initialize_session_guard()

# ========================================================
# 🔒 إعداد الاتصال السحابي بالـ Firebase وتجهيز المخطط
# ========================================================
db = None
try:
    firebase_config = None

    if (
        "textkey" in st.secrets
        and isinstance(st.secrets.get("textkey"), dict)
        and "textkey" in st.secrets.get("textkey")
    ):
        raw_json = st.secrets["textkey"]["textkey"]
        firebase_config = json.loads(raw_json)

    elif "firebase" in st.secrets:
        firebase_config = dict(st.secrets["firebase"])
        if "private_key" in firebase_config and isinstance(
            firebase_config["private_key"], str
        ):
            firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")

    if firebase_config and not firebase_admin._apps:
        cred = credentials.Certificate(firebase_config)
        initialize_app(cred)

    db = firestore.client()

    def initialize_database_schema():
        if db is None:
            return
        user_schema_ref = db.collection("users").document("_schema_template_")
        user_schema_ref.set({
            "uid": "string",
            "name": "string",
            "phone": "string",
            "role": "string",
            "wallet_balance": "number",
            "status": "string",
            "kyc_status": "string",
            "language": "string",
            "audio_notifications": "boolean",
            "created_at": "timestamp"
        }, merge=True)

    initialize_database_schema()

except Exception as e:
    st.error(f"⚠️ خطأ في الاتصال بقاعدة البيانات: {str(e)}")

# ========================================================
# 🛡️ نظام التحقق من الهوية والتوثيق (KYC Engine)
# ========================================================
def check_driver_kyc_status(username):
    try:
        if db is None:
            return False, "DB Not Connected"
        doc_id = str(username).strip().lower()
        user_ref = db.collection("users").document(doc_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            user_ref.set({
                "name": username,
                "role": "driver",
                "kyc_status": "Pending Review",
                "wallet_balance": 0.0,
                "language": "العربية",
                "audio_notifications": True,
                "created_at": firestore.SERVER_TIMESTAMP
            }, merge=True)
            return False, "Pending Review"
            
        data = user_doc.to_dict()
        kyc_status = data.get("kyc_status", "Pending Review")
        
        if kyc_status in ["Verified", "موثق", "active"]:
            return True, kyc_status
        return False, kyc_status
    except Exception:
        return False, "Error Checking"

# ========================================================
# ⚙️ لوحة الإعدادات التقنية والملف الشخصي (مع التحديث الفوري المضمون)
# ========================================================
def render_technical_settings_engine(username):
    st.markdown("---")
    st.subheader("⚙️ لوحة الإعدادات التقنية والملف الشخصي المتقدم")
    
    try:
        if db is None:
            st.error("قاعدة البيانات غير متصلة حالياً.")
            return
            
        doc_id = str(username).strip().lower()
        user_ref = db.collection("users").document(doc_id)
        user_doc = user_ref.get()
        
        user_data = user_doc.to_dict() if user_doc.exists else {
            "language": "العربية",
            "audio_notifications": True,
            "phone": ""
        }
        
        with st.form("tech_settings_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                current_lang = user_data.get("language", "العربية")
                selected_lang = st.selectbox(
                    "🌐 لغة النظام المفضلة (Language):", 
                    ["العربية", "English"], 
                    index=0 if current_lang == "العربية" else 1
                )
                phone_num = st.text_input("📱 رقم الهاتف الرسمي:", value=user_data.get("phone", ""))
                
            with col2:
                audio_enabled = st.checkbox(
                    "🔊 تفعيل التنبيهات الصوتية الفورية للطلبات", 
                    value=user_data.get("audio_notifications", True)
                )
                st.info("🔒 الحساب مؤمن بتقنية الحماية السحابية (Session Guard Active).")
                
            submit_settings = st.form_submit_button("💾 حفظ وتطبيق الإعدادات التقنية")
            
            if submit_settings:
                # استخدام set مع merge=True لضمان الإنشاء الفوري وتفادي خطأ 404 نهائياً
                user_ref.set({
                    "name": username,
                    "language": selected_lang,
                    "phone": phone_num,
                    "audio_notifications": audio_enabled,
                    "updated_at": firestore.SERVER_TIMESTAMP
                }, merge=True)
                
                st.session_state["language"] = selected_lang
                st.session_state["audio_notifications_enabled"] = audio_enabled
                st.success("✅ تم حفظ وتحديث الإعدادات في قاعدة البيانات بنجاح تام!")
                st.rerun()
                
    except Exception as ex:
        st.error(f"⚠️ تعذر حفظ الإعدادات حالياً: {str(ex)}")

# ========================================================
# 🖥️ الشاشة الرئيسية والتحكم بالتدفق والتناغم الكامل
# ========================================================
def main():
    st.sidebar.title("منصة مُنجز الذكية")
    user_role = st.sidebar.selectbox("اختر هويتك:", ["عميل", "سائق", "مسؤول"], key="main_role_select")
    user_name = st.sidebar.text_input("اسم المستخدم:", value=st.session_state.get("user_name", "أحمد مصطفى"))
    st.session_state["user_name"] = user_name

    nav_option = st.sidebar.radio("🧭 التنقل السريع:", ["الخدمات الرئيسية", "⚙️ الإعدادات والملف الشخصي"])

    st.title("🤖 غرفة العمليات المركزية لـ منجز الذكية")
    st.markdown(f"**مرحباً بك يا {user_name}** في النظام السحابي الموحد.")

    if nav_option == "⚙️ الإعدادات والملف الشخصي":
        render_technical_settings_engine(user_name)
        return

    if user_role == "عميل":
        st.info("مرحباً بك في بوابة العملاء للطلبات والتاكسي.")
        render_parcels_page(user_name=user_name)
        
    elif user_role == "سائق":
        st.markdown("### 🚕 لوحة تحكم السائق والمندوب")
        
        is_verified, status_msg = check_driver_kyc_status(user_name)
        
        if not is_verified:
            st.error(f"🚨 **حسابك غير موثق حالياً (الحالة: {status_msg})!** يرجى رفع المستندات المطلوبة أدناه للتفعيل.")
            
            with st.form("driver_kyc_submission_form"):
                st.subheader("📝 مستندات التحقق الإلزامية (KYC)")
                id_num = st.text_input("رقم الهوية الوطنية / الإقامة:")
                drv_lic = st.text_input("رقم رخصة القيادة:")
                veh_lic = st.text_input("رقم رخصة المركبة / اللوحة:")
                
                submitted = st.form_submit_button("💾 إرسال المستندات للاعتماد الفوري")
                if submitted:
                    if id_num and drv_lic and veh_lic:
                        if db is not None:
                            doc_id = str(user_name).strip().lower()
                            db.collection("users").document(doc_id).set({
                                "id_number": id_num,
                                "driving_license": drv_lic,
                                "vehicle_license": veh_lic,
                                "kyc_status": "Under Admin Review",
                                "name": user_name,
                                "role": "driver",
                                "updated_at": firestore.SERVER_TIMESTAMP
                            }, merge=True)
                            st.success("✅ تم إرسال مستندات التحقق بنجاح للاعتماد!")
                            st.rerun()
                    else:
                        st.warning("⚠️ يرجى تعبئة جميع حقول التوثيق المطلوبة.")
            return
            
        else:
            st.success("🌟 **حسابك موثق ومعتمد بنجاح!** يمكنك إدارة إعداداتك بالأسفل.")
            render_technical_settings_engine(user_name)

    else:
        st.info("مرحباً بك في لوحة تحكم المشرفين.")

if __name__ == "__main__":
    main()
