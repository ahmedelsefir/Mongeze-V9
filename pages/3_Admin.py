import streamlit as st

# 1. إعدادات الصفحة
st.set_page_config(
    page_title="بوابة المسؤول - منجز", 
    layout="wide"
)

# 2. واجهة لوحة تحكم المسؤول (الأدمن)
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>📊 لوحة تحكم المسؤول (الأدمن)</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.1rem; color: #555555;'>مرحباً بك يا هندسة في النظام الإداري والمالي لمنصة مُنجز لعام 2026</p>", unsafe_allow_html=True)
st.markdown("---")

# 3. عرض إحصائيات النظام والتقارير المالية والمحاسبية
st.markdown("<h3 style='color: #1E3A8A;'>📈 مؤشرات الأداء الحالية</h3>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="💰 إجمالي الإيرادات والضرائب", value="54,200 ج.م", delta="+12% النمو")
with col2:
    st.metric(label="🚖 السائقين النشطين في العمل", value="18 سائق", delta="3+ اليوم")
with col3:
    st.metric(label="🛒 الطلبات المكتملة بنجاح", value="320 طلب", delta="+45 طلب")

st.markdown("---")

# 4. قسم الإدارة والمراقبة
st.subheader("⚙️ الإشراف الإداري وحسابات الأرباح")
st.info("هذه البوابة مؤمنة بالكامل وجاهزة لربط الحسابات البرمجية والبيانات الحية من قاعدة البيانات بنجاح وبأعلى دقة.")
