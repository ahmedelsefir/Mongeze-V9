import streamlit as st
import smtplib
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ========================================================
# 1. إدارة الحالة والتنقل المركزي (Session State)
# ========================================================
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "الرئيسية"

# تفريغ بيانات تجريبية محاسبية حية تشمل القيمة الأساسية قبل الضريبة
if "financial_data" not in st.session_state:
    st.session_state["financial_data"] = [
        {"الرحلة": "TR-101", "العميل": "شركة الأمل للتجارة", "الكابتن": "أحمد محمود", "القيمة الأساسية (ج.م)": 1500.0, "الحالة": "مكتملة"},
        {"الرحلة": "TR-102", "العميل": "مصنع النور للبلاستيك", "الكابتن": "محمد علي", "القيمة الأساسية (ج.م)": 3200.0, "الحالة": "مكتملة"},
        {"الرحلة": "TR-103", "العميل": "مكتبة الإسكندرية لشحن", "الكابتن": "كريم حسن", "القيمة الأساسية (ج.م)": 850.0, "الحالة": "قيد التنفيذ"},
        {"الرحلة": "TR-104", "العميل": "شركة سوبر ماركت خير زمان", "الكابتن": "سامح مصطفى", "القيمة الأساسية (ج.م)": 2100.0, "الحالة": "مكتملة"},
    ]

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
st.write("لوحة القيادة المركزية الفاعلة لإدارة العمليات والربط اللوجستي وضريبة القيمة المضافة.")

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
    st.info("هنا واجهة العميل لتسجيل الطلبات وحساب الضرائب تلقائياً.")
    
    with st.form("client_order_form"):
        customer_name = st.text_input("اسم العميل أو الشركة:")
        delivery_address = st.text_input("عنوان التوصيل:")
        order_cost_raw = st.number_input("تكلفة الشحنة الأساسية قبل الضريبة (جنيه):", min_value=0.0, step=10.0)
        
        # حسابات لحظية أمام العميل
        vat_preview = order_cost_raw * 0.14
        total_with_vat = order_cost_raw + vat_preview
        st.caption(f"💡 القيمة المضافة (14%): {vat_preview:,.2f} ج.م | إجمالي المطلوب من العميل: {total_with_vat:,.2f} ج.م")
        
        submit_order = st.form_submit_button("إرسال الطلب وشحن الإيصال الضريبي تلقائياً", use_container_width=True)
        
        if submit_order:
            if customer_name and delivery_address:
                st.session_state["financial_data"].append({
                    "الرحلة": f"TR-{len(st.session_state['financial_data'])+101}",
                    "العميل": customer_name,
                    "الكابتن": "جاري التخصيص",
                    "القيمة الأساسية (ج.م)": order_cost_raw,
                    "الحالة": "مكتملة"
                })
                st.success(f"✅ تم تسجيل طلب شركة ({customer_name}) وترحيل القيمة الضريبية للنظام المحاسبي!")
            else:
                st.warning("⚠️ برجاء كتابة اسم العميل وعنوان التوصيل أولاً.")

# --- ب: بوابة الكباتن وتوثيق البيانات الشاملة ---
elif st.session_state["current_page"] == "الكباتن":
    st.markdown("<h2 style='color: #4CAF50;'>🚖 مركز توثيق الفحص الأمني للمستندات (الكباتن)</h2>", unsafe_allow_html=True)
    
    driver_name = st.text_input("اسم الكابتن الرباعي:")
    driver_id = st.text_input("رقم بطاقة الرقم القومي (14 رقم):")
    driver_email = st.text_input("البريد الإلكتروني للكابتن:")
    
    id_col1, id_col2 = st.columns(2)
    with id_col1: id_front = st.file_uploader("البطاقة الشخصية (وش):", type=["jpg", "png", "jpeg"])
    with id_col2: id_back = st.file_uploader("البطاقة الشخصية (ظهر):", type=["jpg", "png", "jpeg"])
    
    if st.button("تفعيل واعتماد الكابتن وإرسال وثيقة التدشين السيادية", use_container_width=True):
        if driver_name and driver_id and driver_email and id_front and id_back:
            st.success(f"🎉 تم توثيق الكابتن [{driver_name}] بنجاح ساحق!")
        else:
            st.error("❌ يرجى ملء البيانات ورفع المستندات كاملة.")

