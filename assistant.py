import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. تأمين الاتصال (القراءة من Streamlit Secrets مباشرة)
#
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
        # استخدام المعيار الجديد لعرض الصور في ستريم ليت
        st.image(img, caption="الفاتورة المرفوعة", use_container_width=True)
        
        if st.button("تحليل المبلغ والعمولة"):
            with st.spinner("جاري معالجة البيانات بالذكاء الاصطناعي..."):
                try:
                    # استخدمنا gemini-1.5-flash لسرعته في معالجة الصور
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # الـ Prompt المصمم خصيصاً لمشروع منجز [cite: 2026-01-18]
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
                    # لمعالجة خطأ NotFound أو مشاكل الـ API
                    st.error(f"حدثت مشكلة تقنية: {e}")
                    st.info("نصيحة: تأكد من تحديث مكتبة google-generativeai في ملف requirements.txt")

# --- فرع الرئيسية ---
elif choice == "الرئيسية":
    st.title("🏠 شاشة العميل")
    st.write("أهلاً بك في **منجز**، اطلب وسنصلك فوراً.")
    st.info("هذه الواجهة مخصصة لاستقبال طلبات العملاء قريباً.")

# --- فرع لوحة التحكم ---
elif choice == "لوحة التحكم":
    st.title("📊 لوحة الإدارة")
    st.write("متابعة العمليات والمناديب.")
    # هنا سيتم ربط Firebase لاحقاً لعرض البيانات الحقيقية
    st.warning("هذه المنطقة تحت التطوير لربطها بقاعدة بيانات Firebase.")
