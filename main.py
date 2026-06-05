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

# ========================================================
# 🤖 إعداد واجهة منصة منجز الذكية وحماية الجلسة
# ========================================================
st.set_page_config(page_title="منصة منجز الذكية", page_icon="🤖", layout="wide")

if "current_page" not in st.session_state:
    st.session_state["current_page"] = "الرئيسية"
if "my_active_order_id" not in st.session_state:
    st.session_state["my_active_order_id"] = ""

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
    st.sidebar.error(f"⚠️ خطأ في تحميل مفتاح Firebase الحساس: {str(e)}")

# ========================================================
# 📡 دوال وظائف بايثون للاتصال المباشر والربط (لايف)
# ========================================================
def send_to_firebase(node, data):
    try:
        url = f"{FIREBASE_URL.rstrip('/')}/{node.strip('/')}.json"
        return requests.post(url, json=data, timeout=10).ok
    except: return False

def update_firebase_node(node, data):
    try:
        url = f"{FIREBASE_URL.rstrip('/')}/{node.strip('/')}.json"
        return requests.patch(url, json=data, timeout=10).ok
    except: return False

def fetch_from_firebase(node):
    try:
        url = f"{FIREBASE_URL.rstrip('/')}/{node.strip('/')}.json"
        res = requests.get(url, timeout=10)
        if res.ok and res.json():
            return [{"db_id": k, **v} for k, v in res.json().items() if isinstance(v, dict)]
        return []
    except: return []

# ========================================================
# 📧 محرك الإشعارات والاتصال الفوري (SMTP Gmail & Zoho)
# ========================================================
def send_system_email(subject, body_text):
    try:
        smtp_user = st.secrets.get("smtp", {}).get("user", "ahmedelsefir9@gmail.com")
        smtp_pass = st.secrets.get("smtp", {}).get("pass", "pawp eezt ahxr pbet")
        server_host = st.secrets.get("smtp", {}).get("server", "smtp.gmail.com")
        server_port = int(st.secrets.get("smtp", {}).get("port", 587))
        
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = smtp_user  # إرسال لنفسك أو لإيميل الإدارة كإشعار
        msg['Subject'] = subject
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(server_host, server_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, smtp_user, msg.as_string())
        server.quit()
        return True
    except:
        return False

# ========================================================
# 📱 شريط التوجيه ودمج الصفحات الموحد
# ========================================================
st.title("🤖 غرفة العمليات المركزية لـ منجز الذكية")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    if st.button("🏠 شاشة المراقبة", use_container_width=True): st.session_state["current_page"] = "الرئيسية"
with col2:
    if st.button("📦 بوابة الطرود", use_container_width=True): st.session_state["current_page"] = "الطرود"
with col3:
    if st.button("🚕 توصيل تاكسي", use_container_width=True): st.session_state["current_page"] = "التاكسي"
with col4:
    if st.button("💬 شات منجز الخاص 🟢", use_container_width=True): st.session_state["current_page"] = "الدردشة"
with col5:
    if st.button("🛰️ رادار تتبع الطلبات (لايف)", use_container_width=True): st.session_state["current_page"] = "التتبع"

st.write("---")

# ملف التحكم الجانبي بالهوية والصلاحيات الميكانيكية
st.sidebar.markdown("### 👤 ملف المستخدم")
user_role = st.sidebar.selectbox("اختر هويتك في السيستم:", ["عميل", "مندوب / كابتن", "إدارة وموظفين"])
user_name = st.sidebar.text_input("اسمك المسجل:", value="أحمد مصطفى")

# 1️⃣ الشاشة الرئيسية (شاشة مراقبة العمليات لايف)
if st.session_state["current_page"] == "الرئيسية":
    st.markdown("### 📡 لوحة بث واستقبال العمليات السحابية")
    orders = fetch_from_firebase("orders")
    if orders:
        st.write("📊 الطلبات الشغالة على السيرفر حالياً:")
        st.dataframe(pd.DataFrame(orders).drop(columns=["db_id"], errors="ignore"), use_container_width=True)
    else:
        st.warning("📭 السيرفر نظيف ولا توجد رحلات جارية حالياً.")

# 2️⃣ بوابة الطرود تكميلي
elif st.session_state["current_page"] == "الطرود":
    st.markdown("## 📦 مركز بث طلبات الطرود والشحن التجاري")
    with st.form("parcel_v10"):
        details = st.text_area("تفاصيل الشحنة وعنوان الالتقاط والتوصيل بدقة:")
        price = st.number_input("الميزانية المقترحة (ج.م):", min_value=10.0, value=70.0)
        if st.form_submit_button("🚀 بث الطلب فوراً للشبكة") and details.strip():
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

# 3️⃣ بوابة تاكسي أفراد
elif st.session_state["current_page"] == "التاكسي":
    st.markdown("## 🚕 مركز طلبات توصيل التاكسي والأفراد")
    with st.form("taxi_v10"):
        start = st.text_input("نقطة الانطلاق (منين؟):")
        end = st.text_input("الوجهة المراد الوصول إليها (على فين؟):")
        price = st.number_input("عرض السعر المقترح للرحلة:", min_value=20.0, value=120.0)
        if st.form_submit_button("🚕 بث الرحلة فوراً لايف") and start.strip() and end.strip():
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

