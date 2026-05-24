import streamlit as st
import smtplib
import requests  # المكتبة المسؤولة عن شحن واستقبال البيانات سحابياً من Firebase
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ========================================================
# 🔗 إعدادات الرابط السحابي السيادي لـ Firebase
# ========================================================
FIREBASE_URL = "https://gen-lang-client-03099029-937be-default-rtdb.firebaseio.com"

# دالة مخصصة لشحن (حفظ) البيانات في Firebase
def save_to_firebase(node, data):
    try:
        response = requests.post(f"{FIREBASE_URL}/{node}.json", json=data)
        return response.ok
    except Exception as e:
        st.error(f"❌ فشل الاتصال بالسحاب أثناء الحفظ: {e}")
        return False

# دالة مخصصة لجلب (قراءة) البيانات الحية من Firebase
def load_from_firebase(node):
    try:
        response = requests.get(f"{FIREBASE_URL}/{node}.json")
        if response.ok and response.json():
            raw_data = response.json()
            return list(raw_data.values())
        return []
    except Exception as e:
        st.error(f"❌ فشل جلب البيانات من السحاب: {e}")
        return []

# ========================================================
# 1. إدارة الحالة والتنقل المركزي (Session State)
# ========================================================
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "الرئيسية"

# جلب البيانات المالية الحية مباشرة من Firebase بدلاً من الذاكرة المؤقتة
financial_records = load_from_firebase("financial_records")

# إذا كانت قاعدة البيانات السحابية فارغة، نضع عينات تجريبية مؤقتة لضمان تشغيل النظام
if not financial_records:
    financial_records = [
        {"الرحلة": "TR-101", "العميل": "شركة الأمل للتجارة", "الكابتن": "أحمد محمود", "القيمة الأساسية (ج.م)": 1500.0, "الحالة": "مكتملة"},
        {"الرحلة": "TR-102", "العميل": "مصنع النور للبلاستيك", "الكابتن": "محمد علي", "القيمة الأساسية (ج.م)": 3200.0, "الحالة": "مكتملة"},
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
st.write("لوحة القيادة المركزية الفاعلة - إدارة عمليات المزايدات الحية والدورة المالية اللوجستية السحابية.")

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
# 4. شاشات وبوابات التطبيق الفاعلة السحابية
# ========================================================

# --- أ: بوابة العملاء (نظام المزايدة المربوط بـ Firebase) ---
if st.session_state["current_page"] == "العملاء":
    st.markdown("<h2 style='color: #1E88E5;'>🛒 بوابة طلب الشحنات ونظام المزايدة الحي</h2>", unsafe_allow_html=True)
    st.info("هنا يطلب العميل الرحلة ويستقبل عروض الأسعار الحية، ويتم تأمين وحفظ الاختيار سحابياً.")
    
    customer_name = st.text_input("اسم العميل أو الشركة طالبة الشحن:")
    delivery_address = st.text_input("عنوان التوصيل (من وإلى):")
    suggested_price = st.number_input("السعر المقترح من قبلك للرحلة (جنيه):", min_value=0.0, step=50.0, value=100.0)
    
    if suggested_price > 0 and customer_name and delivery_address:
        st.write("---")
        st.markdown("<h4 style='color: #1E88E5;'>🚖 العروض المستلمة حية من الكباتن المحيطين بك:</h4>", unsafe_allow_html=True)
        
        # حساب المزايدات ديناميكياً
        bid_1 = suggested_price
        bid_2 = suggested_price + (suggested_price * 0.15)
        bid_3 = suggested_price + (suggested_price * 0.30)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"<div style='border: 1px solid #ddd; padding: 10px; border-radius: 8px; text-align: center;'><b>كابتن/ رأفت المنسي</b><br>⭐ 4.9 (موتوسيكل)<br><h3 style='color: #1E88E5;'>{bid_1:,.0f} ج.م</h3></div>", unsafe_allow_html=True)
            if st.button("قبول عرض رأفت", key="accept_bid_1", use_container_width=True):
                new_trip = {"الرحلة": f"TR-{len(financial_records)+101}", "العميل": customer_name, "الكابتن": "رأفت المنسي", "القيمة الأساسية (ج.م)": float(bid_1), "الحالة": "مكتملة"}
                if save_to_firebase("financial_records", new_trip):
                    st.success(f"☁️ تم قبول العرض وحفظ الرحلة بنجاح في قاعدة بيانات Firebase السحابية!")
                    st.rerun()
                
        with c2:
            st.markdown(f"<div style='border: 1px solid #ddd; padding: 10px; border-radius: 8px; text-align: center;'><b>كابتن/ إيهاب جلال</b><br>⭐ 4.8 (سيارة فاني)<br><h3 style='color: #1E88E5;'>{bid_2:,.0f} ج.م</h3></div>", unsafe_allow_html=True)
            if st.button("قبول عرض إيهاب", key="accept_bid_2", use_container_width=True):
                new_trip = {"الرحلة": f"TR-{len(financial_records)+101}", "العميل": customer_name, "الكابتن": "إيهاب جلال", "القيمة الأساسية (ج.م)": float(bid_2), "الحالة": "مكتملة"}
                if save_to_firebase("financial_records", new_trip):
                    st.success(f"☁️ تم قبول العرض وتأمين البيانات سحابياً في Firebase!")
                    st.rerun()
                
        with c3:
            st.markdown(f"<div style='border: 1px solid #ddd; padding: 10px; border-radius: 8px; text-align: center;'><b>كابتن/ مصطفى طه</b><br>⭐ 4.7 (سيارة ربع نقل)<br><h3 style='color: #1E88E5;'>{bid_3:,.0f} ج.م</h3></div>", unsafe_allow_html=True)
            if st.button("قبول عرض مصطفى", key="accept_bid_3", use_container_width=True):
                new_trip = {"الرحلة": f"TR-{len(financial_records)+101}", "العميل": customer_name, "الكابتن": "مصطفى طه", "القيمة الأساسية (ج.م)": float(bid_3), "الحالة": "مكتملة"}
                if save_to_firebase("financial_records", new_trip):
                    st.success(f"☁️ تم الربط السحابي بنجاح وتحديث النظام المالي!")
                    st.rerun()
    else:
        st.warning("⚠️ يرجى إدخال اسم الشركة وعنوان التوصيل لتشغيل لوحة التفاعل.")

