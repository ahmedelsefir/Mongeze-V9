import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_monjez_email(receiver_email, subject, body_html):
    """
    محرك الإرسال الخفي لمنصة مُنجز السيادية - يرسل إيميلات وفواتير للعملاء والكباتن
    """
    smtp_server = "smtp.zoho.com"
    port = 465  # منفذ SSL المشفر لـ Zoho
    
    # جلب البيانات الحساسة من خزنة Secrets لمنع تسريب الباسورد على GitHub
    try:
        sender_email = st.secrets["zoho"]["sender_email"]
        app_password = st.secrets["zoho"]["app_password"]
    except Exception:
        st.error("❌ خطأ حرج: لم يتم العثور على مفاتيح زوهو السرية في إعدادات Secrets الخاصة بـ Streamlit!")
        return False

    # بناء هيكل الرسالة الأساسي وتأمين دعم اللغة العربية
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"منصة مُنجز السيادية <{sender_email}>"
    message["To"] = receiver_email

    # ربط كود الـ HTML وتأمين ترميز النصوص
    part_html = MIMEText(body_html, "html", "utf-8")
    message.attach(part_html)

    try:
        # فتح اتصال مشفر وآمن بالسيرفر وشحن الرسالة فوراً
        with smtplib.SMTP_SSL(smtp_server, port) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        return True
    except Exception as e:
        print(f"فشل إرسال البريد: {e}")
        return False
