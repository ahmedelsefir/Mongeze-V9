import streamlit as st
import google.generativeai as genai

# قراءة المفتاح بأمان دون إظهاره في الكود الرئيسي
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)
