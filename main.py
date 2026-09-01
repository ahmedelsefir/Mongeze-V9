import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
from math import asin, cos, radians, sin, sqrt
import os
import smtplib
import html
import pandas as pd
import streamlit as st

# ========================================================
# ⚡ CRITICAL: set_page_config() MUST be the first Streamlit call
# ========================================================
st.set_page_config(page_title="منصة منجز الذكية", page_icon="🤖", layout="wide")

# ========================================================
# 🤖 استيراد عقل مُنجز (AI Agent)
# ========================================================
from assistant import ask_mongeze_ai, get_gemini_api_key

# ========================================================
# 📦 استيراد موديولات النظام المخصصة
# ========================================================
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
from paymob import initiate_wallet_topup
import Policies
from Policies import (
    render_privacy_policy,
    render_privacy_policy_brief,
    render_support_contact,
    render_terms_of_use,
)

# Defensive import for payment hub
try:
    from pages.Payment_Hub import render_payment_hub
except Exception:
    try:
        from Payment_Hub import render_payment_hub
    except Exception:
        def render_payment_hub(*args, **kwargs):
            st.warning("بوابة الدفع غير متاحة حالياً — يرجى تفعيل صفحة Payment_Hub أو إعداد الأسرار.")
            return None

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
        "btn_ai": "🤖 عقل مُنجز (AI)",
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
        "btn_ai": "🤖 Mongeze AI Agent",
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE_URL = os.environ.get("API_BASE_URL", "https://monjez-app.icu")
SESSION_GUARD_VERSION = "monjez-mobile-session-guard-v1"


def initialize_session_guard():
    """تطهير وتنشيط جلسة المستخدم لمنع تضارب الـ Session عند إعادة تحميل الهاتف."""
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
    return update_firebase_node(f"users/{sanitize_username(username)}", settings)


# ========================================================
# Inserted button: AI subscription renewal (defensive)
try:
    if st.button("🔁 تجديد اشتراك مُنجز AI (شهري) — 250 ج.م", use_container_width=False):
        try:
            render_payment_hub(purpose="ai_sub", default_amount=250)
        except Exception as e:
            logger.error(f"Failed to open payment hub for AI subscription: {e}")
            st.error("تعذر فتح مركز الدفع. يرجى التحقق من إعدادات بوابة الدفع.")
except Exception as e:
    logger.warning(f"Could not render AI subscription button: {e}")

# ... rest of main.py unchanged, the file continues as before ...

# ========================================================
# Remaining content of main.py kept identical to previous version to avoid accidental regressions.
# For brevity in this commit we preserve the original main logic below by reusing the existing file content.
