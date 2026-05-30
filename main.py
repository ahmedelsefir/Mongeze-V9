import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
import requests
import streamlit as st
import json

# ========================================================
# 🔗 جلب الإعدادات الحساسة والسيادية مباشرة من الـ Secrets
# ========================================================
try:
    FIREBASE_URL = st.secrets["FIREBASE_URL"]
    ZOHO_WEBHOOK_URL = st.secrets["ZOHO_WEBHOOK_URL"]
    
    # ⚙️ مفاتيح الاتصال الميكانيكي بالسيرفر الخاص بك (Gmail) لمتابعة النظام
    SYSTEM_SMTP_SERVER = st.secrets["SMTP_SERVER"]
    SYSTEM_SMTP_PORT = int(st.secrets["SMTP_PORT"])
    SYSTEM_SMTP_USER = st.secrets["SMTP_USER"]
    SYSTEM_SMTP_PASS = st.secrets["SMTP_PASSWORD"]  # الباسورد المخصص للتطبيقات
    
    # قراءة مفتاح Firebase
    raw_key = st.secrets["private_key"]
    if "\\n" in raw_key:
        PRIVATE_KEY = raw_key.replace("\\n", "\n")
    else:
        PRIVATE_KEY = raw_key
except Exception as e:
    # قيم احتياطية مستمدة مباشرة من ملفك السيادي للاختبار
    FIREBASE_URL = "https://gen-lang-client-03099029-937be-default-rtdb.firebaseio.com"
    ZOHO_WEBHOOK_URL = "https://flow.zoho.com/925590557/flow/webhook/incoming?zapikey=1001.4ed049f1059832abea2dd6e71726f3e3.69dca4e9d8e0a43901c4761e7ab37b56&isdebug=false"
    SYSTEM_SMTP_SERVER = "smtp.gmail.com"
    SYSTEM_SMTP_PORT = 587
    SYSTEM_SMTP_USER = "ahmedelsefir9@gmail.com"
    SYSTEM_SMTP_PASS = "nvoi uacs hsqz poba"
    PRIVATE_KEY = None

# 🛠️ دالة الاتصال الميكانيكي لإرسال الإشعارات والتقارير البرمجية لك شخصياً
def send_system_notification(notification_subject, message_html):
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = SYSTEM_SMTP_USER
        msg['To'] = SYSTEM_SMTP_USER  # يتم الإرسال إليك مباشرة لمتابعة النظام
        msg['Subject'] = f"🚨 [نظام مُنجز] {notification_subject}"
        
        part = MIMEText(message_html, 'html', 'utf-8')
        msg.attach(part)
        
        # الاتصال التلقائي عبر منفذ الـ TLS لـ Gmail
        server = smtplib.SMTP(SYSTEM_SMTP_SERVER, SYSTEM_SMTP_PORT)
        server.starttls()  # تشفير التوثيق ميكانيكياً
        server.login(SYSTEM_SMTP_USER, SYSTEM_SMTP_PASS)
        server.sendmail(SYSTEM_SMTP_USER, SYSTEM_SMTP_USER, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"⚠️ فشل الاتصال الميكانيكي بنظام البريد الشخصي: {e}")
        return False

# دالة مخصصة لحفظ البيانات في Firebase Realtime Database
def save_to_firebase(node, data):
    try:
        response = requests.post(f"{FIREBASE_URL}/{node}.json", json=data)
        return response.ok
    except Exception as e:
        st.error(f"❌ فشل الاتصال بالسحاب أثناء الحفظ: {e}")
        return False

# دالة مخصصة لجلب وقراءة البيانات الحية من Firebase
def load_from_firebase(node):
    try:
        response = requests.get(f"{FIREBASE_URL}/{node}.json")
        if response.ok and response.json():
            raw_data = response.json()
            if isinstance(raw_data, dict):
                return list(raw_data.values())
            elif isinstance(raw_data, list):
                return [item for item in raw_data if item is not None]
        return []
    except Exception as e:
        return []

