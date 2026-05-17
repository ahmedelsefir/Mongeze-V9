import streamlit as st
from firebase_admin import firestore

# التأكد من الاتصال بقاعدة البيانات
try:
    db = firestore.client()
except Exception:
    st.error("فشل الاتصال بقاعدة البيانات")

st.set_page_config(page_title="بوابة السائق - منجز", layout="wide")

st.markdown("<h1 style='text-align: center; color: #00A86B;'>🚖 بوابة السائق الذكية</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>الطلبات المتاحة حالياً في النظام</p>", unsafe_allow_html=True)
st.markdown("---")

st.subheader("📥 طلبات العملاء الواردة حالياً:")

try:
    # جلب جميع الطلبات من Firebase وترتيبها من الأحدث للأقدم
    orders_ref = db.collection("orders").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
    
    has_orders = False
    for order in orders_ref:
        has_orders = True
        order_data = order.to_dict()
        
        # تصميم كارت احترافي لكل طلب يظهر للسائق
        with st.container():
            st.markdown(f"""
            <div style='background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-right: 5px solid #00A86B;'>
                <h4>👤 العميل: {order_data.get('client_name')}</h4>
                <p>📦 <b>تفاصيل الطلب:</b> {order_data.get('order_details')}</p>
                <p>🚨 <b>حالة الطلب:</b> <span style='color: #FF6B35;'>{order_data.get('status')}</span></p>
            </div>
            """, unsafe_allow_html=True)
            
            # زر إضافي للسائق لقبول الشحنة
            if st.button(f"قبول طلب {order_data.get('client_name')}", key=order.id):
                st.success("تم قبول الطلب وجاري توجيهك للعميل!")

    if not has_orders:
        st.info("لا توجد طلبات جديدة حالياً. ابقَ مستعداً!")

except Exception as e:
    st.error(f"تعذر جلب البيانات: {e}")
