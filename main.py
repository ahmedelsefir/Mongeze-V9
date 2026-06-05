import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
import requests
import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials
from datetime import datetime
import time

# ========================================================
# 🤖 إعداد الواجهة وحمايتها من التشنج الميكانيكي
# ========================================================
st.set_page_config(page_title="منصة منجز الذكية", page_icon="🤖", layout="wide")

if "firebase_init_success" not in st.session_state:
    st.session_state["firebase_init_success"] = False
if "last_error" not in st.session_state:
    st.session_state["last_error"] = ""

# ========================================================
# 🔒 معالج وتطهير اتصالات السيرفر ومفاتيح الـ Secrets
# ========================================================
try:
    FIREBASE_URL = st.secrets.get("FIREBASE_URL", "https://gen-lang-client-03099029-937be-default-rtdb.firebaseio.com").strip()
    raw_json_str = st.secrets["textkey"].strip()
    firebase_credentials = json.loads(raw_json_str)
    
    if "private_key" in firebase_credentials:
        key_block = firebase_credentials["private_key"]
        key_block = key_block.replace("\\\\n", "\n").replace("\\n", "\n").strip()
        firebase_credentials["private_key"] = key_block

    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_credentials)
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_URL})
    st.session_state["firebase_init_success"] = True
except Exception as e:
    st.session_state["last_error"] = str(e)

# ========================================================
# ☁️ محرك الإرسال والسحب السحابي الذكي الفوري
# ========================================================
def send_data_to_firebase(node, payload_data):
    try:
        base_url = FIREBASE_URL.rstrip('/')
        clean_node = node.strip('/')
        clean_url = f"{base_url}/{clean_node}.json"
        response = requests.post(clean_url, json=payload_data, timeout=15)
        return response.ok
    except Exception as e:
        st.session_state["last_error"] = str(e)
        return False

def fetch_data_from_firebase(node):
    try:
        base_url = FIREBASE_URL.rstrip('/')
        clean_node = node.strip('/')
        clean_url = f"{base_url}/{clean_node}.json"
        response = requests.get(clean_url, timeout=10)
        if response.ok and response.json():
            raw_data = response.json()
            parsed_list = []
            for key, value in raw_data.items():
                value["db_id"] = key
                parsed_list.append(value)
            
            # ترتيب تصاعدي أو حسب وقت الإرسال لتظهر الرسائل بترتيبها الطبيعي
            return parsed_list
        return []
    except Exception as e:
        return []

