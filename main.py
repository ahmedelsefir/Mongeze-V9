import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
from math import asin, cos, radians, sin, sqrt
import os  # 🌐 تم إضافة os لقراءة أسرار ومتغيرات السيرفر السحابي
import smtplib

from Admin import (
    render_admin_kyc_console,
    render_admin_tracking,
    render_commission_engine,
)
from Client import (
    render_chat_page,
    render_customer_tracking,
    render_parcels_page,
    render_taxi_page,
)
from Driver import (
    render_driver_kyc_tab,
    render_driver_settings_tab,
    render_wallet_topup,
)
import firebase_admin
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
import html
import pandas as pd
from paymob import initiate_wallet_topup
import Policies
from Policies import (
    render_privacy_policy,
    render_privacy_policy_brief,
    render_support_contact,
    render_terms_of_use,
)
import streamlit as st

# ========================================================
# 🌐 قاموس الترجمة الموحد لمنصة منجز الذكية (Localization)
# ========================================================
LANG_TEXTS = {
    "العربية": {
        "app_title": "🤖 غرفة العمليات المركزية لـ منجز الذكية",
        "api_caption": "🔗 خط اتصال الدومين النشط حالياً:",
        "btn_monitor": "🏠 شاشة المراقبة",
        "btn_parcels": "📦 بوابة الطرود",
        "btn_taxi": "🚕 توصيل تاكسي",
        "btn_chat": "💬 شات منجز الخاص 🟢",
        "btn_tracking": "🛰️ رادار تتبع الطلبات (لايف)",
        "btn_settings": "⚙️ الإعدادات والملف الشخصي",
        "sidebar_profile": "### 👤 ملف المستخدم",
        "sidebar_role_lbl": "اختر هويتك في السيستم:",
        "sidebar_name_lbl": "اسمك المسجل:",
        "main_dashboard_title": "### 📡 لوحة بث واستقبال العمليات السحابية",
        "active_orders_lbl": "📊 الطلبات الشغالة على السيرفر حالياً:",
        "clean_server_msg": "📭 السيرفر نظيف ولا توجد رحلات جارية حالياً.",
        "tracking_radar_title": "## 📡 رادار التتبع والاتصال السحابي المباشر",
        "tracking_radar_cap": "🔄 الرادار نشط: يتم تحديث وسحب الحالات تلقائياً من السيرفر كل 3 ثوانٍ...",
        "settings_center_title": "## ⚙️ مركز الإعدادات والملف الشخصي المتقدم",
        "global_settings_sub": "📱 الإعدادات العامة (Global Settings)",
        "edit_profile_title": "### 👤 تعديل البروفايل الشخصي",
        "form_full_name": "🔤 الاسم الكامل:",
        "form_whatsapp": "📱 رقم الواتساب:",
        "form_save_btn": "💾 حفظ تعديلات البروفايل",
        "audio_settings_title": "### 🎵 إعدادات التنبيهات الصوتية",
        "audio_checkbox": "🔊 تفعيل التنبيهات الصوتية",
        "audio_enabled_msg": "✅ التنبيهات الصوتية مفعّلة",
        "audio_disabled_msg": "❌ التنبيهات الصوتية معطّلة",
        "audio_test_btn": "🔊 تجربة الصوت",
        "lang_settings_title": "### 🌐 إعدادات اللغة",
        "lang_select_lbl": "اختر لغة الواجهة:",
        "lang_success_msg": "✅ تم تعيين اللغة بنجاح!",
        "manual_refresh_btn": "🔄 تحديث الرادار والمحادثات",
        "error_fetch": "حدث خطأ في جلب البيانات",
        "profile_success": "✅ تم حفظ تعديلات البروفايل بنجاح!",
        "profile_error": "❌ فشل حفظ التعديلات. حاول مرة أخرى.",
        "support_title": "📋 المساعدة والدعم (Support & Maintenance)",
        "tab_general": "🌍 الإعدادات العامة",
        "tab_driver": "🚕 إعدادات المندوب",
        "tab_kyc": "🎖️ التحقق من الهوية (KYC)",
        "tab_support": "📋 المساعدة والدعم",
    },
    "English": {
        "app_title": "🤖 Mongeze Smart Central Operations Room",
        "api_caption": "🔗 Active Live Domain Connection:",
        "btn_monitor": "🏠 Operations Monitor",
        "btn_parcels": "📦 Parcels Portal",
        "btn_taxi": "🚕 Taxi Delivery",
        "btn_chat": "💬 Private Mongeze Chat 🟢",
        "btn_tracking": "🛰️ Live Tracking Radar",
        "btn_settings": "⚙️ Settings & Profile",
        "sidebar_profile": "### 👤 User Profile",
        "sidebar_role_lbl": "Choose your identity:",
        "sidebar_name_lbl": "Registered Name:",
        "main_dashboard_title": "### 📡 Cloud Operations Broadcasting Panel",
        "active_orders_lbl": "📊 Active server orders currently running:",
        "clean_server_msg": "📭 Server is clean. No active trips right now.",
        "tracking_radar_title": "## 📡 Tracking Radar & Direct Cloud Link",
        "tracking_radar_cap": "🔄 Radar Active: Fetching status automatically from server every 3 seconds...",
        "settings_center_title": "## ⚙️ Advanced Settings & Profile Center",
        "global_settings_sub": "📱 Global Settings",
        "edit_profile_title": "### 👤 Edit Personal Profile",
        "form_full_name": "🔤 Full Name:",
        "form_whatsapp": "📱 WhatsApp Number:",
        "form_save_btn": "💾 Save Profile Modifications",
        "audio_settings_title": "### 🎵 Audio Alert Settings",
        "audio_checkbox": "🔊 Enable Audio Notifications",
        "audio_enabled_msg": "✅ Audio alerts are enabled",
        "audio_disabled_msg": "❌ Audio alerts are disabled",
        "audio_test_btn": "🔊 Test Sound",
        "lang_settings_title": "### 🌐 Language Settings",
        "lang_select_lbl": "Choose Interface Language:",
        "lang_success_msg": "✅ Language updated successfully!",
        "manual_refresh_btn": "🔄 Quick Sync Radar & Chats",
        "error_fetch": "Error fetching data from server",
        "profile_success": "✅ Profile modifications saved successfully!",
        "profile_error": "❌ Failed to save profile. Please try again.",
        "support_title": "📋 Support & Maintenance",
        "tab_general": "🌍 General Settings",
        "tab_driver": "🚕 Driver Config",
        "tab_kyc": "🎖️ KYC Identity Verification",
        "tab_support": "📋 Help & Support",
    },
}

