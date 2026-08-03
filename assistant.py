import google.generativeai as genai
import streamlit as st

def get_gemini_api_key():
    """جلب المفتاح الذكي تلقائياً مع تنظيف المسافات"""
    key = None
    if "GOOGLE_API_KEY" in st.secrets and st.secrets["GOOGLE_API_KEY"]:
        key = st.secrets["GOOGLE_API_KEY"]
    elif "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"]:
        key = st.secrets["GEMINI_API_KEY"]
    elif "google" in st.secrets and "api_key" in st.secrets["google"]:
        key = st.secrets["google"]["api_key"]
    elif "github" in st.secrets and "GEMINI_API_KEY" in st.secrets["github"]:
        key = st.secrets["github"]["GEMINI_API_KEY"]
        
    return str(key).strip() if key else None
