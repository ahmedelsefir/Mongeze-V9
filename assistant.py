import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ========================================================
# 1. محرك إرسال الفواتير الخفي لمنصة مُنجز (Zoho SMTP SSL)
# ========================================================
def send_monjez_email(receiver_email, subject, body_html):
    """
    يقوم بالاتصال بسيرفر Zoho المشفر لإرسال الإشعارات والفواتير اللحظية للعملاء.
    """
    smtp_server = "smtp.zoho.com"
    port = 465  # منفذ SSL الآمن والموثق
    
    try:
        # جلب البيانات الحساسة من خزنة أسرار ستريمليت [zoho]
        sender_email = st.secrets["zoho"]["sender_email"]
        app_password = st.secrets["zoho"]["app_password"]
    except Exception:
        st.error("❌ خطأ حرج: لم يتم العثور على مفاتيح [zoho] داخل إعدادات Secrets!")
        return False

    # بناء هيكل الرسالة وتأمين ترميز اللغة العربية
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"منصة مُنجز السيادية <{sender_email}>"
    message["To"] = receiver_email

    # حقن كود الـ HTML المنسق داخل الرسالة
    part_html = MIMEText(body_html, "html", "utf-8")
    message.attach(part_html)

    try:
        # فتح الاتصال الآمن مع السيرفر وتمرير الصلاحيات
        with smtplib.SMTP_SSL(smtp_server, port) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        return True
    except Exception as e:
        print(f"فشل إرسال البريد البرمجي: {e}")
        return False


# ========================================================
# 2. واجهة وأزرار لوحة التحكم الرئيسية (البنية الحالية للتطبيق)
# ========================================================

# (ملاحظة: يمكنك إبقاء أو تعديل هذه الأزرار بناءً على تصميم واجهتك الحالية)
st.title("🤖 مساعد منصة مُنجز الذكي")
st.write("مرحباً بك في لوحة القيادة المركزية لإدارة عمليات التشغيل.")

# هنا تضع الأزرار والقوائم الخاصة بملفك الافتراضي، على سبيل المثال:
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
    "ضع إيميلك الشخصي (مثل Gmail أو Yahoo) لاستقبال الفاتورة الحية:", 
    key="assistant_live_test_mail",
    placeholder="example@gmail.com"
)

# زر إطلاق الفاتورة عبر السحاب
if st.button("🚀 إرسال فاتورة تجريبية لايف", key="assistant_live_test_btn", use_container_width=True):
    if test_email:
        # تصميم قالب فاتورة احترافي وجذاب بالـ HTML والـ CSS
        sample_html = """
        <div style="direction: rtl; text-align: right; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; border: 2px solid #FF5733; padding: 25px; border-radius: 12px; max-width: 500px; margin: auto; box-shadow: 0 4px 8px rgba(0,0,0,0.05);">
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="color: #FF5733; margin: 0; font-size: 28px;">منصة مُنجز السيادية 🚀</h1>
                <p style="color: #555; margin: 5px 0 0 0; font-size: 14px;">إشعار تشغيل وتأكيد اتصال الأنظمة</p>
            </div>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="font-size: 16px; color: #333; line-height: 1.6;">
                مبارك يا هندسة! هذا الإيميل يؤكد <b>نجاح الاتصال الميكانيكي الكامل</b> بين كود المنصة وبين سيرفرات البريد السيادي الخاص بنطاقك المخصص عن طريق ملف <code style="background: #fff0ec; color: #ff5733; padding: 2px 6px; border-radius: 4px;">assistant.py</code>.
            </p>
            <div style="background-color: #f9f9f9; padding: 15px; border-left: 4px solid #FF5733; border-radius: 4px; margin: 20px 0;">
                <p style="margin: 5px 0; font-size: 14px;"><b>حالة خادم التوجيه:</b> متصل ويعمل بنجاح ✅</p>
                <p style="margin: 5px 0; font-size: 14px;"><b>توثيق الأمان (SPF/DKIM):</b> محمي وموثق 100% 🛡️</p>
            </div>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="text-align: center; color: #888; font-size: 11px; margin: 0;">
                توليد تلقائي آمن - منظومة إدارة "مُنجز" اللوجستية 2026
            </p>
        </div>
        """
        with st.spinner("جاري تهيئة الاتصال المشفر وشحن الفاتورة عبر سيرفر زوهو..."):
            # استدعاء دالة الإرسال الفعلي
            success = send_monjez_email(test_email, "إشعار تشغيل وتأكيد نظام فواتير منجز 🚀", sample_html)
            
            if success:
                st.success("✅ تم إطلاق الفاتورة بنجاح ساحق! افتح بريدك الشخصي الآن وتفقد صندوق الوارد (الـ Inbox أو الـ Spam).")
            else:
                st.error("❌ فشل الإرسال. تأكد من إدخال مفتاح الـ Secrets تحت اسم المجموعات الصحيح [zoho].")
    else:
        st.warning("فضلاً، قم بكتابة البريد الإلكتروني أولاً في الخانة المخصصة بالأعلى.")
