import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import requests

# 1. إعدادات المنصة
st.set_page_config(page_title="Mongez Admin", page_icon="🛡️", layout="wide")

# 2. تهيئة النظام
def initialize_system():
    if not firebase_admin._apps:
        try:
            fb_dict = dict(st.secrets["firebase"])
            if "private_key" in fb_dict:
                fb_dict["private_key"] = fb_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(fb_dict)
            firebase_admin.initialize_app(cred)
        except: return None
    return firestore.client()

db = initialize_system()

# 3. دالة إرسال سلاك مع معالجة الأخطاء (صمام أمان)
def send_interactive_slack(task_details):
    try:
        # التأكد من وجود المفاتيح قبل الاستخدام
        if "slack" not in st.secrets or "bot_token" not in st.secrets["slack"]:
            st.error("⚠️ خطأ: مفتاح Slack غير معرف في الإعدادات (Secrets)")
            return
        
        token = st.secrets["slack"]["bot_token"]
        url = "https://slack.com/api/chat.postMessage"
        
        payload = {
            "channel": "general",
            "blocks": [
                {"type": "section", "text": {"type": "mrkdwn", "text": f"🚚 *طلب جديد*\n*العميل:* {task_details['name']}\n*التفاصيل:* {task_details['issue']}"}},
                {"type": "actions", "elements": [
                    {"type": "button", "text": {"type": "plain_text", "text": "✅ قبول"}, "style": "primary", "value": "ok"},
                    {"type": "button", "text": {"type": "plain_text", "text": "❌ رفض"}, "style": "danger", "value": "no"}
                ]}
            ]
        }
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        requests.post(url, headers=headers, json=payload)
    except Exception as e:
        st.error(f"حدث خطأ أثناء الإرسال: {e}")

# 4. الواجهة الرئيسية
def main():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🛡️ بوابة منجز")
        if st.button("دخول تجريبي (أحمد السفير)"):
            st.session_state.update({"authenticated": True, "user_name": "أحمد السفير", "user_email": "ahmed@mongez.com"})
            st.rerun()
    else:
        with st.sidebar:
            st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=80)
            st.write(f"👋 أهلاً {st.session_state.user_name}")
            if st.button("خروج"):
                st.session_state.authenticated = False
                st.rerun()

        t1, t2 = st.tabs(["🍔 سوق المطاعم", "📦 أطلب أي شيء"])

        with t1:
            st.subheader("🍟 المطاعم المتاحة حولك")
            # عرض المطاعم بشكل كروت احترافية
            m_col1, m_col2 = st.columns(2)
            
            with m_col1:
                with st.container(border=True):
                    st.image("https://img.freepik.com/free-photo/delicious-burger-with-fresh-ingredients_23-2150857908.jpg", use_column_width=True)
                    st.markdown("### مطعم كينج برجر")
                    st.markdown("⭐ 4.8 | 🕒 20-30 دقيقة")
                    if st.button("تصفح قائمة الطعام", key="rest1"):
                        st.toast("جاري تحميل المنيو...")

            with m_col2:
                with st.container(border=True):
                    st.image("https://img.freepik.com/free-photo/top-view-pepperoni-pizza-with-mushroom-sausages-bell-peppers-olive-corn-black-wooden_141793-2158.jpg", use_column_width=True)
                    st.markdown("### بيتزا السفير")
                    st.markdown("⭐ 4.5 | 🕒 15-25 دقيقة")
                    if st.button("تصفح قائمة الطعام", key="rest2"):
                        st.toast("جاري تحميل المنيو...")

        with t2:
            st.subheader("📦 خدمة أطلب أي شيء")
            issue = st.text_area("وصف الطلب بالتفصيل", placeholder="مثال: هات لي 2 كيلو برتقال من سوق العبور...", key="order_input")
            
            c1, c2 = st.columns([1, 4])
            with c1:
                if st.button("🚫 إلغاء", use_container_width=True):
                    st.info("تم مسح البيانات")
                    st.rerun() # لإعادة تحميل الصفحة ومسح المدخلات
            with c2:
                if st.button("🚀 تأكيد وتنبيه المندوبين", use_container_width=True):
                    if issue:
                        send_interactive_slack({"name": st.session_state.user_name, "issue": issue})
                        st.success("✅ تم إرسال الطلب بنجاح لسلاك!")
                    else:
                        st.warning("الرجاء كتابة تفاصيل الطلب أولاً.")

if __name__ == "__main__":
    main()
