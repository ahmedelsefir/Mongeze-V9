import streamlit as st
import google.generativeai as genai

# التأكد من قراءة المفتاح من Streamlit Secrets
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    # st.success("المفتاح اتصل بنجاح ✅") # سطر اختياري للتأكد
else:
    st.error("خطأ: التطبيق لسه مش شايف GEMINI_API_KEY في الإعدادات")
