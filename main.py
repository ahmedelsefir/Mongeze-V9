import streamlit as st
import time
from datetime import datetime
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
from math import radians, cos, sin, asin, sqrt
import base64

from firebase_helpers import (
    get_current_timestamp,
    sanitize_username,
    send_to_firebase,
    update_firebase_node,
    fetch_from_firebase,
    fetch_firebase_dict,
    delete_firebase_node,
    init_firebase_admin,
)

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
if not init_firebase_admin():
    st.sidebar.error("⚠️ خطأ في تحميل مفتاح Firebase الحساس")

# ========================================================
# 📡 send_to_firebase / update_firebase_node / fetch_from_firebase
#    are now imported from firebase_helpers.py
# ========================================================

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

        file_bytes = file_data.read()
        if not file_bytes:
            logger.error(f"File is empty: {document_type}")
            return False

        file_base64 = base64.b64encode(file_bytes).decode('utf-8')
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
            logger.info(f"Document {document_type} uploaded successfully for {username}")
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
            "verification_status": "Pending Approval",
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
# 🛠️ Extracted UI helpers to reduce duplication
# ========================================================

def _submit_order(order_prefix, order_type, payload_extra, email_subject, email_body):
    """
    Shared order-submission logic used by both parcel and taxi forms.

    Generates an order ID, sends to Firebase, sends email notification,
    and triggers an audio alert if enabled.
    """
    try:
        order_id = f"{order_prefix}-{int(time.time())}"
        payload = {
            "order_id": order_id,
            "type": order_type,
            "customer": user_name,
            "status": "\u062c\u0627\u0631\u064a \u0627\u0644\u0628\u062d\u062b \u0639\u0646 \u0643\u0627\u0628\u062a\u0646",
            "driver": "\u0644\u0645 \u064a\u062d\u062f\u062f \u0628\u0639\u062f",
            "timestamp": get_current_timestamp(),
        }
        payload.update(payload_extra)

        if send_to_firebase("orders", payload):
            st.session_state["my_active_order_id"] = order_id
            send_system_email(email_subject.format(order_id=order_id), email_body)
            st.success(f"\ud83c\udf89 \u062a\u0645 \u0628\u062b \u0627\u0644\u0637\u0644\u0628 \u0628\u0646\u062c\u0627\u062d! \u0643\u0648\u062f \u0627\u0644\u062a\u062a\u0628\u0639: {order_id}")
            if st.session_state.get("audio_notifications_enabled", False):
                trigger_audio_alert()
        else:
            st.error("\u274c \u0641\u0634\u0644 \u0628\u062b \u0627\u0644\u0637\u0644\u0628. \u062a\u062d\u0642\u0642 \u0645\u0646 \u0627\u0644\u0627\u062a\u0635\u0627\u0644.")
    except Exception as e:
        logger.error(f"Error creating {order_type} order: {str(e)}")
        st.error(f"\u062d\u062f\u062b \u062e\u0637\u0623: {str(e)}")


