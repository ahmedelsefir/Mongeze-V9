import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)

def send_monjez_email(receiver_email, subject, body_html):
    """
    محرك الإرسال الخفي لمنصة مُنجز السيادية - يرسل إيميلات وفواتير للعملاء والكباتن
    
    Args:
        receiver_email: Email address of the recipient
        subject: Email subject line
        body_html: HTML body content
    
    Returns:
        True if email sent successfully, False otherwise
    """
    smtp_server = "smtp.zoho.com"
    port = 465  # منفذ SSL المشفر لـ Zoho

    # جلب البيانات الحساسة من خزنة Secrets لمنع تسريب الباسورد على GitHub
    try:
        sender_email = st.secrets["zoho"]["sender_email"]
        app_password = st.secrets["zoho"]["app_password"]
    except KeyError as e:
        logger.error(f"Missing Zoho secret key: {e}")
        st.error("❌ خطأ حرج: لم يتم العثور على مفاتيح زوهو السرية في إعدادات Secrets الخاصة بـ Streamlit!")
        return False
    except Exception as e:
        logger.error(f"Unexpected error reading Zoho secrets: {e}")
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
        logger.info(f"Email sent successfully to {receiver_email}: {subject}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP authentication failed for Zoho: {e}")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"Recipient refused ({receiver_email}): {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending to {receiver_email}: {e}")
        return False
    except OSError as e:
        logger.error(f"Network error connecting to {smtp_server}:{port}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email to {receiver_email}: {e}")
        return False
