import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import requests

# --- 1. التعرف على فيربايس (Firebase Connection) ---
def initialize_firebase():
    try:
        # التأكد من عدم تكرار الاتصال
        if not firebase_admin._apps:
            # استدعاء بيانات المفتاح من Secrets
            fb_secrets = st.secrets["firebase"]
            
            # تحويل المفتاح الخاص لضمان قراءة السطور الجديدة بشكل صحيح
            private_key = fb_secrets["private_key"].replace("\\n", "\n")
            
            cred_dict = {
                "type": fb_secrets["type"],
                "project_id": fb_secrets["project_id"],
                "private_key_id": fb_secrets["private_key_id"],
                "private_key": private_key,
                "client_email": fb_secrets["client_email"],
                "client_id": fb_secrets["client_id"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            st.success("✅ Connected to Mongeze Database Successfully!")
    except Exception as e:
        st.error(f"❌ Firebase Connection Error: {e}")

# --- 2. التعرف على جوجل (Google AI Key) ---
def get_google_ai_key():
    return st.secrets["google"]["api_key"]

# --- 3. إرسال تنبيه لسلاك (Slack Integration) ---
def send_slack_message(text):
    webhook_url = st.secrets["slack"]["webhook_url"]
    payload = {"text": f"🚀 *Mongeze Update:* {text}"}
    requests.post(webhook_url, json=payload)

# --- 4. إعدادات البريد الإلكتروني (SMTP Setup) ---
def get_email_config():
    return {
        "user": st.secrets["smtp"]["user"],
        "pass": st.secrets["smtp"]["pass"],
        "server": st.secrets["smtp"]["server"],
        "port": st.secrets["smtp"]["port"]
    }

# تشغيل الربط عند فتح التطبيق
initialize_firebase()
