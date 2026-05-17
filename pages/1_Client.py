import streamlit as st
from firebase_admin import firestore

# التأكد من الاتصال بقاعدة البيانات
try:
    db = firestore.client()
except Exception:
    st.error("فشل الاتصال بقاعدة البيانات، تأكد من إعدادات Firebase")

st.set_page_config(page_title="واجهة العميل - منجز", layout="wide")

st.markdown("<h1 style='text-align: center; color: #FF6B35;'>🛒 بوابة العميل الذكية</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>اطلب خدماتك اللوجستية لعام 2026 وسيتم ربطها بالسائق فوراً</p>", unsafe_allow_html=True)
st.markdown("---")

with st.form("client_order_form"):
    st.subheader("📦 إنشاء طلب جديد")
    name = st.text_input("اسم العميل بالكامل")
    details = st.text_area("تفاصيل الشحنة أو الطلب")
    submit = st.form_submit_button("إرسال الطلب إلى السائقين")
    
    if submit:
        if name and details:
            try:
                # حفظ الطلب في جدول اسمه orders داخل Firebase
                db.collection("orders").add({
                    "client_name": name,
                    "order_details": details,
                    "status": "جاري البحث عن سائق",
                    "timestamp": firestore.SERVER_TIMESTAMP
                })
                st.success(f"ممتاز يا {name}! تم رفع طلبك على قاعدة البيانات وجاري تنبيه السائقين حالاً.")
            except Exception as e:
                st.error(f"حدث خطأ أثناء إرسال الطلب: {e}")
        else:
            st.error("الرجاء ملء جميع الحقول المطلوبة.")
