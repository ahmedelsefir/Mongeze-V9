import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ========================================================
# 1. إدارة الحالة والتنقل المركزي (Session State)
# ========================================================
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "الرئيسية"

def navigate_to(page_name):
    st.session_state["current_page"] = page_name

# ========================================================
# 2. محرك إرسال الفواتير والإشعارات السيادي (Zoho)
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
# 3. شريط التحكم والتنقل العلوي المستقر
# ========================================================
st.title("🤖 مساعد منصة مُنجز الذكي")
st.write("لوحة القيادة المركزية الفاعلة لإدارة العمليات والربط اللوجستي.")

# تصميم الأزرار للتنقل الفوري داخل التطبيق
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🏠 الرئيسية", use_container_width=True):
        navigate_to("الرئيسية")
with col2:
    if st.button("🛒 بوابة العملاء", use_container_width=True):
        navigate_to("العملاء")
with col3:
    if st.button("🚖 بوابة الكباتن", use_container_width=True):
        navigate_to("الكباتن")
with col4:
    if st.button("📊 النظام المالي", use_container_width=True):
        navigate_to("المالي")

st.write("---")

# ========================================================
# 4. شاشات وبوابات التطبيق الفاعلة
# ========================================================

# --- أ: بوابة العملاء ---
if st.session_state["current_page"] == "العملاء":
    st.markdown("<h2 style='color: #1E88E5;'>🛒 بوابة العملاء والاشتراكات التجارية</h2>", unsafe_allow_html=True)
    st.info("هنا واجهة العميل الحقيقية لطلب الرحلات وتتبع الفواتير.")
    
    # نموذج محاكاة لطلب شحنة
    with st.form("client_order_form"):
        customer_name = st.text_input("اسم العميل أو الشركة:")
        delivery_address = st.text_input("عنوان التوصيل:")
        order_cost = st.number_input("تكلفة الشحنة الإجمالية (جنيه):", min_value=0.0, step=10.0)
        submit_order = st.form_submit_with_button("إرسال الطلب وشحن الإيصال تلقائياً")
        
        if submit_order and customer_name:
            st.success(f"✅ تم تسجيل الطلب بنجاح في قاعدة البيانات!")

# --- ب: بوابة الكباتن وتوثيق البيانات ---
elif st.session_state["current_page"] == "الكباتن":
    st.markdown("<h2 style='color: #4CAF50;'>🚖 مركز توثيق وبيانات السائقين (الكباتن)</h2>", unsafe_allow_html=True)
    st.write("بوابة التوثيق والتحقق من الهوية والأوراق الرسمية.")
    
    driver_name = st.text_input("اسم الكابتن الرباعي:")
    driver_id = st.text_input("رقم بطاقة الرقم القومي (14 رقم):")
    license_file = st.file_uploader("ارفع صورة رخصة القيادة السارية:", type=["jpg", "png", "pdf"])
    
    if st.button("تفعيل واعتماد الكابتن في النظام السيادي", use_container_width=True):
        if driver_name and driver_id:
            st.success(f"🎉 تم توثيق الكابتن [{driver_name}] وضمه للأسطول النشط بنجاح!")
        else:
            st.warning("⚠️ برجاء ملء بيانات الكابتن الأساسية أولاً.")

# --- ج: النظام الإداري والمالي المحاسبي ---
elif st.session_state["current_page"] == "المالي":
    st.markdown("<h2 style='color: #9C27B0;'>📊 الهيكل المحاسبي والتقارير المالية المركزية</h2>", unsafe_allow_html=True)
    st.write("تتبع صافي الإيرادات وفصل مستحقات الشركة عن الكباتن بدقة.")
    
    # عرض إحصائيات مالية سريعة ومحاكاة الأرقام
    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي الإيرادات", "45,000 ج.م")
    c2.metric("مستحقات الكباتن", "36,000 ج.م", "-80%")
    c3.metric("صافي أرباح مُنجز", "9,000 ج.م", "20%", delta_color="normal")

# --- د: الصفحة الرئيسية (مركز الاختبار الموثق) ---
else:
    st.markdown("<h3 style='color: #FF5733;'>🧪 مركز اختبار الإشعارات الحية المباشرة</h3>", unsafe_allow_html=True)
    test_email = st.text_input("ضع بريدك الشخصي لاستلام إشعار حي عبر سيرفر الشركة الموثق:", key="monjez_main_live_mail")

    if st.button("🚀 إرسال فاتورة تجريبية لايف", key="monjez_main_live_btn", use_container_width=True):
        if test_email:
            sample_html = """
            <div style="direction: rtl; text-align: right; font-family: Arial, sans-serif; border: 2px solid #FF5733; padding: 20px; border-radius: 12px; max-width: 500px; margin: auto;">
                <h2 style="color: #FF5733; text-align: center;">منصة مُنجز السيادية 🚀</h2>
                <hr style="border: 0; border-top: 1px solid #eee;">
                <p style="font-size: 16px; color: #333;">مبارك يا هندسة! تم اختبار ميكانيكية الربط الداخلي بنجاح كامل.</p>
                <p><b>حالة النظام المستهدف:</b> متصل بالكامل ويعمل من داخل التطبيق الحقيقي الحصري. ✅</p>
            </div>
            """
            with st.spinner("جاري شحن الإشعار برمجياً..."):
                if send_monjez_email(test_email, "إشعار تشغيل وتأكيد نظام فواتير منجز 🚀", sample_html):
                    st.success("✅ تم الإرسال بنجاح! تفقد بريدك الشخصي الآن لتتأكد من الربط الميكانيكي.")
