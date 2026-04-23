import streamlit as st
from google import genai
from google.genai import types
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
    api_key = st.secrets.get("GEMINI_API_KEY")

    if not api_key:
        st.error("⚠️ لم يتم العثور على 'GEMINI_API_KEY' في الإعدادات (Secrets).")
        return None

    try:
        client = genai.Client(api_key=api_key)
        # التحقق من صلاحية المفتاح
        models = client.models.list()
        for m in models:
            if "gemini" in m.name:
                return client  # ✅ رجّع الـ client مباشرة
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال: {str(e)}")
        return None

    return None

# --- الهيكل الرئيسي للتطبيق ---
def main():
    st.title("🚀 مساعد Mongeze الذكي")
    st.markdown("---")

    # البدء بالتحقق من الاتصال
    client = initialize_api()
    if not client:
        st.warning("يرجى ضبط مفاتيح الوصول للاستمرار.")
        st.stop()

    # ذاكرة الجلسة للدردشة
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # عرض الرسائل السابقة
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # مدخلات المستخدم
    if prompt := st.chat_input("كيف يمكنني مساعدتك في تطوير Mongeze اليوم؟"):
        with st.chat_message("user"):
            st.markdown(prompt)

        st.session_state.chat_history.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            try:
                # بناء تاريخ المحادثة بالصيغة الجديدة
                history = []
                for msg in st.session_state.chat_history[:-1]:
                    role = "user" if msg["role"] == "user" else "model"
                    history.append(
                        types.Content(
                            role=role,
                            parts=[types.Part(text=msg["content"])]
                        )
                    )

                # إضافة رسالة المستخدم الحالية
                history.append(
                    types.Content(
                        role="user",
                        parts=[types.Part(text=prompt)]
                    )
                )

                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=history,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        top_p=0.95,
                        top_k=64,
                        max_output_tokens=8192,
                    )
                )

                full_response = response.text
                st.markdown(full_response)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": full_response
                })

            except Exception as e:
                st.error(f"حدث خطأ أثناء معالجة الرد: {e}")

# --- تشغيل البرنامج ---
if __name__ == "__main__":
    main()
