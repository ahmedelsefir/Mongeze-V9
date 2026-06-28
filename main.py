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
# 🤖 إعداد واجهة منصة منجز الذكية وحماية الجلسة
# ========================================================
st.set_page_config(page_title="منصة منجز الذكية", page_icon="🤖", layout="wide")

# Setup logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# جلب رابط الـ API الموثق أوتوماتيكياً من الأسرار السحابية التي قمت بتهيئتها
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

    for key in [
        "current_page",
        "my_active_order_id",
        "user_name",
        "audio_notifications_enabled",
        "language",
        "driver_verification_status",
    ]:
        if key not in st.session_state:
            if key == "current_page":
                st.session_state[key] = "الرئيسية"
            elif key == "my_active_order_id":
                st.session_state[key] = ""
            elif key == "user_name":
                st.session_state[key] = "أحمد مصطفى"
            elif key == "audio_notifications_enabled":
                st.session_state[key] = False
            elif key == "language":
                st.session_state[key] = "العربية"
            elif key == "driver_verification_status":
                st.session_state[key] = "Pending Manual Review"

    if st.session_state.get("_session_guard_version") != SESSION_GUARD_VERSION:
        for key in list(st.session_state.keys()):
            if key not in protected_keys:
                st.session_state.pop(key, None)
        st.session_state["_session_guard_version"] = SESSION_GUARD_VERSION


initialize_session_guard()

# ========================================================
# 🔒 جلب التكوينات وإعداد الاتصال السحابي بالـ Firebase
# ========================================================
if not init_firebase_admin():
    st.sidebar.error("⚠️ خطأ في تحميل مفتاح Firebase الحساس")

# ========================================================
# 📡 دوال الفايربيز الأساسية المخصصة
# ========================================================


def fetch_firebase_raw(node):
    """Fetch raw JSON data from a Firebase node without list transformation."""
    try:
        res = firebase_request("get", node)
        if res and res.ok:
            return res.json()
        return None
    except Exception as e:
        logger.error(f"Error fetching raw Firebase node {node}: {str(e)}")
        return None


def fetch_user_settings(username):
    """Fetch user settings from Firebase with null-safety"""
    return fetch_firebase_dict(f"users/{sanitize_username(username)}")


def save_user_settings(username, settings):
    """Save user settings to Firebase with comprehensive error handling"""
    return update_firebase_node(f"users/{sanitize_username(username)}", settings)


def fetch_driver_account(username):
    """Fetch driver payout account settings with null-safety"""
    data = fetch_firebase_dict(f"drivers_accounts/{sanitize_username(username)}")
    if not data:
        return {"payment_method": None, "account_number": None}
    return data


def save_driver_account(username, account_data):
    """Save driver account information securely"""
    account_data["last_updated"] = get_current_timestamp()
    return update_firebase_node(
        f"drivers_accounts/{sanitize_username(username)}", account_data
    )


def delete_user_from_firebase(username):
    """Delete all user data from Firebase with cascading deletion"""
    try:
        safe_name = sanitize_username(username)

        delete_firebase_node(f"users/{safe_name}")
        delete_firebase_node(f"drivers_accounts/{safe_name}")

        chats = fetch_firebase_dict("private_chats")
        if chats:
            for chat_key in chats:
                if safe_name in str(chat_key).lower():
                    delete_firebase_node(f"private_chats/{chat_key}")

        logger.info(f"User {username} completely deleted from Firebase")
        return True
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        return False


# ========================================================
# 🎖️ نظام التحقق من هوية المندوب (KYC - Know Your Driver)
# ========================================================
def upload_document_to_firebase(username, document_type, file_data):
    """Upload driver documents safely to Firebase with base64 encoding"""
    try:
        if not file_data:
            logger.warning(f"Empty file data for {document_type}")
            return False

        file_bytes = file_data.read()
        if not file_bytes:
            logger.error(f"File is empty: {document_type}")
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

        node = f"driver_kyc/{safe_name}/{document_type}"
        if update_firebase_node(node, doc_data):
            logger.info(
                f"Document {document_type} uploaded successfully for {username}"
            )
            return True
        logger.error("Firebase upload failed")
        return False

    except Exception as e:
        logger.error(f"Error uploading document to Firebase: {str(e)}")
        return False


def fetch_driver_kyc_documents(username):
    """Fetch all KYC documents for a driver with null-safety"""
    return fetch_firebase_dict(f"driver_kyc/{sanitize_username(username)}")


