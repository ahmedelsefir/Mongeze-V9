import requests
import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials
from datetime import datetime
import time
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
from math import radians, cos, sin, asin, sqrt
import base64
from io import BytesIO

from Client import render_parcels_page, render_taxi_page, render_chat_page, render_customer_tracking
from Driver import render_driver_tracking, render_driver_settings_tab, render_driver_kyc_tab, render_wallet_topup
from Admin import render_admin_tracking, render_admin_kyc_console, render_commission_engine
from Policies import render_privacy_policy, render_terms_of_use, render_support_contact, render_privacy_policy_brief
from paymob import initiate_wallet_topup, process_paymob_webhook

# ========================================================
# 🤖 إعداد واجهة منصة منجز الذكية وحماية الجلسة
# ========================================================
st.set_page_config(page_title="منصة منجز الذكية", page_icon="🤖", layout="wide")

# Setup logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
FIREBASE_URL = st.secrets.get("FIREBASE_URL", "https://gen-lang-client-03099029-937be-default-rtdb.firebaseio.com/").strip()

try:
    raw_json_str = st.secrets["textkey"].strip()
    firebase_credentials = json.loads(raw_json_str)
    if "private_key" in firebase_credentials:
        firebase_credentials["private_key"] = firebase_credentials["private_key"].replace("\\\\n", "\n").replace("\\n", "\n").strip()
    
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_credentials)
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_URL})
except Exception as e:
    logger.error(f"Firebase initialization error: {str(e)}")
    st.sidebar.error(f"⚠️ خطأ في تحميل مفتاح Firebase الحساس: {str(e)}")

# ========================================================
# 📡 دوال وظائف بايثون للاتصال المباشر والربط (لايف)
# ========================================================
def send_to_firebase(node, data):
    """Send data to Firebase with error handling"""
    try:
        url = f"{FIREBASE_URL.rstrip('/')}/{node.strip('/')}.json"
        response = requests.post(url, json=data, timeout=10)
        return response.ok
    except requests.exceptions.Timeout:
        logger.error(f"Timeout sending to Firebase node: {node}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error sending to Firebase: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending to Firebase: {str(e)}")
        return False

def update_firebase_node(node, data):
    """Update Firebase node with error handling"""
    try:
        url = f"{FIREBASE_URL.rstrip('/')}/{node.strip('/')}.json"
        response = requests.patch(url, json=data, timeout=10)
        return response.ok
    except requests.exceptions.Timeout:
        logger.error(f"Timeout updating Firebase node: {node}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error updating Firebase: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating Firebase: {str(e)}")
        return False

def fetch_from_firebase(node):
    """Fetch data from Firebase with robust error handling"""
    try:
        url = f"{FIREBASE_URL.rstrip('/')}/{node.strip('/')}.json"
        res = requests.get(url, timeout=10)
        
        if res.ok:
            data = res.json()
            if data and isinstance(data, dict):
                # Safely construct list of items
                items = []
                for k, v in data.items():
                    try:
                        if isinstance(v, dict):
                            item = {"db_id": k}
                            item.update(v)
                            items.append(item)
                    except Exception as item_error:
                        logger.warning(f"Error processing item {k}: {str(item_error)}")
                        continue
                return items
        return []
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching from Firebase node: {node}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching from Firebase: {str(e)}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error from Firebase: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching from Firebase: {str(e)}")
        return []

def fetch_user_settings(username):
    """Fetch user settings from Firebase with null-safety"""
    try:
        url = f"{FIREBASE_URL.rstrip('/')}/users/{username.replace(' ', '_')}.json"
        res = requests.get(url, timeout=10)
        
        if res.ok and res.json():
            return res.json()
        return {}
    except Exception as e:
        logger.warning(f"Error fetching user settings for {username}: {str(e)}")
        return {}

def save_user_settings(username, settings):
    """Save user settings to Firebase with comprehensive error handling"""
    try:
        sanitized_username = username.replace(" ", "_").replace(".", "_")
        url = f"{FIREBASE_URL.rstrip('/')}/users/{sanitized_username}.json"
        response = requests.patch(url, json=settings, timeout=10)
        return response.ok
    except Exception as e:
        logger.error(f"Error saving user settings: {str(e)}")
        return False

def fetch_driver_account(username):
    """Fetch driver payout account settings with null-safety"""
    try:
        sanitized_username = username.replace(" ", "_").replace(".", "_")
        url = f"{FIREBASE_URL.rstrip('/')}/drivers_accounts/{sanitized_username}.json"
        res = requests.get(url, timeout=10)
        
        if res.ok and res.json():
            return res.json()
        return {"payment_method": None, "account_number": None}
    except Exception as e:
        logger.warning(f"Error fetching driver account for {username}: {str(e)}")
        return {"payment_method": None, "account_number": None}

