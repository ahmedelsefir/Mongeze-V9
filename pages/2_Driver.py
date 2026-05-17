import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="بوابة السائق - منجز", layout="wide")

# --- 2. تفعيل قاعدة البيانات ---
try:
    if not firebase_admin._apps:
        key_dict = json.loads(st.secrets["textkey"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error(f"❌ فشل الاتصال بقاعدة البيانات: {e}")
    db = None

# --- 3. النظام الإرشادي لإدارة الصفحات الديناميكية (Session State) ---
# هنا بنخلق متغير سري جوه ذاكرة الصفحة عشان نعرف السائق في أنهي خطوة حالياً
if "current_step" not in st.session_state:
    st.session_state.current_step = "view_orders" # الخطوة الافتراضية: تصفح الطلبات

if "active_order_id" not in st.session_state:
    st.session_state.active_order_id = None # حفظ رقم الطلب اللي السائق استلمه

# ##########################################
# # الخطوة الأولى: عرض الطلبات المتاحة (الرئيسية)
# ##########################################
if st.session_state.current_step == "view_orders":
    st.markdown("<h1 style='text-align: center; color: #00A86B;'>🚖 الطلبات المتاحة حالياً</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    if db is not None:
        try:
            orders_ref = db.collection("orders").where("status", "==", "processing").stream()
            has_orders = False
            
            for order in orders_ref:
                has_orders = True
                order_data = order.to_dict()
                order_id = order.id
                
                # تصميم كارت احترافي يشبه تطبيقات التوصيل التجارية
                st.markdown(f"""
                <div style='background-color: #ffffff; padding: 20px; border-radius: 12px; margin-bottom: 15px; 
                            box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-right: 6px solid #00A86B; color: #333;'>
                    <h4 style='margin: 0;'>👤 العميل: {order_data.get('client_name', 'غير معروف')}</h4>
                    <p style='margin: 10px 0;'>📦 <b>الطلب:</b> {order_data.get('order_details', 'لا توجد تفاصيل')}</p>
                    <div style='background-color: #E8F5E9; color: #00A86B; padding: 5px 10px; border-radius: 8px; display: inline-block; font-weight: bold;'>
                        💰 القيمة: 35.00 جنيه
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # زر قبول الطلب الديناميكي
                if st.button("🤝 قبول الطلب والتحرك الآن", key=f"btn_{order_id}"):
                    # تحديث الحالة في قاعدة البيانات فوراً
                    db.collection("orders").document(order_id).update({"status": "🚖 جاري الاستلام"})
                    
                    # نقل السائق ديناميكياً للخطوة التالية في الذاكرة
                    st.session_state.active_order_id = order_id
                    st.session_state.current_step = "track_trip"
                    st.rerun() # إعادة تشغيل الصفحة فوراً لتحديث الواجهة
                    
            if not has_orders:
                st.info("📭 لا توجد طلبات جديدة حالياً في الانتظار. ابقَ مستعداً!")
        except Exception as e:
            st.error(f"تعذر جلب البيانات: {e}")

# ##########################################
# # الخطوة الثانية: صفحة تتبع الرحلة الديناميكية (تفتح تلقائياً بعد القبول)
# ##########################################
elif st.session_state.current_step == "track_trip":
    st.markdown("<h1 style='text-align: center; color: #FF6B35;'>📍 رحلة التوصيل الحالية</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    active_id = st.session_state.active_order_id
    
    if db is not None and active_id is not None:
        # جلب بيانات الطلب المستلم الحالي بالظبط
        doc = db.collection("orders").document(active_id).get()
        if doc.exists:
            order_data = doc.to_dict()
            
            # عرض واجهة خريطة وتفاصيل تشبه السكرين شوت التجاري اللي بعته
            st.markdown(f"""
            <div style='background-color: #111; padding: 25px; border-radius: 15px; color: #fff; margin-bottom: 20px;'>
                <h3 style='color: #FF6B35; margin: 0;'>🚖 الطلب مستلم وجاري التنفيذ</h3>
                <p style='font-size: 18px; margin: 15px 0;'>👤 <b>العميل:</b> {order_data.get('client_name', 'غير معروف')}</p>
                <p style='font-size: 16px; color: #aaa;'>📦 <b>محتوى الشحنة:</b> {order_data.get('order_details', '')}</p>
                <hr style='border-color: #333;'>
                <p style='font-size: 14px; color: #00A86B;'>🏁 موقع الاستلام: 2.15 كم | موقع التسليم: 4.0 كم</p>
            </div>
            """, unsafe_allow_html=True)
            
            # أزرار التحكم في خط سير الرحلة
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📦 تم استلام الشحنة من المتجر"):
                    db.collection("orders").document(active_id).update({"status": "🚚 جاري التوصيل للعميل"})
                    st.success("تم تحديث الحالة إلى (جاري التوصيل)!")
                    
            with col2:
                if st.button("🏁 إنهاء وتوصيل الطلب بنجاح"):
                    # تحديث الحالة في الفايربيز للانتهاء
                    db.collection("orders").document(active_id).update({"status": "✅ تم التسليم بنجاح"})
                    st.balloons() # إطلاق بالونات احتفالية على الشاشة للسائق
                    
                    # إعادة السائق ديناميكياً لصفحة الطلبات الرئيسية لاستلام طلب آخر
                    st.session_state.current_step = "view_orders"
                    st.session_state.active_order_id = None
                    st.success("تم إقفال الرحلة، وجاري إعادتك للرئيسية...")
                    st.rerun()
