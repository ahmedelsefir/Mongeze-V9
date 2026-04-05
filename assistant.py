import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# 1. تهيئة الاتصال بـ Firebase (مرة واحدة فقط)
if not firebase_admin._apps:
    # جلب البيانات من Streamlit Secrets التي أعددناها سوياً
    fb_dict = st.secrets["firebase"]
    cred = credentials.Certificate(fb_dict)
    firebase_admin.initialize_app(cred)

db = firestore.client()

def check_user_access(email_to_check):
    """
    دالة للتحقق هل الإيميل موجود في مجموعة 'users' في Firebase أم لا
    """
    try:
        # البحث في مجموعة (Collection) تسمى 'users'
        # نفترض أن المستند (Document ID) هو الإيميل نفسه
        user_ref = db.collection("users").document(email_to_check).get()
        
        if user_ref.exists:
            return True, user_ref.to_dict()
        else:
            return False, None
    except Exception as e:
        st.error(f"حدث خطأ في الاتصال بقاعدة البيانات: {e}")
        return False, None

# --- واجهة بوابة دخول المنجز ---
st.title("🦅 S9 بوابة دخول المنجز")

email_input = st.text_input("البريد الإلكتروني", placeholder="example@gmail.com")

if st.button("تفعيل الدخول"):
    if email_input:
        is_allowed, user_data = check_user_access(email_input.lower().strip())
        
        if is_allowed:
            st.success(f"✅ مرحباً بك يا {user_data.get('name', 'قائد')}! تم تسجيل الدخول بنجاح.")
            st.session_state["authenticated"] = True
            st.session_state["user_email"] = email_input
            # هنا تضع كود الانتقال للوحة التحكم (مشروع منجز)
        else:
            st.error("❌ البريد غير مسجل في قاعدة بيانات Firebase")
    else:
        st.warning("⚠️ يرجى إدخال البريد الإلكتروني أولاً")
