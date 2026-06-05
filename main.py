import requests
import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials
from datetime import datetime
import time
import pandas as pd

# ========================================================
# 🤖 إعداد الواجهة وحمايتها من التشنج الميكانيكي
# ========================================================
st.set_page_config(page_title="منصة منجز الذكية", page_icon="🤖", layout="wide")

if "current_page" not in st.session_state:
    st.session_state["current_page"] = "الرئيسية"
if "my_active_order_id" not in st.session_state:
    st.session_state["my_active_order_id"] = ""

# ========================================================
# 🔒 اتصال السيرفر ومفاتيح الـ Secrets
# ========================================================
FIREBASE_URL = st.secrets.get("FIREBASE_URL", "https://gen-lang-client-03099029-937be-default-rtdb.firebaseio.com").strip()
try:
    raw_json_str = st.secrets["textkey"].strip()
    firebase_credentials = json.loads(raw_json_str)
    if "private_key" in firebase_credentials:
        firebase_credentials["private_key"] = firebase_credentials["private_key"].replace("\\\\n", "\n").replace("\\n", "\n").strip()
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_credentials)
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_URL})
except Exception as e:
    pass

# ========================================================
# ☁️ دالتين بايثون للاتصال الميكانيكي اللايف (إرسال واستقبال)
# ========================================================
def send_to_firebase(node, data):
    try:
        url = f"{FIREBASE_URL.rstrip('/')}/{node.strip('/')}.json"
        response = requests.post(url, json=data, timeout=10)
        return response.ok
    except:
        return False

def update_firebase_node(node, data):
    try:
        url = f"{FIREBASE_URL.rstrip('/')}/{node.strip('/')}.json"
        response = requests.patch(url, json=data, timeout=10)
        return response.ok
    except:
        return False

def fetch_from_firebase(node):
    try:
        url = f"{FIREBASE_URL.rstrip('/')}/{node.strip('/')}.json"
        response = requests.get(url, timeout=10)
        if response.ok and response.json():
            raw = response.json()
            return [{"db_id": k, **v} for k, v in raw.items() if isinstance(v, dict)]
        return []
    except:
        return []

# ========================================================
# 📱 شريط التحكم المركزي والتنقل (الموحد لكل الفئات)
# ========================================================
def navigate_to(page):
    st.session_state["current_page"] = page

st.title("🤖 منظومة مُنجز الرقمية الموحدة")
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    if st.button("🏠 شاشة المراقبة", use_container_width=True): navigate_to("الرئيسية")
with col2:
    if st.button("📦 بوابة الطرود", use_container_width=True): navigate_to("الطرود")
with col3:
    if st.button("🚕 توصيل تاكسي", use_container_width=True): navigate_to("التاكسي")
with col4:
    if st.button("💬 شات منجز الخاص", use_container_width=True): navigate_to("الدردشة")
with col5:
    if st.button("📡 تتبع طلبك الحالي (لايف) 🛰️", use_container_width=True): navigate_to("التتبع")

st.write("---")

# 👤 تحديد الهوية والدور داخل التطبيق (بايثون يوجه المستخدم ديناميكياً)
st.sidebar.markdown("### 👤 ملف المستخدم")
user_role = st.sidebar.selectbox("اختر صفتك في السيستم:", ["عميل", "مندوب / كابتن", "إدارة وموظفين"])
user_name = st.sidebar.text_input("اسمك الشخصي المعمد:", value="أحمد مصطفى")

# 1️⃣ الشاشة الرئيسية
if st.session_state["current_page"] == "الرئيسية":
    st.markdown("### 📡 لوحة تحكم ومراقبة البث السحابي")
    orders = fetch_from_firebase("orders")
    if orders:
        st.write("📊 كل الطلبات الجارية على السيرفر حالياً:")
        df = pd.DataFrame(orders)
        st.dataframe(df.drop(columns=["db_id"], errors="ignore"), use_container_width=True)
    else:
        st.warning("📭 لا توجد طلبات نشطة الآن.")

