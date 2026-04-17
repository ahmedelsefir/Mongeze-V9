import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import requests
import json
import smtplib
from email.mime.text import MIMEText

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="Mongez Control Center", page_icon="🏠", layout="wide")

# --- 2. تهيئة النظام والاتصال بقاعدة البيانات ---
def initialize_system():
    if not firebase_admin._apps:
        try:
            fb_dict = dict(st.secrets["firebase"])
            # معالجة مفتاح التشفير لضمان القراءة الصحيحة
            if "private_key" in fb_dict:
                fb_dict["private_key"] = fb_dict["private_key"].replace("\\n", "\n")
            
            cred = credentials.Certificate(fb_dict)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"System Initialization Error: {e}")
            return None
    return firestore.client()

db = initialize_system()

# --- 3. الدوال البرمجية (Automation Functions) ---

def send_slack_message(message):
    """إرسال تنبيهات فورية لـ Slack"""
    url = "https://slack.com/api/chat.postMessage"
    token = st.secrets["slack"].get("bot_token", "") # تأكد من وجوده في الأسرار
    payload = {"channel": "general", "text": message}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        requests.post(url, headers=headers, data=json.dumps(payload))
    except: pass

def sync_to_notion(name, phone, address, srv_type, amount):
    """مزامنة الطلب مع قاعدة بيانات Notion"""
    try:
        token = st.secrets["notion"]["token"]
        database_id = st.secrets["notion"]["database_id"]
        url = "https://api.notion.com/v1/pages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        data = {
            "parent": {"database_id": database_id},
            "properties": {
                "العميل": {"title": [{"text": {"content": name}}]},
                "رقم الهاتف": {"rich_text": [{"text": {"content": phone}}]},
                "العنوان": {"rich_text": [{"text": {"content": address}}]},
                "نوع الخدمة": {"select": {"name": srv_type}},
                "المبلغ الإجمالي": {"number": float(amount)}
            }
        }
        res = requests.post(url, headers=headers, json=data)
        return res.status_code == 200
    except: return False

def save_task_to_firebase(user_email, task_data):
    """حفظ سجل العملية في Firebase"""
    try:
        db.collection("tasks").add({
            "user": user_email,
            "details": task_data,
            "status": "Completed",
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        return True
    except: return False

# --- 4. واجهة التطبيق الرئيسية (Main UI) ---

def main():
    st.title("🏠 Mongez Control Center")
    
    # التحقق من حالة تسجيل الدخول
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # --- بوابة تسجيل الدخول (Admin Login First) ---
    if not st.session_state.authenticated:
        st.subheader("🔐 تسجيل دخول المسؤول")
        with st.container():
            col_a, col_b = st.columns([1, 2])
            with col_a:
                admin_email = st.text_input("بريد المسؤول").strip().lower()
                admin_pass = st.text_input("كلمة المرور", type="password")
                if st.button("دخول النظام"):
                    # التحقق من وجود المسؤول في مجموعة users بصلاحية admin
                    user_ref = db.collection("users").document(admin_email).get()
                    if user_ref.exists:
                        user_data = user_ref.to_dict()
                        if str(user_data.get("password")) == admin_pass:
                            st.session_state.authenticated = True
                            st.session_state.user_email = admin_email
                            st.session_state.user_name = user_data.get("name", "Admin")
                            st.rerun()
                        else: st.error("❌ كلمة المرور غير صحيحة")
                    else: st.error("❌ هذا البريد ليس له صلاحية مسؤول")
        return

    # --- محتوى التطبيق بعد الدخول ---
    st.sidebar.success(f"مرحباً: {st.session_state.user_name}")
    if st.sidebar.button("🚪 تسجيل الخروج"):
        st.session_state.authenticated = False
        st.rerun()

    tab1, tab2 = st.tabs(["🚀 إرسال طلب", "📜 سجل العمليات"])

    with tab1:
        st.subheader("تسجيل طلب جديد في الأنظمة")
        c_name = st.text_input("اسم العميل")
        c_phone = st.text_input("هاتف العميل")
        srv_type = st.selectbox("الخدمة", ["سوق المنجز", "اطلب أي شيء"])
        amount = st.number_input("المبلغ", min_value=0.0)
        address = st.text_area("العنوان")

        if st.button("تشغيل الربط التلقائي"):
            with st.spinner("جاري تحديث Firebase, Notion, و Slack..."):
                # 1. المزامنة
                notion_ok = sync_to_notion(c_name, c_phone, address, srv_type, amount)
                # 2. الحفظ في Firebase
                fb_ok = save_task_to_firebase(st.session_state.user_email, f"{srv_type} لـ {c_name}")
                # 3. إرسال تنبيه سلاك
                send_slack_message(f"✅ طلب جديد: {srv_type} | العميل: {c_name} | بمبلغ: {amount}")

                if notion_ok and fb_ok:
                    st.balloons()
                    st.success("🎉 تم تحديث كافة الأنظمة بنجاح!")
                else:
                    st.warning("⚠️ تمت العملية ولكن قد يكون هناك نقص في ربط Notion.")

    with tab2:
        st.subheader("الأحداث الأخيرة")
        logs = db.collection("tasks").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(5).get()
        for log in logs:
            d = log.to_dict()
            st.info(f"👤 {d.get('user')} | 📝 {d.get('details')} | ⏰ {d.get('timestamp')}")

if __name__ == "__main__":
    main()
