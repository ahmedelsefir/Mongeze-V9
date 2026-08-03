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
    استدعاء 'عقل مُنجز' مع اكتشاف النماذج المتاحة تلقائياً من سيرفر جوجل
    """
    api_key = get_gemini_api_key()
    if not api_key:
        return "❌ خطأ: لم يتم العثور على مفتاح API في Streamlit Secrets!"

    try:
        genai.configure(api_key=api_key)

        # 1. استعلام مباشر من سيرفر جوجل عن الموديلات المتاحة لمفتاحك
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)

        if not available_models:
            return "⚠️ المفتاح مقبول، ولكن لا توجد نماذج توليد نصوص مفعّلة حالياً على هذا المشروع."

        # 2. اختيار أول موديل متاح من جوجل تلقائياً
        chosen_model = available_models[0]

        instruction = (
            f"أنت 'عقل مُنجز' - الذكاء الاصطناعي التابع لمنظومة منجز ديليفري. "
            f"دورك الحالي: {system_role}. أجب بلباقة وبالعامية المصرية الراقية وبدقة شديدة."
        )

        model = genai.GenerativeModel(
            model_name=chosen_model,
            system_instruction=instruction
        )

        response = model.generate_content(prompt)
        return response.text if response and response.text else "⚠️ لم يتم استلام رد من الموديل."

    except Exception as e:
        logger.error(f"Error in ask_mongeze_ai: {str(e)}")
        return f"❌ خطأ في الاتصال بالذكاء الاصطناعي: {str(e)}"
