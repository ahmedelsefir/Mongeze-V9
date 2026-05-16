import streamlit as st

st.set_page_config(page_title="واجهة العميل - منجز", layout="wide")

st.markdown("<h1 style='text-align: center; color: #FF6B35;'>🛒 بوابة العميل الذكية</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>مرحباً بك في واجهة العميل. من هنا يمكنك طلب الخدمات ومتابعة طلباتك بدقة لعام 2026.</p>", unsafe_allow_html=True)
st.markdown("---")

# نموذج طلب جديد
with st.form("client_order_form"):
    st.subheader("📦 إنشاء طلب خدمات لوجستية جديد")
    name = st.text_input("الاسم بالكامل")
    details = st.text_area("ماذا تريد أن تطلب؟")
    submit = st.form_submit_button("إرسال الطلب")
    
    if submit:
        if name and details:
            st.success(f"شكراً لك يا {name}! جاري البحث عن أقرب سائق وتم استلام طلبك بأعلى دقة.")
        else:
            st.error("الرجاء ملء جميع الحقول المطلوبة لإتمام الطلب بنجاح.")
