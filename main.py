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
            
            if parsed_list and "timestamp" in parsed_list[0]:
                parsed_list.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return parsed_list
        return []
    except Exception as e:
        return []

# ========================================================
# 📧 محرك رسائل الايميل الأوتوماتيكي (Zoho Integrator)
# ========================================================
def send_zoho_alert_email(subject, body_text):
    try:
        # سحب إعدادات سيرفر Zoho المؤمنة من الـ Secrets الخاصة بك
        zoho_user = st.secrets.get("ZOHO_EMAIL", "support@zohoteaminbox.com")
        zoho_pass = st.secrets.get("ZOHO_PASSWORD", "") 
        
        msg = MIMEMultipart()
        msg['From'] = zoho_user
        msg['To'] = zoho_user  # إرسال لنفسك لإخطار الإدارة فوراً
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
        
        # الاتصال الميكانيكي بسيرفر SMTP الخاص بـ Zoho
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
st.write("نظام إدارة الرحلات، غرف الدردشة الفورية، والمراقبة الميكانيكية للسيستم.")

# شريط أزرار التنقل المستقر
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    if st.button("🏠 شاشة المراقبة الحية", use_container_width=True): navigate_to("الرئيسية")
with col2:
    if st.button("📦 بوابة الطرود", use_container_width=True): navigate_to("الطرود")
with col3:
    if st.button("🚕 توصيل تاكسي", use_container_width=True): navigate_to("التاكسي")
with col4:
    if st.button("💬 شات منجز اللايف", use_container_width=True): navigate_to("الدردشة")
with col5:
    if st.button("📢 التعميمات الإدارية", use_container_width=True): navigate_to("التنبيهات")

st.write("---")

# 1️⃣ الشاشة الرئيسية (لوحة استقبال ومراقبة البث الحي الفوري)
if st.session_state["current_page"] == "الرئيسية":
    st.markdown("<h3 style='color: #FF5733;'>📡 شاشة الاستقبال والمراقبة الحية للسيستم</h3>", unsafe_allow_html=True)
    
    # تفقد تلقائي لحالة التنبيه التجريبي لـ Zoho وإرسال إشعار فوري
    if st.button("📧 فحص حالة اشتراك سيرفر Zoho الفوري"):
        alert_body = "Hello,\n\nThis is to inform you that the trial period for the Standard Trial is about to expire. You have only two more days left. Please upgrade here."
        if send_zoho_alert_email("Your trial is about to expire", alert_body):
            st.success("📩 تم فحص الاتصال وإرسال تنبيه الاشتراك بنجاح تام إلى بريد Zoho الإداري!")
        else:
            st.warning("⚠️ تم محاكاة التنبيه محلياً: يرجى إدخال باسورد Zoho SMTP في الـ Secrets لتفعيل الإرسال الحقيقي.")

    tab1, tab2, tab3 = st.tabs(["📋 كل الطلبات الحالية لايف", "🚨 التنبيهات الإدارية النشطة", "⚙️ حالة الرادار"])
    
    with tab1:
        st.write("📊 الطلبات الشغالة الآن على السيرفر (تاكسي + طرود):")
        all_orders = fetch_data_from_firebase("orders")
        if all_orders:
            df = pd.DataFrame(all_orders)
            st.dataframe(df.drop(columns=["db_id"], errors="ignore"), use_container_width=True)
        else:
            st.warning("📭 لا توجد طلبات نشطة حالياً في قاعدة البيانات.")
            
    with tab2:
        st.write("📢 آخر الإشعارات الموجهة للكباتن والعملاء:")
        all_alerts = fetch_data_from_firebase("system_alerts")
        if all_alerts:
            for alert in all_alerts[:5]:
                st.info(f"🔔 **{alert.get('sender', 'الإدارة')}** إلى **{alert.get('target', 'الجميع')}** [{alert.get('time', '')}]:\n\n {alert.get('message', '')}")
        else:
            st.write("✅ لا توجد تعميمات طارئة حالياً.")
            
    with tab3:
        if st.session_state["firebase_init_success"]:
            st.success("🔒 الرادار متصل ومؤمن بالكامل بالخادم السحابي.")
        else:
            st.error(f"❌ عطل بالرادار: {st.session_state['last_error']}")