# 4️⃣ غرفة الدردشة الذكية (غرف الواتساب الثنائية المؤمنة لكل طلب)
elif st.session_state["current_page"] == "الدردشة":
    st.markdown("## 💬 غرف المحادثة والاتصال اللحظي الموحد (نظام واتساب)")
    orders = fetch_from_firebase("orders")
    room_options = ["الشات العام للإدارة والموظفين"]
    if orders:
        for o in orders:
            room_options.append(f"محادثة طلب {o.get('order_id')} - العميل: {o.get('customer')}")
    
    selected_room = st.selectbox("🎯 اختر قناة أو غرفة المحادثة النشطة لمتابعتها وتحديثها:", room_options)
    clean_room = selected_room.replace(" ", "_").replace(":", "_").replace("-", "_")
    
    with st.form("chat_form_v10", clear_on_submit=True):
        msg_text = st.text_input("📝 اكتب رسالتك اللحظية هنا:")
        if st.form_submit_button("💬 إرسال وبث") and msg_text.strip():
            send_to_firebase(f"private_chats/{clean_room}", {
                "role": user_role, "sender": user_name, "message": msg_text.strip(), "timestamp": datetime.now().strftime("%H:%M:%S")
            })
            time.sleep(0.2)
    
    # سحب وعرض الرسائل الحية للغرفة المحددة من الأحدث للأقدم
    chats = fetch_from_firebase(f"private_chats/{clean_room}")
    if chats:
        for m in chats[-20:]:
            role_color = "#1E88E5" if m.get("role") == "إدارة وموظفين" else "#2ECC71" if m.get("role") == "عميل" else "#F1C40F"
            st.markdown(f"""
            <div style='background-color: #f4f6f7; padding: 10px; border-radius: 8px; margin-bottom: 6px; border-right: 5px solid {role_color}; text-align: right;'>
                <span style='color: {role_color}; font-weight: bold;'>[{m.get('role')}] {m.get('sender')}</span> 
                <span style='font-size: 0.75em; color: gray;'>({m.get('timestamp')})</span>: 
                <p style='margin-top: 4px; font-size: 1.1em; color: black;'>{m.get('message')}</p>
            </div>
            """, unsafe_allow_html=True)

# 5️⃣ 📡 رادار تتبع الحالات الحالي والالتقاط الميكانيكي (Satellite Tracking)
elif st.session_state["current_page"] == "التتبع":
    st.markdown("## 📡 رادار التتبع والاتصال السحابي المباشر")
    st.caption("🔄 الرادار نشط: يتم تحديث وسحب الحالات تلقائياً من السيرفر كل 3 ثوانٍ...")
    
    orders = fetch_from_firebase("orders")
    
    if user_role == "عميل":
        st.subheader("🕵️‍♂️ مراقبة حالة طلبك الحالي:")
        my_order = next((o for o in orders if o.get("order_id") == st.session_state["my_active_order_id"]), None) if orders else None
        
        if my_order:
            st.info(f"🔢 رقم الطلب الحالي: {my_order.get('order_id')} | الحالة الجارية: **{my_order.get('status')}**")
            if my_order.get("status") == "الكابتن في الطريق إليك":
                st.success(f"⚡ إشعار لايف: الكابتن ({my_order.get('driver')}) قبل طلبك وهو في طريقه لموقعك الآن!")
            st.metric(label="الفاتورة والحساب الجاري", value=f"{my_order.get('price')} ج.م")
        else:
            st.warning("📭 لا يوجد طلب نشط تحت التتبع حالياً لك. اذهب للأعلى وانشئ طرد أو تاكسي.")

    elif user_role == "مندوب / كابتن":
        st.subheader("🚕 الطلبات المتاحة في رادار السوق للالتقاط فوراً:")
        if orders:
            for o in orders:
                if o.get("status") == "جاري البحث عن كابتن":
                    st.markdown(f"**📦 {o.get('type')} جديد!** | العميل: {o.get('customer')} | السعر: {o.get('price')} ج.م")
                    if o.get('from'): st.write(f"📍 من: {o.get('from')} -> إلى: {o.get('to')}")
                    if o.get('details'): st.write(f"📝 التفاصيل: {o.get('details')}")
                    
                    if st.button(f"✅ وافق واستلم الطلب {o.get('order_id')}", key=o.get('order_id')):
                        url_patch = f"orders/{o['db_id']}"
                        if update_firebase_node(url_patch, {"status": "الكابتن في الطريق إليك", "driver": user_name}):
                            st.success("🚀 تم حجز وتعميد الطلب باسمك يا كابتن! انتقل لغرفة الشات للتواصل مع العميل.")
                            time.sleep(1)
                            st.rerun()
        else:
            st.write("✅ الرادار نظيف، لا توجد طلبات معلقة حالياً في السوق.")

    elif user_role == "إدارة وموظفين":
        st.subheader("📊 لوحة الرقابة الشاملة للموظفين")
        if orders: 
            st.table(pd.DataFrame(orders)[["order_id", "type", "customer", "status", "driver", "price"]])

# زر التحديث اليدوي السريع لضمان حركة التدفق الفوري للرادار
if st.button("🔄 تحديث الرادار والمحادثات"):
    st.rerun()