def _render_document_upload(doc_label, doc_type, uploader_key, username):
    """
    Render a file-uploader + upload-button block for a single KYC document.

    Eliminates the three near-identical upload sections for national ID,
    driving licence, and vehicle licence.
    """
    uploaded_file = st.file_uploader(
        f"\u0627\u062e\u062a\u0631 \u0635\u0648\u0631\u0629 {doc_label}",
        type=["jpg", "jpeg", "png", "pdf"],
        key=uploader_key,
        help=f"\u0627\u062e\u062a\u0631 \u0635\u0648\u0631\u0629 \u0648\u0627\u0636\u062d\u0629 \u0644\u0640{doc_label}",
    )

    if uploaded_file and st.button(f"\ud83d\udce4 \u0631\u0641\u0639 {doc_label}", key=f"upload_{doc_type}"):
        try:
            with st.spinner("\u062c\u0627\u0631\u064a \u0631\u0641\u0639 \u0627\u0644\u0648\u062b\u064a\u0642\u0629..."):
                if upload_document_to_firebase(username, doc_type, uploaded_file):
                    st.success(f"\u2705 \u062a\u0645 \u0631\u0641\u0639 {doc_label} \u0628\u0646\u062c\u0627\u062d!")
                    send_system_email(
                        f"\u0648\u062b\u064a\u0642\u0629 \u062c\u062f\u064a\u062f\u0629: {doc_label} - {username}",
                        f"\u0627\u0644\u0645\u0646\u062f\u0648\u0628 {username} \u0631\u0641\u0639 \u0635\u0648\u0631\u0629 {doc_label} \u0644\u0644\u0645\u0631\u0627\u062c\u0639\u0629",
                    )
                else:
                    st.error("\u274c \u0641\u0634\u0644 \u0631\u0641\u0639 \u0627\u0644\u0648\u062b\u064a\u0642\u0629. \u062d\u0627\u0648\u0644 \u0645\u0631\u0629 \u0623\u062e\u0631\u0649.")
        except Exception as e:
            logger.error(f"Error uploading {doc_type}: {str(e)}")
            st.error(f"\u062e\u0637\u0623: {str(e)}")

    return uploaded_file


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
            _submit_order(
                order_prefix="PRCL",
                order_type="طرد تكميلي",
                payload_extra={"details": details.strip(), "price": price},
                email_subject="طلب طرد جديد {order_id}",
                email_body=f"العميل {user_name} طلب توصيل طرد بقيمة {price} ج.م",
            )

# 3️⃣ بوابة تاكسي أفراد
elif st.session_state["current_page"] == "التاكسي":
    st.markdown("## 🚕 مركز طلبات توصيل التاكسي والأفراد")
    with st.form("taxi_v10"):
        start = st.text_input("نقطة الانطلاق (منين؟):")
        end = st.text_input("الوجهة المراد الوصول إليها (على فين؟):")
        price = st.number_input("عرض السعر المقترح للرحلة:", min_value=20.0, value=120.0)
        if st.form_submit_button("🚕 بث الرحلة فوراً لايف") and start.strip() and end.strip():
            _submit_order(
                order_prefix="TAXI",
                order_type="تاكسي أفراد",
                payload_extra={"from": start.strip(), "to": end.strip(), "price": price},
                email_subject="طلب تاكسي جديد {order_id}",
                email_body=f"الراكب {user_name} اطلب رحلة من {start} إلى {end}",
            )

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
                            "last_updated": get_current_timestamp(),
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
                                    "last_updated": get_current_timestamp()
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
                        st.warning("⏳ **حالتك معلقة** - جاري المراجعة من قبل الفريق الإداري")
                    
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
                    
                    # Each document type: (section heading, doc_type key, uploader widget key, display label)
                    _kyc_documents = [
                        ("🆔 صورة البطاقة الشخصية", "national_id", "national_id_uploader", "البطاقة الشخصية"),
                        ("🚗 رخصة القيادة", "driving_license", "driving_license_uploader", "رخصة القيادة"),
                        ("🛞 رخصة المركبة (إن وجدت)", "vehicle_license", "vehicle_license_uploader", "رخصة المركبة"),
                    ]

                    for heading, doc_type, uploader_key, display_label in _kyc_documents:
                        st.markdown(f"#### {heading}")
                        _render_document_upload(display_label, doc_type, uploader_key, user_name)

                        if doc_type in kyc_docs and kyc_docs[doc_type].get("file_base64"):
                            verified = kyc_docs[doc_type].get("verified", False)
                            st.info(f"📋 {display_label}: {'✅ مسجلة' if verified else '⏳ قيد المراجعة'}")

                        st.divider()
            
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
                                                "تم الموافقة على طلب التحقق من هويتك. يمكنك الآن استخدام المنصة بالكامل والقبول على الطلبات!"
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