def save_driver_account(username, account_data):
    """Save driver account information securely"""
    try:
        sanitized_username = username.replace(" ", "_").replace(".", "_")
        url = f"{FIREBASE_URL.rstrip('/')}/drivers_accounts/{sanitized_username}.json"
        account_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        response = requests.patch(url, json=account_data, timeout=10)
        return response.ok
    except Exception as e:
        logger.error(f"Error saving driver account: {str(e)}")
        return False

def delete_user_from_firebase(username):
    """Delete all user data from Firebase with cascading deletion"""
    try:
        sanitized_username = username.replace(" ", "_").replace(".", "_")
        
        # Delete from users node
        url_users = f"{FIREBASE_URL.rstrip('/')}/users/{sanitized_username}.json"
        requests.delete(url_users, timeout=10)
        
        # Delete from drivers_accounts if driver
        url_driver = f"{FIREBASE_URL.rstrip('/')}/drivers_accounts/{sanitized_username}.json"
        requests.delete(url_driver, timeout=10)
        
        # Delete from private_chats
        url_chats = f"{FIREBASE_URL.rstrip('/')}/private_chats.json"
        res = requests.get(url_chats, timeout=10)
        if res.ok and res.json():
            chats = res.json()
            for chat_key in chats:
                if sanitized_username in str(chat_key).lower():
                    delete_url = f"{FIREBASE_URL.rstrip('/')}/private_chats/{chat_key}.json"
                    requests.delete(delete_url, timeout=10)
        
        logger.info(f"User {username} completely deleted from Firebase")
        return True
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        return False

# ========================================================
# 🎖️ نظام التحقق من هوية المندوب (KYC - Know Your Driver)
# ========================================================
def upload_document_to_firebase(username, document_type, file_data):
    """
    Upload driver documents safely to Firebase with base64 encoding
    
    Args:
        username: Driver username
        document_type: Type of document (national_id, driving_license, vehicle_license)
        file_data: File bytes from st.file_uploader
    
    Returns:
        True if upload successful, False otherwise
    """
    try:
        if not file_data:
            logger.warning(f"Empty file data for {document_type}")
            return False
        
        # Read file and encode to base64
        try:
            file_bytes = file_data.read()
            if not file_bytes:
                logger.error(f"File is empty: {document_type}")
                return False
            
            file_base64 = base64.b64encode(file_bytes).decode('utf-8')
            
            # Sanitize username
            sanitized_username = username.replace(" ", "_").replace(".", "_")
            
            # Create document metadata
            doc_data = {
                "document_type": document_type,
                "file_base64": file_base64,
                "file_name": file_data.name,
                "file_size": len(file_bytes),
                "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "verified": False
            }
            
            # Upload to Firebase
            node = f"driver_kyc/{sanitized_username}/{document_type}"
            url = f"{FIREBASE_URL.rstrip('/')}/{node}.json"
            response = requests.patch(url, json=doc_data, timeout=30)
            
            if response.ok:
                logger.info(f"Document {document_type} uploaded successfully for {username}")
                return True
            else:
                logger.error(f"Firebase upload failed with status {response.status_code}")
                return False
        
        except Exception as upload_error:
            logger.error(f"Error encoding/uploading file: {str(upload_error)}")
            return False
    
    except Exception as e:
        logger.error(f"Error uploading document to Firebase: {str(e)}")
        return False

def fetch_driver_kyc_documents(username):
    """Fetch all KYC documents for a driver with null-safety"""
    try:
        sanitized_username = username.replace(" ", "_").replace(".", "_")
        url = f"{FIREBASE_URL.rstrip('/')}/driver_kyc/{sanitized_username}.json"
        res = requests.get(url, timeout=10)
        
        if res.ok and res.json():
            return res.json()
        return {}
    except Exception as e:
        logger.warning(f"Error fetching KYC documents for {username}: {str(e)}")
        return {}

def create_driver_kyc_record(username, user_role, car_type=None):
    """Create initial KYC record for new driver"""
    try:
        sanitized_username = username.replace(" ", "_").replace(".", "_")
        
        kyc_record = {
            "driver_name": username,
            "user_role": user_role,
            "verification_status": "Pending Manual Review",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "approved_at": None,
            "rejected_at": None,
            "rejection_reason": None,
            "documents_submitted": False,
            "car_type": car_type if car_type else "Personal"
        }
        
        node = f"driver_kyc/{sanitized_username}/metadata"
        url = f"{FIREBASE_URL.rstrip('/')}/{node}.json"
        response = requests.patch(url, json=kyc_record, timeout=10)
        
        if response.ok:
            logger.info(f"KYC record created for {username}")
            # Update user settings with verification status
            save_user_settings(username, {"verification_status": "Pending Manual Review"})
            return True
        return False
    
    except Exception as e:
        logger.error(f"Error creating KYC record: {str(e)}")
        return False