# ========================================================
# 🤖 إعداد واجهة منصة منجز الذكية وحماية الجلسة
# ========================================================
st.set_page_config(page_title="منصة منجز الذكية", page_icon="🤖", layout="wide")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE_URL = os.environ.get("API_BASE_URL", "https://monjez-app.icu")
SESSION_GUARD_VERSION = "monjez-mobile-session-guard-v1"


def initialize_session_guard():
    """Clean stale transient session state to reduce browser-side SessionInfo conflicts on mobile reloads."""
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
        st.session_state["driver_verification_status"] = (
            "Pending Manual Review"
        )

    if st.session_state.get("_session_guard_version") != SESSION_GUARD_VERSION:
        for key in list(st.session_state.keys()):
            if key not in protected_keys:
                st.session_state.pop(key, None)
        st.session_state["_session_guard_version"] = SESSION_GUARD_VERSION


initialize_session_guard()

# جلب متوافقات اللغة الحالية المختارة
current_lang = st.session_state.get("language", "العربية")
t = LANG_TEXTS[current_lang]

# ========================================================
# 🔒 جلب التكوينات وإعداد الاتصال السحابي بالـ Firebase
# ========================================================
if not init_firebase_admin():
    st.sidebar.error("⚠️ خطأ في تحميل مفتاح Firebase الحساس")


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
    return update_firebase_node(
        f"users/{sanitize_username(username)}", settings
    )


