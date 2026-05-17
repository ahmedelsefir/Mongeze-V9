import streamlit as st
import firebase_admin
from firebase_admin import firestore

# إعداد الصفحة وتصميمها
st.set_page_config(page_title="بوابة السائق - منجز", layout="wide")

st.markdown("<h1 style='text-align: center; color: #00A86B;'>🚖 بوابة السائق الذكية</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>الطلبات المتاحة حالياً في النظام</p>", unsafe_allow_html=True)
st.markdown("---")

# الطريقة الآمنة بنسبة 100% للاتصال بقاعدة البيانات من الصفحات الفرعية
try:
    # التحقق أولاً إذا كان التطبيق تم تشغيله في main.py أم لا
    if not firebase_admin._apps:
        st.error("الرجاء تشغيل التطبيق من الصفحة الرئيسية أولاً لتفعيل قاعدة البيانات.")
        db = None
    else:
        # استدعاء قاعدة البيانات الحية المعرفة مسبقاً في النظام
        db = firestore.client()
except Exception as e:
    st.error(f"فشل الاتصال البرمجي بقاعدة البيانات: {e}")
    db = None

st.subheader("📥 طلبات العملاء الواردة حالياً:")

# لا نقوم بطلب البيانات إلا إذا كان db معرفاً بنجاح
if db is not None:
    try:
        # جلب الطلبات وترتيبها من الأحدث للأقدم
        orders_ref = db.collection("orders").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
        
        has_orders = False
        for order in orders_ref:
            has_orders = True
            order_data = order.to_dict()
            
            # عرض كارت الطلب الاحترافي
            with st.container():
                st.markdown(f"""
                <div style='background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-right: 5px solid #00A86B; color: #333333;'>
                    <h4 style='color: #111;'>👤 العميل: {order_data.get('client_name', 'غير معروف')}</h4>
                    <p>📦 <b>تفاصيل الطلب:</b> {order_data.get('order_details', 'لا توجد تفاصيل')}</p>
                    <p>🚨 <b>حالة الطلب:</b> <span style='color: #FF6B35;'>{order_data.get('status', 'معلق')}</span></p>
                </div>
                """, unsafe_allow_html=True)
                
                # زر قبول الطلب
                if st.button(f"قبول طلب {order_data.get('client_name', 'العميل')}", key=order.id):
                    st.success("تم قبول الطلب وجاري توجيهك للعميل!")

        if not has_orders:
            st.info("لا توجد طلبات جديدة حالياً في الانتظار. ابقَ مستعداً!")

    except Exception as e:
        st.error(f"تعذر جلب البيانات الحية: {e}")
else:
    st.warning("النظام في انتظار تفعيل شريان الاتصال بـ Firebase.")
