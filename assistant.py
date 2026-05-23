import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ========================================================
# 1. إدارة الحالة والتنقل المركزي (Session State)
# ========================================================
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "الرئيسية"

# دالة لتغيير الصفحة
def navigate_to(page_name):
    st.session_state["current_page"] = page_name

# ========================================================
# 2. محرك إرسال الفواتير السيادي المباشر (Zoho SMTP SSL)
# ========================================================
def send_monjez_email(receiver_email, subject, body_html):
    smtp_server = "smtp.zoho.com"
    port = 465
    sender_email = "ahmed.mustafa@monjez-app.icu"
    app_password = "42s1kTKByngN"

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
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
# 3. شريط التنقل العلوي والأزرار الرئيسية
# ========================================================
st.title("🤖 مساعد منصة مُنجز الذكي")
st.write("مرحباً بك في لوحة القيادة المركزية لإدارة عمليات التشغيل اللوجستية.")

col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🏠 الصفحة الرئيسية", use_container_width=True):
        navigate_to("الرئيسية")
with col2:
    if st.button("🛒 بوابة العملاء", use_container_width=True):
        navigate_to("العملاء")
with col3:
    if st.button("🚖 بوابة الكباتن", use_container_width=True):
        navigate_to("الكباتن")
with col4:
    if st.button("📊 الإدارة والتقارير", use_container_width=True):
        navigate_to("التقارير")

st.write("---")

# ========================================================
# 4. توجيه عرض الصفحات بناءً على اختيارك
# ========================================================

# --- أ: صفحة بوابة العملاء ---
if st.session_state["current_page"] == "العملاء":
    st.markdown("<h2 style='color: #1E88E5;'>🛒 لوحة تحكم بوابة العملاء</h2>", unsafe_allow_html=True)
    st.write("هنا سيقوم العميل بطلب الشحنات، تتبع التوصيل، وإدارة الاشتراكات.")
    # (هنا سنضع كود المحاسبة والطلبات الخاص بالعملاء لاحقاً بدقة)

# --- ب: صفحة بوابة الكباتن ---
elif st.session_state["current_page"] == "الكباتن":
    st.markdown("<h2 style='color: #4CAF50;'>🚖 لوحة تحكم بوابة الكباتن (السائقين)</h2>", unsafe_allow_html=True)
    st.write("هنا يستطيع السائق استقبال الطلبات الحية، وتحديث حالة الشحنة، واستعراض محفظته الماليّة.")

# --- ج: صفحة التقارير والإدارة ---
elif st.session_state["current_page"] == "التقارير":
    st.markdown("<h2 style='color: #9C27B0;'>📊 النظام المحاسبي والتقارير السيادية</h2>", unsafe_allow_html=True)
    st.write("التقرير المالي العام، حساب صافي الأرباح، وفصل مستحقات الكباتن.")

# --- د: الصفحة الرئيسية (مركز الاختبار الحالي) ---
else:
    st.markdown("<h3 style='color: #FF5733;'>🧪 مركز اختبار فواتير مُنجز السيادية</h3>", unsafe_allow_html=True)
    test_email = st.text_input("ضع بريدك الشخصي (Gmail) لاستقبل الفاتورة الحية:", key="monjez_direct_live_mail")

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
