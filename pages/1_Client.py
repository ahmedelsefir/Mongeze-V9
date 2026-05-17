import streamlit as st
import firebase_admin
from firebase_admin import firestore

# 1. إعداد الصفحة وتصميمها
st.set_page_config(page_title="واجهة العميل - منجز", layout="wide")

st.markdown("<h1 style='text-align: center; color: #FF6B35;'>🛒 بوابة العميل الذكية</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>اطلب خدماتك اللوجستية لعام 2026 وسيتم ربطها بالسائق فوراً</p>", unsafe_allow_html=True)
st.markdown("---")

# 2. الطريقة الآمنة بنسبة 100% للاتصال بقاعدة البيانات من الصفحات الفرعية
try:
    if not firebase_admin._apps:
        st.error("الرجاء تشغيل التطبيق من الصفحة الرئيسية أولاً لتفعيل قاعدة البيانات.")
        db = None
    else:
        db = firestore.client()
except Exception as e:
    st.error(f"فشل الاتصال البرمجي بقاعدة البيانات: {e}")
    db = None

# 3. نموذج طلب جديد (لا يظهر كخطأ إذا لم يكتمل الاتصال)
with st.form("client_order_form"):
    st.subheader("📦 إنشاء طلب خدمات لوجستية جديد")
    name = st.text_input("اسم العميل بالكامل")
    details = st.text_area("تفاصيل الشحنة أو الطلب (العنوان، المحتوى، إلخ)")
    submit = st.form_submit_button("إرسال الطلب إلى السائقين")
    
    if submit:
        if name and details:
            if db is not None:
                try:
                    # حفظ الطلب في جدول اسمه orders داخل Firebase
                    db.collection("orders").add({
                        "client_name": name,
                        "order_details": details,
                        "status": "جاري البحث عن سائق",
                        "timestamp": firestore.SERVER_TIMESTAMP
                    })
                    st.success(f"ممتاز يا {name}! تم رفع طلبك على قاعدة البيانات بنجاح وجاري تنبيه السائقين حالاً.")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء إرسال الطلب إلى السيرفر: {e}")
            else:
                st.warning("عذراً، لا يمكن إرسال الطلب حالياً لعدم وجود اتصال نشط بقاعدة البيانات.")
        else:
            st.error("الرجاء ملء جميع الحقول المطلوبة لإتمام الطلب.")