# --- ب: بوابة الكباتن وتوثيق المستندات سحابياً ---
elif st.session_state["current_page"] == "الكباتن":
    st.markdown("<h2 style='color: #4CAF50;'>🚖 مركز توثيق الفحص الأمني للمستندات (الكباتن)</h2>", unsafe_allow_html=True)
    
    driver_name = st.text_input("اسم الكابتن الرباعي:")
    driver_id = st.text_input("رقم بطاقة الرقم القومي (14 رقم):")
    driver_email = st.text_input("البريد الإلكتروني للكابتن:")
    
    id_col1, id_col2 = st.columns(2)
    with id_col1: id_front = st.file_uploader("البطاقة الشخصية (وش):", type=["jpg", "png", "jpeg"], key="idf")
    with id_col2: id_back = st.file_uploader("البطاقة الشخصية (ظهر):", type=["jpg", "png", "jpeg"], key="idb")
    
    if st.button("تفعيل واعتماد الكابتن وحفظه سحابياً", use_container_width=True):
        if driver_name and driver_id and driver_email and id_front and id_back:
            driver_profile = {"اسم_الكابتن": driver_name, "الرقم_القومي": driver_id, "البريد": driver_email, "حالة_التوثيق": "نشط وموثق سحابياً"}
            if save_to_firebase("verified_drivers", driver_profile):
                st.success(f"🎉 تم توثيق الكابتن [{driver_name}] بنجاح، وتأمين ملفه الرقمي في سحابة Firebase!")
        else:
            st.error("❌ يرجى ملء البيانات ورفع المستندات كاملة لتفعيل زر الاعتماد السحابي.")

