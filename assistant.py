import os
import streamlit as st
import google.generativeai as genai

# استدعاء المفتاح من بيئة النظام (GitHub Secrets)
# ملاحظة: عند التشغيل محلياً، يجب تعريف هذا المتغير في جهازك
api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    # إعداد المكتبة باستخدام المفتاح المؤمن
    genai.configure(api_key=api_key)
    # st.success("تم الاتصال بالواجهة الخلفية بنجاح ✅")
else:
    st.error("خطأ: لم يتم العثور على مفتاح API في الأسرار. يرجى مراجعة إعدادات GitHub.")

# وظيفة معالجة بيانات المندوب باستخدام المفتاح
def process_backend_data():
    if api_key:
        model = genai.GenerativeModel('gemini-1.5-flash')
        # كمل باقي وظائف معالجة الفواتير هنا
        pass
