import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import requests
import json

# ==========================================
# 1. إعدادات الصفحة والهوية البصرية
# ==========================================
st.set_page_config(
    page_title="Mongez Smart Assistant",
    page_icon="🚀",
    layout="wide"
)

# ==========================================
# 2. تهيئة النظام والربط بالقاعدة (Backend)
# ==========================================
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

# ==========================================
# 3. دوال Apigee و Logic النظام (The Brain)
# ==========================================

def get_user_profile(email):
    """جلب بيانات المستخدم من Firestore"""
    try:
        user_doc = db.collection("users").document(email).get()
        return user_doc.to_dict() if user_doc.exists else None
    except: return None

def create_user_account(email, password, name, phone):
    """إنشاء بروفايل جديد (Backend)"""
    try:
        email = email.strip().lower() 
        users_ref = db.collection("users").document(email)
        if users_ref.get().exists:
            return False, "⚠️ هذا البريد مسجل مسبقاً"
        
        users_ref.set({
            "email": email, "name": name, "phone": phone, "password": password, 
            "role": "client", "job_title": "عضو منجز", 
            "profile_pic": "https://cdn-icons-png.flaticon.com/512/149/149071.png", # صورة افتراضية
            "created_at": firestore.SERVER_TIMESTAMP
        })
        return True, "✅ تم إنشاء الحساب بنجاح!"
    except Exception as e: return False, str(e)