def fetch_driver_account(username):
    data = fetch_firebase_dict(f"drivers_accounts/{sanitize_username(username)}")
    if not data:
        return {"payment_method": None, "account_number": None}
    return data


def save_driver_account(username, account_data):
    account_data["last_updated"] = get_current_timestamp()
    return update_firebase_node(
        f"drivers_accounts/{sanitize_username(username)}", account_data
    )


def delete_user_from_firebase(username):
    try:
        safe_name = sanitize_username(username)
        delete_firebase_node(f"users/{safe_name}")
        delete_firebase_node(f"drivers_accounts/{safe_name}")

        chats = fetch_firebase_dict("private_chats")
        if chats:
            for chat_key in chats:
                if safe_name in str(chat_key).lower():
                    delete_firebase_node(f"private_chats/{chat_key}")
        return True
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        return False


# ========================================================
# 🎖️ نظام التحقق من هوية المندوب (KYC)
# ========================================================
def upload_document_to_firebase(username, document_type, file_data):
    try:
        if not file_data:
            return False
        file_bytes = file_data.read()
        if not file_bytes:
            return False

        file_base64 = base64.b64encode(file_bytes).decode("utf-8")
        safe_name = sanitize_username(username)

        doc_data = {
            "document_type": document_type,
            "file_base64": file_base64,
            "file_name": file_data.name,
            "file_size": len(file_bytes),
            "uploaded_at": get_current_timestamp(),
            "verified": False,
        }

        if update_firebase_node(f"driver_kyc/{safe_name}/{document_type}", doc_data):
            return True
        return False
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        return False


def fetch_driver_kyc_documents(username):
    return fetch_firebase_dict(f"driver_kyc/{sanitize_username(username)}")


def create_driver_kyc_record(username, user_role, car_type=None):
    try:
        kyc_record = {
            "driver_name": username,
            "user_role": user_role,
            "verification_status": "Pending Manual Review",
            "created_at": get_current_timestamp(),
            "approved_at": None,
            "rejected_at": None,
            "rejection_reason": None,
            "documents_submitted": False,
            "car_type": car_type if car_type else "Personal",
        }
        if update_firebase_node(f"driver_kyc/{sanitize_username(username)}/metadata", kyc_record):
            save_user_settings(
                username, {"verification_status": "Pending Manual Review"}
            )
            return True
        return False
    except Exception as e:
        logger.error(f"Error creating KYC: {str(e)}")
        return False


def update_driver_verification_status(username, status, rejection_reason=None):
    try:
        now = get_current_timestamp()
        update_data = {"verification_status": status, "last_updated": now}
        if status == "Active":
            update_data["approved_at"] = now
        elif status == "Rejected":
            update_data["rejected_at"] = now
            if rejection_reason:
                update_data["rejection_reason"] = rejection_reason

        if update_firebase_node(f"driver_kyc/{sanitize_username(username)}/metadata", update_data):
            save_user_settings(username, {"verification_status": status})
            return True
        return False
    except Exception as e:
        logger.error(f"Error updating status: {str(e)}")
        return False


# ========================================================
# 💰 دوال المحفظة والمحاسبة (Wallet & Accounting)
# ========================================================
def credit_driver_wallet(username, amount):
    try:
        safe_name = sanitize_username(username)
        if firebase_admin._apps:
            try:
                from firebase_admin import db as fb_db

                ref = fb_db.reference(f"drivers/{safe_name}/wallet_balance")

                def increment_balance(current_value):
                    current_balance = 0.0
                    if current_value is not None:
                        try:
                            current_balance = float(current_value)
                        except (ValueError, TypeError):
                            current_balance = 0.0
                    return round(current_balance + float(amount), 2)

                ref.transaction(increment_balance)
                return True
            except Exception as sdk_err:
                logger.warning(f"Fallback to REST: {str(sdk_err)}")

        res = firebase_request("get", f"drivers/{safe_name}/wallet_balance")
        current_balance = 0.0
        if res and res.ok and res.json() is not None:
            try:
                current_balance = float(res.json())
            except (ValueError, TypeError):
                current_balance = 0.0

        new_balance = round(current_balance + float(amount), 2)
        response = firebase_request(
            "patch", f"drivers/{safe_name}", {"wallet_balance": new_balance}
        )
        return response and response.ok
    except Exception as e:
        logger.error(f"Error crediting wallet: {str(e)}")
        return False


