import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ========================================================
# 1. محرك إرسال الفواتير السيادي المباشر (Zoho SMTP SSL)
# ========================================================
def send_monjez_email(receiver_email, subject, body_html):
    smtp_server = "smtp.zoho.com"
    port = 465
    
    # 🛡️ تثبيت البيانات الصافية مباشرة داخل الكود لقطع الشك باليقين
    sender_email = "ahmed.mustafa@monjez-app.icu"
    app_password = "42s1kTKByngN"  # الرمز الأحدث والمفعّل من لوحة زوهو

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    
    # ✨ التعديل السحري والأخير: جعل المرسل هو الإيميل الصافي لتخطي حظر الـ Relay تماماً
    message["From"] = sender_email
    message["To"] = receiver_email
    
    part_html = MIMEText(body_html, "html", "utf-8")
    message.attach(part_html)

    try:
        with smtplib.SMTP_SSL(smtp_server, port) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        return True
    except Exception as e:
        st.error(f"❌ استجابة سيرفر Zoho: {e}")
        return False


# ========================================================
# 2. واجهة التطبيق التشغيلية المركزية
# ========================================================
st.title("🤖 مساعد منصة مُنجز الذكي")
st.write("مرحباً بك في لوحة القيادة المركزية لإدارة عمليات التشغيل اللوجستية.")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🛒 بوابة العملاء", use_container_width=True):
        st.info("جاري الانتقال لبوابة العملاء...")
with col2:
    if st.button("🚖 بوابة الكباتن", use_container_width=True):
        st.info("جاري الانتقال لبوابة السائقين...")
with col3:
    if st.button("📊 الإدارة والتقارير", use_container_width=True):
        st.info("جاري فتح التقارير المالية...")


# ========================================================
# 3. مركز اختبار الفواتير اللحظية لايف
# ========================================================
st.write("---")
st.markdown("<h3 style='color: #FF5733;'>🧪 مركز اختبار فواتير مُنجز السيادية</h3>", unsafe_allow_html=True)

test_email = st.text_input("ضع بريدك الشخصي (Gmail) لاستقبال الفاتورة الحية:", key="monjez_direct_live_mail")

if st.button("🚀 إرسال فاتورة تجريبية لايف", key="monjez_direct_live_btn", use_container_width=True):
    if test_email:
        sample_html = """
        <div style="direction: rtl; text-align: right; font-family: Arial, sans-serif; border: 2px solid #FF5733; padding: 20px; border-radius: 12px; max-width: 500px; margin: auto;">
            <h2 style="color: #FF5733; text-align: center;">منصة مُنجز السيادية 🚀</h2>
            <hr style="border: 0; border-top: 1px solid #eee;">
            <p style="font-size: 16px; color: #333;">مبارك يا هندسة! تم الربط الميكانيكي المباشر بنجاح واكتمل تشغيل المنظومة بنسبة 100%.</p>
            <p><b>حالة النظام:</b> متصل ويعمل لايف عبر السحاب وموثق بالكامل! ✅</p>
        </div>
        """
        with st.spinner("جاري شحن وإطلاق الفاتورة السيادية مباشرة..."):
            if send_monjez_email(test_email, "إشعار تشغيل وتأكيد نظام فواتير منجز 🚀", sample_html):
                st.success("✅ تم الإرسال بنجاح ساحق ومباشر! تفقد بريدك الشخصي الآن واحتفل بالنجاح.")