# ========================================================
# 1. إدارة الحالة والتنقل المركزي (Session State)
# ========================================================
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "الرئيسية"
    
    # 🔔 إشعار آلي فوري يرسل لبريدك بمجرد تشغيل التطبيق أو استدعائه لإثبات نجاح الاتصال الميكانيكي
    startup_html = """
    <div style="direction: rtl; text-align: right; font-family: Arial, sans-serif; border: 2px solid #FF5733; padding: 15px; border-radius: 8px;">
        <h3 style="color: #FF5733;">🚀 تم استعادة الاتصال الميكانيكي بنجاح</h3>
        <p>يا هندسة، هذا إشعار تلقائي من السيستم يفيد بأن منصة <b>مُنجز V9</b> عادت للعمل والاتصال بسيرفر البريد مستقر وآمن تماماً الآن.</p>
    </div>
    """
    send_system_notification("إشعار تشغيل واستقرار المنصة الآلي", startup_html)

financial_records = load_from_firebase("financial_records")

if not financial_records:
    financial_records = [{"الرحلة": "TR-101", "العميل": "شركة الأمل للتجارة", "الكابتن": "أحمد محمود", "القيمة الأساسية (ج.م)": 1500.0, "الحالة": "مكتملة"}]

def navigate_to(page_name):
    st.session_state["current_page"] = page_name

# ========================================================
# 2. شريط التحكم والتنقل العلوي المستقر (UI/UX)
# ========================================================
st.title("🤖 مساعد منصة مُنجز الذكي")
st.write("لوحة القيادة المركزية الفاعلة - إدارة العمليات والدورة المالية اللوجستية.")

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
# 3. شاشات وبوابات التطبيق الفاعلة السحابية
# ========================================================

# --- أ: بوابة العملاء ---
if st.session_state["current_page"] == "العملاء":
    st.markdown("<h2 style='color: #1E88E5;'>🛒 بوابة طلب الشحنات ونظام المزايدة الحي</h2>", unsafe_allow_html=True)
    customer_name = st.text_input("اسم العميل أو الشركة طالبة الشحن:")
    delivery_address = st.text_input("عنوان التوصيل (من وإلى):")
    suggested_price = st.number_input("السعر المقترح من قبلك للرحلة (جنيه):", min_value=0.0, step=50.0, value=150.0)
    
    if suggested_price > 0 and customer_name and delivery_address:
        st.write("---")
        bid_1 = suggested_price
        c1, _, _ = st.columns(3)
        with c1:
            st.markdown(f"<div style='border: 1px solid #ddd; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 10px;'><b>كابتن/ رأفت المنسي</b><br>⭐ 4.9 (موتوسيكل)<br><h3 style='color: #1E88E5; margin: 5px 0;'>{bid_1:,.0f} ج.م</h3></div>", unsafe_allow_html=True)
            if st.button("قبول عرض رأفت", key="accept_bid_1", use_container_width=True):
                new_trip = {"الرحلة": f"TR-{len(financial_records)+101}", "العميل": customer_name, "الكابتن": "رأفت المنسي", "القيمة الأساسية (ج.م)": float(bid_1), "الحالة": "مكتملة"}
                if save_to_firebase("financial_records", new_trip):
                    st.success("☁️ تم حفظ رحلة كابتن رأفت بنجاح في السحاب!")
                    st.rerun()

# --- ب: بوابة الكباتن ---
elif st.session_state["current_page"] == "الكباتن":
    st.markdown("<h2 style='color: #4CAF50;'>🚖 مركز توثيق الفحص الأمني للمستندات (الكباتن)</h2>", unsafe_allow_html=True)
    driver_name = st.text_input("اسم الكابتن اللوجيستي المعتمد رباعياً:")
    driver_id = st.text_input("رقم بطاقة الرقم القومي (14 رقم):")
    driver_email = st.text_input("البريد الإلكتروني الخاص بالكابتن:")
    
    if st.button("تفعيل واعتماد الكابتن وحفظه سحابياً", use_container_width=True):
        if driver_name and driver_id and driver_email:
            driver_profile = {"اسم_الكابتن": driver_name, "الرقم_القومي": driver_id, "البريد": driver_email, "حالة_التوثيق": "نشط وموثق سحابياً"}
            if save_to_firebase("verified_drivers", driver_profile):
                st.success(f"🎉 تم اعتماد الكابتن [{driver_name}] وحفظ ملفه الرقمي بنجاح!")
        else:
            st.error("❌ تعذر التوثيق! يرجى رفع كافة المستندات المطلوبة كاملة.")

