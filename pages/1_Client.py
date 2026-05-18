import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

st.set_page_config(page_title="بوابة العميل الذكية - منجز", layout="wide")

try:
    if not firebase_admin._apps:
        key_dict = json.loads(st.secrets["textkey"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error(f"❌ فشل الاتصال بقاعدة البيانات: {e}")
    db = None

col_main, col_settings = st.columns([2, 1])

with col_main:
    st.markdown("<h2 style='color: #1E3A8A; text-align: right;'>🛒 إنشاء طلب خدمة توصيل ومزايدة</h2>", unsafe_allow_html=True)
    
    with st.form("order_bidding_form"):
        client_name = st.text_input("👤 اسم العميل بالكامل")
        order_details = st.text_area("📝 تفاصيل ومحتويات الشحنة بدقة")
        suggested_price = st.number_input("💰 ميزانيتك المقترحة للطلب (جنيه)", min_value=10, value=30)
        submit_btn = st.form_submit_button("🚀 نشر الطلب لاستقبال عروض الأسعار")
        
        if submit_btn and client_name and order_details:
            if db is not None:
                db.collection("orders").add({
                    "client_name": client_name,
                    "order_details": order_details,
                    "suggested_price": suggested_price,
                    "status": "processing",
                    "timestamp": firestore.SERVER_TIMESTAMP
                })
                st.success("🎯 تم نشر طلبك بنجاح على خريطة المزايدة الحية للسائقين!")

    st.markdown("---")
    st.markdown("<h3 style='color: #00A86B; text-align: right;'>📋 لوحة متابعة وتتبع طلباتك الحالية</h3>", unsafe_allow_html=True)
    
    if db is not None:
        try:
            # جلب كافة الحالات النشطة بما فيها حالات الانتظار والتقييم لمنع اختفاء الطلبات فجأة
            all_my_orders = db.collection("orders").where("status", "in", ["processing", "🚖 جاري الاستلام", "🚚 جاري التوصيل", "✅ في انتظار تقييم الطرفين"]).stream()
            has_data = False
            
            for order in all_my_orders:
                has_data = True
                order_info = order.to_dict()
                order_id = order.id
                status = order_info.get("status")
                
                if status == "processing":
                    st.markdown(f"📦 طلبك لـ **({order_info.get('order_details')[:25]}...)** يتلقى عروضاً الآن:")
                    bids = db.collection("orders").document(order_id).collection("bids").stream()
                    has_bids = False
                    for bid in bids:
                        has_bids = True
                        bid_data = bid.to_dict()
                        
                        col_text, col_action = st.columns([2, 1])
                        with col_text:
                            st.info(f"🚖 عرض من {bid_data.get('driver_name')}: السعر المقترح {bid_data.get('proposed_price')} جنيه")
                        with col_action:
                            if st.button("🤝 قبول السعر", key=f"accept_action_{order_id}_{bid_data.get('driver_name')}"):
                                db.collection("orders").document(order_id).update({
                                    "status": "🚖 جاري الاستلام",
                                    "final_price": bid_data.get('proposed_price'),
                                    "driver_assigned": bid_data.get('driver_name')
                                })
                                st.rerun()
                    if not has_bids:
                        st.caption("⏳ في انتظار تقديم أول عرض مالي من المناديب...")
                        
                elif status in ["🚖 جاري الاستلام", "🚚 جاري التوصيل"]:
                    # صوت تنبيه فوري وبث حي يعلم العميل بتحرك السائق الحقيقي
                    st.markdown('<audio autoplay><source src="https://assets.mixkit.co/active_storage/sfx/911/911-600.wav" type="audio/wav"></audio>', unsafe_allow_html=True)
                    st.markdown(f"""
                    <div style='background-color: #EFF6FF; padding: 15px; border-radius: 8px; border-left: 5px solid #3B82F6; color:#333; text-align: right;'>
                        <h4>✅ تم قبول طلبك وبدأ التنفيذ على الأرض!</h4>
                        <p>👤 <b>المندوب المسؤول:</b> {order_info.get('driver_assigned')}</p>
                        <p>💰 <b>تكلفة التوصيل المتفق عليها:</b> {order_info.get('final_price')} جنيه</p>
                        <p style='font-size:16px;'>🚨 <b>الحالة اللوجستية الحية الآن:</b> <span style='color:#3B82F6; font-weight:bold;'>{status}</span></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                elif status == "✅ في انتظار تقييم الطرفين":
                    st.success(f"🎉 لقد أعلن كابتن {order_info.get('driver_assigned')} عن وصول وتسليم الشحنة بنجاح!")
                    
                    # نموذج التقييم الحقيقي بالنجوم للعميل واجهة احترافية
                    client_rating = st.selectbox("⭐ يرجى تقييم أداء وأمانة المندوب:", [5, 4, 3, 2, 1], key=f"client_rate_box_{order_id}")
                    if st.button("💾 تأكيد واستلام الشحنة وإرسال التقييم", key=f"btn_confirm_delivery_{order_id}", use_container_width=True):
                        db.collection("orders").document(order_id).update({
                            "client_rating_to_driver": client_rating
                        })
                        st.success("❤️ شكرًا لك! تم إغلاق وتوثيق الرحلة بالكامل بنجاح.")
            
            if not has_data:
                st.info("💡 لا توجد طلبات نشطة أو شحنات جاري تتبعها لك حالياً.")
        except Exception as e:
            st.error(f"خطأ: {e}")

with col_settings:
    st.markdown("<h3 style='text-align: right;'>⚙️ الملف الشخصي للعميل</h3>", unsafe_allow_html=True)
    st.text_input("📱 رقم الهاتف", value="+20 1000000000")
    st.toggle("🔔 إشعارات صوتية حية فورية", value=True)