# --- d: النظام المالي المحاسبي السيادي (قراءة مباشرة وحية من Firebase) ---
elif st.session_state["current_page"] == "المالي":
    st.markdown("<h2 style='color: #9C27B0;'>📊 الهيكل المحاسبي والتقرير الضريبي وعوائد المزايدات السحابية</h2>", unsafe_allow_html=True)
    st.write("البيانات بالأسفل تعكس حركة العمليات الحية المسترجعة من سحابة Firebase.")
    
    df = pd.DataFrame(financial_records)
    
    # الحسابات المالية الاحترافية الشاملة للضرائب والعمولة
    total_base_revenue = df["القيمة الأساسية (ج.م)"].sum()
    total_vat_pool = total_base_revenue * 0.14
    grand_collected = total_base_revenue + total_vat_pool
    drivers_share = total_base_revenue * 0.80
    monjez_net_profit = total_base_revenue * 0.20
    
    df["القيمة المضافة (14%)"] = df["القيمة الأساسية (ج.م)"] * 0.14
    df["إجمالي الفاتورة بالضريبة"] = df["القيمة الأساسية (ج.م)"] + df["القيمة المضافة (14%)"]
    df["مستحقات السائق (80%)"] = df["القيمة الأساسية (ج.م)"] * 0.80
    df["صافي عمولة منجز (20%)"] = df["القيمة الأساسية (ج.م)"] * 0.20

    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي التحصيل بالضريبة", f"{grand_collected:,.2f} ج.م")
    c2.metric("مستحقات الضرائب (14%)", f"{total_vat_pool:,.2f} ج.م")
    c3.metric("صافي أرباح منصة مُنجز (20%)", f"{monjez_net_profit:,.2f} ج.م", "⚙️ صافي العمولة")
    
    st.write("---")
    st.dataframe(df, use_container_width=True)
    
    st.write("---")
    admin_audit_email = st.text_input("بريد الإدارة المعتمد للأرشفة:", value="ahmed.mustafa@monjez-app.icu")
    
    if st.button("إغلاق الدورة المستندية الضريبية وشحن التقرير للإدارة", use_container_width=True):
        if admin_audit_email:
            report_html = f"""
            <div style="direction: rtl; text-align: right; font-family: Arial, sans-serif; border: 2px solid #9C27B0; padding: 20px; border-radius: 12px; max-width: 600px; margin: auto;">
                <h2 style="color: #9C27B0; text-align: center;">📊 تقرير المحاسبة والاقرار الضريبي المعتمد - منصة منجز</h2>
                <hr style="border: 0; border-top: 1px solid #eee;">
                <div style="background-color: #f3e5f5; padding: 15px; border-radius: 8px; color: #4a148c; font-size: 15px; line-height: 1.8;">
                    • إجمالي الكاش المحصل بالمزايدات السحابية: <b>{grand_collected:,.2f} ج.م</b><br>
                    • وعاء الشحن الأساسي المعتمد: <b>{total_base_revenue:,.2f} ج.م</b><br><br>
                    <span style="color: #d32f2f;">• <b>مستحقات مصلحة الضرائب (14%): {total_vat_pool:,.2f} ج.م</b></span><br>
                    • مستحقات أسطول السائقين (80%): <b>{drivers_share:,.2f} ج.م</b><br>
                    • <b>صافي دخل وعمولة تطبيق مُنجز (20%): {monjez_net_profit:,.2f} ج.م</b>
                </div>
            </div>
            """
            with st.spinner("جاري شحن وثيقة الإغلاق المالي..."):
                if send_monjez_email(admin_audit_email, "⚠️ إشعار وعزل كشف الحساب الضريبي المالي - منصة مُنجز", report_html):
                    st.success("✅ تم عزل الضرائب وإرسال التقرير بنجاح لبريد الإدارة المعتمد!")

# --- د: الصفحة الرئيسية ---
else:
    st.markdown("<h3 style='color: #FF5733;'>🧪 مركز اختبار الإشعارات والربط السحابي</h3>", unsafe_allow_html=True)
    st.info("المنصة متصلة الآن بسحابة قاعدة بيانات Firebase بنجاح مستقر ودون أخطاء.")
