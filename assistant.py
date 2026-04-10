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
    """إنشاء بروفايل للعميل في Firebase"""
    try:
        users_ref = db.collection("users").document(email)
        if users_ref.get().exists:
            return False, "⚠️ هذا البريد مسجل مسبقاً"
        
        users_ref.set({
            "name": name,
            "phone": phone,
            "password": password, 
            "role": "client",
            "created_at": firestore.SERVER_TIMESTAMP
        })
        return True, "✅ تم إنشاء الحساب بنجاح!"
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
        # نظام الدخول والتسجيل الجديد
        auth_tab1, auth_tab2 = st.tabs(["🔑 تسجيل دخول", "📝 إنشاء حساب جديد"])
        
        with auth_tab1:
            email = st.text_input("البريد الإلكتروني", key="login_email")
            password = st.text_input("كلمة المرور", type="password", key="login_pass")
            if st.button("دخول للمنصة", key="login_btn"):
                user_doc = db.collection("users").document(email).get()
                if user_doc.exists and user_doc.to_dict()["password"] == password:
                    st.session_state.authenticated = True
                    st.session_state.user_email = email
                    st.session_state.user_name = user_doc.to_dict()["name"]
                    st.rerun()
                else:
                    st.error("خطأ في بيانات الدخول")

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
        st.sidebar.success("✔️ System Online")
        st.sidebar.write(f"Logged in as: {st.session_state.user_name}")

        tab1, tab2 = st.tabs(["🚀 Launch Automation", "📜 Database Logs"])

        with tab1:
            st.subheader("تسجيل طلب (سوق متعدد / اطلب أي شيء)")
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
                    with st.spinner("Syncing systems..."):
                        # المزامنة الشاملة
                        saved = save_to_mongez_db(st.session_state.user_email, f"{srv_type}: {c_name}")
                        slack_res = send_slack_message(f"🚀 طلب جديد: {srv_type} للعميل {c_name}")
                        notion_saved = sync_to_notion(c_name, c_phone, address, srv_type, amount)

                        if saved and notion_saved:
                            st.balloons()
                            st.success("✅ تم المزامنة بنجاح مع Notion و Firebase!")
                        else:
                            st.warning("⚠️ نجاح جزئي. تأكد من إعدادات Notion.")
                else:
                    st.error("يرجى إدخال البيانات الأساسية.")

        if st.sidebar.button("Secure Logout", key="logout_btn"):
            st.session_state.authenticated = False
            st.rerun()

if __name__ == "__main__":
    main()
