import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# 1. تنظيف وإعداد إعدادات الصفحة (لحل مشكلة SyntaxError)
st.set_page_config(
    page_title="اللوحة العامة المركزية",
    page_icon="🏠",
    layout="wide"
)

# 2. وظيفة الربط بـ Firebase (التعامل مع شهادة الاعتماد)
def initialize_firebase():
    if not firebase_admin._apps:
        try:
            # تحويل secrets إلى قاموس بايثون صريح
            fb_dict = dict(st.secrets["firebase"])
            
            # معالجة مفتاح الـ private_key للتأكد من قراءة السطور الجديدة (\n) بشكل صحيح
            if "private_key" in fb_dict:
                fb_dict["private_key"] = fb_dict["private_key"].replace("\\n", "\n")
            
            cred = credentials.Certificate(fb_dict)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"حدث خطأ أثناء الاتصال بالقاعدة: {e}")
            return None
    return firestore.client()

# تفعيل قاعدة البيانات
db = initialize_firebase()

# 3. واجهة التطبيق التعريفية
def main():
    st.title("🏠 نظام المساعد الذكي - Mongeze")
    st.info("تم تفعيل التطبيق بنجاح. هذا النظام مصمم لإدارة العمليات وتقديم الخدمات للعملاء المشتركين.")

    if db:
        st.success("✅ بوابة البيانات مفتوحة وجاهزة للعمل.")
    else:
        st.warning("⚠️ البوابة مغلقة. يرجى التحقق من إعدادات Secrets في Streamlit.")

if __name__ == "__main__":
    main()
