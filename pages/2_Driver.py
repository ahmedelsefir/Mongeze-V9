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

# اسم السائق الثابت للمحاكاة الذكية
DRIVER_NAME = "الكابتن أحمد"

st.markdown("<h2 style='margin:0;'>مرحباً بك، كابتن أحمد 🚖</h2>", unsafe_allow_html=True)
st.markdown("---")

tab_offers, tab_active_order, tab_settings = st.tabs(["📋 طلبات المزايدة الحية", "📍 الشحنة الحالية والتنفيذ", "⚙️ الإعدادات"])

# --- التبويب الأول: طلبات المزايدة الحية ---
with tab_offers:
    st.subheader("📥 الطلبات المتاحة للمزايدة حالياً:")
    if db is not None:
        try:
            orders_ref = db.collection("orders").where("status", "==", "processing").stream()
            has_orders = False
            for order in orders_ref:
                has_orders = True
                order_data = order.to_dict()
                order_id = order.id
                
                st.markdown(f"""
                <div style='background-color: #ffffff; padding: 15px; border-radius: 10px; margin-bottom: 10px; 
                            box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-right: 5px solid #00A86B; color: #333;'>
                    <b>📍 طلب توصيل من: {order_data.get('client_name', 'عميل غير معروف')}</b>
                    <p>📦 تفاصيل الشحنة: {order_data.get('order_details', '')}</p>
                    <p style='color: #00A86B; font-weight: bold;'>💰 ميزانية العميل المقترحة: {order_data.get('suggested_price', 0)} جنيه</p>
                </div>
                """, unsafe_allow_html=True)
                
                col_price, col_btn = st.columns([1, 1])
                with col_price:
                    driver_bid = st.number_input("عرض السعر الخاص بك (جنيه)", min_value=10, value=int(order_data.get('suggested_price', 30)), key=f"bid_{order_id}")
                with col_btn:
                    st.write("#")
                    if st.button("🚀 إرسال العرض المالي", key=f"btn_{order_id}", use_container_width=True):
                        db.collection("orders").document(order_id).collection("bids").document(DRIVER_NAME).set({
                            "driver_name": DRIVER_NAME,
                            "driver_phone": "+20 123 456 789",
                            "proposed_price": driver_bid,
                            "timestamp": firestore.SERVER_TIMESTAMP
                        })
                        st.success("🟢 تم إرسال العرض بنجاح! بانتظار موافقة العميل.")
            if not has_orders:
                st.info("📭 لا توجد طلبات جديدة تحتاج عروض أسعار حالياً.")
        except Exception as e:
            st.error(f"خطأ: {e}")

# --- التبويب الثاني: شاشة التنفيذ وتتبع الشحنة الحالية (الحل الجذري) ---
with tab_active_order:
    st.subheader("📍 شاشة التنفيذ وتتبع الشحنة الحالية")
    if db is not None:
        try:
            # جلب الطلبات المسندة لهذا السائق والتي هي في مرحلة التنفيذ
            running_orders = db.collection("orders").where("driver_assigned", "==", DRIVER_NAME).where("status", "in", ["🚖 جاري الاستلام", "🚚 جاري التوصيل"]).stream()
            has_running = False
            
            for order in running_orders:
                has_running = True
                order_data = order.to_dict()
                order_id = order.id
                current_status = order_data.get("status")
                
                # كارت التنفيذ الاحترافي التجاري المعروض بالصورة
                st.markdown(f"""
                <div style='background-color: #1E293B; padding: 20px; border-radius: 12px; color: white; margin-bottom: 15px;'>
                    <h3 style='color: #38BDF8; margin-top:0;'>🚚 العميل بانتظارك</h3>
                    <p><b>👤 الاسم:</b> {order_data.get('client_name')}</p>
                    <p><b>📦 محتوى الشحنة:</b> {order_data.get('order_details')}</p>
                    <h4 style='color: #FBBF24;'>💰 القيمة الصافية للرحلة: {order_data.get('final_price')} جنيه</h4>
                    <p>🚨 <b>حالة الطلب الحالية:</b> <span style='color:#FBBF24;'>{current_status}</span></p>
                </div>
                """, unsafe_allow_html=True)
                
                # أزرار التحديث الحركي للمناوبة والرحلة
                if current_status == "🚖 جاري الاستلام":
                    if st.button("📦 تم استلام الشحنة من المتجر/العميل", use_container_width=True):
                        db.collection("orders").document(order_id).update({"status": "🚚 جاري التوصيل"})
                        st.rerun()
                        
                elif current_status == "🚚 جاري التوصيل":
                    if st.button("🏁 إنهاء وتوصيل الطلب بنجاح", use_container_width=True):
                        db.collection("orders").document(order_id).update({"status": "✅ تم التسليم بنجاح"})
                        st.balloons()
                        st.success("🎉 ممتاز يا كابتن! تم إقفال الطلب وتوصيله بنجاح وتحويل الأرباح للمحفظة.")
                        st.rerun()
            
            if not has_running:
                st.info("🚖 لا توجد شحنات نشطة جاري تنفيذها حالياً. قدم عروضك في التبويب الأول!")
        except Exception as e:
            st.error(f"خطأ في شاشة التنفيذ: {e}")

# --- التبويب الثالث: الإعدادات العامة ---
with tab_settings:
    st.text_input("📱 رقم الهاتف المعتمد", value="+20 123 456 789")
    st.toggle("🔔 تفعيل التنبيهات الصوتية الحية للطلبات", value=True)
    if st.button("💾 حفظ الإعدادات"):
        st.success("تم الحفظ!")
