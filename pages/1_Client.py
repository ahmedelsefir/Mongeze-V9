import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

# ##########################################
# # --- 1. إعدادات الصفحة والواجهة المرئية ---
# ##########################################
st.set_page_config(page_title="واجهة العميل - منجز", layout="wide")

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🛒 بوابة العميل الذكية</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #555;'>اطلب خدماتك اللوجستية لعام 2026 وسيتم ربطها بأقرب سائق فوراً</p>", unsafe_allow_html=True)
st.markdown("---")

# ##########################################
# # --- 2. تفعيل الاتصال المستقل بـ Firebase ---
# ##########################################
try:
    if not firebase_admin._apps:
        key_dict = json.loads(st.secrets["textkey"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error(f"❌ فشل الاتصال التلقائي بقاعدة البيانات: {e}")
    db = None

# ##########################################
# # --- 3. نموذج إنشاء الطلب المتوافق مع السائق ---
# ##########################################
with st.form("client_order_form"):
    st.subheader("📦 إنشاء طلب توصيل وشحن جديد")
    
    # حقول إدخال البيانات scannable ومنظمة جداً
    name = st.text_input("👤 اسم العميل بالكامل")
    details = st.text_area("📝 تفاصيل الشحنة أو الطرد (مثال: توصيل أكل، مستندات مستعجلة)")
    
    # زر الإرسال الرئيسي
    submit = st.form_submit_button("🚀 إرسال الطلب إلى شبكة السائقين")
    
    if submit:
        if name and details:
            if db is not None:
                try:
                    # # --- التوافق البرمجي الحاسم (Match Core) ---
                    # هنا بنرفع الطلب بالحالة القياسية 'processing' عشان كود السائق يلقطها فوراً
                    db.collection("orders").add({
                        "client_name": name,
                        "order_details": details,
                        "status": "processing",  # القيمة السرية الموحدة لربط الفروع
                        "timestamp": firestore.SERVER_TIMESTAMP
                    })
                    st.success(f"🎯 ممتاز يا {name}! تم رفع طلبك بنجاح، وظهر الآن في رادار كابتن التوصيل.")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء حفظ الطلب في السحاب: {e}")
            else:
                st.error("لا يمكن إرسال الطلب حالياً لعدم استقرار اتصال قاعدة البيانات.")
        else:
            st.error("⚠️ الرجاء ملء اسمك وتفاصيل الشحنة أولاً قبل الإرسال.")
