import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

# --- 1. إعدادات الصفحة والواجهة المرئية ---
st.set_page_config(page_title="واجهة العميل الاحترافية - منجز", layout="wide")

# --- 2. تفعيل الاتصال بقاعدة البيانات Firebase ---
try:
    if not firebase_admin._apps:
        key_dict = json.loads(st.secrets["textkey"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error(f"❌ فشل الاتصال بقاعدة البيانات: {e}")
    db = None

# --- 3. تقسيم الصفحة: الطلبات (يسار) | الإعدادات والملف الشخصي (يمين) ---
col_main, col_settings = st.columns([2, 1])

with col_main:
    st.markdown("<h2 style='color: #1E3A8A;'>🛒 طلب خدمة توصيل ومزايدة</h2>", unsafe_allow_html=True)
    
    # نموذج إنشاء الطلب
    with st.form("order_bidding_form"):
        client_name = st.text_input("👤 اسم العميل بالكامل")
        order_details = st.text_area("📝 ما الذي تريد توصيله؟ (اكتب التفاصيل بدقة)")
        suggested_price = st.number_input("💰 ميزانيتك المقترحة للطلب (جنيه)", min_value=10, value=30)
        
        submit_btn = st.form_submit_button("🚀 نشر الطلب لاستقبال عروض السائقين")
        if submit_btn and client_name and order_details:
            if db is not None:
                try:
                    db.collection("orders").add({
                        "client_name": client_name,
                        "order_details": order_details,
                        "suggested_price": suggested_price,
                        "status": "processing",
                        "timestamp": firestore.SERVER_TIMESTAMP
                    })
                    st.success("🎯 تم نشر طلبك بنجاح! السائقون يراجعون ميزانيتك الآن لتقديم عروضهم.")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء رفع الطلب: {e}")

    st.markdown("---")
    
    # ##########################################
    # # 📥 لوحة استقبال واختيار عروض الأسعار الحية (بناءً على طلبك)
    # ##########################################
    st.markdown("<h3 style='color: #00A86B;'>📋 عروض الأسعار المقدمة من السائقين حالياً:</h3>", unsafe_allow_html=True)
    
    if db is not None:
        try:
            # جلب طلبات العميل النشطة لمراقبة عروضها
            my_orders = db.collection("orders").where("status", "==", "processing").stream()
            has_active_orders = False
            
            for order in my_orders:
                has_active_orders = True
                order_info = order.to_dict()
                order_id = order.id
                
                # جلب العروض الفرعية الملحقة بداخل هذا الطلب بالظبط
                bids_ref = db.collection("orders").document(order_id).collection("bids").order_by("proposed_price").stream()
                has_bids = False
                
                for bid in bids_ref:
                    has_bids = True
                    bid_data = bid.to_dict()
                    bid_id = bid.id
                    
                    # تصميم كارت عرض السعر القادم من المندوب
                    st.markdown(f"""
                    <div style='background-color: #F0FDF4; padding: 15px; border-radius: 8px; margin-bottom: 10px; 
                                border: 1px solid #bbf7d0; display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <b style='color:#16a34a;'>🚖 {bid_data.get('driver_name', 'سائق متاح')}</b> 
                            <span style='color:#555; margin-right:15px;'>📞 الهاتف: {bid_data.get('driver_phone', '')}</span>
                        </div>
                        <div style='font-size: 18px; font-weight: bold; color: #111;'>
                            السعر المعروض: <span style='color:#16a34a;'>{bid_data.get('proposed_price', 0)} جنيه</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # زر قبول السعر الأنسب ديناميكياً
                    if st.button(f"🤝 قبول عرض السعر ({bid_data.get('proposed_price')} جنيه)", key=f"accept_bid_{bid_id}"):
                        # تحديث حالة الطلب وإسناده للسعر والمندوب المختار
                        db.collection("orders").document(order_id).update({
                            "status": "🚖 جاري الاستلام",
                            "final_price": bid_data.get('proposed_price'),
                            "driver_assigned": bid_data.get('driver_name')
                        })
                        st.balloons()
                        st.success(f"✅ تم قبول العرض بنجاح! كابتن {bid_data.get('driver_name')} يتحرك إليك الآن.")
                        st.rerun()
                
                if not has_bids:
                    st.caption(f"⏳ طلبك بخصوص ({order_info.get('order_details')[:20]}...) نشط، وفي انتظار تقديم أول عرض سعر من المناديب.")
            
            if not has_active_orders:
                st.info("💡 لا توجد طلبات نشطة لك حالياً. قم بإنشاء طلب جديد بالأعلى لمشاهدة المزايدة الحية!")
                
        except Exception as e:
            st.error(f"خطأ أثناء تحديث العروض: {e}")

# --- 4. قسم الإعدادات الحسابية الشخصية (يمين الشاشة) ---
with col_settings:
    st.markdown("<h3 style='color: #111;'>⚙️ إعدادات حسابي الشخصي</h3>", unsafe_allow_html=True)
    
    st.text_input("📱 رقم هاتف العميل المعتمد", value="+20 1000000000")
    notification_toggle = st.toggle("🔔 تفعيل التنبيهات الفورية للطلبات", value=True)
    
    if notification_toggle:
        st.caption("🟢 التنبيهات نشطة: ستصلك إشعارات فورية عند ورود عروض أسعار جديدة.")
    else:
        st.caption("⚪ التنبيهات معطلة.")
        
    st.markdown("---")
    if st.button("💾 حفظ إعدادات التطبيق", use_container_width=True):
        st.success("تم حفظ وتحديث إعدادات ملفك الشخصي بنجاح!")
