import streamlit as st
import pandas as pd
from datetime import datetime

# إعدادات الصفحة لتبدو احترافية
st.set_page_config(page_title="واجهة السائق - منجز", layout="wide")

st.markdown("<h1 style='text-align: center; color: #2E86C1;'>🚀 لوحة تحكم السائق</h1>", unsafe_allow_html=True)

# الجزء العلوي: حالة السائق
col1, col2 = st.columns([3, 1])
with col2:
    status = st.toggle("الحالة: متصل الآن", value=True)
    if status:
        st.success("أنت متاح لاستلام الطلبات")
    else:
        st.error("أنت الآن أوفلاين")

# تبويبات لمتابعة العمل
tab1, tab2, tab3 = st.tabs(["📥 الطلبات المتاحة", "🛣️ رحلة جارية", "💰 أرباحي"])

with tab1:
    st.subheader("الطلبات القريبة منك")
    # محاكاة لبيانات قادمة من العميل
    mock_orders = {
        "العميل": ["أحمد محمد", "سارة علي"],
        "الموقع": ["الدقي - شارع التحرير", "مدينة نصر - عباس العقاد"],
        "نوع الطلب": ["تاكسي 🚕", "توصيل طعام 🍔"],
        "المسافة": ["2.5 كم", "4.2 كم"]
    }
    df = pd.DataFrame(mock_orders)
    st.table(df)
    
    order_id = st.selectbox("اختر رقم الطلب لقبوله:", [1, 2])
    if st.button("✅ قبول الطلب والتحرك الآن", use_container_width=True):
        st.info(f"تم قبول الطلب رقم {order_id}. يرجى التوجه لموقع العميل.")

with tab2:
    st.subheader("تفاصيل الرحلة الحالية")
    st.warning("لا توجد رحلة نشطة حالياً. اذهب لتبويب الطلبات المتاحة.")

with tab3:
    st.subheader("ملخص الأرباح اليومية")
    c1, c2 = st.columns(2)
    c1.metric("إجمالي الدخل", "450 EGP")
    c2.metric("عدد الرحلات", "8")