def log_accounting_entry(trip_id, entry_data):
    try:
        sanitized_trip_id = str(trip_id).replace(" ", "_").replace("/", "_")
        return update_firebase_node(f"accounting_logs/{sanitized_trip_id}", entry_data)
    except Exception as e:
        logger.error(f"Error logging ledger: {str(e)}")
        return False


# ========================================================
# 📧 محرك الإشعارات والاتصال الفوري (SMTP)
# ========================================================
def send_system_email(subject, body_text):
    try:
        smtp_config = st.secrets.get("smtp", {})
        smtp_user = smtp_config.get("user", "")
        smtp_pass = smtp_config.get("pass", "")
        if not smtp_user or not smtp_pass:
            return False
        server_host = smtp_config.get("server", "smtp.gmail.com")
        server_port = int(smtp_config.get("port", 587))

        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = smtp_user
        msg["Subject"] = subject
        msg.attach(MIMEText(body_text, "plain", "utf-8"))

        server = smtplib.SMTP(server_host, server_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, smtp_user, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        logger.error(f"SMTP error: {str(e)}")
        return False


# ========================================================
# 🎵 محرك التنبيهات الصوتية الذكي
# ========================================================
def trigger_audio_alert():
    audio_html = """
    <audio autoplay>
        <source src="data:audio/wav;base64,UklGRiYAAABXQVZFZm10IBAAAAABAAEAQB8AAAB9AAACABAAZGF0YQIAAAAAAA==" type="audio/wav">
    </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)


# ========================================================
# 📍 حساب المسافة الحية (Haversine Formula)
# ========================================================
def calculate_distance_haversine(lat1, lon1, lat2, lon2):
    try:
        if not all(isinstance(x, (int, float)) for x in [lat1, lon1, lat2, lon2]):
            return None
        if not (-90 <= lat1 <= 90 and -180 <= lon1 <= 180 and -90 <= lat2 <= 90 and -180 <= lon2 <= 180):
            return None

        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        return round(c * 6371, 2)
    except Exception:
        return None


def get_live_distance_for_order(order):
    try:
        return calculate_distance_haversine(
            order.get("customer_lat"),
            order.get("customer_lon"),
            order.get("driver_lat"),
            order.get("driver_lon"),
        )
    except Exception:
        return None


def format_distance_display(distance_km):
    if distance_km is None:
        return "غير متاح 📍" if st.session_state["language"] == "العربية" else "N/A 📍"
    if distance_km < 1:
        return f"{int(distance_km * 1000)} متر 🚶" if st.session_state["language"] == "العربية" else f"{int(distance_km * 1000)}m 🚶"
    return f"{distance_km} كم 🚕" if st.session_state["language"] == "العربية" else f"{distance_km} km 🚕"


# ========================================================
# 📱 شريط التوجيه والديناميكية اللغوية الموحدة
# ========================================================
st.title(t["app_title"])
st.caption(f"{t['api_caption']} {API_BASE_URL}")

# أزرار التنقل مع ربط الترجمة تلقائياً وبشكل فوري
col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    if st.button(t["btn_monitor"], use_container_width=True):
        st.session_state["current_page"] = "الرئيسية"
with col2:
    if st.button(t["btn_parcels"], use_container_width=True):
        st.session_state["current_page"] = "الطرود"
with col3:
    if st.button(t["btn_taxi"], use_container_width=True):
        st.session_state["current_page"] = "التاكسي"
with col4:
    if st.button(t["btn_chat"], use_container_width=True):
        st.session_state["current_page"] = "الدردشة"
with col5:
    if st.button(t["btn_tracking"], use_container_width=True):
        st.session_state["current_page"] = "التتبع"
with col6:
    if st.button(t["btn_settings"], use_container_width=True):
        st.session_state["current_page"] = "الإعدادات"

st.write("---")

# القائمة الجانبية لإدارة الحساب والأدوار
st.sidebar.markdown(t["sidebar_profile"])
role_options = (
    ["عميل", "مندوب / كابتن", "إدارة وموظفين"]
    if current_lang == "العربية"
    else ["Client", "Driver / Captain", "Admin & Staff"]
)
selected_role_display = st.sidebar.selectbox(t["sidebar_role_lbl"], role_options)

# ربط القيمة الداخلية لعدم كسر الباك-إند القديم
role_mapping = {
    "عميل": "عميل",
    "Client": "عميل",
    "مندوب / كابتن": "مندوب / كابتن",
    "Driver / Captain": "مندوب / كابتن",
    "إدارة وموظفين": "إدارة وموظفين",
    "Admin & Staff": "إدارة وموظفين",
}
user_role = role_mapping[selected_role_display]

user_name = st.sidebar.text_input(
    t["sidebar_name_lbl"], value=st.session_state.get("user_name", "أحمد مصطفى")
)
st.session_state["user_name"] = user_name

# 1️⃣ الشاشة الرئيسية (شاشة مراقبة العمليات لايف)
if st.session_state["current_page"] == "الرئيسية":
    st.markdown(t["main_dashboard_title"])
    try:
        orders = fetch_from_firebase("orders")
        if orders and len(orders) > 0:
            st.write(t["active_orders_lbl"])
            df = pd.DataFrame(orders)
            cols_to_drop = [col for col in ["db_id"] if col in df.columns]
            if cols_to_drop:
                df = df.drop(columns=cols_to_drop)
            st.dataframe(df, use_container_width=True)
        else:
            st.warning(t["clean_server_msg"])
    except Exception as e:
        logger.error(f"Error in main page: {str(e)}")
        st.error(t["error_fetch"])

# 2️⃣ بوابة الطرود
elif st.session_state["current_page"] == "الطرود":
    render_parcels_page(
        user_name, send_to_firebase, send_system_email, trigger_audio_alert
    )

# 3️⃣ بوابة تاكسي أفراد
elif st.session_state["current_page"] == "التاكسي":
    render_taxi_page(
        user_name, send_to_firebase, send_system_email, trigger_audio_alert
    )

# 4️⃣ غرفة الدردشة الذكية
elif st.session_state["current_page"] == "الدردشة":
    render_chat_page(
        user_name,
        user_role,
        send_to_firebase,
        fetch_from_firebase,
        update_firebase_node=update_firebase_node,
        log_accounting_entry=log_accounting_entry,
        fetch_firebase_raw=fetch_firebase_raw,
    )

# 5️⃣ رادار تتبع الحالات الحالي والالتقاط الميكانيكي
elif st.session_state["current_page"] == "التتبع":
    st.markdown(t["tracking_radar_title"])
    st.caption(t["tracking_radar_cap"])
    try:
        orders = fetch_from_firebase("orders")
        if user_role == "عميل":
            render_customer_tracking(
                fetch_from_firebase,
                get_live_distance_for_order,
                format_distance_display,
            )
        elif user_role == "مندوب / كابتن":
            from Driver import render_driver_tracking

            render_driver_tracking(
                user_name,
                orders,
                update_firebase_node,
                fetch_driver_kyc_documents,
            )
        elif user_role == "إدارة وموظفين":
            render_admin_tracking(
                orders, get_live_distance_for_order, format_distance_display
            )
    except Exception as e:
        logger.error(f"Error in tracking page: {str(e)}")
        st.error(t["error_fetch"])

# 6️⃣ نظام الإعدادات الشامل مع تكامل Firebase الكامل + قاموس اللغات والـ Tabs
elif st.session_state["current_page"] == "الإعدادات":
    st.markdown(t["settings_center_title"])

    if user_role == "مندوب / كابتن":
        settings_tabs = st.tabs(
            [t["tab_general"], t["tab_driver"], t["tab_kyc"], t["tab_support"]]
        )
    else:
        settings_tabs = st.tabs([t["tab_general"], t["tab_support"]])

    # ========== TAB 1: الإعدادات العامة ==========
    with settings_tabs[0]:
        st.subheader(t["global_settings_sub"])
        st.markdown(t["edit_profile_title"])

        try:
            current_settings = fetch_user_settings(user_name)
            default_name = (
                current_settings.get("full_name", user_name)
                if current_settings
                else user_name
            )
            default_whatsapp = (
                current_settings.get("whatsapp_number", "")
                if current_settings
                else ""
            )

            with st.form("profile_edit_form"):
                col1, col2 = st.columns(2)
                with col1:
                    new_name = st.text_input(t["form_full_name"], value=default_name)
                with col2:
                    whatsapp_num = st.text_input(
                        t["form_whatsapp"],
                        value=default_whatsapp,
                        placeholder="+20xxxxxxxxxx",
                    )

                if st.form_submit_button(t["form_save_btn"], use_container_width=True):
                    profile_data = {
                        "full_name": new_name,
                        "whatsapp_number": whatsapp_num,
                        "last_updated": get_current_timestamp(),
                        "user_role": user_role,
                        "language": current_lang,
                    }
                    if save_user_settings(user_name, profile_data):
                        st.session_state["user_name"] = new_name
                        st.success(t["profile_success"])
                    else:
                        st.error(t["profile_error"])
        except Exception:
            st.warning(t["error_fetch"])

        st.divider()

        # إعدادات التنبيهات الصوتية
        st.markdown(t["audio_settings_title"])
        audio_enabled = st.checkbox(
            t["audio_checkbox"],
            value=st.session_state.get("audio_notifications_enabled", False),
        )
        st.session_state["audio_notifications_enabled"] = audio_enabled
        if audio_enabled:
            st.info(t["audio_enabled_msg"])
            if st.button(t["audio_test_btn"]):
                trigger_audio_alert()
        else:
            st.info(t["audio_disabled_msg"])

        st.divider()

        # إعدادات اللغة الديناميكية الفورية
        st.markdown(t["lang_settings_title"])
        language_option = st.selectbox(
            t["lang_select_lbl"],
            options=["العربية", "English"],
            index=0 if st.session_state.get("language", "العربية") == "العربية" else 1,
        )
        if language_option != st.session_state.get("language"):
            st.session_state["language"] = language_option
            st.success(t["lang_success_msg"])
            st.rerun()

    # ========== باقی الـ Tabs للمندوب والعملاء ==========
    if user_role == "مندوب / كابتن":
        with settings_tabs[1]:
            render_driver_settings_tab(
                user_name, fetch_driver_account, save_driver_account, send_system_email
            )
            render_wallet_topup(
                user_name, initiate_wallet_topup_fn=initiate_wallet_topup
            )
        with settings_tabs[2]:
            render_driver_kyc_tab(
                user_name,
                user_role,
                fetch_driver_kyc_documents,
                create_driver_kyc_record,
                upload_document_to_firebase,
                send_system_email,
            )
        with settings_tabs[3]:
            st.subheader(t["support_title"])
            render_privacy_policy()
            render_terms_of_use()
            st.divider()
            render_support_contact()
    else:
        with settings_tabs[1]:
            st.subheader(t["support_title"])
            render_privacy_policy_brief()
            st.divider()
            render_support_contact()

# ========== ADMIN CONSOLE ==========
if user_role == "إدارة وموظفين" and st.session_state["current_page"] == "الإعدادات":
    render_admin_kyc_console(
        fetch_from_firebase, update_driver_verification_status, send_system_email
    )
    render_commission_engine(
        fetch_from_firebase,
        update_firebase_node,
        credit_driver_wallet,
        log_accounting_entry,
    )

# زر التحديث اليدوي الموحد للغة والبيانات
if st.button(t["manual_refresh_btn"]):
    st.rerun()
