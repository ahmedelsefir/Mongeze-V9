import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

st.set_page_config(page_title="بوابة السائق - منجز", layout="wide")

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

DRIVER_NAME = "الكابتن أحمد"

# ==========================================
# 🛑 رادار الأمان والحماية الفوري (رؤيتك العبقرية للحماية من النصب)
# ==========================================
is_banned = False
if db is not None:
    try:
        # فحص هل اسم هذا السائق مدرج في القائمة السوداء بالفايربيز أم لا
        ban_check = db.collection("banned_users").document(DRIVER_NAME).get()
        if ban_check.exists:
            is_banned = True
            ban_info = ban_check.to_dict()
    except Exception as e:
        pass

# لو الحساب محظور، اقطع الشاشة والاتصال تماماً واقفل التطبيق في وجهه
if is_banned:
    st.markdown(f"""
    <div style='background-color: #000000; padding: 40px; border-radius: 15px; border: 4px solid #DC2626; text-align: center; color: white; margin-top: 50px;'>
        <h1 style='color: #DC2626;'>🚫 حسابك مجمد ومحظور مؤقتاً!</h1>
        <h3 style='color: #FFF;'>عذراً يا كابتن أحمد، تم رصد تجاوز للسياسات أو بلاغ معلق ضدك.</h3>
        <p style='background-color: #1E1E1E; padding: 15px; border-radius: 8px; color: #FFA500;'>
            <b>⚠️ سبب الحظر المرصود بالسيستم:</b> {ban_info.get('reason', 'تجاوز شروط وقوانين الأمان للمنصة')}
        </p>
        <p style='color: #AAA; font-size: 14px;'>🛡️ تم اتخاذ هذا الإجراء بواسطة: {ban_info.get('banned_by', 'غرفة العمليات المركزية')}</p>
        <h4 style='color: #38BDF8;'>📞 يرجى التواصل فوراً مع إدارة الدعم الفني لمنصة مُنجز لحل النزاع.</h4>
    </div>
    """, unsafe_allow_html=True)
    st.stop() # أمر برمجي صارم يوقف قراءة بقية الملف والأزرار نهائياً!

# ==========================================
# 🟢 الكود الطبيعي وبقية الواجهة تفتح فقط لو الحساب سليم وآمن
# ==========================================
st.markdown("<h2 style='margin:0;'>🚖 بوابة الكابتن أحمد</h2>", unsafe_allow_html=True)
st.markdown("---")

tab_offers, tab_active_order, tab_settings = st.tabs(["📋 طلبات المزايدة الحية", "📍 الشحنة الحالية والتنفيذ", "⚙️ الإعدادات"])

# تبويب المزايدات
with tab_offers:
    st.subheader("📥 الطلبات المتاحة للمزايدة حالياً:")
    if db is not None:
        orders_ref = db.collection("orders").where("status", "==", "processing").stream()
        has_orders = False
        for order in orders_ref:
            has_orders = True
            order_data = order.to_dict()
            order_id = order.id
            
            st.markdown(f"<b>📍 طلب توصيل من: {order_data.get('client_name')}</b>", unsafe_allow_html=True)
            col_p, col_b = st.columns([1, 1])
            with col_p:
                driver_bid = st.number_input("عرض السعر الخاص بك (جنيه)", min_value=10, value=int(order_data.get('suggested_price', 30)), key=f"bid_in_{order_id}")
            with col_b:
                st.write("#")
                if st.button("🚀 إرسال العرض المالي", key=f"sub_btn_{order_id}", use_container_width=True):
                    db.collection("orders").document(order_id).collection("bids").document(DRIVER_NAME).set({
                        "driver_name": DRIVER_NAME, "proposed_price": driver_bid, "timestamp": firestore.SERVER_TIMESTAMP
                    })
                    st.success("🟢 تم إرسال العرض!")
        if not has_orders:
            st.info("📭 لا توجد طلبات جديدة.")

# تبويب الشحنة الحالية والتنفيذ
with tab_active_order:
    st.subheader("📍 شاشة التنفيذ الحية")
    if db is not None:
        running_orders = db.collection("orders").where("driver_assigned", "==", DRIVER_NAME).where("status", "in", ["🚖 جاري الاستلام", "🚚 جاري التوصيل"]).stream()
        has_running = False
        for order in running_orders:
            has_running = True
            order_data = order.to_dict()
            order_id = order.id
            current_status = order_data.get("status")
            
            st.info(f"📋 طلب نشط للعميل: {order_data.get('client_name')} | الحالة: {current_status}")
            if current_status == "🚖 جاري الاستلام":
                if st.button("📦 تم استلام الشحنة", key=f"pck_{order_id}", use_container_width=True):
                    db.collection("orders").document(order_id).update({"status": "🚚 جاري التوصيل"})\
                    ; st.rerun()
            elif current_status == "🚚 جاري التوصيل":
                if st.button("🏁 إنهاء وتوصيل الطلب بنجاح", key=f"dlv_{order_id}", use_container_width=True):
                    db.collection("orders").document(order_id).update({"status": "✅ في انتظار تقييم الطرفين"})\
                    ; st.rerun()
                    
        # لقطة تقييم الطرفين المتبادل
        rating_orders = db.collection("orders").where("driver_assigned", "==", DRIVER_NAME).where("status", "==", "✅ في انتظار تقييم الطرفين").stream()
        for r_order in rating_orders:
            has_running = True
            st.warning(f"🏁 يرجى تقييم العميل لإغلاق الطلب الكلي:")
            driver_eval = st.slider("⭐ تقييم سلوك العميل:", 1, 5, 5, key=f"sld_{r_order.id}")
            if st.button("💾 إرسال التقييم وحفظ الرحلة", key=f"sv_rt_{r_order.id}", use_container_width=True):
                db.collection("orders").document(r_order.id).update({"status": "⭐ تم الإغلاق والتقييم بالكامل", "driver_rating_to_client": driver_eval})\
                ; st.rerun()
                
        if not has_running:
            st.info("🚖 لا توجد شحنات نشطة جاري تنفيذها حالياً.")

# تبويب الإعدادات
with tab_settings:
    st.text_input("📱 رقم الهاتف", value="+20 123 456 789")