# 2️⃣ بوابة طلبات الطرود
elif st.session_state["current_page"] == "الطرود":
    st.markdown("<h2 style='color: #1E88E5;'>📦 بث شحن الطرود والطلبات التجارية</h2>", unsafe_allow_html=True)
    with st.form(key="parcel_form_v5"):
        customer_name = st.text_input("اسم العميل أو التاجر:", value="أحمد مصطفى")
        item_details = st.text_area("تفاصيل محتوى الطرد والعنوان بدقة:")
        suggested_price = st.number_input("الميزانية المقترحة للتوصيل (ج.م):", min_value=10.0, value=80.0, step=5.0)
        submit_parcel = st.form_submit_button("🚀 نشر طلب الطرد سحابياً", use_container_width=True)
        
        if submit_parcel:
            if not item_details.strip():
                st.error("⚠️ خطأ: من فضلك اكتب تفاصيل الطرد أولاً!")
            else:
                payload = {
                    "service_type": "Parcel",
                    "customer": customer_name,
                    "details": item_details.strip(),
                    "price": suggested_price,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                if send_data_to_firebase("orders", payload):
                    st.success("🎉 تم بث طلب الطرد بنجاح!")
                else:
                    st.error(f"❌ فشل الإرسال.")

# 3️⃣ بوابة توصيل تاكسي
elif st.session_state["current_page"] == "التاكسي":
    st.markdown("<h2 style='color: #F1C40F;'>🚕 خدمة طلب تاكسي وتوصيل الأفراد الفوري</h2>", unsafe_allow_html=True)
    with st.form(key="taxi_form_v5"):
        passenger_name = st.text_input("اسم الراكب:", value="عميل منجز")
        pickup_location = st.text_input("点 الانطلاق (منين؟):", value="شارع الدندراوي أرض اللواء المهندسين 17")
        dropoff_location = st.text_input("وجهة الوصول (على فين؟):", value="التجمع الأول مستشفى أورام الثدي")
        fare_offer = st.number_input("عرض السعر المقترح للرحلة (ج.م):", min_value=20.0, value=230.0, step=10.0)
        submit_taxi = st.form_submit_button("🚕 اطلب التاكسي الآن وبث المزايدة", use_container_width=True)
        
        if submit_taxi:
            payload = {
                "service_type": "Taxi",
                "customer": passenger_name,
                "from": pickup_location.strip(),
                "to": dropoff_location.strip(),
                "price": fare_offer,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            if send_data_to_firebase("orders", payload):
                st.success("🎉 تم بث رحلة التاكسي حياً!")

# 4️⃣ 💬 غرفة الدردشة الحية واللحظية بين الفئات (Chat Room Active)
elif st.session_state["current_page"] == "الدردشة":
    st.markdown("<h2 style='color: #9B59B6;'>💬 غرف المحادثة والربط اللحظي المشترك</h2>", unsafe_allow_html=True)
    st.write("قناة اتصال فورية لايف لربط العملاء، المناديب، السائقين، والموظفين تلقائياً.")
    
    # استمارة إرسال رسالة شات جديدة
    with st.form(key="chat_form", clear_on_submit=True):
        user_role = st.selectbox("هويتك في المنصة:", ["موظف / إدارة", "عميل", "مندوب طرود", "سائق تاكسي"])
        sender_name = st.text_input("اسمك الشخصي:", value="أحمد مصطفى")
        chat_message = st.text_input("اكتب رسالتك اللحظية هنا:")
        send_chat = st.form_submit_button("💬 إرسال وبث في الشات اللحظي", use_container_width=True)
        
        if send_chat:
            if chat_message.strip():
                chat_payload = {
                    "role": user_role,
                    "sender": sender_name,
                    "message": chat_message.strip(),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                send_data_to_firebase("live_chat", chat_payload)
    
    st.write("---")
    st.subheader("📜 سجل المحادثة الجارية الآن (لايف)")
    
    # سحب وعرض رسائل الشات الحية من الـ Firebase تلقائياً
    active_chats = fetch_data_from_firebase("live_chat")
    if active_chats:
        for msg in active_chats[:20]:  # عرض آخر 20 رسالة متبادلة
            role_color = "#1E88E5" if msg.get("role") == "موظف / إدارة" else "#2ECC71" if msg.get("role") == "عميل" else "#F1C40F"
            st.markdown(f"""
            <div style='background-color: #f4f6f7; padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 5px solid {role_color};'>
                <span style='color: {role_color}; font-weight: bold;'>[{msg.get('role')}] {msg.get('sender')}</span> 
                <span style='font-size: 0.8em; color: gray;'>({msg.get('timestamp')})</span>: 
                <p style='margin-top: 5px; font-size: 1.1em;'>{msg.get('message')}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("💬 غرف الشات فارغة حالياً. ابدأ بإرسال أول رسالة لربط الفريق!")

# 5️⃣ مركز التنبيهات
elif st.session_state["current_page"] == "التنبيهات":
    st.markdown("<h2 style='color: #E67E22;'>📢 مركز إرسال الإشعارات والتعميمات المركزية</h2>", unsafe_allow_html=True)
    with st.form(key="alert_form_v5"):
        sender_staff = st.text_input("المسؤول عن البث الإداري:", value="إدارة العمليات")
        notif_target = st.selectbox("الفئة المستهدفة بالتنبيه الفوري:", ["الجميع", "العملاء فقط", "الكباتن فقط"])
        notif_text = st.text_area("نص التنبيه أو التعميم المراد بثه للهواتف:", value="يرجى الاستمرار في دفع المبلغ كامل للمنصة")
        submit_alert = st.form_submit_button("📡 بث التنبيه الفوري الآن", use_container_width=True)
        
        if submit_alert:
            if not notif_text.strip():
                st.error("⚠️ لا يمكن بث تنبيه فارغ!")
            else:
                notif_payload = {
                    "sender": sender_staff,
                    "target": notif_target,
                    "message": notif_text.strip(),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                if send_data_to_firebase("system_alerts", notif_payload):
                    st.success("📡 تم تعميم التنبيه السحابي بنجاح!")