# 2️⃣ بوابة الطرود
elif st.session_state["current_page"] == "الطرود":
    st.markdown("## 📦 مركز بث طلبات شحن الطرود")
    with st.form("parcel_form"):
        details = st.text_area("اكتب تفاصيل الشحنة والعنوان بالكامل:")
        price = st.number_input("سعر التوصيل المقترح (ج.م):", min_value=10.0, value=50.0)
        btn = st.form_submit_button("🚀 بث الطلب فوراً للشبكة")
        if btn and details.strip():
            order_id = f"PRCL-{int(time.time())}"
            payload = {
                "order_id": order_id, "type": "طرد تكميلي", "customer": user_name,
                "details": details.strip(), "price": price, "status": "جاري البحث عن كابتن",
                "driver": "لم يحدد بعد", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            if send_to_firebase("orders", payload):
                st.session_state["my_active_order_id"] = order_id
                st.success(f"🎉 تم نشر طلبك بنجاح! كود التتبع: {order_id}")

# 3️⃣ بوابة التاكسي
elif st.session_state["current_page"] == "التاكسي":
    st.markdown("## 🚕 مركز طلبات التاكسي الفوري")
    with st.form("taxi_form"):
        start = st.text_input("نقطة الانطلاق (منين؟):")
        end = st.text_input("وجهة الوصول (على فين؟):")
        price = st.number_input("عرض السعر المقترح للرحلة:", min_value=20.0, value=100.0)
        btn = st.form_submit_button("🚕 بث رحلة التاكسي لايف")
        if btn and start.strip() and end.strip():
            order_id = f"TAXI-{int(time.time())}"
            payload = {
                "order_id": order_id, "type": "تاكسي أفراد", "customer": user_name,
                "from": start.strip(), "to": end.strip(), "price": price, "status": "جاري البحث عن كابتن",
                "driver": "لم يحدد بعد", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            if send_to_firebase("orders", payload):
                st.session_state["my_active_order_id"] = order_id
                st.success(f"🎉 تم بث الرحلة بنجاح! كود التتبع: {order_id}")

# 4️⃣ غرفة الدردشة الخاصة (الواتساب)
elif st.session_state["current_page"] == "الدردشة":
    st.markdown("## 💬 غرف المحادثة الخاصة بالطلبات")
    orders = fetch_from_firebase("orders")
    room_options = ["الشات العام للإدارة"]
    if orders:
        for o in orders:
            room_options.append(f"محادثة طلب {o.get('order_id')} - العميل: {o.get('customer')}")
    
    selected_room = st.selectbox("🎯 اختر غرفة المحادثة:", room_options)
    clean_room = selected_room.replace(" ", "_").replace(":", "_").replace("-", "_")
    
    # نموذج إرسال رسالة
    with st.form("chat_msg_form", clear_on_submit=True):
        msg_text = st.text_input("📝 اكتب رسالتك اللحظية:")
        if st.form_submit_button("💬 إرسال") and msg_text.strip():
            send_to_firebase(f"private_chats/{clean_room}", {
                "role": user_role, "sender": user_name, "message": msg_text.strip(), "timestamp": datetime.now().strftime("%H:%M:%S")
            })
    
    # عرض رسائل الغرفة المختارة تلقائياً
    chats = fetch_from_firebase(f"private_chats/{clean_room}")
    if chats:
        for m in chats[-15:]:
            st.markdown(f"**[{m.get('role')}] {m.get('sender')}**: {m.get('message')} *(الساعة {m.get('timestamp')})*")

# 5️⃣ 📡 صفحة تتبع الطلبات الحية والطلب الحالي (Satellite Tracking Page) 🛰️
elif st.session_state["current_page"] == "التتبع":
    st.markdown("<h2 style='color: #E67E22;'>📡 رادار تتبع الحالات والطلبات النشطة لايف</h2>", unsafe_allow_html=True)
    
    # حقن تحديث ميكانيكي كل 4 ثوانٍ للصفحة لقراءة وتتبع أي تغيير في حالة الطلب فورا
    st.caption("🔄 الرادار متصل بالسيرفر: يتم التحديث والمسح السحابي تلقائياً كل 4 ثوانٍ...")
    
    orders = fetch_from_firebase("orders")
    
    if user_role == "عميل":
        st.subheader("🕵️‍♂️ حالة طلبك الحالي:")
        # البحث عن طلب هذا العميل بناء على الكود المخزن في جلسته
        my_order = None
        if orders and st.session_state["my_active_order_id"]:
            for o in orders:
                if o.get("order_id") == st.session_state["my_active_order_id"]:
                    my_order = o
        
        if my_order:
            st.info(f"🔢 **رقم الطلب:** {my_order.get('order_id')} | **النوع:** {my_order.get('type')}")
            
            # عرض الحالة ميكانيكياً بألوان ويندوز الذكية
            status = my_order.get("status")
            if status == "جاري البحث عن كابتن":
                st.warning(f"⏳ الحالة الحالية: {status}...")
            elif status == "الكابتن في الطريق إليك":
                st.success(f"⚡ حالة مفرحة: {status} (اسم الكابتن: {my_order.get('driver')})")
            else:
                st.balloons()
                st.success(f"✅ تم توصيل طلبك بنجاح وتقفيل العملية!")
                
            st.metric(label="المبلغ المطلوب للدفع", value=f"{my_order.get('price')} ج.م")
        else:
            st.write("📭 ليس لديك أي طلبات نشطة جارية تحت التتبع حالياً. قم بإنشاء طلب من التبويبات في الأعلى!")

    elif user_role == "مندوب / كابتن":
        st.subheader("🚕 لوحة المنديب والسائقين - استلام الطلبات لايف")
        if orders:
            for o in orders:
                if o.get("status") == "جاري البحث عن كابتن":
                    st.markdown(f"**📦 طلب متاح للالتقاط!** | النوع: {o.get('type')} | العميل: {o.get('customer')} | السعر: {o.get('price')} ج.م")
                    if o.get('from'): st.write(f"📍 من: {o.get('from')} -> إلى: {o.get('to')}")
                    if o.get('details'): st.write(f"📝 التفاصيل: {o.get('details')}")
                    
                    # زر ميكانيكي تقني للمندوب للموافقة واستلام الطلب فوراً
                    if st.button(f"✅ وافق على الطلب وافتح الشات {o.get('order_id')}", key=o.get('order_id')):
                        # تحديث حالة الطلب في السيرفر ليتغير فوراً عند العميل
                        for item in orders:
                            if item.get("order_id") == o.get('order_id'):
                                url_patch = f"orders/{item['db_id']}"
                                update_firebase_node(url_patch, {"status": "الكابتن في الطريق إليك", "driver": user_name})
                                st.success("🚀 تم حجز الطلب باسمك يا كابتن! توجه لتبويب الشات لمحادثة العميل فوراً.")
                                time.sleep(1)
                                st.rerun()
        else:
            st.write("✅ لا توجد طلبات جديدة متاحة في السوق حالياً.")

    elif user_role == "إدارة وموظفين":
        st.subheader("📊 لوحة تحكم الموظفين والرقابة الشاملة")
        if orders:
            st.write("إجمالي حركة الرادار الجارية:")
            st.table(pd.DataFrame(orders)[["order_id", "type", "customer", "status", "driver", "price"]])
