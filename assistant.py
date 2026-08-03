import os
import logging
import streamlit as st
import google.generativeai as genai

logger = logging.getLogger(__name__)

def get_gemini_api_key():
    """جلب المفتاح من Streamlit Secrets"""
    key = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")
    return str(key).strip() if key else None

def ask_mongeze_ai(prompt: str, system_role: str = "مساعد عام لتطبيق منجز") -> str:
    """
    استدعاء 'عقل مُنجز' بدون الاعتماد على اسم موديل ثابت
    """
    api_key = get_gemini_api_key()
    if not api_key:
        return "❌ خطأ: لم يتم العثور على مفتاح API في Streamlit Secrets!"

    try:
        genai.configure(api_key=api_key)

        # 1. الاستعلام المباشر من سيرفر جوجل عن الموديلات المتاحة للمفتاح
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)

        if not available_models:
            return "⚠️ المفتاح مقبول، لكن سيرفر جوجل لم يرجّع أي نماذج مفعّلة لهذا المشروع."

        # 2. التجربة الذكية لكل الموديلات المتاحة حتى ينجح أحدها
        last_error = None
        for model_name in available_models:
            try:
                instruction = (
                    f"أنت 'عقل مُنجز' - الذكاء الاصطناعي التابع لمنظومة منجز ديليفري. "
                    f"دورك الحالي: {system_role}. أجب بلباقة وبالعامية المصرية الراقية وبدقة شديدة."
                )
                
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=instruction
                )
                
                response = model.generate_content(prompt)
                if response and response.text:
                    # تم الاتصال بنجاح!
                    return response.text
            except Exception as ex:
                last_error = ex
                continue

        return f"❌ تعذر الاتصال بالنماذج المتاحة ({available_models}): {str(last_error)}"

    except Exception as e:
        logger.error(f"Error in ask_mongeze_ai: {str(e)}")
        return f"❌ خطأ في الاتصال بالذكاء الاصطناعي: {str(e)}"
