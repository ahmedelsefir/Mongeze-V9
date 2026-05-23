import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ========================================================
# 1. محرك إرسال الفواتير السيادي (Zoho SMTP SSL) - نسخة الإصلاح الشامل
# ========================================================
def send_monjez_email(receiver_email, subject, body_html):
    smtp_server = "smtp.zoho.com"
    port = 465  # منفذ SSL الآمن والموثق لـ Zoho
    
    try:
        # 🛡️ نظام فحص مرن لقراءة البيانات بأي اسم مكتوب في الـ Secrets ومنع الأخطاء الحمراء
        if "zoho_user" in st.secrets["zoho"]:
            sender_email = st.secrets["zoho"]["zoho_user"]
            raw_password = st.secrets["zoho"]["zoho_password"]
        else:
            sender_email = st.secrets["zoho"]["sender_email"]
            raw_password = st.secrets["zoho"]["app_password"]
            
        # ✨ التعديل السحري: حذف أي مسافات خفية بين الحروف ناتجة عن النسخ من لوحة زوهو
        app_password = str(raw_password).replace(" ", "").strip()
        
    except Exception as e:
        st.error(f"❌ خطأ حرج في الـ Secrets: تأكد من كتابة صندوق [zoho] بشكل صحيح! التفاصيل: {e}")
        return False

    # بناء هيكل الرسالة وتأمين دعم اللغة العربية 100%
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"منصة مُنجز السيادية <{sender_email}>"
    message["To"] = receiver_email

    # ربط كود الـ HTML المنسق
    part_html = MIMEText(body_html, "html", "utf-8")
    message.attach(part_html)

    try:
        # فتح الاتصال المشفر مع السيرفر وشحن الفاتورة فوراً
        with smtplib.SMTP_SSL(smtp_server, port) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        return True
    except Exception as e:
        st.error(f"❌ فشل السيرفر في التوثيق: الـ App Password مرفوض من Zoho أو الإيميل غير مفعل SMTP. السبب: {e}")
        return False


# ========================================================
# 2. واجهة وأزرار لوحة التحكم الرئيسية للتطبيق
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
# 3. مركز اختبار الفواتير اللحظية لايف (يظهر أسفل الشاشة)
# ========================================================
st.write("---")
st.markdown("<h3 style='color: #FF5733;'>🧪 مركز اختبار فواتير مُنجز السيادية</h3>", unsafe_allow_html=True)
st.write("استخدم هذه الخانة لاختبار كفاءة ربط النطاق وإرسال الفواتير عبر بريدك الرسمي.")

# خانة إدخال بريد العميل التجريبي
test_email = st.text_input(
    "ضع إيميلك الشخصي (مثل Gmail) لاستقبال الفاتورة الحية:", 
    key="assistant_live_final_mail",
    placeholder="example@gmail.com"
)

# زر إطلاق الفاتورة عبر السحاب
if st.button("🚀 إرسال فاتورة تجريبية لايف", key="assistant_live_final_btn", use_container_width=True):
    if test_email:
        # تصميم قالب فاتورة احترافي وجذاب بالـ HTML
        sample_html = """
        <div style="direction: rtl; text-align: right; font-family: Arial, sans-serif; border: 2px solid #FF5733; padding: 25px; border-radius: 12px; max-width: 500px; margin: auto;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="color: #FF5733; margin: 0; font-size: 26px;">منصة مُنجز السيادية 🚀</h1>
                <p style="color: #555; margin: 5px 0 0 0; font-size: 14px;">تأكيد نظام ربط المراسلات اللوجستية</p>
            </div>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="font-size: 16px; color: #333; line-height: 1.6;">
                مبارك يا هندسة! هذا الإيميل يؤكد <b>نجاح الاتصال الميكانيكي بالكامل</b>. السيرفر استقبل كود الباسورد ونظفه، وتمت عملية الإرسال بنجاح استثنائي!
            </p>
            <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #FF5733; border-radius: 4px; margin: 20px 0;">
                <p style="margin: 5px 0; font-size: 14px;"><b>حالة الاتصال:</b> متصل ويعمل بنجاح ✅</p>
                <p style="margin: 5px 0; font-size: 14px;"><b>الملف المسؤول:</b> assistant.py 📑</p>
            </div>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="text-align: center; color: #888; font-size: 11px; margin: 0;">
                توليد تلقائي آمن - منظومة إدارة "مُنجز" اللوجستية 2026
            </p>
        </div>
        """
        with st.spinner("جاري تهيئة الاتصال الآمن وشحن الفاتورة عبر سيرفر Zoho..."):
            success = send_monjez_email(test_email, "إشعار تشغيل وتأكيد نظام فواتير منجز 🚀", sample_html)
            
            if success:
                st.success("✅ تم إطلاق الفاتورة بنجاح ساحق! افتح بريدك الشخصي الآن وتفقد صندوق الوارد أو الـ Spam.")
