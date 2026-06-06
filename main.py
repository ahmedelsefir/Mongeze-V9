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
    st.session_state["driver_verification_status"] = "Pending Approval"

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
        
        if not res.ok:
            logger.error(f"Firebase GET {node} returned HTTP {res.status_code}: {res.text[:200]}")
            return []
        
        data = res.json()
        if data is None:
            return []
        
        if isinstance(data, dict):
            # Safely construct list of items
            items = []
            for k, v in data.items():
                try:
                    if isinstance(v, dict):
                        item = {"db_id": k}
                        item.update(v)
                        items.append(item)
                    else:
                        logger.warning(f"Skipping non-dict item in {node}/{k}: type={type(v).__name__}")
                except Exception as item_error:
                    logger.warning(f"Error processing item {k}: {str(item_error)}")
                    continue
            return items
        elif isinstance(data, list):
            logger.info(f"Firebase node {node} returned a list ({len(data)} items) instead of dict")
            return [item for item in data if item is not None]
        else:
            logger.warning(f"Firebase node {node} returned unexpected type: {type(data).__name__}")
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
        
        if not res.ok:
            logger.warning(f"Failed to fetch settings for {username}: HTTP {res.status_code}")
            return {}
        
        data = res.json()
        if data and isinstance(data, dict):
            return data
        return {}
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout fetching user settings for {username}")
        return {}
    except requests.exceptions.RequestException as e:
        logger.warning(f"Network error fetching user settings for {username}: {str(e)}")
        return {}
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in user settings for {username}: {str(e)}")
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
        deletion_errors = []
        
        # Delete from users node
        url_users = f"{FIREBASE_URL.rstrip('/')}/users/{sanitized_username}.json"
        res_users = requests.delete(url_users, timeout=10)
        if not res_users.ok:
            deletion_errors.append(f"users node (HTTP {res_users.status_code})")
            logger.warning(f"Failed to delete users/{sanitized_username}: HTTP {res_users.status_code}")
        
        # Delete from drivers_accounts if driver
        url_driver = f"{FIREBASE_URL.rstrip('/')}/drivers_accounts/{sanitized_username}.json"
        res_driver = requests.delete(url_driver, timeout=10)
        if not res_driver.ok:
            deletion_errors.append(f"drivers_accounts node (HTTP {res_driver.status_code})")
            logger.warning(f"Failed to delete drivers_accounts/{sanitized_username}: HTTP {res_driver.status_code}")
        
        # Delete from private_chats
        url_chats = f"{FIREBASE_URL.rstrip('/')}/private_chats.json"
        res = requests.get(url_chats, timeout=10)
        if res.ok and res.json():
            chats = res.json()
            for chat_key in chats:
                if sanitized_username in str(chat_key).lower():
                    delete_url = f"{FIREBASE_URL.rstrip('/')}/private_chats/{chat_key}.json"
                    res_chat = requests.delete(delete_url, timeout=10)
                    if not res_chat.ok:
                        deletion_errors.append(f"private_chats/{chat_key} (HTTP {res_chat.status_code})")
                        logger.warning(f"Failed to delete private_chats/{chat_key}: HTTP {res_chat.status_code}")
        elif not res.ok:
            deletion_errors.append(f"private_chats fetch failed (HTTP {res.status_code})")
            logger.warning(f"Failed to fetch private_chats for cleanup: HTTP {res.status_code}")
        
        if deletion_errors:
            logger.warning(f"User {username} deletion completed with errors: {deletion_errors}")
            return False
        
        logger.info(f"User {username} completely deleted from Firebase")
        return True
    except requests.exceptions.Timeout:
        logger.error(f"Timeout while deleting user {username}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error deleting user {username}: {str(e)}")
        return False
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
            "verification_status": "Pending Approval",
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
            save_user_settings(username, {"verification_status": "Pending Approval"})
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
    st.markdown("## 📦 مركز بث طلبات الطرود والشحن التجاري")
    with st.form("parcel_v10"):
        details = st.text_area("تفاصيل الشحنة وعنوان الالتقاط والتوصيل بدقة:")
        price = st.number_input("الميزانية المقترحة (ج.م):", min_value=10.0, value=70.0)
        if st.form_submit_button("🚀 بث الطلب فوراً للشبكة") and details.strip():
            try:
                order_id = f"PRCL-{int(time.time())}"
                payload = {
                    "order_id": order_id, "type": "طرد تكميلي", "customer": user_name,
                    "details": details.strip(), "price": price, "status": "جاري البحث عن كابتن",
                    "driver": "لم يحدد بعد", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                if send_to_firebase("orders", payload):
                    st.session_state["my_active_order_id"] = order_id
                    send_system_email(f"طلب طرد جديد {order_id}", f"العميل {user_name} طلب توصيل طرد بقيمة {price} ج.م")
                    st.success(f"🎉 تم بث الطلب بنجاح! كود التتبع الفريد هو: {order_id}")
                    if st.session_state.get("audio_notifications_enabled", False):
                        trigger_audio_alert()
                else:
                    st.error("❌ فشل بث الطلب. تحقق من الاتصال.")
            except Exception as e:
                logger.error(f"Error creating parcel order: {str(e)}")
                st.error(f"حدث خطأ: {str(e)}")

# 3️⃣ بوابة تاكسي أفراد
elif st.session_state["current_page"] == "التاكسي":
    st.markdown("## 🚕 مركز طلبات توصيل التاكسي والأفراد")
    with st.form("taxi_v10"):
        start = st.text_input("نقطة الانطلاق (منين؟):")
        end = st.text_input("الوجهة المراد الوصول إليها (على فين؟):")
        price = st.number_input("عرض السعر المقترح للرحلة:", min_value=20.0, value=120.0)
        if st.form_submit_button("🚕 بث الرحلة فوراً لايف") and start.strip() and end.strip():
            try:
                order_id = f"TAXI-{int(time.time())}"
                payload = {
                    "order_id": order_id, "type": "تاكسي أفراد", "customer": user_name,
                    "from": start.strip(), "to": end.strip(), "price": price, "status": "جاري البحث عن كابتن",
                    "driver": "لم يحدد بعد", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                if send_to_firebase("orders", payload):
                    st.session_state["my_active_order_id"] = order_id
                    send_system_email(f"طلب تاكسي جديد {order_id}", f"الراكب {user_name} اطلب رحلة من {start} إلى {end}")
                    st.success(f"🎉 تم بث الرحلة بنجاح! كود التتبع: {order_id}")
                    if st.session_state.get("audio_notifications_enabled", False):
                        trigger_audio_alert()
                else:
                    st.error("❌ فشل بث الرحلة. تحقق من الاتصال.")
            except Exception as e:
                logger.error(f"Error creating taxi order: {str(e)}")
                st.error(f"حدث خطأ: {str(e)}")

# 4️⃣ غرفة الدردشة الذكية (غرف الواتساب الثنائية المؤمنة لكل طلب)
elif st.session_state["current_page"] == "الدردشة":
    st.markdown("## 💬 غرف المحادثة والاتصال اللحظي الموحد (نظام واتساب)")
    try:
        orders = fetch_from_firebase("orders")
        room_options = ["الشات العام للإدارة والموظفين"]
        if orders:
            for o in orders:
                try:
                    room_options.append(f"محادثة طلب {o.get('order_id', 'unknown')} - العميل: {o.get('customer', 'unknown')}")
                except Exception as option_error:
                    logger.warning(f"Error building room option: {str(option_error)}")
                    continue
        
        selected_room = st.selectbox("🎯 اختر قناة أو غرفة المحادثة النشطة لمتابعتها وتحديثها:", room_options)
        clean_room = selected_room.replace(" ", "_").replace(":", "_").replace("-", "_")
        
        with st.form("chat_form_v10", clear_on_submit=True):
            msg_text = st.text_input("📝 اكتب رسالتك اللحظية هنا:")
            if st.form_submit_button("💬 إرسال وبث") and msg_text.strip():
                try:
                    send_to_firebase(f"private_chats/{clean_room}", {
                        "role": user_role, "sender": user_name, "message": msg_text.strip(), 
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    time.sleep(0.2)
                except Exception as chat_error:
                    logger.error(f"Error sending chat message: {str(chat_error)}")
                    st.error("❌ فشل إرسال الرسالة")
        
        # سحب وعرض الرسائل الحية للغرفة المحددة من الأحدث للأقدم
        try:
            chats = fetch_from_firebase(f"private_chats/{clean_room}")
            if chats and len(chats) > 0:
                for m in chats[-20:]:
                    try:
                        role_color = "#1E88E5" if m.get("role") == "إدارة وموظفين" else "#2ECC71" if m.get("role") == "عميل" else "#F1C40F"
                        st.markdown(f"""
                        <div style='background-color: #f4f6f7; padding: 10px; border-radius: 8px; margin-bottom: 6px; border-right: 5px solid {role_color}; text-align: right;'>
                            <span style='color: {role_color}; font-weight: bold;'>[{m.get('role', 'Unknown')}] {m.get('sender', 'Unknown')}</span> 
                            <span style='font-size: 0.75em; color: gray;'>({m.get('timestamp', '')})</span>: 
                            <p style='margin-top: 4px; font-size: 1.1em; color: black;'>{m.get('message', '')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    except Exception as msg_error:
                        logger.warning(f"Error rendering message: {str(msg_error)}")
                        continue
        except Exception as chat_fetch_error:
            logger.error(f"Error fetching chat messages: {str(chat_fetch_error)}")
            st.warning("⚠️ خطأ في جلب الرسائل")
    except Exception as e:
        logger.error(f"Error in chat page: {str(e)}")
        st.error("حدث خطأ في صفحة الدردشة")

# 5️⃣ 📡 رادار تتبع الحالات الحالي والالتقاط الميكانيكي (Satellite Tracking)
elif st.session_state["current_page"] == "التتبع":
    st.markdown("## 📡 رادار التتبع والاتصال السحابي المباشر")
    st.caption("🔄 الرادار نشط: يتم تحديث وسحب الحالات تلقائياً من السيرفر كل 3 ثوانٍ...")
    
    try:
        orders = fetch_from_firebase("orders")
        
        if user_role == "عميل":
            st.subheader("🕵️‍♂️ مراقبة حالة طلبك الحالي:")
            my_order = None
            if orders and st.session_state["my_active_order_id"]:
                my_order = next((o for o in orders if o.get("order_id") == st.session_state["my_active_order_id"]), None)
            
            if my_order:
                st.info(f"🔢 رقم الطلب الحالي: {my_order.get('order_id')} | الحالة الجارية: **{my_order.get('status')}**")
                if my_order.get("status") == "الكابتن في الطريق إليك":
                    st.success(f"⚡ إشعار لايف: الكابتن ({my_order.get('driver')}) قبل طلبك وهو في طريقه لموقعك الآن!")
                    # عرض المسافة الحية
                    distance = get_live_distance_for_order(my_order)
                    distance_text = format_distance_display(distance)
                    st.metric(label="المسافة الحية بينك وبين السائق", value=distance_text)
                st.metric(label="الفاتورة والحساب الجاري", value=f"{my_order.get('price')} ج.م")
            else:
                st.warning("📭 لا يوجد طلب نشط تحت التتبع حالياً لك. اذهب للأعلى وانشئ طرد أو تاكسي.")

        elif user_role == "مندوب / كابتن":
            st.subheader("🚕 الطلبات المتاحة في رادار السوق للالتقاط فوراً:")
            if orders and len(orders) > 0:
                available_orders = [o for o in orders if o.get("status") == "جاري البحث عن كابتن"]
                if available_orders:
                    for o in available_orders:
                        try:
                            st.markdown(f"**📦 {o.get('type', 'طلب')} جديد!** | العميل: {o.get('customer', 'unknown')} | السعر: {o.get('price', 0)} ج.م")
                            if o.get('from'): 
                                st.write(f"📍 من: {o.get('from')} -> إلى: {o.get('to', 'unknown')}")
                            if o.get('details'): 
                                st.write(f"📝 التفاصيل: {o.get('details')}")
                            
                            if st.button(f"✅ وافق واستلم الطلب {o.get('order_id')}", key=o.get('order_id')):
                                try:
                                    url_patch = f"orders/{o.get('db_id')}"
                                    if update_firebase_node(url_patch, {"status": "الكابتن في الطريق إليك", "driver": user_name}):
                                        st.success("🚀 تم حجز وتعميد الطلب باسمك يا كابتن! انتقل لغرفة الشات للتواصل مع العميل.")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("❌ فشل حجز الطلب. حاول مرة أخرى.")
                                except Exception as accept_error:
                                    logger.error(f"Error accepting order: {str(accept_error)}")
                                    st.error(f"خطأ: {str(accept_error)}")
                        except Exception as order_display_error:
                            logger.warning(f"Error displaying order: {str(order_display_error)}")
                            continue
                else:
                    st.write("✅ الرادار نظيف، لا توجد طلبات معلقة حالياً في السوق.")
            else:
                st.write("✅ الرادار نظيف، لا توجد طلبات معلقة حالياً في السوق.")

        elif user_role == "إدارة وموظفين":
            st.subheader("📊 لوحة الرقابة الشاملة للموظفين")
            if orders and len(orders) > 0:
                try:
                    df = pd.DataFrame(orders)
                    display_cols = ["order_id", "type", "customer", "status", "driver", "price"]
                    available_cols = [col for col in display_cols if col in df.columns]
                    st.table(df[available_cols])
                    
                    # عرض المسافات الحية لجميع الطلبات
                    st.subheader("📍 المسافات الحية للطلبات النشطة")
                    for order in orders:
                        if order.get("status") == "الكابتن في الطريق إليك":
                            distance = get_live_distance_for_order(order)
                            distance_text = format_distance_display(distance)
                            st.write(f"🚕 **{order.get('order_id')}** - السائق: {order.get('driver', 'unknown')} | المسافة: {distance_text}")
                except Exception as table_error:
                    logger.error(f"Error displaying table: {str(table_error)}")
                    st.write(orders)
            else:
                st.info("لا توجد طلبات حالياً")
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
            st.subheader("🚕 إعدادات المندوب (Driver Settings)")
            st.markdown("### 💰 تسجيل حسابات السحب والدفع")
            st.caption("قم بتسجيل معلومات حسابك البنكي بأمان تام - البيانات مشفرة في الخادم")
            
            try:
                # Fetch current driver account info
                driver_account = fetch_driver_account(user_name)
                
                current_method = driver_account.get("payment_method") or "اختر الطريقة"
                current_account = driver_account.get("account_number") or ""
                
                with st.form("driver_payout_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        payment_method = st.selectbox(
                            "💳 طريقة الدفع المفضلة:",
                            options=["اختر الطريقة", "Vodafone Cash 🟠", "InstaPay 💳", "Bank Transfer 🏦"],
                            index=0,
                            help="اختر طريقة تحويل الرصيد المفضلة لديك"
                        )
                    
                    with col2:
                        account_num = st.text_input(
                            "📱 رقم الحساب / الهاتف:",
                            value=current_account,
                            placeholder="أدخل رقم هاتفك أو رقم حسابك البنكي",
                            help="رقم محفظتك أو حسابك البنكي"
                        )
                    
                    st.info("🔐 تحذير أمني: تأكد من صحة البيانات قبل الحفظ - لا يمكن الرجوع فيها بسهولة")
                    
                    if st.form_submit_button("✅ حفظ حساب السحب بأمان", use_container_width=True):
                        try:
                            if payment_method == "اختر الطريقة":
                                st.error("❌ يجب اختيار طريقة دفع أولاً")
                            elif not account_num.strip():
                                st.error("❌ يجب إدخال رقم الحساب")
                            else:
                                account_data = {
                                    "payment_method": payment_method,
                                    "account_number": account_num.strip(),
                                    "verified": False,
                                    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                                
                                if save_driver_account(user_name, account_data):
                                    st.success("✅ تم حفظ معلومات حسابك بنجاح! سيتم تحقق الفريق من البيانات")
                                    send_system_email(
                                        f"تسجيل حساب سحب جديد - {user_name}",
                                        f"المندوب {user_name} قام بتسجيل حساب: {payment_method}"
                                    )
                                    logger.info(f"Driver account saved for: {user_name}")
                                else:
                                    st.error("❌ فشل حفظ البيانات. حاول مرة أخرى.")
                        except Exception as e:
                            logger.error(f"Error saving driver account: {str(e)}")
                            st.error(f"خطأ: {str(e)}")
                
                # Display current account info (if exists)
                if driver_account and driver_account.get("account_number"):
                    st.divider()
                    st.markdown("### 📋 معلومات الحساب الحالية")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("طريقة الدفع", driver_account.get("payment_method", "غير محدد"))
                    with col2:
                        masked_account = "*" * (len(str(driver_account.get("account_number", ""))) - 4) + str(driver_account.get("account_number", ""))[-4:]
                        st.metric("الحساب (مشفر)", masked_account)
                    with col3:
                        st.metric("الحالة", "✅ مسجل" if driver_account.get("verified") else "⏳ قيد التحقق")
            
            except Exception as e:
                logger.error(f"Error in driver settings: {str(e)}")
                st.warning("⚠️ خطأ في تحميل إعدادات المندوب")
        
        # ========== TAB 3: KYC Verification System ==========
        with settings_tabs[2]:
            st.subheader("🎖️ نظام التحقق من الهوية (Know Your Driver - KYC)")
            
            try:
                # Fetch KYC status
                kyc_docs = fetch_driver_kyc_documents(user_name)
                
                # Check if KYC record exists
                if not kyc_docs or "metadata" not in kyc_docs:
                    st.info("📝 أنت جديد في النظام. يجب تسجيل وثائقك للتفعيل الكامل.")
                    if st.button("🆕 بدء عملية التحقق من الهوية"):
                        try:
                            if create_driver_kyc_record(user_name, user_role, car_type="Personal"):
                                st.success("✅ تم إنشاء ملف التحقق الخاص بك! الآن قم برفع الوثائق المطلوبة.")
                                st.session_state["driver_verification_status"] = "Pending Approval"
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ فشل إنشاء ملف التحقق")
                        except Exception as e:
                            logger.error(f"Error creating KYC record: {str(e)}")
                            st.error(f"خطأ: {str(e)}")
                else:
                    # Display KYC status
                    metadata = kyc_docs.get("metadata", {})
                    verification_status = metadata.get("verification_status", "Unknown")
                    
                    st.markdown("### 📊 حالة التحقق من الهوية")
                    
                    # Status indicator
                    if verification_status == "Active":
                        st.success("✅ **حالتك مفعّلة** - يمكنك استخدام المنصة بالكامل!")
                    elif verification_status == "Rejected":
                        rejection_reason = metadata.get("rejection_reason", "لم يتم تحديد السبب")
                        st.error(f"❌ **تم رفض طلبك** - السبب: {rejection_reason}")
                    else:
                        st.warning(f"⏳ **حالتك معلقة** - جاري المراجعة من قبل الفريق الإداري")
                    
                    # Display metadata
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("الحالة", verification_status)
                    with col2:
                        created_date = metadata.get("created_at", "N/A")
                        st.metric("تاريخ الطلب", created_date[:10] if created_date else "N/A")
                    with col3:
                        st.metric("النوع", metadata.get("user_role", "Unknown"))
                    
                    st.divider()
                    
                    # Document Upload Section
                    st.markdown("### 📄 رفع الوثائق المطلوبة")
                    st.caption("يجب رفع جميع الوثائق أدناه لتفعيل حسابك بالكامل")
                    
                    # National ID
                    st.markdown("#### 🆔 صورة البطاقة الشخصية")
                    national_id_file = st.file_uploader(
                        "اختر صورة البطاقة الشخصية",
                        type=["jpg", "jpeg", "png", "pdf"],
                        key="national_id_uploader",
                        help="اختر صورة واضحة لبطاقتك الشخصية (الوجه + الخلف)"
                    )
                    
                    if national_id_file and st.button("📤 رفع صورة البطاقة"):
                        try:
                            with st.spinner("جاري رفع الصورة..."):
                                if upload_document_to_firebase(user_name, "national_id", national_id_file):
                                    st.success("✅ تم رفع صورة البطاقة بنجاح!")
                                    send_system_email(
                                        f"وثيقة جديدة: بطاقة شخصية - {user_name}",
                                        f"المندوب {user_name} رفع صورة البطاقة الشخصية للمراجعة"
                                    )
                                else:
                                    st.error("❌ فشل رفع الصورة. حاول مرة أخرى.")
                        except Exception as e:
                            logger.error(f"Error uploading national ID: {str(e)}")
                            st.error(f"خطأ: {str(e)}")
                    
                    # Display current status
                    if "national_id" in kyc_docs and kyc_docs["national_id"].get("file_base64"):
                        nat_id_status = kyc_docs["national_id"].get("verified", False)
                        st.info(f"📋 البطاقة الشخصية: {'✅ مسجلة' if nat_id_status else '⏳ قيد المراجعة'}")
                    
                    st.divider()
                    
                    # Driving License
                    st.markdown("#### 🚗 رخصة القيادة")
                    driving_license_file = st.file_uploader(
                        "اختر صورة رخصة القيادة",
                        type=["jpg", "jpeg", "png", "pdf"],
                        key="driving_license_uploader",
                        help="اختر صورة واضحة لرخصة القيادة"
                    )
                    
                    if driving_license_file and st.button("📤 رفع رخصة القيادة"):
                        try:
                            with st.spinner("جاري رفع الوثيقة..."):
                                if upload_document_to_firebase(user_name, "driving_license", driving_license_file):
                                    st.success("✅ تم رفع رخصة القيادة بنجاح!")
                                    send_system_email(
                                        f"وثيقة جديدة: رخصة القيادة - {user_name}",
                                        f"المندوب {user_name} رفع صورة رخصة القيادة للمراجعة"
                                    )
                                else:
                                    st.error("❌ فشل رفع الوثيقة. حاول مرة أخرى.")
                        except Exception as e:
                            logger.error(f"Error uploading driving license: {str(e)}")
                            st.error(f"خطأ: {str(e)}")
                    
                    # Display current status
                    if "driving_license" in kyc_docs and kyc_docs["driving_license"].get("file_base64"):
                        lic_status = kyc_docs["driving_license"].get("verified", False)
                        st.info(f"📋 رخصة القيادة: {'✅ مسجلة' if lic_status else '⏳ قيد المراجعة'}")
                    
                    st.divider()
                    
                    # Vehicle License (if applicable)
                    st.markdown("#### 🛞 رخصة المركبة (إن وجدت)")
                    st.caption("اختياري - رفع هذه الوثيقة إذا كنت تملك مركبة")
                    vehicle_license_file = st.file_uploader(
                        "اختر صورة رخصة المركبة",
                        type=["jpg", "jpeg", "png", "pdf"],
                        key="vehicle_license_uploader",
                        help="اختر صورة واضحة لرخصة المركبة"
                    )
                    
                    if vehicle_license_file and st.button("📤 رفع رخصة المركبة"):
                        try:
                            with st.spinner("جاري رفع الوثيقة..."):
                                if upload_document_to_firebase(user_name, "vehicle_license", vehicle_license_file):
                                    st.success("✅ تم رفع رخصة المركبة بنجاح!")
                                    send_system_email(
                                        f"وثيقة جديدة: رخصة المركبة - {user_name}",
                                        f"المندوب {user_name} رفع صورة رخصة المركبة للمراجعة"
                                    )
                                else:
                                    st.error("❌ فشل رفع الوثيقة. حاول مرة أخرى.")
                        except Exception as e:
                            logger.error(f"Error uploading vehicle license: {str(e)}")
                            st.error(f"خطأ: {str(e)}")
                    
                    # Display current status
                    if "vehicle_license" in kyc_docs and kyc_docs["vehicle_license"].get("file_base64"):
                        veh_status = kyc_docs["vehicle_license"].get("verified", False)
                        st.info(f"📋 رخصة المركبة: {'✅ مسجلة' if veh_status else '⏳ قيد المراجعة'}")
            
            except Exception as e:
                logger.error(f"Error in KYC section: {str(e)}")
                st.warning("⚠️ خطأ في قسم التحقق من الهوية")
        
        # ========== TAB 4: المساعدة والدعم (للمندوب) ==========
        settings_tab_index = 3
        with settings_tabs[settings_tab_index]:
            st.subheader("📋 المساعدة والدعم (Support & Maintenance)")
            
            with st.expander("🔐 سياسة الخصوصية وحماية البيانات"):
                st.markdown("""
                #### سياسة الخصوصية 🔒
                
                **منصة منجز الذكية** تلتزم بحماية بيانات المستخدمين وفقاً لأعلى معايير الأمان:
                
                ✅ **تشفير المحادثات**: جميع الرسائل والمحادثات في الشات الخاص مشفرة بتقنية SSL/TLS
                
                ✅ **حماية البيانات الشخصية**: تُخزن جميع البيانات بشكل آمن في خوادم Firebase مع نسخ احتياطية
                
                ✅ **عدم المشاركة**: لن نشارك بيانات المستخدمين مع طرف ثالث بدون موافقة صريحة
                
                ✅ **الوصول المقيد**: الوصول إلى بيانات المستخدم محصور على موظفي الشركة الموثوقين فقط
                
                ✅ **الامتثال**: نمتثل لجميع القوانين المحلية والدولية المتعلقة بحماية البيانات
                
                **آخر تحديث**: 2026-01-13
                """)
            
            with st.expander("📋 شروط الاستخدام"):
                st.markdown("""
                #### شروط الاستخدام 📋
                
                باستخدامك لمنصة منجز الذكية، فإنك توافق على:
                
                1️⃣ **الاستخدام المشروع**: استخدام المنصة فقط للأغراض المشروعة والقانونية
                
                2️⃣ **المسؤولية الشخصية**: أنت مسؤول عن جميع الأنشطة التي تحدث تحت حسابك
                
                3️⃣ **عدم الإساءة**: لا يُسمح بإساءة الاستخدام أو الاحتيال أو الأنشطة الضارة
                
                4️⃣ **الامتثال للقوانين**: التزام كامل بقوانين الدولة والمحافظة
                
                5️⃣ **الاتفاقية الملزمة**: هذه الشروط تشكل اتفاقية ملزمة بيننا وبينك
                
                **آخر تحديث**: 2026-01-13
                """)
            
            st.divider()
            
            st.markdown("### 📞 التواصل مع الدعم الفني")
            st.info("""
            🆘 **هل تحتاج إلى مساعدة؟**
            
            - 📧 **البريد الإلكتروني**: support@mongeza.app
            - 📱 **الواتساب**: +20xxxxxxxxxx
            - 🌐 **الموقع الرسمي**: www.mongeza.app
            - ⏰ **ساعات العمل**: ٢٤/٧ خدمة العملاء
            """)
    
    else:
        # For non-driver users, show basic support
        with settings_tabs[1]:
            st.subheader("📋 المساعدة والدعم (Support & Maintenance)")
            
            with st.expander("🔐 سياسة الخصوصية وحماية البيانات"):
                st.markdown("""
                #### سياسة الخصوصية 🔒
                
                **منصة منجز الذكية** تلتزم بحماية بيانات المستخدمين وفقاً لأعلى معايير الأمان.
                """)
            
            st.divider()
            st.markdown("### 📞 التواصل مع الدعم الفني")
            st.info("للتواصل مع فريق الدعم، استخدم البيانات أعلاه.")

# ========== ADMIN CONSOLE: Pending Verification Radar ==========
if user_role == "إدارة وموظفين" and st.session_state["current_page"] == "الإعدادات":
    st.markdown("---")
    st.markdown("## 🔍 لوحة تحكم التحقق من الهوية (Admin KYC Console)")
    
    try:
        # Fetch all KYC records
        kyc_records = fetch_from_firebase("driver_kyc")
        
        if kyc_records and len(kyc_records) > 0:
            # Filter pending drivers
            pending_drivers = []
            for record in kyc_records:
                try:
                    metadata = record.get("metadata", {})
                    if metadata.get("verification_status") == "Pending Approval":
                        pending_drivers.append({
                            "db_id": record.get("db_id"),
                            "driver_name": metadata.get("driver_name", "Unknown"),
                            "created_at": metadata.get("created_at", "N/A"),
                            "documents": record
                        })
                except Exception as e:
                    logger.warning(f"Error processing KYC record: {str(e)}")
                    continue
            
            if pending_drivers:
                st.subheader(f"📡 رادار المحتاجين للمراجعة ({len(pending_drivers)} معلقة)")
                
                for driver in pending_drivers:
                    try:
                        driver_name = driver.get("driver_name", "Unknown")
                        created_at = driver.get("created_at", "N/A")
                        
                        with st.expander(f"👤 {driver_name} - المُرسل: {created_at}"):
                            # Show documents status
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                nat_id_exists = "national_id" in driver.get("documents", {})
                                st.metric("🆔 البطاقة", "✅ موجودة" if nat_id_exists else "❌ مفقودة")
                            
                            with col2:
                                lic_exists = "driving_license" in driver.get("documents", {})
                                st.metric("🚗 الرخصة", "✅ موجودة" if lic_exists else "❌ مفقودة")
                            
                            with col3:
                                veh_exists = "vehicle_license" in driver.get("documents", {})
                                st.metric("🛞 المركبة", "✅ موجودة" if veh_exists else "❌ مفقودة")
                            
                            st.divider()
                            
                            # Action buttons
                            st.markdown("### 🎯 الإجراءات الإدارية")
                            
                            col_approve, col_reject = st.columns(2)
                            
                            with col_approve:
                                if st.button(f"🟢 موافقة وتفعيل الحساب - {driver_name}", key=f"approve_{driver_name}"):
                                    try:
                                        if update_driver_verification_status(driver_name, "Active"):
                                            st.success(f"✅ تم تفعيل حساب {driver_name} بنجاح!")
                                            send_system_email(
                                                f"✅ تم الموافقة على حسابك - {driver_name}",
                                                f"تم الموافقة على طلب التحقق من هويتك. يمكنك الآن استخدام المنصة بالكامل والقبول على الطلبات!"
                                            )
                                            logger.info(f"Driver {driver_name} approved")
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error("❌ فشلت عملية التفعيل")
                                    except Exception as e:
                                        logger.error(f"Error approving driver: {str(e)}")
                                        st.error(f"خطأ: {str(e)}")
                            
                            with col_reject:
                                rejection_reason = st.text_input(
                                    "سبب الرفض (إن وجد):",
                                    placeholder="مثال: الوثائق غير واضحة",
                                    key=f"reject_reason_{driver_name}"
                                )
                                
                                if st.button(f"🔴 رفض الطلب - {driver_name}", key=f"reject_{driver_name}"):
                                    try:
                                        if not rejection_reason.strip():
                                            st.error("❌ يجب إدخال سبب الرفض")
                                        else:
                                            if update_driver_verification_status(driver_name, "Rejected", rejection_reason.strip()):
                                                st.success(f"✅ تم رفض طلب {driver_name}")
                                                send_system_email(
                                                    f"❌ تم رفض طلبك - {driver_name}",
                                                    f"للأسف، تم رفض طلب التحقق من هويتك. السبب: {rejection_reason}\n\nيمكنك إعادة محاولة رفع الوثائق مرة أخرى."
                                                )
                                                logger.info(f"Driver {driver_name} rejected")
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error("❌ فشلت عملية الرفض")
                                    except Exception as e:
                                        logger.error(f"Error rejecting driver: {str(e)}")
                                        st.error(f"خطأ: {str(e)}")
                    
                    except Exception as display_error:
                        logger.warning(f"Error displaying driver: {str(display_error)}")
                        continue
            
            else:
                st.info("✅ لا توجد طلبات معلقة للمراجعة - جميع المندوبين تم مراجعتهم!")
        
        else:
            st.info("📭 لا توجد طلبات KYC حتى الآن")
    
    except Exception as e:
        logger.error(f"Error in admin KYC console: {str(e)}")
        st.error("⚠️ خطأ في تحميل لوحة التحكم")

# زر التحديث اليدوي السريع لضمان حركة التدفق الفوري للرادار
if st.button("🔄 تحديث الرادار والمحادثات"):
    st.rerun()
