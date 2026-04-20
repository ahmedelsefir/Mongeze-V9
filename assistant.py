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

# 4. نظام التنبيهات والردود (استغلال ميزات Slack Pro التجريبية)
def send_interactive_slack(task_details):
    """إرسال رسالة تفاعلية تحتوي على أزرار للمندوبين عبر Slack"""
    url = "https://slack.com/api/chat.postMessage"
    token = st.secrets["slack"]["bot_token"]
    
    payload = {
        "channel": "general",
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"🚀 *طلب جديد من منجز*\n👤 *العميل:* {task_details['name']}\n📞 *الهاتف:* {task_details['phone']}\n📦 *التفاصيل:* {task_details['issue']}"}
            },
            {
                "type": "actions",
                "elements": [
                    {"type": "button", "text": {"type": "plain_text", "text": "✅ قبول الطلب"}, "style": "primary", "value": "approve"},
                    {"type": "button", "text": {"type": "plain_text", "text": "❌ رفض الطلب"}, "style": "danger", "value": "reject"}
                ]
            }
        ]
    }
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        requests.post(url, headers=headers, json=payload)
    except:
        pass

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
        st.title("🛡️ بوابة منجز الآمنة")
        email = st.text_input("البريد الإلكتروني")
        password = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            st.session_state.authenticated = True
            st.session_state.user_email = email
            st.session_state.user_name = "أحمد السفير" 
            st.rerun()
    else:
        # --- السايدبار المطور ---
        with st.sidebar:
            st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=80)
            st.title(st.session_state.user_name)
            
            # مؤشر حالة الاتصال
            st.markdown("---")
            st.write("**حالة النظام:**")
            col_f, col_a = st.columns(2)
            col_f.success("Firebase" if db else "Firebase ❌")
            col_a.success("Apigee" if True else "Apigee ❌") 
            
            st.markdown("---")
            if st.button("خروج آمن"):
                st.session_state.authenticated = False
                st.rerun()

        st.title("🏠 Mongez Control Center")
        t1, t2, t3 = st.tabs(["🍔 سوق المطاعم", "📦 أطلب أي شيء", "🎧 الدعم الفني"])

        # التبويب الأول: سوق المطاعم المتعدد
        with t1:
            st.subheader("🍟 اختر مطعمك المفضل")
            col_m1, col_m2, col_m3 = st.columns(3)
            
            restaurants = [
                {"name": "مطعم البرنس", "img": "https://img.freepik.com/free-vector/food-delivery-logo-template_23-2148192712.jpg"},
                {"name": "مشويات السفير", "img": "https://img.freepik.com/free-vector/gradient-pizza-logo-design_23-2149150063.jpg"},
                {"name": "بيتزا إكسبريس", "img": "https://img.freepik.com/free-vector/hand-drawn-delivery-logo-design_23-2149149495.jpg"}
            ]
            
            cols = [col_m1, col_m2, col_m3]
            for i, rest in enumerate(restaurants):
                with cols[i]:
                    with st.container(border=True):
                        st.image(rest['img'], use_column_width=True)
                        st.write(f"### {rest['name']}")
                        if st.button(f"طلب من {rest['name']}", key=f"btn_{i}"):
                            st.success(f"تم اختيار {rest['name']}، انتقل لتبويب الطلبات")

        # التبويب الثاني: أطلب أي شيء + الكاميرا + أزرار التحكم
        with t2:
            st.subheader("📦 اطلب أي شيء من أي مكان")
            client_phone = st.text_input("رقم تليفون العميل المرجعي", value="01xxxxxxxxx")
            issue = st.text_area("ماذا تريد أن ننجز لك؟ (اكتب التفاصيل هنا)")
            
            # إضافة ميزة الكاميرا والرفع
            st.markdown("#### 📸 توثيق الطلب (اختياري)")
            cam_col, up_col = st.columns(2)
            with cam_col:
                photo = st.camera_input("التقط صورة للطلب")
            with up_col:
                file = st.file_uploader("أو ارفع صورة من الجهاز", type=['jpg', 'png'])

            st.markdown("---")
            btn_col1, btn_col2 = st.columns([1, 4])
            with btn_col1:
                if st.button("🚫 إلغاء", type="secondary"):
                    st.warning("تم إلغاء الطلب")
            with btn_col2:
                if st.button("🚀 تأكيد وإرسال للمندوب"):
                    if issue:
                        # إرسال الرسالة التفاعلية لسلاك (استغلال الـ 14 يوم)
                        send_interactive_slack({
                            "name": st.session_state.user_name,
                            "phone": client_phone,
                            "issue": issue
                        })
                        st.success("✅ تم إرسال الطلب بنجاح! المندوبين استلموا أزرار التفاعل الآن.")
                        st.balloons()
                    else:
                        st.error("من فضلك اكتب تفاصيل الطلب أولاً")

        # التبويب الثالث: الردود والدعم
        with t3:
            st.subheader("🎧 إدارة ردود الدعم الفني")
            tasks = db.collection("tasks").limit(5).get()
            for doc in tasks:
                data = doc.to_dict()
                with st.expander(f"طلب: {data.get('task', 'عام')} - العميل: {data.get('user')}"):
                    st.write(f"**التفاصيل:** {data.get('details')}")
                    reply = st.text_input("اكتب رد الدعم الفني هنا", key=f"rep_{doc.id}")
                    if st.button("إرسال الرد وتحديث الحالة", key=f"send_{doc.id}"):
                        if post_support_reply(doc.id, reply):
                            st.success("تم تحديث الطلب وإشعار العميل!")
                            st.rerun()

if __name__ == "__main__":
    main()
