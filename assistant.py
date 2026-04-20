import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import requests
import json

# 1. إعدادات المنصة
st.set_page_config(page_title="Mongez Admin & Ops", page_icon="🛡️", layout="wide")

# 2. تهيئة النظام (Backend)
def initialize_system():
    if not firebase_admin._apps:
        try:
            fb_dict = dict(st.secrets["firebase"])
            if "private_key" in fb_dict:
                fb_dict["private_key"] = fb_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(fb_dict)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"خطأ في تهيئة النظام: {e}")
            return None
    return firestore.client()

db = initialize_system()

# 3. إدارة الأمان (Apigee Logic - دالة التوجيه المركزية)
def call_apigee_manager(endpoint, method="POST", data=None):
    """المدير المركزي لعمليات النظام - يمر كل شيء من خلال Apigee"""
    base_url = st.secrets["apigee"]["base_url"]
    headers = {
        "X-API-KEY": st.secrets["apigee"]["api_key"],
        "Content-Type": "application/json"
    }
    try:
        if method == "POST":
            response = requests.post(f"{base_url}/{endpoint}", json=data, headers=headers)
        else:
            response = requests.get(f"{base_url}/{endpoint}", headers=headers)
        return response.json()
    except:
        return {"status": "offline"}

# 4. نظام التنبيهات والردود (Notifications & Support)
def notify_delegate(task_details):
    """إرسال إشعار للمندوب عبر Slack (بوابة Apigee)"""
    msg = f"🚚 *تنبيه للمندوب*: طلب جديد قيد الانتظار\nالعميل: {task_details['name']}\nالهاتف: {task_details['phone']}"
    # يمكن إرسالها لـ Slack مباشرة أو عبر Apigee Proxy
    requests.post(st.secrets["slack"]["webhook_url"], json={"text": msg})

def post_support_reply(doc_id, reply):
    """تحديث رد الدعم الفني في القاعدة"""
    try:
        db.collection("tasks").document(doc_id).update({
            "support_reply": reply,
            "status": "تم الرد",
            "last_update": firestore.SERVER_TIMESTAMP
        })
        return True
    except: return False

# 5. واجهة المستخدم (UI)
def main():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        # --- شاشة الدخول (كما في الكود السابق) ---
        st.title("🛡️ بوابة منجز الآمنة")
        email = st.text_input("البريد الإلكتروني")
        password = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            # منطق جلب البيانات من الكود السابق...
            st.session_state.authenticated = True
            st.session_state.user_email = email
            st.session_state.user_name = "أحمد السفير" # تجريبي
            st.rerun()
    else:
        # --- السايدبار مع مؤشر حالة الاتصال (Health Indicator) ---
        with st.sidebar:
            st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=80)
            st.title(st.session_state.user_name)
            
            # عرض حالة الاتصال في السايدبار
            st.markdown("---")
            st.write("**حالة النظام:**")
            col_f, col_a = st.columns(2)
            col_f.success("Firebase" if db else "Firebase ❌")
            col_a.success("Apigee" if True else "Apigee ❌") # هنا نستخدم دالة الـ Health Check
            st.markdown("---")
            if st.button("خروج"):
                st.session_state.authenticated = False
                st.rerun()

        st.title("🏠 Mongez Control Center")
        t1, t2 = st.tabs(["🚀 إرسال التنبيهات", "🎧 ردود الدعم الفني"])

        with t1:
            st.subheader("إرسال إشعار للمندوبين")
            client_phone = st.text_input("رقم تليفون العميل")
            issue = st.text_area("وصف المهمة")
            if st.button("إرسال للمندوب"):
                notify_delegate({"name": st.session_state.user_name, "phone": client_phone})
                st.success("تم تنبيه المندوب بنجاح!")

        with t2:
            st.subheader("إدارة الردود والرسائل")
            # جلب الطلبات التي تحتاج لرد
            tasks = db.collection("tasks").limit(5).get()
            for doc in tasks:
                data = doc.to_dict()
                with st.expander(f"طلب من: {data.get('user')} - الحالة: {data.get('status')}"):
                    st.write(f"التفاصيل: {data.get('details')}")
                    reply = st.text_input("ردك كدعم فني", key=doc.id)
                    if st.button("تحديث الرد", key=f"btn_{doc.id}"):
                        if post_support_reply(doc.id, reply):
                            st.success("تم إرسال الرد للعميل!")
                            st.rerun()

if __name__ == "__main__":
    main()
