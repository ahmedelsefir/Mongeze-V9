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
