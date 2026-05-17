import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

# ##########################################
# # --- 1. إعدادات الصفحة والواجهة المرئية ---
# ##########################################
st.set_page_config(page_title="بوابة السائق الذكية - منجز", layout="wide")

# تصميم رأس الصفحة بأسلوب احترافي متناسق مع تطبيقات التوصيل لعام 2026
st.markdown("<h1 style='text-align: center; color: #00A86B;'>🚖 بوابة السائق الذكية</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>إدارة الطلبات، تتبع الأرباح، وتحديث حالات التوصيل فورياً</p>", unsafe_allow_html=True)
st.markdown("---")

# ##########################################
# # --- 2. شريان الاتصال التلقائي بـ FIREBASE ---
# ##########################################
try:
    if not firebase_admin._apps:
        # قراءة مفتاح الـ JSON المؤمن من إعدادات السيرفر السحرية
        key_dict = json.loads(st.secrets["textkey"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error(f"❌ فشل الاتصال التلقائي بقاعدة البيانات: {e}")
    db = None

# ##########################################
# # --- 3. عرض الطلبات الحية والنظام الإرشادي ---
# ##########################################
st.subheader("📥 الطلبات النشطة المتاحة في منطقتك:")

if db is not None:
    try:
        # جلب الطلبات من الفايربيز وترتيبها من الأحدث للأقدم
        orders_ref = db.collection("orders").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
        has_orders = False
        
        for order in orders_ref:
            has_orders = True
            order_data = order.to_dict()
            order_id = order.id
            
            # قراءة البيانات الحالية من الفايربيز مع وضع قيم افتراضية حمايةً من الأخطاء
            client_name = order_data.get('client_name', 'عميل غير معروف')
            order_details = order_data.get('order_details', 'لا توجد تفاصيل شحنة')
            current_status = order_data.get('status', 'جاري البحث عن سائق')
            
            # # --- حسابات مالية إرشادية داخل الكارت (مثل الصورة الاحترافية) ---
            # هنا بنضع قيم افتراضية ذكية للأرباح والمسافات تظهر للسائق لجذب انتباهه للطلب
            estimated_earnings = "35.00 جنيه"
            pickup_distance = "1.2 كم"
            delivery_distance = "4.5 كم"
            
            # # --- تصميم كارت الرحلة الاحترافي بـ HTML & CSS ---
            st.markdown(f"""
            <div style='background-color: #ffffff; padding: 20px; border-radius: 12px; margin-bottom: 15px; 
                        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-right: 6px solid #00A86B; color: #333;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <h4 style='margin: 0; color: #111;'>👤 العميل: {client_name}</h4>
                    <span style='background-color: #E8F5E9; color: #00A86B; padding: 5px 10px; border-radius: 20px; font-size: 14px; font-weight: bold;'>
                        💰 أرباحك: {estimated_earnings}
                    </span>
                </div>
                <hr style='border: 0; border-top: 1px solid #eee; margin: 10px 0;'>
                <p style='margin: 5px 0;'>📦 <b>تفاصيل الشحنة:</b> {order_details}</p>
                <p style='margin: 5px 0; font-size: 14px; color: #666;'>📍 مسافة الاستلام: {pickup_distance} | مسافة التوصيل: {delivery_distance}</p>
                <p style='margin: 5px 0;'>🚨 <b>الحالة الحالية:</b> <span style='color: #FF6B35; font-weight: bold;'>{current_status}</span></p>
            </div>
            """, unsafe_allow_html=True)
            
            # # --- 4. الأزرار التفاعلية لتحديث حالات الطلب الحية ---
            # نستخدم نظام تقسيم الأعمدة لوضع الأزرار جنب بعضها بنسق scannable ومريح للعين
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # زر قبول الطلب: يغير الحالة في الفايربيز فوراً إلى "جاري الاستلام"
                if st.button(f"🤝 قبول الطلب", key=f"accept_{order_id}"):
                    db.collection("orders").document(order_id).update({"status": "🚖 جاري استلام الشحنة"})
                    st.success("تم قبول الطلب وتحديث النظام! ارفع الشحنة الآن.")
                    st.rerun()
                    
            with col2:
                # زر بدء التوصيل: يغير الحالة عندما يتحرك السائق بالشحنة
                if st.button(f"🚀 بدء التوصيل", key=f"deliver_{order_id}"):
                    db.collection("orders").document(order_id).update({"status": "📦 جاري التوصيل للوجهة"})
                    st.info("تم تحديث الحالة لـ (جاري التوصيل). قد بحذر يا بطل!")
                    st.rerun()
                    
            with col3:
                # زر إتمام المهمة: يغلق الطلب بنجاح ويحوله لـ "تم التسليم"
                if st.button(f"✅ تم التسليم", key=f"done_{order_id}"):
                    db.collection("orders").document(order_id).update({"status": "🏁 تم تسليم الشحنة بنجاح"})
                    st.success("عاش يا وحش! تم قفل الطلب بنجاح وإضافة الأرباح لمفضلتك.")
                    st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)

        if not has_orders:
            st.info("📭 لا توجد طلبات جديدة حالياً في الانتظار. ابقَ متصلاً ومستعداً!")
            
    except Exception as e:
        st.error(f"تعذر تحديث البيانات الحية من السيرفر: {e}")
else:
    st.warning("⚠️ النظام في انتظار تفعيل شريان الاتصال الآمن.")
