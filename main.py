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
        "btn_settings": "⚙️ الإعدادات والملف الشخصي",
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
SESSION_GUARD_VERSION = "monjez-mobile-session-guard-v1"


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
        st.session_state["driver_verification_status"] = "Pending Manual Review"
    if "ai_messages" not in st.session_state:
        st.session_state["ai_messages"] = []

    if st.session_state.get("_session_guard_version") != SESSION_GUARD_VERSION:
        for key in list(st.session_state.keys()):
            if key not in protected_keys:
                st.session_state.pop(key, None)
        st.session_state["_session_guard_version"] = SESSION_GUARD_VERSION


initialize_session_guard()

# ========================================================
# 🔒 جلب التكوينات وإعداد الاتصال السحابي بالـ Firebase + هيكل القاعدة والـ Triggers
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

        # تهيئة الهيكل الموحد لقاعدة البيانات والأتمتة المالية
        db = firestore.client()

        def initialize_database_schema():
            print("جاري تهيئة الهيكل الخرساني لقاعدة البيانات...")
            user_schema_ref = db.collection("users").document("_schema_template_")
            user_schema_ref.set({
                "uid": "string (Unique Identifier)",
                "name": "string",
                "phone": "string",
                "role": "string (client, driver, admin)",
                "wallet_balance": "number (default: 0.0)",
                "status": "string (active, suspended)",
                "created_at": "timestamp"
            }, merge=True)

            order_schema_ref = db.collection("orders").document("_schema_template_")
            order_schema_ref.set({
                "order_id": "string (Unique Identifier)",
                "client_id": "string",
                "driver_id": "string",
                "service_type": "string",
                "order_detail": "string",
                "suggested_price": "number",
                "status": "string",
                "timestamp": "timestamp"
            }, merge=True)
            print("تم إنشاء الهيكل والوثائق المرجعية بنجاح تام.")

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

        # تشغيل التهيئة فور الإقلاع
        initialize_database_schema()

except Exception as e:
    st.error("⚠️ حدث خطأ أثناء تحليل المفتاح أو تهيئة القاعدة:")
    st.exception(e)


# ========================================================
# 📡 دوال الفايربيز الأساسية المخصصة
# ========================================================
def fetch_firebase_raw(node):
    try:
        res = firebase_request("get", node)
        if res and res.ok:
            return res.json()
        return None
    except Exception as e:
        logger.error(f"Error fetching raw Firebase node {node}: {str(e)}")
        return None


def fetch_user_settings(username):
    return fetch_firebase_dict(f"users/{sanitize_username(username)}")


def save_user_settings(username, settings):
    return update_firebase_node(f"users/{sanitize_username(username)}", settings)


# عرض الواجهة الأساسية والجانبية عند تشغيل الملف الرئيسي
def main():
    st.sidebar.title("منصة مُنجز الذكية")
    user_role = st.sidebar.selectbox("اختر هويتك:", ["عميل", "سائق", "مسؤول"], key="main_role_select")
    user_name = st.sidebar.text_input("اسم المستخدم:", value=st.session_state.get("user_name", "أحمد مصطفى"))
    st.session_state["user_name"] = user_name

    st.title("🤖 غرفة العمليات المركزية لـ منجز الذكية")
    st.markdown(f"**مرحباً بك يا {user_name}** في النظام السحابي الموحد.")

    if user_role == "عميل":
        st.info("قم باختيار الصفحات الفرعية المتاحة من القائمة الجانبية للوصول إلى بوابة الطرود أو التاكسي.")
        render_parcels_page(user_name=user_name)
    elif user_role == "سائق":
        st.info("مرحباً بك في نافذة السائقين.")
    else:
        st.info("مرحباً بك في لوحة تحكم المشرفين.")


if __name__ == "__main__":
    main()
