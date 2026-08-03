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
    استدعاء 'عقل مُنجز' مع اكتشاف النماذج المتاحة تلقائياً بدون أخطاء 404
    """
    api_key = get_gemini_api_key()
    if not api_key:
        return "❌ خطأ: لم يتم العثور على مفتاح API في Streamlit Secrets!"

    try:
        genai.configure(api_key=api_key)
        
        # 1. الاستعلام الديناميكي المباشر من جوجل عن النماذج المتاحة للمفتاح
        supported_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                supported_models.append(m.name)

        if not supported_models:
            return "⚠️ المفتاح مقبول، ولكن لا توجد نماذج توليد نصوص مفعّلة حالياً لهذا المشروع."

        # 2. اختيار أول نموذج متاح ومفعل تلقائياً
        target_model = supported_models[0]

        instruction = (
            f"أنت 'عقل مُنجز' - الذكاء الاصطناعي التابع لمنظومة منجز ديليفري. "
            f"دورك الحالي: {system_role}. أجب بلباقة وبالعامية المصرية الراقية وبدقة شديدة."
        )

        model = genai.GenerativeModel(
            model_name=target_model,
            system_instruction=instruction
        )

        response = model.generate_content(prompt)
        return response.text if response and response.text else "⚠️ لم يتم استلام رد من الموديل."

    except Exception as e:
        logger.error(f"Error in ask_mongeze_ai: {str(e)}")
        return f"❌ خطأ في الاتصال بالذكاء الاصطناعي: {str(e)}"
