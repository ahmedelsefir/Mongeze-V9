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

# 3. Automation Functions (Slack & Firebase)
def send_slack_message(message):
    """Sends a notification to your Slack Workspace."""
    url = "https://slack.com/api/chat.postMessage"
    token = st.secrets["slack"]["bot_token"]
    payload = {
        "channel": "general", # You can change this to your specific channel name or ID
        "text": message
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.json()

def save_to_mongez_db(user_email, task_name):
    """Saves the task and logs it in Firebase."""
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

    # Security Check
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.subheader("🔑 Secure Partner Access")
        email = st.text_input("Admin Email")
        password = st.text_input("Access Key", type="password")
        
        if st.button("Authorize"):
            if email == st.secrets["SMTP_USER"] and password != "":
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.rerun()
            else:
                st.error("Access Denied.")
    else:
        # Dashboard UI
        st.sidebar.success("✅ System Online")
        st.sidebar.write(f"Logged in as: {st.session_state.user_email}")
        
        tab1, tab2 = st.tabs(["🚀 Launch Automation", "📈 Database Logs"])

        with tab1:
            st.subheader("Create New Operation")
            task_input = st.text_input("Enter Task or Order Name", placeholder="e.g., New Delivery Request")
            
            if st.button("Run Sync & Notify"):
                if task_input:
                    with st.spinner("Syncing systems..."):
                        # Step A: Save to Firebase
                        saved = save_to_mongez_db(st.session_state.user_email, task_input)
                        
                        # Step B: Notify Slack
                        slack_res = send_slack_message(f"🚀 *New Task in Mongez:* {task_input} by {st.session_state.user_email}")
                        
                        if saved and slack_res.get("ok"):
                            st.balloons()
                            st.success("Task Synced to Firebase & Slack Notification Sent! ✅")
                        else:
                            st.warning("Task saved, but Slack notification failed. Check Bot Token.")
                else:
                    st.error("Please enter a task name.")

        with tab2:
            st.subheader("Recent Activities (Firebase)")
            if db:
                tasks = db.collection("tasks").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(5).stream()
                for task in tasks:
                    data = task.to_dict()
                    st.text(f"🕒 {data.get('timestamp')} | {data.get('user')} | Task: {data.get('task')}")

        if st.sidebar.button("Secure Logout"):
            st.session_state.authenticated = False
            st.rerun()

if __name__ == "__main__":
    main()
# --- وظائف المزامنة المطورة ---

def sync_to_notion(task_name):
    """إرسال البيانات إلى Notion"""
    import requests
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
                "Name": {"title": [{"text": {"content": task_name}}]}
            }
        }
        response = requests.post(url, headers=headers, json=data)
        return response.status_code == 200
    except Exception as e:
        return False

# --- الواجهة الرئيسية الموحدة (بدون تكرار) ---
def main():
    st.title("🏠 Mongez Control Center")
    st.markdown("---")

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.subheader("🔑 Secure Partner Access")
        email = st.text_input("Admin Email", key="login_email") # مفتاح فريد لمنع التكرار
        password = st.text_input("Access Key", type="password", key="login_pass")

        if st.button("Authorize"):
            if email == st.secrets["SMTP_USER"] and password != "":
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.rerun()
            else:
                st.error("Access Denied.")
    else:
        st.sidebar.success("✔️ System Online")
        st.sidebar.write(f"Logged in as: {st.session_state.user_email}")

        tab1, tab2 = st.tabs(["🚀 Launch Automation", "📜 Database Logs"])

        with tab1:
            st.subheader("Create New Operation")
            task_input = st.text_input("Enter Task Name", placeholder="e.g., New Order", key="task_in")

            if st.button("Run Sync & Notify"):
                if task_input:
                    with st.spinner("Syncing systems..."):
                        # استخدام الدوال المعرفة سابقاً في ملفك
                        saved = save_to_mongez_db(st.session_state.user_email, task_input)
                        slack_res = send_slack_message(f"🚀 New Task: {task_input}")
                        notion_saved = sync_to_notion(task_input)

                        if saved and slack_res.get("ok") and notion_saved:
                            st.balloons()
                            st.success("✅ Triple Sync Success: Firebase, Slack & Notion!")
                        else:
                            st.warning("⚠️ Partial Success. Check Notion/Slack settings.")
                else:
                    st.error("Please enter a task name.")

        if st.sidebar.button("Secure Logout"):
            st.session_state.authenticated = False
            st.rerun()

if __name__ == "__main__":
    main()