def create_driver_kyc_record(username, user_role, car_type=None):
    """Create initial KYC record for new driver"""
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

        node = f"driver_kyc/{sanitize_username(username)}/metadata"
        if update_firebase_node(node, kyc_record):
            logger.info(f"KYC record created for {username}")
            save_user_settings(
                username, {"verification_status": "Pending Manual Review"}
            )
            return True
        return False

    except Exception as e:
        logger.error(f"Error creating KYC record: {str(e)}")
        return False


def update_driver_verification_status(username, status, rejection_reason=None):
    """Update driver verification status in Firebase"""
    try:
        now = get_current_timestamp()
        update_data = {
            "verification_status": status,
            "last_updated": now,
        }

        if status == "Active":
            update_data["approved_at"] = now
        elif status == "Rejected":
            update_data["rejected_at"] = now
            if rejection_reason:
                update_data["rejection_reason"] = rejection_reason

        node = f"driver_kyc/{sanitize_username(username)}/metadata"
        if update_firebase_node(node, update_data):
            save_user_settings(username, {"verification_status": status})
            logger.info(f"Driver {username} verification status updated to {status}")
            return True
        return False

    except Exception as e:
        logger.error(f"Error updating driver verification status: {str(e)}")
        return False


# ========================================================
# 💰 دوال المحفظة والمحاسبة (Wallet & Accounting Helpers)
# ========================================================


def credit_driver_wallet(username, amount):
    """Atomically credit amount to driver's wallet balance in Firebase."""
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

                new_balance = ref.transaction(increment_balance)
                logger.info(
                    f"Wallet credited (atomic): {username} += {amount}, new balance = {new_balance}"
                )
                return True
            except Exception as sdk_err:
                logger.warning(
                    f"Firebase Admin SDK transaction failed, falling back to REST: {str(sdk_err)}"
                )

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

        if response and response.ok:
            logger.info(
                f"Wallet credited (REST fallback): {username} += {amount}, new balance = {new_balance}"
            )
            return True
        return False

    except Exception as e:
        logger.error(f"Error crediting wallet for {username}: {str(e)}")
        return False


def log_accounting_entry(trip_id, entry_data):
    """Log a permanent accounting ledger entry under accounting_logs/{trip_id}."""
    try:
        sanitized_trip_id = str(trip_id).replace(" ", "_").replace("/", "_")
        node = f"accounting_logs/{sanitized_trip_id}"
        if update_firebase_node(node, entry_data):
            logger.info(f"Accounting log created for trip: {trip_id}")
            return True
        return False

    except Exception as e:
        logger.error(f"Error logging accounting entry for {trip_id}: {str(e)}")
        return False


# ========================================================
# 📧 محرك الإشعارات والاتصال الفوري (SMTP Gmail & Zoho)
# ========================================================
def send_system_email(subject, body_text):
    """Send email with comprehensive error handling"""
    try:
        smtp_config = st.secrets.get("smtp", {})
        smtp_user = smtp_config.get("user", "")
        smtp_pass = smtp_config.get("pass", "")
        if not smtp_user or not smtp_pass:
            logger.error("SMTP credentials not configured in secrets")
            return False
        server_host = smtp_config.get("server", "smtp.gmail.com")

        try:
            server_port = int(smtp_config.get("port", 587))
        except (ValueError, TypeError):
            server_port = 587

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
        logger.info(f"Email sent successfully: {subject}")
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed - check credentials")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email: {str(e)}")
        return False


