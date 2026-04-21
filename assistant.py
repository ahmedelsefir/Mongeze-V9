import streamlit as st
import os
import google.generativeai as genai
from PIL import Image

# 1. إعدادات الخصوصية والأمان (المفتاح السري)
#
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# 2. تصميم القائمة الجانبية (نظام الفروع)
st.sidebar.title("🚀 نظام منجز الذكي")
menu = ["الرئيسية", "واجهة المناديب (Backend)", "لوحة التحكم (Admin)"]
choice = st.sidebar.selectbox("انتقل إلى الفرع:", menu)

# --- الفرع الأول: واجهة المناديب (هنا يتم سحر الذكاء الاصطناعي) ---
if choice == "واجهة المناديب (Backend)":
    st.title("📲 واجهة المندوب الذكية")
    st.write("ارفع صورة الفاتورة لتدقيقها وحساب العمولة فوراً.")
    
    uploaded_file = st.file_uploader("التقط صورة الفاتورة", type=['jpg', 'jpeg', 'png'])
    
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="الفاتورة المرفوعة", use_column_width=True)
        
        if st.button("تحليل الفاتورة بالذكاء الاصطناعي"):
            # استدعاء Gemini AI لقراءة البيانات
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = "استخرج المبلغ الإجمالي من هذه الفاتورة واحسب عمولة 10% والمجموع النهائي."
            
            with st.spinner("جاري التحليل..."):
                response = model.generate_content([prompt, img])
                st.success("تم التحليل بنجاح!")
                st.info(response.text)

# --- الفرع الثاني: لوحة الإدارة (لمتابعة العمولات) ---
elif choice == "لوحة التحكم (Admin)":
    st.title("📊 إدارة نظام منجز")
    st.write("هنا تظهر تقارير الأرباح والعمولات المسجلة في Firebase.")
    # هنا سنربط لاحقاً بـ Firebase Database اللي فعلناها
    #

# --- الصفحة الرئيسية ---
else:
    st.title("🏠 مرحبا بك في منجز")
    st.write("مشروعك الآن مدعوم بأقوى تقنيات الذكاء الاصطناعي في العالم.")
