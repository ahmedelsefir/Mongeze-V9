import streamlit as st
import google.generativeai as genai
import os

# --- إعدادات الصفحة ---
st.set_page_config(
    page_title="Mongeze AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# --- دالة التحقق من مفتاح API والاتصال ---
def initialize_api():
    """التحقق من وجود المفتاح وتهيئة المكتبة"""
    # جلب المفتاح من Secrets (تأكد من تسميته GEMINI_API_KEY في الإعدادات)
    api_key = st.secrets.get("GEMINI_API_KEY")
    
    if not api_key:
        st.error("⚠️ لم يتم العثور على 'GEMINI_API_KEY' في الإعدادات (Secrets).")
        return False

    try:
        # تهيئة المكتبة
        genai.configure(api_key=api_key)
        # التحقق من صلاحية المفتاح عبر طلب قائمة الموديلات (اختياري لكن مفيد للأمان)
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                return True
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال: {str(e)}")
        return False
    return False

# --- الهيكل الرئيسي للتطبيق ---
def main():
    st.title("🚀 مساعد Mongeze الذكي")
    st.markdown("---")

    # البدء بالتحقق من الاتصال
    if not initialize_api():
        st.warning("يرجى ضبط مفاتيح الوصول للاستمرار.")
        st.stop()

    # إعداد الموديل
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
    }
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )

    # ذاكرة الجلسة للدردشة (للحفاظ على سياق العمل)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # عرض الرسائل السابقة
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # مدخلات المستخدم
    if prompt := st.chat_input("كيف يمكنني مساعدتك في تطوير Mongeze اليوم؟"):
        # عرض رسالة المستخدم
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # إضافة رسالة المستخدم للتاريخ
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # توليد الرد من الذكاء الاصطناعي
        with st.chat_message("assistant"):
            try:
                # إرسال التاريخ بالكامل للحفاظ على سياق "البرنامج المحاسبي" والتفاصيل السابقة
                chat_session = model.start_chat(history=[]) # يمكن تطويرها لإرسال التاريخ الفعلي
                response = chat_session.send_message(prompt)
                full_response = response.text
                st.markdown(full_response)
                
                # إضافة رد المساعد للتاريخ
                st.session_state.chat_history.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"حدث خطأ أثناء معالجة الرد: {e}")

# --- تشغيل البرنامج ---
if __name__ == "__main__":
    main()
