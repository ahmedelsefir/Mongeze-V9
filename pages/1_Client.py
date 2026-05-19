import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

st.set_page_config(page_title="بوابة العميل - منجز", layout="wide")

# --- تفعيل الفايربيز ---
try:
    if not firebase_admin._apps:
        key_dict = json.loads(st.secrets["textkey"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error(f"❌ اتصال قاعدة البيانات مقطوع: {e}")
    db = None

# --- الهيكل الجانبي (طبق الأصل من واجهة دي دي المرفقة) ---
st.sidebar.markdown("""
<div style='text-align: center; padding: 10px;'>
    <img src='https://cdn-icons-png.flaticon.com/512/3135/3135715.png' style='width: 80px; border-radius: 50%;'>
    <h3 style='margin: 10px 0 5px 0;'>AHMED mostafa</h3>
    <p style='color: #888; font-size: 14px;'>تعديل المعلومات الشخصية ✏️</p>
</div>
""", unsafe_allow_html=True)

menu = st.sidebar.radio("🗺️ قائمة العميل الرئيسية", [
    "🚖 طلب مشوار / توصيل طرد", 
    "📜 مشاويري (سجل الرحلات)", 
    "💳 الدفع والمحفظة", 
    "🛡️ مركز السلامة والطوارئ",
    "⚙️ الإعدادات والخصومات"
])

# --- تشغيل الخصائص بناءً على القائمة ---
if menu == "🚖 طلب مشوار / توصيل طرد":
    st.markdown("<h3 style='color: #1E3A8A;'>🛒 طلب خدمة توصيل ومزايدة حية</h3>", unsafe_allow_html=True)
    
    with st.form("order_form"):
        client_name = st.text_input("👤 اسم العميل بالكامل", value="أحمد مصطفى")
        order_details = st.text_area("📝 تفاصيل الشحنة أو وجهة المشوار بدقة")
        suggested_price = st.number_input("💰 ميزانيتك المقترحة للطلب (جنيه)", min_value=10, value=30)
        phone = st.text_input("📱 رقم هاتف التواصل", value="+20 1000000000")
        
        submit = st.form_submit_button("🚀 نشر الطلب لاستقبال عروض السائقين")
        if submit and db:
            db.collection("orders").add({
                "client_name": client_name,
                "order_details": order_details,
                "suggested_price": suggested_price,
                "phone": phone,
                "status": "processing",
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            st.success("🎯 تم نشر طلبك بنجاح وفي انتظار مزايدات الكباتن!")

    # مراقبة وتتبع الطلبات الحالية (التي ظهرت في صورتك الأخيرة)
    st.markdown("---")
    st.markdown("#### 📋 مراقبة وتتبع طلباتك الحالية")
    if db:
        my_orders = db.collection("orders").where("client_name", "==", "أحمد مصطفى").stream()
        for o in my_orders:
            o_data = o.to_dict()
            status = o_data.get("status")
            if status != "⭐ تم الإغلاق والتقييم بالكامل":
                st.info(f"📍 طلبك: {o_data.get('order_details')[:20]}... | الحالة: {status} | السائق المعين: {o_data.get('driver_assigned', 'جاري البحث...')}")

elif menu == "📜 مشاويري (سجل الرحلات)":
    st.subheader("📜 سجل مشاويرك السابقة")
    st.info("هنا تظهر قائمة بكافة الرحلات التي قمت بها مع تفاصيل السائقين والأسعار لتسهيل الرجوع إليها.")

elif menu == "💳 الدفع والمحفظة":
    st.subheader("💳 الإدارة المالية للمحفظة")
    col1, col2 = st.columns(2)
    col1.metric("الرصيد الحالي", "0.00 جنيه")
    col2.selectbox("طريقة الدفع الافتراضية", ["نقداً (Cash)", "بطاقة ائتمان (Visa/Mastercard)", "محفظة إلكترونية"])

elif menu == "🛡️ مركز السلامة والطوارئ":
    st.subheader("🛡️ مركز السلامة والحماية")
    st.error("🚨 زر الطوارئ (SOS): اضغط هنا لمشاركة موقعك فوراً مع الإدارة وجهات الاتصال في حالة أي تجاوز أو خطر.")

elif menu == "⚙️ الإعدادات والخصومات":
    st.subheader("⚙️ إعدادات التطبيق والخصومات")
    st.text_input("إضافة كود الخصم (كوبون)", placeholder="ادخل رمز الكوبون هنا")
    st.toggle("تفعيل التنبيهات الفورية الفويس للطلبات")
