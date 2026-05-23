# ========================================================
# 🧪 محرك فواتير مُنجز ومركز الاختبار لايف (يُوضع أسفل assistant.py)
# ========================================================
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_monjez_email(receiver_email, subject, body_html):
    smtp_server = "smtp.zoho.com"
    port = 465
    try:
        # جلب البيانات من الخزنة السرية
        sender_email = st.secrets["zoho"]["sender_email"]
        app_password = st.secrets["zoho"]["app_password"]
    except Exception:
        st.error("❌ خطأ: تأكد من كتابة [zoho] والبيانات بشكل صحيح في الـ Secrets!")
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
        print(f"فشل الإرسال: {e}")
        return False

# تصميم واجهة الزرار في أسفل الشاشة
st.write("---")
st.subheader("🧪 مركز اختبار فواتير مُنجز")

test_email = st.text_input("اكتب إيميلك الشخصي (الجيميل) لتجربة الاستقبال:", key="assistant_test_mail")

if st.button("🚀 إرسال فاتورة تجريبية لايف", key="assistant_test_btn"):
    if test_email:
        sample_html = """
        <div style="direction: rtl; text-align: right; font-family: Arial; border: 2px solid #FF5733; padding: 20px; border-radius: 10px;">
            <h2 style="color: #FF5733;">منصة مُنجز السيادية 🚀</h2>
            <p>مرحباً يا هندسة! هذا الإيميل يؤكد اتصال التطبيق بنجاح بمحرك زوهو عبر ملف assistant.py</p>
            <hr>
            <p><b>حالة الاتصال:</b> ممتازة 100% ✅</p>
        </div>
        """
        with st.spinner("جاري إطلاق الفاتورة عبر سيرفر زوهو..."):
            success = send_monjez_email(test_email, "تأكيد اتصال محرك منجز 🚀", sample_html)
            if success:
                st.success("✅ تم الإرسال بنجاح! تفقد بريدك الآن.")
            else:
                st.error("❌ فشل الإرسال. راجع كود الـ Secrets.")
    else:
        st.warning("فضلاً اكتب الإيميل أولاً.")
