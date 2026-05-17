import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

# 1. إعداد الصفحة
st.set_page_config(page_title="واجهة العميل - منجز", layout="wide")

st.markdown("<h1 style='text-align: center; color: #FF6B35;'>🛒 بوابة العميل الذكية</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>اطلب خدماتك اللوجستية لعام 2026 وسيتم ربطها بالسائق فوراً</p>", unsafe_allow_html=True)
st.markdown("---")

# 2. تفعيل الاتصال المباشر والمستقل بـ Firebase
try:
    if not firebase_admin._apps:
        # قراءة مفتاح الـ JSON من إعدادات السيرفر الآمنة Secrets
        key_dict = json.loads(st.secrets["textkey"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error(f"فشل الاتصال التلقائي بقاعدة البيانات: {e}")
    db = None

# 3. نموذج الطلب
with st.form("client_order_form"):
    st.subheader("📦 إنشاء طلب خدمات لوجستية جديد")
    name = st.text_input("اسم العميل بالكامل")
    details = st.text_area("تفاصيل الشحنة أو الطلب")
    submit = st.form_submit_button("إرسال الطلب إلى السائقين")
    
    if submit:
        if name and details:
            if db is not None:
                try:
                    db.collection("orders").add({
                        "client_name": name,
                        "order_details": details,
                        "status": "جاري البحث عن سائق",
                        "timestamp": firestore.SERVER_TIMESTAMP
                    })
                    st.success(f"ممتاز يا {name}! تم رفع طلبك على قاعدة البيانات الحية بنجاح.")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء حفظ الطلب: {e}")
            else:
                st.error("لا يمكن إرسال الطلب حالياً لعدم استقرار اتصال قاعدة البيانات.")
        else:
            st.error("الرجاء ملء جميع الحقول المطلوبة.")
