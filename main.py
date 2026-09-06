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
    from pages.Admin import (
        render_admin_kyc_console,
        render_admin_tracking,
        render_commission_engine,
    )
except Exception:
    try:
        from Admin import (
            render_admin_kyc_console,
            render_admin_tracking,
            render_commission_engine,
        )
    except Exception:

        def render_admin_kyc_console(*args, **kwargs):
            st.info("لوحة تحكم المشرف غير متاحة في هذا السياق.")

        def render_admin_tracking(*args, **kwargs):
            pass

        def render_commission_engine(*args, **kwargs):
            pass


try:
    from pages.Client import (
        render_chat_page,
        render_customer_tracking,
        render_parcels_page,
        render_taxi_page,
    )
except Exception:
    try:
        from Client import (
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


try:
    from pages.Driver import (
        render_driver_kyc_tab,
        render_driver_settings_tab,
        render_wallet_topup,
    )
except Exception:
    try:
        from Driver import (
            render_driver_kyc_tab,
            render_driver_settings_tab,
            render_wallet_topup,
        )
    except Exception:

        def render_driver_kyc_tab(*args, **kwargs):
            pass

        def render_driver_settings_tab(*args, **kwargs):
            pass

        def render_wallet_topup(*args, **kwargs):
            pass


import firebase_admin

try:
    from firebase_helpers import (
        delete_firebase_node,
        fetch_firebase_dict,
        fetch_from_firebase,
        firebase_request,
        get_current_timestamp,
        init_firebase_admin,
        sanitize_username,
        send_to_firebase,
        update_firebase_node,
    )
except Exception:
    def delete_firebase_node(*args, **kwargs):
        pass

    def fetch_firebase_dict(*args, **kwargs):
        return {}

    def fetch_from_firebase(*args, **kwargs):
        return None

    def firebase_request(*args, **kwargs):
        return None

    def get_current_timestamp(*args, **kwargs):
        return 0

    def init_firebase_admin(*args, **kwargs):
        return None

    def sanitize_username(name):
        return str(name).strip().lower()

    def send_to_firebase(*args, **kwargs):
        pass

    def update_firebase_node(*args, **kwargs):
        pass


try:
    from paymob import initiate_wallet_topup
except Exception:

    def initiate_wallet_topup(*args, **kwargs):
        return None


try:
    import Policies
    from Policies import (
        render_privacy_policy,
        render_privacy_policy_brief,
        render_support_contact,
        render_terms_of_use,
    )
except Exception:

    def render_privacy_policy(*args, **kwargs):
        st.write("سياسة الخصوصية غير متاحة.")

    def render_privacy_policy_brief(*args, **kwargs):
        pass

    def render_support_contact(*args, **kwargs):
        st.write("الدعم الفني غير متاح.")

    def render_terms_of_use(*args, **kwargs):
        pass


try:
    from pages.Payment_Hub import render_payment_hub
except Exception:
    try:
        from Payment_Hub import render_payment_hub
    except Exception:

        def render_payment_hub(*args, **kwargs):
            st.warning("بوابة الدفع غير متاحة حالياً.")
            return None


# ========================================================
# 🌐 قاموس الترجمة الموحد لمنصة منجز الذكية
# ========================================================
LANG_TEXTS = {
    "العربية": {
        "app_title": "🤖 غرفة العمليات المركزية لـ منجز الذكية",
        "api_caption": "🔗 خط اتصال الدومين النشط حالياً:",
        "btn_monitor": "🏠 شاشة المراقبة",
        "btn_parcels": "📦 بوابة الطرود",
        "btn_taxi": "🚕 توصيل تاكسي",
        "btn_ai": "🤖 عقل مُنجز (AI)",
        "btn_chat": "💬 شات منجز الخاص 🟢",
        "btn_tracking": "🛰️ رادار التتبع والاتصال السحابي المباشر",
        "btn_settings": "⚙️ إعدادات التطبيق والملف الشخصي",
    },
    "English": {
        "app_title": "🤖 Mongeze Smart Central Operations Room",
        "api_caption": "🔗 Active Live Domain Connection:",
        "btn_monitor": "🏠 Operations Monitor",
        "btn_parcels": "📦 Parcels Portal",
        "btn_taxi": "🚕 Taxi Delivery",
        "btn_ai": "🤖 Mongeze AI Agent",
        "btn_chat": "💬 Private Mongeze Chat 🟢",
        "btn_tracking": "🛰️ Live Tracking Radar",
        "btn_settings": "⚙️ Settings & Profile",
    },
}

# ========================================================
# 🤖 إعداد واجهة منصة منجز الذكية وحماية الجلسة
# ========================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE_URL = os.environ.get("API_BASE_URL", "https://monjez-app.icu")
SESSION_GUARD_VERSION = "monjez-mobile-session-guard-v3"


def initialize_session_guard():
    protected_keys = {
        "current_page",
        "my_active_order_id",
        "user_name",
        "audio_notifications_enabled",
        "language",
        "driver_verification_status",
        "ai_messages",
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
    if "ai_messages" not in st.session_state:
        st.session_state["ai_messages"] = []

    if st.session_state.get("_session_guard_version") != SESSION_GUARD_VERSION:
        for key in list(st.session_state.keys()):
            if key not in protected_keys:
                st.session_state.pop(key, None)
        st.session_state["_session_guard_version"] = SESSION_GUARD_VERSION


initialize_session_guard()

# ========================================================
# 🔒 إعداد الاتصال السحابي بالـ Firebase + هيكل الـ KYC والـ Triggers
# ========================================================
try:
    firebase_config = None

    if (
        "textkey" in st.secrets
        and isinstance(st.secrets.get("textkey"), dict)
        and "textkey" in st.secrets.get("textkey")
    ):
        try:
            raw_json = st.secrets["textkey"]["textkey"]
            firebase_config = json.loads(raw_json)
            st.success("✅ تم العثور على المفتاح بنجاح عبر [textkey]!")
        except Exception as ex:
            st.error("❌ فشل تحليل JSON داخل [textkey].")
            st.exception(ex)

    elif "firebase" in st.secrets:
        firebase_config = dict(st.secrets["firebase"])
        if "private_key" in firebase_config and isinstance(
            firebase_config["private_key"], str
        ):
            firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")
        st.success("✅ تم العثور على المفتاح بنجاح عبر [firebase]!")

    else:
        st.error("❌ عذراً، لم يتم العثور على بيانات الاعتماد في الـ Secrets!")

    if firebase_config and not firebase_admin._apps:
        from firebase_admin import credentials, initialize_app, firestore
        cred = credentials.Certificate(firebase_config)
        initialize_app(cred)
        st.success("🔥 تم ربط Firebase بنجاح تام!")

        db = firestore.client()

        def initialize_database_schema():
            print("جاري تهيئة الهيكل الخرساني لقاعدة البيانات والإعدادات...")
            user_schema_ref = db.collection("users").document("_schema_template_")
            user_schema_ref.set({
                "uid": "string",
                "name": "string",
                "phone": "string",
                "role": "string (client, driver, admin)",
                "wallet_balance": "number",
                "status": "string",
                "kyc_status": "string",
                "language": "string (العربية, English)",
                "audio_notifications": "boolean",
                "created_at": "timestamp"
            }, merge=True)

            order_schema_ref = db.collection("orders").document("_schema_template_")
            order_schema_ref.set({
                "order_id": "string",
                "client_id": "string",
                "driver_id": "string",
                "service_type": "string",
                "suggested_price": "number",
                "status": "string",
                "timestamp": "timestamp"
            }, merge=True)

        def process_completed_order_trigger(order_id):
            order_ref = db.collection("orders").document(order_id)
            order_doc = order_ref.get()
            if not order_doc.exists:
                return False
            order_data = order_doc.to_dict()
            if order_data.get("status") == "completed" and order_data.get("driver_id"):
                driver_ref = db.collection("users").document(order_data.get("driver_id"))
                price = order_data.get("suggested_price", 0)
                driver_net_earnings = price - (price * 0.10)
                db.run_transaction(lambda transaction: update_driver_wallet(transaction, driver_ref, driver_net_earnings))
                return True
            return False

        @firestore.transactional
        def update_driver_wallet(transaction, driver_ref, earnings):
            driver_snapshot = driver_ref.get(transaction=transaction)
            if driver_snapshot.exists:
                current_balance = driver_snapshot.to_dict().get("wallet_balance", 0.0)
                transaction.update(driver_ref, {"wallet_balance": current_balance + earnings})

        initialize_database_schema()

except Exception as e:
    st.error("⚠️ حدث خطأ أثناء تحليل المفتاح أو تهيئة القاعدة:")
    st.exception(e)


# ========================================================
# 🛡️ نظام حماية والتحقق من الهوية (KYC Guard)
# ========================================================
def check_driver_kyc_status(username):
    try:
        db = firestore.client()
        user_ref = db.collection("users").document(str(username).strip().lower())
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            user_ref.set({
                "name": username,
                "role": "driver",
                "kyc_status": "Pending Review",
                "wallet_balance": 0.0,
                "language": "العربية",
                "audio_notifications": True
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
# ⚙️ دالة إدارة الإعدادات التقنية والملف الشخصي المتكاملة
# ========================================================
def render_technical_settings_engine(username):
    st.markdown("---")
    st.subheader("⚙️ لوحة الإعدادات التقنية والملف الشخصي المتقدم")
    
    try:
        db = firestore.client()
        user_ref = db.collection("users").document(str(username).strip().lower())
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
                user_ref.update({
                    "language": selected_lang,
                    "phone": phone_num,
                    "audio_notifications": audio_enabled
                })
                st.session_state["language"] = selected_lang
                st.session_state["audio_notifications_enabled"] = audio_enabled
                st.success("✅ تم تحديث إعدادات التطبيق وحفظها في قاعدة البيانات بنجاح!")
                st.rerun()
                
    except Exception as ex:
        st.error(f"⚠️ تعذر تحميل الإعدادات التقنية حالياً: {str(ex)}")


# ========================================================
# 🖥️ الشاشة الرئيسية والتحكم بالتدفق
# ========================================================
def main():
    st.sidebar.title("منصة مُنجز الذكية")
    user_role = st.sidebar.selectbox("اختر هويتك:", ["عميل", "سائق", "مسؤول"], key="main_role_select")
    user_name = st.sidebar.text_input("اسم المستخدم:", value=st.session_state.get("user_name", "أحمد مصطفى"))
    st.session_state["user_name"] = user_name

    # اختيار التنقل بين الخدمات أو الإعدادات من القائمة الجانبية
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
        
        # فحص التوثيق الإلزامي (KYC Guard)
        is_verified, status_msg = check_driver_kyc_status(user_name)
        
        if not is_verified:
            st.error(f"🚨 **حسابك غير موثق حالياً (الحالة: {status_msg})!** يرجى رفع المستندات المطلوبة أدناه لتفعيل التدفق الفوري للطلبات.")
            
            with st.form("driver_kyc_submission_form"):
                st.subheader("📝 مستندات التحقق الإلزامية (KYC)")
                id_num = st.text_input("رقم الهوية الوطنية / الإقامة:")
                drv_lic = st.text_input("رقم رخصة القيادة:")
                veh_lic = st.text_input("رقم رخصة المركبة / اللوحة:")
                
                submitted = st.form_submit_button("💾 إرسال المستندات للاعتماد الفوري")
                if submitted:
                    if id_num and drv_lic and veh_lic:
                        db = firestore.client()
                        db.collection("users").document(str(user_name).strip().lower()).update({
                            "id_number": id_num,
                            "driving_license": drv_lic,
                            "vehicle_license": veh_lic,
                            "kyc_status": "Under Admin Review"
                        })
                        st.success("✅ تم إرسال بياناتك بنجاح وسيتم اعتمادها من الإدارة قريباً!")
                        st.rerun()
                    else:
                        st.warning("⚠️ يرجى تعبئة جميع الحقول المطلوبة للتوثيق.")
            return
            
        else:
            st.success("🌟 **حسابك موثق ومعتمد بنجاح!** يمكنك الآن استقبال الطلبات.")
            render_technical_settings_engine(user_name)

    else:
        st.info("مرحباً بك في لوحة تحكم المشرفين.")


if __name__ == "__main__":
    main()
