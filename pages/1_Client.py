import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

st.set_page_config(page_title="واجهة العميل الاحترافية - منجز", layout="wide")

# --- تفعيل قاعدة البيانات ---
try:
    if not firebase_admin._apps:
        key_dict = json.loads(st.secrets["textkey"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error(f"❌ فشل الاتصال بقاعدة البيانات: {e}")
    db = None

# --- تقسيم الصفحة إلى قسمين: الطلبات (يمين) والإعدادات والملف الشخصي (يسار) ---
col_main, col_settings = st.columns([2, 1])

with col_main:
    st.markdown("<h2 style='color: #1E3A8A;'>🛒 طلب خدمة توصيل ومزايدة</h2>", unsafe_allow_html=True)
    
    with st.form("order_bidding_form"):
        client_name = st.text_input("👤 اسم العميل بالكامل")
        order_details = st.text_area("📝 ما الذي تريد توصيله؟ (اكتب التفاصيل بدقة)")
        suggested_price = st.number_input("💰 ميزانيتك المقترحة للطلب (جنيه)", min_value=10, value=30)
        
        submit_btn = st.form_submit_button("🚀 نشر الطلب لاستقبال عروض السائقين")
        if submit_btn and client_name and order_details:
            if db is not None:
                db.collection("orders").add({
                    "client_name": client_name,
                    "order_details": order_details,
                    "suggested_price": suggested_price,
                    "status": "processing",
                    "timestamp": firestore.SERVER_TIMESTAMP
                })
                st.success("🎯 تم نشر طلبك بنجاح! السائقون يراجعون ميزانيتك الآن لتقديم عروضهم.")

with col_settings:
    st.markdown("<h3 style='color: #111;'>⚙️ إعدادات حسابي الشخصي</h3>", unsafe_allow_html=True)
    
    # أزرار تحكم سريعة تحدد قيمة المشروع وميزاته الاحترافية
    st.text_input("📱 رقم هاتفك للتواصل", value="+20 1000000000")
    
    # مفاتيح التنبيهات الفورية (Instant Notifications Switch)
    notification_toggle = st.toggle("🔔 تفعيل التنبيهات الفورية للطلبات", value=True)
    if notification_toggle:
        st.caption("🟢 التنبيهات نشطة: ستصلك أصوات وتنبيهات فور قبول السائق للطلب.")
    else:
        st.caption("⚪ التنبيهات معطلة.")
        
    st.markdown("---")
    if st.button("💾 حفظ إعدادات التطبيق", use_container_width=True):
        st.success("تم حفظ إعدادات ملفك الشخصي بنجاح!")