def send_slack_notification(message):
    """تنبيه المندوبين (Apigee-ready Logic)"""
    try:
        url = "https://slack.com/api/chat.postMessage"
        token = st.secrets["slack"]["bot_token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {"channel": "general", "text": message}
        requests.post(url, headers=headers, json=payload)
    except: pass

def add_support_reply(task_id, reply_text):
    """دالة رد الدعم الفني وتحديث الحالة"""
    try:
        db.collection("tasks").document(task_id).update({
            "support_reply": reply_text,
            "status": "In Progress",
            "replied_at": firestore.SERVER_TIMESTAMP
        })
        return True
    except: return False

# ==========================================
# 4. واجهة المستخدم الرئيسية (Frontend UI)
# ==========================================

def main():
    # التحقق من حالة الدخول
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # --- شاشة تسجيل الدخول والترحيب ---
    if not st.session_state.authenticated:
        st.title("🏠 مرحبا بكم في منصة منجز")
        st.info("نظام الإدارة الذكي للخدمات اللوجستية")
        
        tab_log, tab_reg = st.tabs(["🔑 تسجيل الدخول", "📝 إنشاء حساب جديد"])
        
        with tab_log:
            email = st.text_input("البريد الإلكتروني").strip().lower()
            password = st.text_input("كلمة المرور", type="password")
            if st.button("دخول للمنصة"):
                user_data = get_user_profile(email)
                if user_data and str(user_data.get("password")) == str(password):
                    st.session_state.update({
                        "authenticated": True, "user_email": email,
                        "user_name": user_data.get("name"),
                        "user_phone": user_data.get("phone"),
                        "user_job": user_data.get("job_title"),
                        "user_pic": user_data.get("profile_pic"),
                        "role": user_data.get("role")
                    })
                    st.success(f"تم الدخول بنجاح، أهلاً {st.session_state.user_name}")
                    st.rerun()
                else: st.error("❌ البريد أو كلمة المرور غير صحيحة")
        
        with tab_reg:
            n_name = st.text_input("الاسم بالكامل")
            n_email = st.text_input("البريد الإلكتروني (سيكون معرفك الخاص)")
            n_phone = st.text_input("رقم الهاتف")
            n_pass = st.text_input("اختر كلمة مرور", type="password")
            if st.button("تأكيد إنشاء الحساب"):
                if n_name and n_email and n_pass:
                    ok, msg = create_user_account(n_email, n_pass, n_name, n_phone)
                    if ok: st.success(msg)
                    else: st.error(msg)
                else: st.warning("من فضلك املأ جميع الخانات")

    # --- واجهة المنصة (بعد تسجيل الدخول بنجاح) ---
    else:
        # Sidebar: بروفايل المستخدم الاحترافي
        with st.sidebar:
            st.image(st.session_state.user_pic, width=100)
            st.title(st.session_state.user_name)
            st.markdown(f"**الوظيفة:** {st.session_state.user_job}")
            st.markdown(f"**الهاتف:** {st.session_state.user_phone}")
            st.markdown("---")
            st.success("✔️ نظام منجز متصل (Online)")
            if st.button("تسجيل الخروج"):
                st.session_state.authenticated = False
                st.rerun()

        st.title("🏠 Mongez Control Center")
        
        tab_action, tab_logs = st.tabs(["🚀 طلب خدمة جديدة", "📜 سجلات العمليات والردود"])

        # التبويب الأول: طلب الخدمة والتنبيهات
        with tab_action:
            st.subheader("ماذا تريد أن تنجز اليوم؟")
            col1, col2 = st.columns(2)
            with col1:
                srv = st.selectbox("نوع الخدمة", ["سوق المنجز", "اطلب أي شيء", "دعم فني سريع"])
                amount = st.number_input("الميزانية التقديرية (اختياري)", min_value=0.0)
            with col2:
                addr = st.text_area("تفاصيل الطلب / عنوان التسليم")
            
            if st.button("إرسال الطلب للمندوبين"):
                if addr:
                    with st.spinner("جاري معالجة الطلب وتنبيه الفريق..."):
                        # 1. حفظ في Firestore
                        task_ref = db.collection("tasks").document()
                        task_id = task_ref.id
                        task_ref.set({
                            "user": st.session_state.user_email, "task": srv, 
                            "details": addr, "amount": amount,
                            "status": "Pending", "timestamp": firestore.SERVER_TIMESTAMP,
                            "support_reply": "جاري مراجعة طلبك من قبل الدعم الفني..."
                        })
                        
                        # 2. إرسال تنبيه للمندوبين عبر Slack
                        msg = f"🚀 *طلب جديد من منجز* \n👤 العميل: {st.session_state.user_name}\n📞 هاتف: {st.session_state.user_phone}\n📦 الخدمة: {srv}\n📍 التفاصيل: {addr}"
                        send_slack_notification(msg)
                        
                        st.balloons()
                        st.success(f"تم إرسال طلبك بنجاح! رقم الطلب: {task_id}")
                else: st.error("من فضلك اكتب تفاصيل الطلب")

        # التبويب الثاني: السجلات والردود (الدعم الفني)
        with tab_logs:
            st.subheader("📦 متابعة طلباتك الأخيرة")
            tasks = db.collection("tasks").where("user", "==", st.session_state.user_email).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(10).get()
            
            if not tasks:
                st.info("لا توجد طلبات سابقة حتى الآن.")
            
            for doc in tasks:
                data = doc.to_dict()
                status_color = "orange" if data.get("status") == "Pending" else "green"
                
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"### الطلب: {data.get('task')}")
                    c1.write(f"📝 {data.get('details')}")
                    c2.markdown(f":{status_color}[الحالة: {data.get('status')}]")
                    
                    st.divider()
                    st.write(f"🎧 **رد الدعم الفني:** {data.get('support_reply')}")
                    
                    # ميزة خاصة لك كأدمن للاختبار والرد
                    if st.session_state.user_email == "ahmedelsefir7@gmail.com": # إيميلك المسجل في القاعدة
                        with st.expander("🛠️ الرد كدعم فني (خاص بك)"):
                            reply_text = st.text_input("اكتب ردك هنا", key=f"reply_{doc.id}")
                            if st.button("إرسال الرد للعميل", key=f"btn_{doc.id}"):
                                if add_support_reply(doc.id, reply_text):
                                    st.success("تم تحديث الرد!")
                                    st.rerun()

if __name__ == "__main__":
    main()