def update_driver_verification_status(username, status, rejection_reason=None):
    """
    Update driver verification status in Firebase
    
    Status options:
    - "Active": Approved and can use the platform
    - "Rejected": Rejected, cannot use platform
    - "Pending Approval": Awaiting admin review
    """
    try:
        sanitized_username = username.replace(" ", "_").replace(".", "_")
        
        update_data = {
            "verification_status": status,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if status == "Active":
            update_data["approved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif status == "Rejected":
            update_data["rejected_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if rejection_reason:
                update_data["rejection_reason"] = rejection_reason
        
        # Update in driver_kyc node
        node = f"driver_kyc/{sanitized_username}/metadata"
        url = f"{FIREBASE_URL.rstrip('/')}/{node}.json"
        response = requests.patch(url, json=update_data, timeout=10)
        
        if response.ok:
            # Also update in users node
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
    """Atomically credit amount to driver's wallet balance in Firebase.
    Uses Firebase Admin SDK transaction for true atomic read-modify-write.
    Falls back to REST API if Admin SDK is not initialized."""
    try:
        sanitized_username = username.replace(" ", "_").replace(".", "_")

        # Try atomic transaction via Firebase Admin SDK
        if firebase_admin._apps:
            try:
                from firebase_admin import db as fb_db
                ref = fb_db.reference(f"drivers/{sanitized_username}/wallet_balance")

                def increment_balance(current_value):
                    current_balance = 0.0
                    if current_value is not None:
                        try:
                            current_balance = float(current_value)
                        except (ValueError, TypeError):
                            current_balance = 0.0
                    return round(current_balance + float(amount), 2)

                new_balance = ref.transaction(increment_balance)
                logger.info(f"Wallet credited (atomic): {username} += {amount}, new balance = {new_balance}")
                return True
            except Exception as sdk_err:
                logger.warning(f"Firebase Admin SDK transaction failed, falling back to REST: {str(sdk_err)}")

        # Fallback: REST API read-then-write (best-effort if SDK unavailable)
        wallet_url = f"{FIREBASE_URL.rstrip('/')}/drivers/{sanitized_username}/wallet_balance.json"
        res = requests.get(wallet_url, timeout=10)
        current_balance = 0.0
        if res.ok and res.json() is not None:
            try:
                current_balance = float(res.json())
            except (ValueError, TypeError):
                current_balance = 0.0

        new_balance = round(current_balance + float(amount), 2)
        node_url = f"{FIREBASE_URL.rstrip('/')}/drivers/{sanitized_username}.json"
        response = requests.patch(node_url, json={"wallet_balance": new_balance}, timeout=10)

        if response.ok:
            logger.info(f"Wallet credited (REST fallback): {username} += {amount}, new balance = {new_balance}")
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
        url = f"{FIREBASE_URL.rstrip('/')}/{node}.json"
        response = requests.patch(url, json=entry_data, timeout=10)

        if response.ok:
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
        smtp_user = smtp_config.get("user", "ahmedelsefir9@gmail.com")
        smtp_pass = smtp_config.get("pass", "pawp eezt ahxr pbet")
        server_host = smtp_config.get("server", "smtp.gmail.com")
        
        try:
            server_port = int(smtp_config.get("port", 587))
        except (ValueError, TypeError):
            server_port = 587
        
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = smtp_user
        msg['Subject'] = subject
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
        
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
    """
    حساب المسافة بين نقطتين باستخدام صيغة Haversine 
    (تحسب المسافة على سطح الكرة الأرضية بدقة عالية)
    
    المعاملات:
        lat1, lon1: إحداثيات العميل (latitude, longitude)
        lat2, lon2: إحداثيات السائق (latitude, longitude)
    
    القيمة المرجعة:
        المسافة بالكيلومتر
    """
    try:
        # التحقق من صحة الإحداثيات
        if not all(isinstance(x, (int, float)) for x in [lat1, lon1, lat2, lon2]):
            logger.error("Invalid coordinates format - must be numeric")
            return None
        
        # التحقق من نطاق الإحداثيات
        if not (-90 <= lat1 <= 90 and -180 <= lon1 <= 180 and -90 <= lat2 <= 90 and -180 <= lon2 <= 180):
            logger.error("Coordinates out of range")
            return None
        
        # تحويل الدرجات إلى راديان
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        
        # صيغة Haversine
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        
        # نصف قطر الأرض بالكيلومتر
        r = 6371
        distance = c * r
        
        logger.info(f"Distance calculated: {distance:.2f} km from ({lat1}, {lon1}) to ({lat2}, {lon2})")
        return round(distance, 2)
    
    except TypeError as e:
        logger.error(f"Type error in distance calculation: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in distance calculation: {str(e)}")
        return None

def get_live_distance_for_order(order):
    """
    جلب المسافة الحية للطلب من Firebase
    يحسب المسافة بين إحداثيات العميل والسائق
    
    المعاملات:
        order: قاموس الطلب من Firebase
    
    القيمة المرجعة:
        المسافة بالكيلومتر أو None في حالة الخطأ
    """
    try:
        # استخراج الإحداثيات من الطلب
        customer_lat = order.get("customer_lat")
        customer_lon = order.get("customer_lon")
        driver_lat = order.get("driver_lat")
        driver_lon = order.get("driver_lon")
        
        # التحقق من وجود جميع الإحداثيات المطلوبة
        if None in [customer_lat, customer_lon, driver_lat, driver_lon]:
            logger.warning(f"Missing coordinates for order {order.get('order_id')}")
            return None
        
        # حساب المسافة
        distance = calculate_distance_haversine(customer_lat, customer_lon, driver_lat, driver_lon)
        return distance
    
    except Exception as e:
        logger.error(f"Error getting live distance for order: {str(e)}")
        return None

def format_distance_display(distance_km):
    """
    تنسيق عرض المسافة بشكل ملائم
    إذا كانت المسافة أقل من 1 كم، تعرض بالمتر
    
    المعاملات:
        distance_km: المسافة بالكيلومتر
    
    القيمة المرجعة:
        نص مُنسّق للعرض
    """
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

# ملف التحكم الجانبي بالهوية والصلاحيات الميكانيكية
st.sidebar.markdown("### 👤 ملف المستخدم")
user_role = st.sidebar.selectbox("اختر هويتك في السيستم:", ["عميل", "مندوب / كابتن", "إدارة وموظفين"])
user_name = st.sidebar.text_input("اسمك المسجل:", value=st.session_state.get("user_name", "أحمد مصطفى"))

# Update session state with current user info
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
                # Safely remove columns
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

# 2️⃣ بوابة الطرود تكميلي
elif st.session_state["current_page"] == "الطرود":
    render_parcels_page(user_name, send_to_firebase, send_system_email, trigger_audio_alert)

# 3️⃣ بوابة تاكسي أفراد
elif st.session_state["current_page"] == "التاكسي":
    render_taxi_page(user_name, send_to_firebase, send_system_email, trigger_audio_alert)

# 4️⃣ غرفة الدردشة الذكية (غرف الواتساب الثنائية المؤمنة لكل طلب)
elif st.session_state["current_page"] == "الدردشة":
    render_chat_page(user_name, user_role, send_to_firebase, fetch_from_firebase,
                     update_firebase_node=update_firebase_node,
                     log_accounting_entry=log_accounting_entry)

# 5️⃣ 📡 رادار تتبع الحالات الحالي والالتقاط الميكانيكي (Satellite Tracking)
elif st.session_state["current_page"] == "التتبع":
    st.markdown("## 📡 رادار التتبع والاتصال السحابي المباشر")
    st.caption("🔄 الرادار نشط: يتم تحديث وسحب الحالات تلقائياً من السيرفر كل 3 ثوانٍ...")
    
    try:
        orders = fetch_from_firebase("orders")
        
        if user_role == "عميل":
            render_customer_tracking(fetch_from_firebase, get_live_distance_for_order, format_distance_display)

        elif user_role == "مندوب / كابتن":
            render_driver_tracking(user_name, orders, update_firebase_node,
                                   fetch_driver_kyc_documents)

        elif user_role == "إدارة وموظفين":
            render_admin_tracking(orders, get_live_distance_for_order, format_distance_display)
    except Exception as e:
        logger.error(f"Error in tracking page: {str(e)}")
        st.error("حدث خطأ في صفحة التتبع")

# 6️⃣ ⚙️ نظام الإعدادات الشامل مع تكامل Firebase الكامل + نظام KYC
elif st.session_state["current_page"] == "الإعدادات":
    st.markdown("## ⚙️ مركز الإعدادات والملف الشخصي المتقدم")
    
    # Initialize tabs for settings
    if user_role == "مندوب / كابتن":
        settings_tabs = st.tabs(["🌍 الإعدادات العامة", "🚕 إعدادات المندوب", "🎖️ التحقق من الهوية (KYC)", "📋 المساعدة والدعم"])
    else:
        settings_tabs = st.tabs(["🌍 الإعدادات العامة", "📋 المساعدة والدعم"])
    
    # ========== TAB 1: الإعدادات العامة ==========
    with settings_tabs[0]:
        st.subheader("📱 الإعدادات العامة (Global Settings)")
        
        # Profile Section
        st.markdown("### 👤 تعديل البروفايل الشخصي")
        
        try:
            # Fetch current user settings
            current_settings = fetch_user_settings(user_name)
            
            # Safe defaults for null-safety
            default_name = current_settings.get("full_name", user_name) if current_settings else user_name
            default_whatsapp = current_settings.get("whatsapp_number", "") if current_settings else ""
            
            with st.form("profile_edit_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_name = st.text_input(
                        "🔤 الاسم الكامل:",
                        value=default_name,
                        help="أدخل اسمك الكامل كما تريد أن يظهر في النظام"
                    )
                
                with col2:
                    whatsapp_num = st.text_input(
                        "📱 رقم الواتساب:",
                        value=default_whatsapp,
                        placeholder="+20xxxxxxxxxx",
                        help="رقم واتساب للتواصل السريع"
                    )
                
                if st.form_submit_button("💾 حفظ تعديلات البروفايل", use_container_width=True):
                    try:
                        profile_data = {
                            "full_name": new_name,
                            "whatsapp_number": whatsapp_num,
                            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "user_role": user_role
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
        st.caption("فعّل التنبيهات الصوتية لتلقي تنويهات عند وصول طلبات جديدة أو تحديثات الرادار")
        
        try:
            audio_enabled = st.checkbox(
                "🔊 تفعيل التنبيهات الصوتية",
                value=st.session_state.get("audio_notifications_enabled", False),
                help="عند التفعيل، سيسمع صوت تنبيه عند كل طلب جديد"
            )
            
            st.session_state["audio_notifications_enabled"] = audio_enabled
            
            if audio_enabled:
                st.info("✅ التنبيهات الصوتية **مفعّلة** - ستسمع صوت عند وصول طلب جديد")
                if st.button("🔊 تجربة الصوت"):
                    trigger_audio_alert()
                    st.success("تم تشغيل الصوت!")
            else:
                st.info("❌ التنبيهات الصوتية **معطّلة**")
        
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
                index=0 if st.session_state.get("language", "العربية") == "العربية" else 1,
                help="تغيير لغة الواجهة والرسائل"
            )
            
            st.session_state["language"] = language_option
            
            if language_option == "العربية":
                st.success("✅ تم تعيين اللغة على **العربية**")
            else:
                st.success("✅ Language set to **English**")
        
        except Exception as e:
            logger.error(f"Error with language settings: {str(e)}")
            st.warning("⚠️ خطأ في إعدادات اللغة")
    
    # ========== TAB 2: إعدادات المندوب ==========
    if user_role == "مندوب / كابتن":
        with settings_tabs[1]:
            render_driver_settings_tab(user_name, fetch_driver_account, save_driver_account, send_system_email)
            render_wallet_topup(user_name, initiate_wallet_topup_fn=initiate_wallet_topup)
        
        # ========== TAB 3: KYC Verification System ==========
        with settings_tabs[2]:
            render_driver_kyc_tab(user_name, user_role, fetch_driver_kyc_documents,
                                  create_driver_kyc_record, upload_document_to_firebase,
                                  send_system_email)
        
        # ========== TAB 4: المساعدة والدعم (للمندوب) ==========
        with settings_tabs[3]:
            st.subheader("📋 المساعدة والدعم (Support & Maintenance)")
            render_privacy_policy()
            render_terms_of_use()
            st.divider()
            render_support_contact()
    
    else:
        # For non-driver users, show basic support
        with settings_tabs[1]:
            st.subheader("📋 المساعدة والدعم (Support & Maintenance)")
            render_privacy_policy_brief()
            st.divider()
            render_support_contact()

# ========== ADMIN CONSOLE: Verification Radar + Commission Engine ==========
if user_role == "إدارة وموظفين" and st.session_state["current_page"] == "الإعدادات":
    render_admin_kyc_console(fetch_from_firebase, update_driver_verification_status, send_system_email)
    render_commission_engine(fetch_from_firebase, update_firebase_node,
                            credit_driver_wallet, log_accounting_entry)

# زر التحديث اليدوي السريع لضمان حركة التدفق الفوري للرادار
if st.button("🔄 تحديث الرادار والمحادثات"):
    st.rerun()
