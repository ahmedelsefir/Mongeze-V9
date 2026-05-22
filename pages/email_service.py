import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_monjez_email(receiver_email, subject, body_html):
    """
    دالة سيادية لإرسال إيميلات وفواتير منصة منجز للعملاء والسائقين بشكل آمن
    """
    smtp_server = "smtp.zoho.com"
    port = 465  # منفذ SSL الآمن لـ Zoho
    
    # جلب البيانات الحساسة من خزنة Secrets بأمان لمنع التسريب
    try:
        sender_email = st.secrets["zoho"]["sender_email"]
        app_password = st.secrets["zoho"]["app_password"]
    except Exception:
        st.error("❌ خطأ: لم يتم العثور على بيانات زوهو السرية في إعدادات Secrets!")
        return False

    # إنشاء هيكل الرسالة وتحديد الترميز يدعم اللغة العربية والـ HTML
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"منصة مُنجز السيادية <{sender_email}>"
    message["To"] = receiver_email

    # ربط نص الـ HTML بالرسالة
    part_html = MIMEText(body_html, "html", "utf-8")
    message.attach(part_html)

    try:
        # الاتصال المشفر وسحب وإرسال الفاتورة فوراً
        with smtplib.SMTP_SSL(smtp_server, port) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        return True
    except Exception as e:
        print(f"فشل إرسال البريد: {e}")
        return False
