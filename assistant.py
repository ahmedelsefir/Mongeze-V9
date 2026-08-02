import google.generativeai as genai
import streamlit as st

def get_gemini_api_key():
    """جلب المفتاح الذكي تلقائياً من أي مسار موجود في Streamlit Secrets"""
    if "GOOGLE_API_KEY" in st.secrets:
        return st.secrets["GOOGLE_API_KEY"]
    elif "google" in st.secrets and "api_key" in st.secrets["google"]:
        return st.secrets["google"]["api_key"]
    elif "github" in st.secrets and "GEMINI_API_KEY" in st.secrets["github"]:
        return st.secrets["github"]["GEMINI_API_KEY"]
    elif "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    return None

def ask_mongeze_ai(prompt: str, system_role: str = "مساعد عام لتطبيق منجز") -> str:
    """
    الدالة الرئيسية لاستدعاء 'عقل مُنجز' من أي مكان في التطبيق
    """
    api_key = get_gemini_api_key()
    
    if not api_key:
        return "⚠️ خطأ: لم يتم العثور على مفتاح API في Streamlit Secrets!"
        
    try:
        # 1. تهيئة المفتاح
        genai.configure(api_key=api_key)
        
        # 2. إعطاء التعليمات والتوجيهات للذكاء الاصطناعي
        instruction = (
            f"أنت 'عقل مُنجز' - الذكاء الاصطناعي التابع لمنظومة منجز ديليفري. "
            f"دورك الحالي: {system_role}. أجب بلباقة وبالعامية المصرية الراقية وبدقة شديدة."
        )
        
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=instruction
        )
        
        # 3. توليد الإجابة
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"❌ خطأ في الاتصال بالذكاء الاصطناعي: {str(e)}"
