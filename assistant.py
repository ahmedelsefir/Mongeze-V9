import os
import logging
import streamlit as st
import google.generativeai as genai

logger = logging.getLogger(__name__)

def get_gemini_api_key():
    """جلب المفتاح الذكي من Streamlit Secrets"""
    key = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")
    return str(key).strip() if key else None

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

        # تجربة النماذج المتاحة بالترتيب لضمان توافق مشروعك
        candidate_models = [
            'gemini-2.0-flash',
            'gemini-1.5-flash-latest',
            'gemini-1.5-flash',
            'gemini-1.5-pro'
        ]

        last_error = None
        for model_name in candidate_models:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=instruction
                )
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text
            except Exception as e:
                last_error = e
                continue

        return f"❌ خطأ في الاتصال بالنموذج: {str(last_error)}"

    except Exception as e:
        logger.error(f"Error in ask_mongeze_ai: {str(e)}")
        return f"❌ خطأ في الإعدادات: {str(e)}"