# ========================================================
# 🎵 محرك التنبيهات الصوتية الذكي
# ========================================================
def trigger_audio_alert():
    """Trigger an HTML5 audio alert notification"""
    audio_html = """
    <audio autoplay>
        <source src="data:audio/wav;base64,UklGRiYAAABXQVZFZm10IBAAAAABAAEAQB8AAAB9AAACABAAZGF0YQIAAAAAAA==" type="audio/wav">
    </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)


# ========================================================
# 📍 حساب المسافة الحية بين العميل والسائق (Distance Calculation)
# ========================================================
def calculate_distance_haversine(lat1, lon1, lat2, lon2):
    """حساب المسافة بين نقطتين باستخدام صيغة Haversine الدقيقة"""
    try:
        if not all(isinstance(x, (int, float)) for x in [lat1, lon1, lat2, lon2]):
            logger.error("Invalid coordinates format - must be numeric")
            return None

        if not (
            -90 <= lat1 <= 90
            and -180 <= lon1 <= 180
            and -90 <= lat2 <= 90
            and -180 <= lon2 <= 180
        ):
            logger.error("Coordinates out of range")
            return None

        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))

        r = 6371
        distance = c * r

        logger.info(
            f"Distance calculated: {distance:.2f} km from ({lat1}, {lon1}) to ({lat2}, {lon2})"
        )
        return round(distance, 2)

    except TypeError as e:
        logger.error(f"Type error in distance calculation: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in distance calculation: {str(e)}")
        return None


def get_live_distance_for_order(order):
    """جلب المسافة الحية للطلب من Firebase"""
    try:
        customer_lat = order.get("customer_lat")
        customer_lon = order.get("customer_lon")
        driver_lat = order.get("driver_lat")
        driver_lon = order.get("driver_lon")

        if None in [customer_lat, customer_lon, driver_lat, driver_lon]:
            logger.warning(f"Missing coordinates for order {order.get('order_id')}")
            return None

        distance = calculate_distance_haversine(
            customer_lat, customer_lon, driver_lat, driver_lon
        )
        return distance

    except Exception as e:
        logger.error(f"Error getting live distance for order: {str(e)}")
        return None


def format_distance_display(distance_km):
    """تنسيق عرض المسافة بشكل ملائم"""
    if distance_km is None:
        return "غير متاح 📍"

    if distance_km < 1:
        meters = int(distance_km * 1000)
        return f"{meters} متر 🚶"
    elif distance_km < 50:
        return f"{distance_km} كم 🚕"
    else:
        return f"{distance_km} كم 🛣️"


# ========================================================
# 📱 شريط التوجيه ودمج الصفحات الموحد
# ========================================================
st.title("🤖 غرفة العمليات المركزية لـ منجز الذكية")

# طباعة عنوان الـ API الحالي لضمان الاتصال والدمج المباشر لايف
st.caption(f"🔗 خط اتصال الدومين النشط حالياً: {API_BASE_URL}")

col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    if st.button("🏠 شاشة المراقبة", use_container_width=True):
        st.session_state["current_page"] = "الرئيسية"
with col2:
    if st.button("📦 بوابة الطرود", use_container_width=True):
        st.session_state["current_page"] = "الطرود"
with col3:
    if st.button("🚕 توصيل تاكسي", use_container_width=True):
        st.session_state["current_page"] = "التاكسي"
with col4:
    if st.button("💬 شات منجز الخاص 🟢", use_container_width=True):
        st.session_state["current_page"] = "الدردشة"
with col5:
    if st.button("🛰️ رادار تتبع الطلبات (لايف)", use_container_width=True):
        st.session_state["current_page"] = "التتبع"
with col6:
    if st.button("⚙️ الإعدادات والملف الشخصي", use_container_width=True):
        st.session_state["current_page"] = "الإعدادات"

st.write("---")

st.sidebar.markdown("### 👤 ملف المستخدم")
user_role = st.sidebar.selectbox(
    "اختر هويتك في السيستم:", ["عميل", "مندوب / كابتن", "إدارة وموظفين"]
)
user_name = st.sidebar.text_input(
    "اسمك المسجل:", value=st.session_state.get("user_name", "أحمد مصطفى")
)

st.session_state["user_name"] = user_name

# 1️⃣ الشاشة الرئيسية (شاشة مراقبة العمليات لايف)
if st.session_state["current_page"] == "الرئيسية":
    st.markdown("### 📡 لوحة بث واستقبال العمليات السحابية")
    try:
        orders = fetch_from_firebase("orders")
        if orders and len(orders) > 0:
            st.write("📊 الطلبات الشغالة على السيرفر حالياً:")
            try:
                df = pd.DataFrame(orders)
                cols_to_drop = [col for col in ["db_id"] if col in df.columns]
                if cols_to_drop:
                    df = df.drop(columns=cols_to_drop)
                st.dataframe(df, use_container_width=True)
            except Exception as df_error:
                logger.error(f"DataFrame error: {str(df_error)}")
                st.write(orders)
        else:
            st.warning("📭 السيرفر نظيف ولا توجد رحلات جارية حالياً.")
    except Exception as e:
        logger.error(f"Error in main page: {str(e)}")
        st.error("حدث خطأ في جلب البيانات")

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
    st.markdown("## 📡 رادار التتبع والاتصال السحابي المباشر")
    st.caption(
        "🔄 الرادار نشط: يتم تحديث وسحب الحالات تلقائياً من السيرفر كل 3 ثوانٍ..."
    )

    try:
        orders = fetch_from_firebase("orders")

        if user_role == "عميل":
            render_customer_tracking(
                fetch_from_firebase,
                get_live_distance_for_order,
                format_distance_display,
            )

        elif user_role == "مندوب / كابتن":
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
        st.error("حدث خطأ في صفحة التتبع")

# 6️⃣ نظام الإعدادات الشامل مع تكامل Firebase الكامل + نظام KYC
elif st.session_state["current_page"] == "الإعدادات":
    st.markdown("## ⚙️ مركز الإعدادات والملف الشخصي المتقدم")

    if user_role == "مندوب / كابتن":
        settings_tabs = st.tabs(
            [
                "🌍 الإعدادات العامة",
                "🚕 إعدادات المندوب",
                "🎖️ التحقق من الهوية (KYC)",
                "📋 المساعدة والدعم",
            ]
        )
    else:
        settings_tabs = st.tabs(["🌍 الإعدادات العامة", "📋 المساعدة والدعم"])

    # ========== TAB 1: الإعدادات العامة ==========
    with settings_tabs[0]:
        st.subheader("📱 الإعدادات العامة (Global Settings)")
        st.markdown("### 👤 تعديل البروفايل الشخصي")

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
                    new_name = st.text_input(
                        "🔤 الاسم الكامل:",
                        value=default_name,
                        help="أدخل اسمك الكامل كما تريد أن يظهر في النظام",
                    )
                with col2:
                    whatsapp_num = st.text_input(
                        "📱 رقم الواتساب:",
                        value=default_whatsapp,
                        placeholder="+20xxxxxxxxxx",
                        help="رقم واتساب للتواصل السريع",
                    )

                if st.form_submit_button(
                    "💾 حفظ تعديلات البروفايل", use_container_width=True
                ):
                    try:
                        profile_data = {
                            "full_name": new_name,
                            "whatsapp_number": whatsapp_num,
                            "last_updated": get_current_timestamp(),
                            "user_role": user_role,
                        }
                        if save_user_settings(user_name, profile_data):
                            st.session_state["user_name"] = new_name
                            st.success("✅ تم حفظ تعديلات البروفايل بنجاح!")
                            logger.info(f"Profile updated for user: {user_name}")
                        else:
                            st.error("❌ فشل حفظ التعديلات. حاول مرة أخرى.")
                    except Exception as e:
                        logger.error(f"Error saving profile: {str(e)}")
                        st.error(f"خطأ في حفظ البيانات: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading profile settings: {str(e)}")
            st.warning("⚠️ حدث خطأ في تحميل إعدادات البروفايل")

        st.divider()

        # Audio Notifications Section
        st.markdown("### 🎵 إعدادات التنبيهات الصوتية")
        try:
            audio_enabled = st.checkbox(
                "🔊 تفعيل التنبيهات الصوتية",
                value=st.session_state.get("audio_notifications_enabled", False),
            )
            st.session_state["audio_notifications_enabled"] = audio_enabled
            if audio_enabled:
                st.info("✅ التنبيهات الصوتية مفعّلة")
                if st.button("🔊 تجربة الصوت"):
                    trigger_audio_alert()
            else:
                st.info("❌ التنبيهات الصوتية معطّلة")
        except Exception as e:
            logger.error(f"Error with audio notifications: {str(e)}")
            st.warning("⚠️ خطأ في إعدادات التنبيهات الصوتية")

        st.divider()

        # Language Settings
        st.markdown("### 🌐 إعدادات اللغة")
        try:
            language_option = st.selectbox(
                "اختر لغة الواجهة:",
                options=["العربية", "English"],
                index=0
                if st.session_state.get("language", "العربية") == "العربية"
                else 1,
            )
            st.session_state["language"] = language_option
            st.success(f"✅ تم تعيين اللغة على {language_option}")
        except Exception as e:
            logger.error(f"Error with language settings: {str(e)}")
            st.warning("⚠️ خطأ في إعدادات اللغة")

    # ========== TAB 2 & 3 & 4 للمندوب ==========
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
            st.subheader("📋 المساعدة والدعم (Support & Maintenance)")
            render_privacy_policy()
            render_terms_of_use()
            st.divider()
            render_support_contact()
    else:
        with settings_tabs[1]:
            st.subheader("📋 المساعدة والدعم (Support & Maintenance)")
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

# زر التحديث اليدوي السريع
if st.button("🔄 تحديث الرادار والمحادثات"):
    st.rerun() 
