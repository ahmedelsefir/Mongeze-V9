import streamlit as st
import os
import google.generativeai as genai
from PIL import Image

# تأمين المفتاح السري (GitHub Secrets)
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# القائمة الجانبية للتنقل (زي تطبيقات الشركات الكبيرة)
st.sidebar.title("🚀 منظومة منجز")
choice = st.sidebar.radio("انتقل إلى:", ["الرئيسية", "واجهة المندوب (Backend)", "لوحة التحكم"])

# --- فرع واجهة المندوب (الذي سألت عنه) ---
if choice == "واجهة المندوب (Backend)":
    # تصميم الواجهة الاحترافية
    st.title("📲 لوحة تحكم المندوب")
    
    # إحصائيات المندوب
    col1, col2 = st.columns(2)
    col1.metric("إجمالي الدخل", "341.69 ج.م")
    col2.metric("طلبات اليوم", "5")
    
    st.divider()
    
    # ميزة الذكاء الاصطناعي لمعالجة الفاتورة
    st.subheader("📸 تصوير وفحص الفاتورة")
    uploaded_file = st.file_uploader("ارفع صورة الفاتورة هنا", type=['jpg', 'png', 'jpeg'])
    
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="الفاتورة المرفوعة", use_column_width=True)
        
        if st.button("تحليل المبلغ والعمولة"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            with st.spinner("جاري معالجة البيانات..."):
                # الذكاء الاصطناعي بيقرأ الصورة ويحسب حسب القواعد المالية [cite: 2026-01-18]
                response = model.generate_content(["استخرج إجمالي المبلغ واحسب عمولة 10%", img])
                st.success("تم التحليل بنجاح!")
                st.write(response.text)

# --- باقي الفروع (الرئيسية ولوحة التحكم) ---
elif choice == "الرئيسية":
    st.title("🏠 شاشة العميل")
    st.write("أهلاً بك في منجز، اطلب وسنصلك فوراً.")

elif choice == "لوحة التحكم":
    st.title("📊 الإدارة")
    st.write("متابعة المناديب والعمليات المالية.")
