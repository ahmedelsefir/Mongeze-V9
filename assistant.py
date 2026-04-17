import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import requests
import json

# 1. Page Configuration
st.set_page_config(
    page_title="Mongez Smart Assistant",
    page_icon="🏠",
    layout="wide"
)

# 2. Firebase & Tools Initialization
def initialize_system():
    if not firebase_admin._apps:
        try:
            fb_dict = dict(st.secrets["firebase"])
            if "private_key" in fb_dict:
                fb_dict["private_key"] = fb_dict["private_key"].replace("\\n", "\n")
            
            cred = credentials.Certificate(fb_dict)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"System Initialization Error: {e}")
            return None
    return firestore.client()

db = initialize_system()

# 3. Automation Functions (Firebase, Slack & Notion)

def create_user_account(email, password, name, phone):
    """إنشاء بروفايل للعميل باستخدام البريد الإلكتروني كاسم للمستند لضمان سهولة الدخول"""
    try:
        email = email.strip().lower() 
        users_ref = db.collection("users").document(email)
        
        if users_ref.get().exists:
            return False, "⚠️ هذا البريد مسجل مسبقاً"
        
        users_ref.set({
            "email": email,
            "name": name,
            "phone": phone,
            "password": password, 
            "role": "client",
            "created_at": firestore.SERVER_TIMESTAMP
        })
        return True, "✅ تم إنشاء الحساب بنجاح! جرب الدخول الآن."
    except Exception as e:
        return False, str(e)

def send_slack_message(message):
    """إرسال تنبيهات لـ Slack"""
    url = "https://slack.com/api/chat.postMessage"
    token = st.secrets["slack"]["bot_token"]
    payload = {"channel": "general", "text": message}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        return response.json()
    except:
        return {"ok": False}

def sync_to_notion(name, phone, address, srv_type, amount):
    """المزامنة المتقدمة مع Notion"""
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
        response = requests.post(url, headers=headers, json=data)
        return response.status_code == 200
    except:
        return False

def save_to_mongez_db(user_email, task_name):
    """حفظ السجلات في Firebase"""
    if db:
        doc_ref = db.collection("tasks").document()
        doc_ref.set({
            "user": user_email,
            "task": task_name,
            "status": "Completed",
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        return True
    return False

# 4. Main Application UI
def main():
    st.title("🏠 Mongez Control Center")
    st.markdown("---")

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        auth_tab1, auth_tab2 = st.tabs(["🔑 تسجيل دخول", "📝 إنشاء حساب جديد"])
        
        with auth_tab1:
            email = st.text_input("البريد الإلكتروني", key="login_email").strip().lower()
            password = st.text_input("كلمة المرور", type="password", key="login_pass")
            
            if st.button("دخول للمنصة", key="login_btn"):
                if email and password:
                    user_doc = db.collection("users").document(email).get()
                    if user_doc.exists:
                        user_data = user_doc.to_dict()
                        if str(user_data.get("password")) == str(password):
                            st.session_state.authenticated = True
                            st.session_state.user_email = email
                            st.session_state.user_name = user_data.get("name", "مهندس المنجز")
                            st.rerun()
                        else:
                            st.error("❌ خطأ في كلمة المرور")
                    else:
                        st.error("❌ هذا الحساب غير مسجل في النظام")
                else:
                    st.warning("يرجى إدخال البريد وكلمة المرور")

        with auth_tab2:
            new_name = st.text_input("الاسم بالكامل", key="reg_name")
            new_email = st.text_input("البريد الإلكتروني", key="reg_email")
            new_phone = st.text_input("رقم الهاتف", key="reg_phone")
            new_pass = st.text_input("كلمة المرور", type="password", key="reg_pass")
            if st.button("تأكيد التسجيل", key="reg_btn"):
                if new_name and new_email and new_pass:
                    ok, msg = create_user_account(new_email, new_pass, new_name, new_phone)
                    if ok: st.success(msg)
                    else: st.error(msg)
                else: st.warning("يرجى ملء كافة الخانات")
    else:
        # Sidebar Profile
        st.sidebar.success("✔️ System Online")
        st.sidebar.write(f"Logged in as: {st.session_state.user_name}")
        st.sidebar.write(f"Email: {st.session_state.user_email}")

        tab1, tab2 = st.tabs(["🚀 Launch Automation", "📜 Database Logs"])

        with tab1:
            st.subheader("تسجيل طلب جديد")
            col1, col2 = st.columns(2)
            with col1:
                c_name = st.text_input("الاسم", value=st.session_state.user_name, key="c_name")
                c_phone = st.text_input("رقم الهاتف", key="c_phone")
            with col2:
                srv_type = st.selectbox("نوع الخدمة", ["سوق المنجز", "اطلب أي شيء"], key="c_srv")
                amount = st.number_input("المبلغ الإجمالي", min_value=0.0, key="c_amount")
            
            address = st.text_area("العنوان التفصيلي / تفاصيل الطلب", key="c_addr")

            if st.button("Run Sync & Notify", key="main_sync_btn"):
                if c_name and address:
                    with st.spinner("جاري المزامنة مع الأنظمة..."):
                        saved = save_to_mongez_db(st.session_state.user_email, f"{srv_type}: {c_name}")
                        slack_res = send_slack_message(f"🚀 طلب جديد من {c_name}: {srv_type}")
                        notion_saved = sync_to_notion(c_name, c_phone, address, srv_type, amount)

                        if saved and notion_saved:
                            st.balloons()
                            st.success("✅ تم المزامنة بنجاح مع Notion و Firebase!")
                        else:
                            st.warning("⚠️ تم التنفيذ بنجاح جزئي. راجع إعدادات الربط.")
                else:
                    st.error("يرجى إدخال البيانات الأساسية (الاسم والعنوان).")

        with tab2:
            st.subheader("📜 سجلات العمليات الأخيرة")
            try:
                # جلب آخر 10 عمليات مسجلة في قاعدة البيانات وترتيبها بالأحدث
                logs = db.collection("tasks").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(10).get()
                
                if logs:
                    data_list = []
                    for doc in logs:
                        item = doc.to_dict()
                        data_list.append({
                            "المستخدم": item.get("user"),
                            "الطلب": item.get("task"),
                            "الحالة": item.get("status"),
       