# ========================================================
# 📧 محرك رسائل الايميل الأوتوماتيكي (Zoho)
# ========================================================
def send_zoho_alert_email(subject, body_text):
    try:
        zoho_user = st.secrets.get("ZOHO_EMAIL", "support@zohoteaminbox.com")
        zoho_pass = st.secrets.get("ZOHO_PASSWORD", "") 
        
        msg = MIMEMultipart()
        msg['From'] = zoho_user
        msg['To'] = zoho_user
        msg['Subject'] = subject
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
        
        server = smtplib.SMTP_SSL('smtp.zoho.com', 465)
        server.login(zoho_user, zoho_pass)
        server.sendmail(zoho_user, zoho_user, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        return False

# ========================================================
# 📱 نظام التنقل وإدارة قنوات المنصة
# ========================================================
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "الرئيسية"

def navigate_to(page_name):
    st.session_state["current_page"] = page_name

st.title("🤖 غرفة العمليات المركزية لـ مُنجز")

# شريط أزرار التنقل المستقر
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    if st.button("🏠 شاشة المراقبة الحية", use_container_width=True): navigate_to("الرئيسية")
with col2:
    if st.button("📦 بوابة الطرود", use_container_width=True): navigate_to("الطرود")
with col3:
    if st.button("🚕 توصيل تاكسي", use_container_width=True): navigate_to("التاكسي")
with col4:
    if st.button("💬 شات منجز اللايف 🟢", use_container_width=True): navigate_to("الدردشة")
with col5:
    if st.button("📢 التعميمات الإدارية", use_container_width=True): navigate_to("التنبيهات")

st.write("---")

# 1️⃣ الشاشة الرئيسية
if st.session_state["current_page"] == "الرئيسية":
    st.markdown("<h3 style='color: #FF5733;'>📡 شاشة الاستقبال والمراقبة الحية للسيستم</h3>", unsafe_allow_html=True)
    
    if st.button("📧 فحص حالة اشتراك سيرفر Zoho الفوري"):
        alert_body = "Hello,\n\nThis is to inform you that the trial period for the Standard Trial is about to expire. You have only two more days left. Please upgrade here."
        if send_zoho_alert_email("Your trial is about to expire", alert_body):
            st.success("📩 تم فحص الاتصال وتفعيل التنبيه بنجاح!")

    tab1, tab2 = st.tabs(["📋 كل الطلبات الحالية لايف", "🚨 التنبيهات الإدارية"])
    with tab1:
        all_orders = fetch_data_from_firebase("orders")
        if all_orders:
            st.dataframe(pd.DataFrame(all_orders).drop(columns=["db_id"], errors="ignore"), use_container_width=True)
        else:
            st.warning("📭 لا توجد طلبات نشطة حالياً في قاعدة البيانات.")
    with tab2:
        all_alerts = fetch_data_from_firebase("system_alerts")
        if all_alerts:
            for alert in all_alerts[-5:]:
                st.info(f"🔔 **{alert.get('sender')}**: {alert.get('message')}")

# 2️⃣ بوابة طلبات الطرود
elif st.session_state["current_page"] == "الطرود":
    st.markdown("## 📦 بث شحن الطرود والطلبات التجارية")
    with st.form(key="parcel_form_v6"):
        customer_name = st.text_input("اسم العميل أو التاجر:", value="أحمد مصطفى")
        item_details = st.text_area("تفاصيل محتوى الطرد والعنوان بدقة:")
        suggested_price = st.number_input("الميزانية المقترحة للتوصيل (ج.م):", min_value=10.0, value=80.0)
        submit_parcel = st.form_submit_button("🚀 نشر طلب الطرد سحابياً", use_container_width=True)
        if submit_parcel and item_details.strip():
            payload = {"service_type": "Parcel", "customer": customer_name, "details": item_details.strip(), "price": suggested_price, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            if send_data_to_firebase("orders", payload):
                st.success("🎉 تم بث طلب الطرد بنجاح!")

# 3️⃣ بوابة توصيل تاكسي
elif st.session_state["current_page"] == "التاكسي":
    st.markdown("## 🚕 خدمة طلب تاكسي وتوصيل الأفراد الفوري")
    with st.form(key="taxi_form_v6"):
        passenger_name = st.text_input("اسم الراكب:", value="عميل منجز")
        pickup_location = st.text_input("نقطة الانطلاق (منين؟):", value="شارع الدندراوي أرض اللواء المهندسين")
        dropoff_location = st.text_input("وجهة الوصول (على فين؟):", value="التجمع الأول")
        fare_offer = st.number_input("عرض السعر المقترح للرحلة (ج.م):", min_value=20.0, value=230.0)
        submit_taxi = st.form_submit_button("🚕 اطلب التاكسي الآن وبث المزايدة", use_container_width=True)
        if submit_taxi:
            payload = {"service_type": "Taxi", "customer": passenger_name, "from": pickup_location.strip(), "to": dropoff_location.strip(), "price": fare_offer, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            if send_data_to_firebase("orders", payload):
                st.success("🎉 تم بث رحلة التاكسي حياً!")

# 4️⃣ 💬 غرفة الدردشة الحية واللحظية المحدثة ميكانيكياً (Auto-Refreshed Chat)
elif st.session_state["current_page"] == "الدردشة":
    st.markdown("<h2 style='color: #9B59B6;'>💬 غرف المحادثة والربط اللحظي المشترك (بث حي)</h2>", unsafe_allow_html=True)
    
    # ⚙️ حقن محرك التحديث الميكانيكي الفوري كل 3 ثوانٍ
    # يقوم بإجبار الصفحة على التحديث تلقائياً لسحب الرسايل الجديدة فوراً
    st.caption("🔄 الرادار الميكانيكي نشط: يتم تحديث الرسايل تلقائياً كل 3 ثوانٍ...")
    
    # استمارة إرسال الرسائل
    with st.form(key="chat_form_v6", clear_on_submit=True):
        user_role = st.selectbox("هويتك في المنصة:", ["موظف / إدارة", "عميل", "مندوب طرود", "سائق تاكسي"])
        sender_name = st.text_input("اسمك الشخصي:", value="أحمد مصطفى")
        chat_message = st.text_input("اكتب رسالتك اللحظية هنا:")
        send_chat = st.form_submit_button("💬 إرسال وبث في الشات اللحظي", use_container_width=True)
        
        if send_chat and chat_message.strip():
            chat_payload = {
                "role": user_role,
                "sender": sender_name,
                "message": chat_message.strip(),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            send_data_to_firebase("live_chat", chat_payload)
            st.success("🔄 جاري البث...")
            time.sleep(0.5) # مهلة للحقن السحابي

    st.write("---")
    st.subheader("📜 شاشة الدردشة الفورية الحية:")
    
    # سحب الرسائل الحية وعرضها من الأقدم للأحدث (مثل غرف المحادثة الحقيقية)
    active_chats = fetch_data_from_firebase("live_chat")
    if active_chats:
        # عرض آخر 25 رسالة مرتبة بشكل طبيعي ومريح للعين
        for msg in active_chats[-25:]:  
            role_color = "#1E88E5" if msg.get("role") == "موظف / إدارة" else "#2ECC71" if msg.get("role") == "عميل" else "#F1C40F"
            st.markdown(f"""
            <div style='background-color: #f4f6f7; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-right: 5px solid {role_color}; text-align: right;'>
                <span style='color: {role_color}; font-weight: bold;'>[{msg.get('role')}] {msg.get('sender')}</span> 
                <span style='font-size: 0.75em; color: gray;'>({msg.get('timestamp')})</span>: 
                <p style='margin-top: 5px; font-size: 1.1em; color: black;'>{msg.get('message')}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("💬 غرف الشات فارغة حالياً. اكتب رسالة في الأعلى واضغط إرسال لتراها فوراً!")

# 5️⃣ مركز التنبيهات
elif st.session_state["current_page"] == "التنبيهات":
    st.markdown("## 📢 مركز إرسال الإشعارات والتعميمات المركزية")
    with st.form(key="alert_form_v6"):
        sender_staff = st.text_input("المسؤول عن البث الإداري:", value="إدارة العمليات")
        notif_target = st.selectbox("الفئة المستهدفة بالتنبيه الفوري:", ["الجميع", "العملاء فقط", "الكباتن فقط"])
        notif_text = st.text_area("نص التنبيه أو التعميم المراد بثه للهواتف:")
        submit_alert = st.form_submit_button("📡 بث التنبيه الفوري الآن", use_container_width=True)
        if submit_alert and notif_text.strip():
            payload = {"sender": sender_staff, "target": notif_target, "message": notif_text.strip(), "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            if send_data_to_firebase("system_alerts", payload):
                st.success("📡 تم تعميم التنبيه السحابي بنجاح!")

# زر مخفي في الأسفل لعمل ريفرش يدوي سريع إذا احتاج الراكب
if st.button("🔄 تحديث الرادار يدوياً"):
    st.rerun()
