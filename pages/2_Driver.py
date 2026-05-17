import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

# 1. إعداد الصفحة
st.set_page_config(page_title="بوابة السائق - منجز", layout="wide")

st.markdown("<h1 style='text-align: center; color: #00A86B;'>🚖 بوابة السائق الذكية</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>الطلبات المتاحة حالياً في النظام</p>", unsafe_allow_html=True)
st.markdown("---")

# 2. تفعيل الاتصال المباشر والمستقل بـ Firebase
try:
    if not firebase_admin._apps:
        key_dict = json.loads(st.secrets["textkey"])
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    st.error(f"فشل الاتصال التلقائي بقاعدة البيانات: {e}")
    db = None

st.subheader("📥 طلبات العملاء الواردة حالياً:")

if db is not None:
    try:
        orders_ref = db.collection("orders").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
        has_orders = False
        
        for order in orders_ref:
            has_orders = True
            order_data = order.to_dict()
            
            with st.container():
                st.markdown(f"""
                <div style='background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-right: 5px solid #00A86B; color: #333333;'>
                    <h4 style='color: #111;'>👤 العميل: {order_data.get('client_name', 'غير معروف')}</h4>
                    <p>📦 <b>تفاصيل الطلب:</b> {order_data.get('order_details', 'لا توجد تفاصيل')}</p>
                    <p>🚨 <b>حالة الطلب:</b> <span style='color: #FF6B35;'>{order_data.get('status', 'معلق')}</span></p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"قبول طلب {order_data.get('client_name', 'العميل')}", key=order.id):
                    st.success("تم قبول الطلب بنجاح!")

        if not has_orders:
            st.info("لا توجد طلبات جديدة حالياً في الانتظار.")
    except Exception as e:
        st.error(f"تعذر جلب البيانات الحية: {e}")
else:
    st.warning("في انتظار تفعيل شريان الاتصال بقاعدة البيانات.")
