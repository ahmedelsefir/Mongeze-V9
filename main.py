import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ========================================================
# 1. دالة محرك الإرسال (Zoho SMTP) - مدمجة ومحمية بـ Secrets
# ========================================================
def send_monjez_email(receiver_email, subject, body_html):
    smtp_server = "smtp.zoho.com"
    port = 465  # منفذ SSL المشفر لـ Zoho
    
    try:
        # جلب البيانات الحساسة من مجموعة [zoho] في الـ Secrets
        sender_email = st.secrets["zoho"]["sender_email"]
        app_password = st.secrets["zoho"]["app_password"]
    except Exception:
        st.error("❌ خطأ حرج: لم يتم العثور على مفاتيح [zoho] السرية في إعدادات Secrets!")
        return False

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"منصة مُنجز السيادية <{sender_email}>"
    message["To"] = receiver_email

    part_html = MIMEText(body_html, "html", "utf-8")
    message.attach(part_html)

    try:
        with smtplib.SMTP_SSL(smtp_server, port) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        return True
    except Exception as e:
        print(f"فشل إرسال البريد: {e}")
        return False


# ========================================================
# 2. إعدادات وتصميم الشاشة الرئيسية للمنصة
# ========================================================
st.set_page_config(
    page_title="منصة مُنجز الذكية",
    page_icon="🚀",
    layout="wide"
)

st.markdown("<h1 style='text-align: center; color: #FF6B35;'>🚀 مرحباً بكم في منصة مُنجز</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #555555;'>نظام الإدارة والخدمات اللوجستية المتكامل لعام 2026</p>", unsafe_allow_html=True)
st.markdown("---")

st.markdown("<h3 style='text-align: center; color: #1E3A8A;'>اختر القسم الذي تود الدخول إليه:</h3>", unsafe_allow_html=True)
st.write("\n")


# ========================================================
# 3. أزرار البوابات الفرعية والتنقل
# ========================================================
if st.button("🛒 دخول بوابة العميل", use_container_width=True):
    st.switch_page("pages/1_Client.py")

st.write("\n")

if st.button("🚖 دخول بوابة السائق", use_container_width=True):
    st.switch_page("pages/2_Driver.py")

st.write("\n")

if st.button("📊 دخول بوابة المسؤول", use_container_width=True):
    st.switch_page("pages/3_Admin.py")


# ========================================================
# 4. مركز اختبار الفواتير لايف (يظهر في أسفل الصفحة)
# ========================================================
st.markdown("---")
st.subheader("🧪 مركز اختبار فواتير مُنجز")

# خانة يكتب فيها بريدك الشخصي لتجربة الاستقبال
test_email = st.text_input("اكتب إيميلك الشخصي (الجيميل مثلاً) لتجربة الاستقبال:", key="main_test_email")

if st.button("🚀 إرسال فاتورة تجريبية لايف", key="main_test_btn"):
    if test_email:
        sample_html = """
        <div style="direction: rtl; text-align: right; font-family: Arial, sans-serif; border: 2px solid #FF5733; padding: 20px; border-radius: 10px;">
            <h2 style="color: #FF5733;">منصة مُنجز السيادية 🚀</h2>
            <p>مرحباً بك يا هندسة، هذا الإيميل يؤكد اتصال محرك زوهو بنجاح بالمنصة واكتمال الربط!</p>
            <hr style="border: 0; border-top: 1px solid #ccc;">
            <p><b>حالة الاتصال:</b> ممتازة 100% ✅</p>
        </div>
        """
        with st.spinner("جاري إطلاق الفاتورة عبر سيرفر زوهو السيادي..."):
            success = send_monjez_email(test_email, "تأكيد اتصال محرك منجز 🚀", sample_html)
            
            if success:
                st.success("✅ تم الإرسال بنجاح! افتح بريدك الشخصي الآن وتفقد صندوق الوارد أو الـ Spam.")
            else:
                st.error("❌ فشل الإرسال. تأكد من إيقاظ التطبيق وصحة مجموعة [zoho] في الـ Secrets.")
    else:
        st.warning("رجاءً اكتب الإيميل أولاً.")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #888888; font-size: 0.9rem;'>تم التصميم بمنتهى الدقة بواسطة فريق مُنجز التقني</p>", unsafe_allow_html=True)
