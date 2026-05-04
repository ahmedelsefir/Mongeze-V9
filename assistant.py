import streamlit as st
from datetime import datetime

# إعدادات الصفحة لتظهر كأنها تطبيق احترافي
st.set_page_config(page_title="مركز المهندس - طلب خدمة", page_icon="⚙️")

st.title("⚙️ مركز المهندس للتركيبات")
st.subheader("طلب معاينة (كاميرات مراقبة / دش)")

# إنشاء النموذج (Form)
with st.form("service_request"):
    client_name = st.text_input("الأسم بالكامل")
    phone_number = st.text_input("رقم الواتساب")
    
    service_type = st.selectbox("نوع الخدمة المطلوبة", 
                                ["تركيب كاميرات مراقبة", "صيانة كاميرات", "تركيب طبق دش", "صيانة دش"])
    
    address = st.text_area("العنوان بالتفصيل")
    preferred_date = st.date_input("موعد المعاينة المفضل")
    notes = st.text_area("ملاحظات إضافية")
    
    submit_button = st.form_submit_button("إرسال الطلب")

if submit_button:
    if client_name and phone_number:
        # هنا هنربط البيانات بـ Firebase زي ما كنت مخطط
        # data = {"name": client_name, "phone": phone_number, "service": service_type, "date": str(preferred_date)}
        
        st.success(f"تم استلام طلبك يا {client_name}! سنتواصل معك عبر واتساب فوراً.")
        st.balloons() # حركة احترافية للعميل
    else:
        st.error("برجاء إدخال الأسم ورقم الهاتف")
