import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. تأمين الاتصال (القراءة من Streamlit Secrets مباشرة)
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
else:
    st.error("⚠️ خطأ في الأسرار: يرجى إضافة GEMINI_API_KEY في إعدادات Streamlit.")

# 2. تصميم القائمة الجانبية
st.sidebar.title("🚀 منظومة منجز")
st.sidebar.markdown("---")
choice = st.sidebar.radio("انتقل إلى:", ["الرئيسية", "واجهة المندوب (Backend)", "لوحة التحكم"])

# --- فرع واجهة المندوب ---
if choice == "واجهة المندوب (Backend)":
    st.title("📲 لوحة تحكم المندوب")
    
    # إحصائيات سريعة للمندوب
    col1, col2 = st.columns(2)
    col1.metric("إجمالي الدخل", "341.69 ج.م")
    col2.metric("طلبات اليوم", "5")
    
    st.divider()
    
    st.subheader("📸 تصوير وفحص الفاتورة")
    uploaded_file = st.file_uploader("ارفع صورة الفاتورة هنا", type=['jpg', 'png', 'jpeg'])
    
    if uploaded_file:
        img = Image.open(uploaded_file)
        # استخدام المعيار الجديد لعرض الصور
        st.image(img, caption="الفاتورة المرفوعة", use_container_width=True)
        
        if st.button("تحليل المبلغ والعمولة"):
            with st.spinner("جاري معالجة البيانات بالذكاء الاصطناعي..."):
                try:
                    # التعديل الذهبي: تحديد الموديل والنسخة المستقرة
                    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
                    
                    # الـ Prompt المصمم خصيصاً لمشروع منجز
                    prompt = """
                    أنت مساعد مالي لمشروع 'منجز'. 
                    قم بتحليل الصورة واستخرج:
                    1. إجمالي المبلغ الموجود في الفاتورة.
                    2. احسب عمولة المندوب (10% من الإجمالي).
                    قم بعرض النتائج بشكل احترافي ومنظم باللغة العربية.
                    """
                    
                    response = model.generate_content([prompt, img])
                    
                    st.success("✅ تم التحليل بنجاح!")
                    st.markdown("---")
                    st.write(response.text)
                    
                except Exception as e:
                    # معالجة الأخطاء بشكل احترافي
                    st.error(f"حدثت مشكلة تقنية: {e}")
                    st.info("نصيحة: تأكد من استخدام google-generativeai>=0.7.2 في ملف requirements.txt")

# --- فرع الرئيسية ---
elif choice == "الرئيسية":
    st.title("🏠 شاشة العميل")
    st.write("أهلاً بك في **منجز**، اطلب وسنصلك فوراً.")

# --- فرع لوحة التحكم ---
elif choice == "لوحة التحكم":
    st.title("📊 لوحة الإدارة")
    st.write("متابعة العمليات والمناديب.")
    st.warning("هذه المنطقة تحت التطوير لربطها بقاعدة بيانات Firebase.")
