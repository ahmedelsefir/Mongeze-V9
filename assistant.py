import streamlit as st
import google.generativeai as genai

# الربط المباشر مع المفتاح بعد تعديلك الأخير
try:
    # بما إنك مسحت [google]، هننادي المفتاح باسمه مباشرة
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    # st.success("🎉 مبروك يا هندسة! المفتاح شغال دلوقتى") 
except Exception as e:
    st.error(f"لسه فيه مشكلة في القراءة: {e}")
