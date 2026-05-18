import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

st.set_page_config(page_title="بوابة السائق الذكية - منجز", layout="wide")

# تفعيل قاعدة البيانات بنظام الأمان والمحاكاة المستقرة
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

st.markdown("<h2 style='margin:0; text-align: right;'>🚖 بوابة الكابتن أحمد</h2>", unsafe_allow_html=True)
st.markdown("---")

tab_offers, tab_active_order, tab_settings = st.tabs(["📋 طلبات المزايدة الحية", "📍 الشحنة الحالية والتنفيذ", "⚙️ الإعدادات والتقييمات"])

# --- التبويب الأول: طلبات المزايدة ---
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
                            box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-right: 5px solid #00A86B; color: #333; text-align: right;'>
                    <b>📍 طلب توصيل من: {order_data.get('client_name')}</b>
                    <p>📦 تفاصيل الشحنة: {order_data.get('order_details')}</p>
                    <p style='color: #00A86B; font-weight: bold;'>💰 ميزانية العميل المقترحة: {order_data.get('suggested_price', 0)} جنيه</p>
                </div>
                """, unsafe_allow_html=True)
                
                col_price, col_btn = st.columns([1, 1])
                with col_price:
                    driver_bid = st.number_input("عرض السعر الخاص بك (جنيه)", min_value=10, value=int(order_data.get('suggested_price', 30)), key=f"bid_input_{order_id}")
                with col_btn:
                    st.write("#")
                    if st.button("🚀 إرسال العرض المالي", key=f"submit_btn_{order_id}", use_container_width=True):
                        db.collection("orders").document(order_id).collection("bids").document(DRIVER_NAME).set({
                            "driver_name": DRIVER_NAME,
                            "driver_phone": "+20 123 456 789",
                            "proposed_price": driver_bid,
                            "timestamp": firestore.SERVER_TIMESTAMP
                        })
                        st.success("🟢 تم إرسال العرض بنجاح بنظام المزايدة الحية!")
            if not has_orders:
                st.info("📭 لا توجد طلبات جديدة تحتاج عروض أسعار حالياً.")
        except Exception as e:
            st.error(f"خطأ: {e}")

# --- التبويب الثاني: شاشة التنفيذ وتتبع الشحنة الحالية (حل مشكلة التكرار والـ Key) ---
with tab_active_order:
    st.subheader("📍 شاشة التنفيذ الحية")
    if db is not None:
        try:
            running_orders = db.collection("orders").where("driver_assigned", "==", DRIVER_NAME).where("status", "in", ["🚖 جاري الاستلام", "🚚 جاري التوصيل"]).stream()
            has_running = False
            
            for order in running_orders:
                has_running = True
                order_data = order.to_dict()
                order_id = order.id
                current_status = order_data.get("status")
                
                # إشعار صوتي خفيف عند التحديث لإحياء روح التطبيق
                st.markdown('<audio autoplay><source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-600.wav" type="audio/wav"></audio>', unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style='background-color: #1E293B; padding: 20px; border-radius: 12px; color: white; margin-bottom: 15px; text-align: right;'>
                    <h3 style='color: #38BDF8; margin-top:0;'>🚚 طلب قيد التنفيذ الآن</h3>
                    <p><b>👤 اسم العميل:</b> {order_data.get('client_name')}</p>
                    <p><b>📦 محتوى الشحنة:</b> {order_data.get('order_details')}</p>
                    <h4 style='color: #FBBF24;'>💰 الأرباح المتفق عليها: {order_data.get('final_price')} جنيه</h4>
                    <p>🚨 <b>حالة التحرك الحالية:</b> <span style='color:#FBBF24;'>{current_status}</span></p>
                </div>
                """, unsafe_allow_html=True)
                
                # استخدام أزرار بمفاتيح ديناميكية فريدة تماماً تمنع الـ Duplicate Key
                if current_status == "🚖 جاري الاستلام":
                    if st.button("📦 تم استلام الشحنة من المتجر/العميل", key=f"btn_pickup_{order_id}", use_container_width=True):
                        db.collection("orders").document(order_id).update({"status": "🚚 جاري التوصيل"})
                        st.rerun()
                        
                elif current_status == "🚚 جاري التوصيل":
                    if st.button("🏁 إنهاء وتوصيل الطلب بنجاح", key=f"btn_deliver_{order_id}", use_container_width=True):
                        db.collection("orders").document(order_id).update({"status": "✅ في انتظار تقييم الطرفين"})
                        st.balloons()
                        st.rerun()
            
            # محاكاة شاشة التقييم الفورية للسائق بعد انتهاء الطلب
            rating_orders = db.collection("orders").where("driver_assigned", "==", DRIVER_NAME).where("status", "==", "✅ في انتظار تقييم الطرفين").stream()
            for r_order in rating_orders:
                has_running = True
                r_id = r_order.id
                r_data = r_order.to_dict()
                st.warning(f"🏁 لقد قمت بتوصيل طلب العميل ({r_data.get('client_name')}) بنجاح! يرجى تقييم العميل لإغلاق الطلب:")
                
                driver_eval = st.slider("⭐ تقييم سلوك العميل ومدى تعاونه:", 1, 5, 5, key=f"rate_slider_{r_id}")
                if st.button("💾 إرسال التقييم وحفظ الرحلة", key=f"btn_save_rate_{r_id}", use_container_width=True):
                    db.collection("orders").document(r_id).update({
                        "status": "⭐ تم الإغلاق والتقييم بالكامل",
                        "driver_rating_to_client": driver_eval
                    })
                    st.success("🎉 تم تسجيل تقييمك وحفظ الرحلة في أرشيف الأرباح بنجاح!")
                    st.rerun()

            if not has_running:
                st.info("🚖 لا توجد شحنات نشطة جاري تنفيذها حالياً.")
        except Exception as e:
            st.error(f"خطأ في شاشة التنفيذ: {e}")

# --- التبويب الثالث: الإعدادات ---
with tab_settings:
    st.subheader("📊 إحصائيات حساب الكابتن")
    st.metric(label="⭐ متوسط تقييمك العام من العملاء", value="4.9 / 5")
    st.text_input("📱 رقم الهاتف المسجل", value="+20 123 456 789")