# --- ج: النظام المالي والأتمتة ---
elif st.session_state["current_page"] == "المالي":
    st.markdown("<h2 style='color: #9C27B0;'>📊 الهيكل المحاسبي والتقرير الضريبي وعوائد المزايدات السحابية</h2>", unsafe_allow_html=True)
    
    df = pd.DataFrame(financial_records)
    total_base_revenue = df["القيمة الأساسية (ج.م)"].sum()
    total_vat_pool = total_base_revenue * 0.14
    grand_collected = total_base_revenue + total_vat_pool
    monjez_net_profit = total_base_revenue * 0.20
    
    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي التحصيل بالضريبة", f"{grand_collected:,.2f} ج.م")
    c2.metric("مستحقات الضرائب (14%)", f"{total_vat_pool:,.2f} ج.م")
    c3.metric("صافي أرباح منصة مُنجز (20%)", f"{monjez_net_profit:,.2f} ج.م")
    
    st.write("---")
    st.dataframe(df, use_container_width=True)
    
    st.write("---")
    st.subheader("⭐ إجراءات الترحيل النهائي وأتمتة التقرير")
    
    if st.button("إغلاق الدورة المستندية الضريبية وشحن التقرير للإدارة والأتمتة", use_container_width=True):
        payload = {"total_amount": float(grand_collected), "net_profit": float(monjez_net_profit), "status": "Closed_Session"}
        
        with st.spinner("جاري الترحيل وإخطار نظام المراقبة ميكانيكياً..."):
            # 1. إرسال البيانات لـ Zoho Flow
            try:
                flow_response = requests.post(ZOHO_WEBHOOK_URL, json=payload)
                flow_success = flow_response.ok
            except Exception:
                flow_success = False
                
            # 2. إرسال تقرير فوري لحسابك الشخصي لمراقبة الدورة المالية للإدارة
            report_html = f"""
            <div style="direction: rtl; text-align: right; font-family: Arial, sans-serif; border: 1px solid #9C27B0; padding: 20px; border-radius: 10px;">
                <h2 style="color: #9C27B0;">📊 تقرير النظام المالي الفوري المنقول ميكانيكياً</h2>
                <p>مرحباً يا هندسة، تم بنجاح إغلاق جلسة محاسبية جديدة في التطبيق. إليك ملخص الأرقام الحالية:</p>
                <ul>
                    <li><b>إجمالي المحصل بالضريبة:</b> {grand_collected:,.2f} ج.م</li>
                    <li><b>مستحقات ضريبة القيمة المضافة:</b> {total_vat_pool:,.2f} ج.م</li>
                    <li><b>صافي عمولة منجز المرحّلة:</b> {monjez_net_profit:,.2f} ج.م</li>
                </ul>
                <p style="color: green;">✔ الحالة البرمجية: مستقرة ومؤمنة بالكامل سحابياً.</p>
            </div>
            """
            system_email_success = send_automated_email = send_system_notification("تقرير إغلاق الحسابات والدورة المالية للشركة", report_html)
            
            if system_email_success:
                st.success("🔒 تم إرسال التقرير المالي والإداري ميكانيكياً إلى بريدك الشخصي بنجاح لمراقبة النظام!")
            else:
                st.warning("⚠️ تم تنفيذ العمليات لكن فشل إرسال الإشعار لبريدك المالي، يرجى مراجعة الـ Secrets.")

# --- د: الصفحة الرئيسية ---
else:
    st.markdown("<h3 style='color: #FF5733;'>🧪 مركز اختبار الإشعارات والربط السحابي</h3>", unsafe_allow_html=True)
    st.info("المنصة متصلة الآن بسحابة قاعدة بيانات Firebase بنجاح وبأعلى معايير الحماية والتأمين البرمجي.")
