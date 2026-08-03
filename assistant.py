import os
import logging
import streamlit as st
import google.generativeai as genai

logger = logging.getLogger(__name__)

def get_gemini_api_key():
    """جلب المفتاح الذكي تلقائياً من أي مسار موجود في Streamlit Secrets"""
    if "GOOGLE_API_KEY" in st.secrets and st.secrets["GOOGLE_API_KEY"]:
        return str(st.secrets["GOOGLE_API_KEY"]).strip()
    if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
        return str(st.secrets["GEMINI_API_KEY"]).strip()
    if "google" in st.secrets and isinstance(st.secrets["google"], dict):
        if "api_key" in st.secrets["google"]:
            return str(st.secrets["google"]["api_key"]).strip()
    return os.environ.get("GOOGLE_API_KEY", os.environ.get("GEMINI_API_KEY", ""))

def ask_mongeze_ai(prompt: str, system_role: str = "مساعد عام لتطبيق منجز") -> str:
    """
    الدالة الرئيسية لاستدعاء 'عقل مُنجز'
    """
    api_key = get_gemini_api_key()
    
    if not api_key:
        return "❌ خطأ: لم يتم العثور على مفتاح API في Streamlit Secrets!"

    try:
        genai.configure(api_key=api_key)
        
        instruction = (
            f"أنت 'عقل مُنجز' - الذكاء الاصطناعي التابع لمنظومة منجز ديليفري. "
            f"دورك الحالي: {system_role}. أجب بلباقة وبالعامية المصرية الراقية وبدقة شديدة."
        )
        
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=instruction
        )
        
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text
        return "⚠️ لم يتم استلام رد من الموديل."
        
    except Exception as e:
        logger.error(f"Error in ask_mongeze_ai: {str(e)}")
        return f"❌ خطأ في الاتصال بالذكاء الاصطناعي: {str(e)}"
