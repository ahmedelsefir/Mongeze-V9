import streamlit as st

# إعداد الصفحة
st.set_page_config(page_title="واجهة العميل - منجز", layout="wide")

st.title("🍔 واجهة طلبات العميل")

# هنا هتحط كود "فودي" اللي كتبناه قبل كدة
st.info("مرحباً بك في واجهة العميل. من هنا يمكنك طلب التاكسي أو الطعام.")

with st.form("order_form"):
    name = st.text_input("الأسم")
    order = st.text_area("ماذا تريد أن تطلب؟")
    submit = st.form_submit_button("إرسال الطلب")
    
    if submit:
        st.success(f"تم استلام طلبك يا {name} وجاري البحث عن أقرب سائق!")