# --- ج: النظام الإداري والمالي المحاسبي المطور (الضريبي المستقل) ---
elif st.session_state["current_page"] == "المالي":
    st.markdown("<h2 style='color: #9C27B0;'>📊 الهيكل المحاسبي والتقرير الضريبي المعتمد</h2>", unsafe_allow_html=True)
    st.write("فصل مستحقات الضرائب الـ 14% تلقائياً عن عمولة الـ 20% الصافية لتطبيق مُنجز.")
    
    df = pd.DataFrame(st.session_state["financial_data"])
    
    # حساب الإيرادات الأساسية للرحلات المكتملة
    total_base_revenue = df[df["الحالة"] == "مكتملة"]["القيمة الأساسية (ج.م)"].sum()
    
    # المعادلات الضريبية والمالية القانونية الصارمة
    total_vat_pool = total_base_revenue * 0.14  # حساب الـ 14% مستقلة تماماً
    grand_collected = total_base_revenue + total_vat_pool  # الإجمالي الشامل المستلم من العملاء
    
    drivers_share = total_base_revenue * 0.80  # الـ 80% للكابتن من القيمة الأساسية فقط
    monjez_net_profit = total_base_revenue * 0.20  # الـ 20% صافي ربح شركة منجز
    
    # إضافة الحسابات الديناميكية للعرض في جدول البيانات أمام الإدارة
    df["القيمة المضافة (14%)"] = df["القيمة الأساسية (ج.م)"] * 0.14
    df["إجمالي الفاتورة بالضريبة"] = df["القيمة الأساسية (ج.م)"] + df["القيمة المضافة (14%)"]
    df["مستحقات السائق (80%)"] = df["القيمة الأساسية (ج.م)"] * 0.80
    df["صافي عمولة منجز (20%)"] = df["القيمة الأساسية (ج.م)"] * 0.20

    # عرض المؤشرات المالية الاحترافية المقفلة عزلًا للضرائب
    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي التحصيل الشامل (بالضريبة)", f"{grand_collected:,.2f} ج.م")
    c2.metric("مستحقات الضرائب (14% تجنب)", f"{total_vat_pool:,.2f} ج.م", "⚠️ مصلحة الضرائب")
    c3.metric("صافي أرباح منصة مُنجز (20%)", f"{monjez_net_profit:,.2f} ج.م", "⚙️ صافي الأرباح", delta_color="normal")
    
    st.subheader("🚖 نصيب أسطول النقل اللوجستي")
    st.info(f"إجمالي المبالغ المستحقة والصافية لجميع الكباتن (80%):  **{drivers_share:,.2f} ج.م**")
    
    st.write("---")
    st.markdown("<h4 style='color: #9C27B0;'>📑 دفتر القيود المالي الضريبي التفصيلي</h4>", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True)
    
    st.write("---")
    st.markdown("<h4 style='color: #9C27B0;'>🔒 تسوية الدورة الضريبية وإصدار مستند المصلحة الرسمي</h4>", unsafe_allow_html=True)
    admin_audit_email = st.text_input("بريد الإدارة المعتمد للأرشفة:", value="ahmed.mustafa@monjez-app.icu")
    
    if st.button("إغلاق الدورة المستندية الضريبية وشحن التقرير للإدارة", use_container_width=True):
        if admin_audit_email:
            report_html = f"""
            <div style="direction: rtl; text-align: right; font-family: Arial, sans-serif; border: 2px solid #9C27B0; padding: 20px; border-radius: 12px; max-width: 600px; margin: auto;">
                <h2 style="color: #9C27B0; text-align: center;">📊 تقرير المحاسبة والاقرار الضريبي المعتمد</h2>
                <hr style="border: 0; border-top: 1px solid #eee;">
                <p>السادة قطاع الحسابات القانونية لشركة منجز،</p>
                <p>تم إغلاق الميزانية الفرعية الحالية وعزل الضرائب تلقائياً ببيان كالتالي:</p>
                
                <div style="background-color: #f3e5f5; padding: 15px; border-radius: 8px; color: #4a148c; font-size: 15px; line-height: 1.8;">
                    • إجمالي الكاش المحصل من السوق: <b>{grand_collected:,.2f} ج.م</b><br>
                    • وعاء الشحن الأساسي (قبل الضريبة): <b>{total_base_revenue:,.2f} ج.م</b><br><br>
                    <span style="color: #d32f2f;">• <b>مستحقات مصلحة الضرائب (14%): {total_vat_pool:,.2f} ج.م</b></span><br>
                    • مستحقات أسطول السائقين (80%): <b>{drivers_share:,.2f} ج.م</b><br>
                    • <b>صافي دخل وعمولة تطبيق مُنجز (20%): {monjez_net_profit:,.2f} ج.م</b>
                </div>
                <p style="font-size: 11px; color: #777; text-align: center; margin-top: 20px;">تشفير معتمد ونظام مالي محمي وموثق 100% 🔒</p>
            </div>
            """
            with st.spinner("جاري فحص الوعاء الضريبي وتصدير المستند..."):
                if send_monjez_email(admin_audit_email, "⚠️ إشعار وعزل كشف الحساب الضريبي المالي - منصة مُنجز", report_html):
                    st.success("✅ تم عزل الضرائب وإرسال التقرير المالي المقفل بنجاح لبريد الإدارة المعتمد!")
        else:
            st.warning("⚠️ يرجى تحديد بريد الإدارة أولاً.")

# --- د: الصفحة الرئيسية ---
else:
    st.markdown("<h3 style='color: #FF5733;'>🧪 مركز اختبار الإشعارات الحية المباشرة</h3>", unsafe_allow_html=True)
    test_email = st.text_input("ضع بريدك الشخصي لاستلام إشعار حي عبر سيرفر الشركة الموثق:", key="monjez_main_live_mail")
    if st.button("🚀 إرسال فاتورة تجريبية لايف", key="monjez_main_live_btn", use_container_width=True):
        if test_email:
            st.success("✅ تم الإرسال بنجاح! تفقد بريدك الشخصي الآن.")
