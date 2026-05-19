import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

st.set_page_config(page_title="بوابة السائق - منجز", layout="wide")

# --- تفعيل الفايربيز ---
try:
    if not firebase_admin._apps:
        key_dict = json.loads(st.secrets["textkey"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error(f"❌ اتصال الفايربيز مقطوع: {e}")
    db = None

DRIVER_NAME = "ahmed mostafa mohammed"

# --- رادار الحظر التلقائي والأمان (منع التجاوزات) ---
if db:
    ban_check = db.collection("banned_users").document(DRIVER_NAME).get()
    if ban_check.exists:
        st.error("🚫 هذا الحساب مجمد مؤقتاً لتجاوز السياسات المالية. يرجى التواصل مع الدعم الفني لفك الحظر.")
        st.stop()

# --- واجهة المندوب الاحترافية (محاكاة دقيقة للصورة المرفقة) ---
st.markdown(f"""
<div style='background-color: #FFF; padding: 20px; border-radius: 12px; border: 1px solid #E5E7EB; text-align: center; color: #333;'>
    <img src='https://cdn-icons-png.flaticon.com/512/4128/4128176.png' style='width: 70px; border-radius: 50%;'>
    <h2 style='margin: 5px 0;'>{DRIVER_NAME} ⭐⭐⭐⭐⭐</h2>
    <span style='background-color: #10B981; color: white; padding: 3px 10px; border-radius: 20px; font-size: 12px;'>🆔 مظهر هوية المرسول موثق</span>
</div>
""", unsafe_allow_html=True)

# العدادات الضخمة الحقيقية المأخوذة من صورتك الحية بالملي
st.markdown("###")
col_stat1, col_stat2 = st.columns(2)
with col_stat1:
    st.metric(label="📊 الطلبات الموصلة الكلية", value="3,536 طلب")
with col_stat2:
    st.metric(label="💰 إجمالي الإيرادات المحققة", value="340,904.74 ج.م")

st.markdown("---")

# القائمة التفاعلية للمندوب
driver_menu = st.selectbox("🗂️ تصفح شاشات المندوب والعمليات", [
    "📥 استلام الطلبات والمزايدات الحية",
    "💳 رصيد الحساب والمحفظة",
    "💬 ملاحظات وشكاوى المستخدمين",
    "⚙️ الدعم الفني والإعدادات"
])

if driver_menu == "📥 استلام الطلبات والمزايدات الحية":
    st.subheader("📥 الطلبات الحرة المتاحة في الميدان")
    
    if db:
        orders_ref = db.collection("orders").where("status", "==", "processing").stream()
        has_orders = False
        for order in orders_ref:
            has_orders = True
            order_data = order.to_dict()
            order_id = order.id
            
            st.markdown(f"""
            <div style='background-color: #F9FAFB; padding: 15px; border-radius: 8px; border-right: 4px solid #10B981; margin-bottom:10px;'>
                <b>📍 طلب من: {order_data.get('client_name')}</b><br>
                <small>📦 التفاصيل: {order_data.get('order_details')}</small><br>
                <b>💵 ميزانية العميل المقترحة: {order_data.get('suggested_price')} ج.م</b>
            </div>
            """, unsafe_allow_html=True)
            
            # منع تكرار الأزرار بإعطاء مفتاح فريد (Key) لكل زرار عبر الـ ID الخاص بالطلب
            bid_price = st.number_input("اكتب عرض السعر الخاص بك (جنيه)", min_value=10, value=int(order_data.get('suggested_price')), key=f"price_{order_id}")
            if st.button("🚀 إرسال العرض المالي للعميل", key=f"btn_{order_id}"):
                db.collection("orders").document(order_id).collection("bids").document(DRIVER_NAME).set({
                    "driver_name": DRIVER_NAME,
                    "proposed_price": bid_price,
                    "timestamp": firestore.SERVER_TIMESTAMP
                })
                st.success("✅ تم إرسال عرضك بنجاح! بانتظار موافقة العميل.")
        if not has_orders:
            st.info("📭 لا توجد طلبات جديدة معروضة في منطقتك حالياً.")

elif driver_menu == "💳 رصيد الحساب والمحفظة":
    st.subheader("💳 كشف حساب المحفظة للمندوب")
    # مأخوذ من الصورة الرقمية الخاصة بك بالملي ليعلم المندوب مديونيته للمنصة
    st.error("📉 رصيد الحساب الحالي بالمنصة: -160.96 ج.م")
    st.warning("⚠️ رصيدك الحالي بالسالب نتيجة لخصم عمولات الرحلات الكاش الفائتة. يرجى شحن المحفظة لتجنب إيقاف الحساب تلقائياً.")
    if st.button("➕ سداد المديونية وشحن الحساب"):
        st.success("💳 جاري توجيهك لبوابة الدفع السريع لفودافون كاش / فيزا...")

elif driver_menu == "💬 ملاحظات وشكاوى المستخدمين":
    st.subheader("💬 ملاحظات المستهلكين والعملاء")
    st.metric("عدد التقييمات الإيجابية والتعليقات", "1,182 تعليق")
    st.markdown("""
    * 🟢 *عميل مجهول:* "مندوب محترم وسريع جداً في التوصيل وأنصح بالتعامل معه."
    * 🟢 *عميل مجهول:* "وصل الأكل سخن وبحالة ممتازة ملتزم بالوقت."
    """)

elif driver_menu == "⚙️ الدعم الفني والإعدادات":
    st.subheader("📞 مركز دعم المناديب الفوري")
    st.markdown("🔧 إذا واجهت مشكلة في التحصيل، أو تهرب العميل من الدفع، اضغط على الأيقونة الخضراء العائمة لفتح محادثة مباشرة مع مشرف الدعم الفني لحل النزاع فوراً.")
    if st.button("📞 فتح خط اتصال مباشر بالطوارئ"):
        st.info("جاري الاتصال بغرفة عمليات منجز...")
