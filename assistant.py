import streamlit as st
import google.generativeai as genai
import os

def initialize_api():
    # 1. جلب المفتاح من الأسرار (Secrets)
    # ملاحظة: تأكد أن الاسم في Secrets هو 'GEMINI_API_KEY'
    api_key = st.secrets["GEMINI_API_KEY"]
    
    if not api_key:
        st.error("لم يتم العثور على مفتاح API في ملف الإعدادات.")
        return False

    try:
        # 2. إعداد المكتبة بالمفتاح الجديد
        genai.configure(api_key=api_key)
        
        # 3. محاولة استدعاء بسيط للتأكد من اتصال "الأبيات" (الإصدارات) المتاحة
        model_list = genai.list_models()
        
        # عرض الموديلات المتاحة للتأكد من نجاح الاتصال
        st.success("تم الاتصال بنجاح بمزود الخدمة.")
        return True
        
    except Exception as e:
        st.error(f"حدث خطأ أثناء محاولة الاتصال: {str(e)}")
        return False

# تشغيل وظيفة التحقق
if initialize_api():
    # هنا تبدأ كتابة منطق تطبيقك (المحاسبة أو البوتات)
    model = genai.GenerativeModel('gemini-1.5-flash')
    st.write("التطبيق جاهز للعمل مع المحرك الجديد.")
