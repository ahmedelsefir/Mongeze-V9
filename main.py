import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
import requests
import streamlit as st
import json

# ========================================================
# 🔗 جلب الإعدادات الحساسة مباشرة من الـ Secrets
# ========================================================
try:
    FIREBASE_URL = st.secrets["FIREBASE_URL"]
    ZOHO_WEBHOOK_URL = st.secrets["ZOHO_WEBHOOK_URL"]
    ZOHO_EMAIL = st.secrets.get("ZOHO_EMAIL", "ahmed.mustafa@monjez-app.icu")
    
    SYSTEM_SMTP_SERVER = st.secrets["SMTP_SERVER"]
    SYSTEM_SMTP_PORT = int(st.secrets["SMTP_PORT"])
    SYSTEM_SMTP_USER = st.secrets["SMTP_USER"]
    SYSTEM_SMTP_PASS = st.secrets["SMTP_PASSWORD"].replace(" ", "") # إزالة أي مسافات بالخطأ
    
    # قراءة المفتاح الخاص بذكاء وتأمين السطور الجديدة
    raw_key = st.secrets["private_key"]
    PRIVATE_KEY = raw_key.replace("\\n", "\n") if "\\n" in raw_key else raw_key
except Exception as e:
    # بيئة احتياطية محلياً
    FIREBASE_URL = "https://gen-lang-client-03099029-937be-default-rtdb.firebaseio.com"
    ZOHO_WEBHOOK_URL = "https://flow.zoho.com/925590557/flow/webhook/incoming?zapikey=1001.4ed049f1059832abea2dd6e71726f3e3.69dca4e9d8e0a43901c4761e7ab37b56&isdebug=false"
    ZOHO_EMAIL = "ahmed.mustafa@monjez-app.icu"
    SYSTEM_SMTP_SERVER = "smtp.gmail.com"
    SYSTEM_SMTP_PORT = 587
    SYSTEM_SMTP_USER = "ahmedelsefir9@gmail.com"
    SYSTEM_SMTP_PASS = "nvoiuacshsqzpoba"
    PRIVATE_KEY = None

# 🛠️ دالة إرسال البريد الإلكتروني (نظام الإشعارات الميكانيكي)
def send_system_notification(notification_subject, message_html, to_email=None):
    if to_email is None:
        to_email = SYSTEM_SMTP_USER
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = SYSTEM_SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = f"🚨 [منصة مُنجز] {notification_subject}"
        
        part = MIMEText(message_html, 'html', 'utf-8')
        msg.attach(part)
        
        server = smtplib.SMTP(SYSTEM_SMTP_SERVER, SYSTEM_SMTP_PORT)
        server.starttls()
        server.login(SYSTEM_SMTP_USER, SYSTEM_SMTP_PASS)
        server.sendmail(SYSTEM_SMTP_USER, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        return False

# دالة حفظ البيانات في Firebase
def save_to_firebase(node, data):
    try:
        response = requests.post(f"{FIREBASE_URL}/{node}.json", json=data)
        return response.ok
    except Exception as e:
        st.error(f"❌ فشل الاتصال بالسحاب أثناء الحفظ: {e}")
        return False

# دالة جلب البيانات من Firebase
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

financial_records = load_from_firebase("financial_records")
if not financial_records:
    financial_records = [{"الرحلة": "TR-101", "العميل": "شركة الأمل للتجارة", "الكابتن": "أحمد محمود", "القيمة الأساسية (ج.م)": 1500.0, "الحالة": "مكتملة"}]

def navigate_to(page_name):
    st.session_state["current_page"] = page_name

# ========================================================
# 2. واجهة المستخدم والتنقل (UI/UX)
# ========================================================
st.title("🤖 مساعد منصة مُنجز الذكي")
st.write("لوحة القيادة المركزية الفاعلة - إدارة العمليات والدورة المالية اللوجستية.")

col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🏠 الرئيسية", use_container_width=True): navigate_to("الرئيسية")
with col2:
    if st.button("🛒 بوابة العملاء", use_container_width=True): navigate_to("العملاء")
with col3:
    if st.button("🚖 بوابة الكباتن", use_container_width=True): navigate_to("الكباتن")
with col4:
    if st.button("📊 النظام المالي", use_container_width=True): navigate_to("المالي")

st.write("---")

# --- الصفحة الرئيسية ومركز الاختبار ---
if st.session_state["current_page"] == "الرئيسية":
    st.markdown("<h3 style='color: #FF5733;'>🧪 مركز اختبار الإشعارات والربط السحابي</h3>", unsafe_allow_html=True)
    
    test_email = st.text_input("اكتب إيميلك الشخصي لتجربة الاستقبال:", value=SYSTEM_SMTP_USER)
    if st.button("🚀 إرسال فاتورة تجريبية لايف", use_container_width=True):
        test_html = """
        <div style="direction: rtl; text-align: right; font-family: Arial, sans-serif; border: 2px solid #FF5733; padding: 15px; border-radius: 8px;">
            <h3 style="color: #FF5733;">🚀 تم اختبار النظام الميكانيكي لـ مُنجز!</h3>
            <p>الربط شغال وسيرفر الـ SMTP متصل تمام وبأعلى كفاءة.</p>
        </div>
        """
        if send_system_notification("فاتورة تجريبية لايف", test_html, test_email):
            st.success("🎉 تم إرسال البريد التجريبي بنجاح! تفقد بريدك الوارد الآن.")
        else:
            st.error("❌ فشل الإرسال. تأكد من صحة الـ App Password في الـ Secrets وبدون مسافات.")

# --- بوابة العملاء ---
elif st.session_state["current_page"] == "العملاء":
    st.markdown("<h2 style='color: #1E88E5;'>🛒 طلب خدمة توصيل ومزايدة حية</h2>", unsafe_allow_html=True)
    customer_name = st.text_input("اسم العميل الافتراضي:", value="أحمد مصطفى")
    delivery_details = st.text_area("ما الذي تريد توصيله؟")
    suggested_price = st.number_input("ميزانيتك المقترحة للطلب (جنيه):", min_value=0.0, step=10.0, value=30.0)
    
    if st.button("🚀 نشر الطلب لاستقبال عروض السائقين", use_container_width=True):
        st.info("جاري معالجة الطلب وبث المزايدة الحية...")

# --- بوابة الكباتن ---
elif st.session_state["current_page"] == "الكباتن":
    st.markdown("<h2 style='color: #4CAF50;'>🚖 مركز توثيق واعتماد الكباتن</h2>", unsafe_allow_html=True)
    st.write("شاشة الفحص الأمني والمستندات.")

# --- النظام المالي والأتمتة ---
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
        
        with st.spinner("جاري الترحيل وإخطار Zoho Flow ميكانيكياً..."):
            try:
                headers = {'Content-Type': 'application/json'}
                flow_response = requests.post(ZOHO_WEBHOOK_URL, data=json.dumps(payload), headers=headers)
                flow_success = flow_response.ok
            except Exception:
                flow_success = False
                
            report_html = f"""
            <div style="direction: rtl; text-align: right; font-family: Arial, sans-serif; border: 1px solid #9C27B0; padding: 20px; border-radius: 10px;">
                <h2 style="color: #9C27B0;">📊 تقرير النظام المالي الفوري لمنصة منجز</h2>
                <p>إجمالي المحصل بالضريبة: {grand_collected:,.2f} ج.م</p>
                <p>صافي عمولة منجز المرحّلة: {monjez_net_profit:,.2f} ج.م</p>
            </div>
            """
            system_email_success = send_system_notification("تقرير إغلاق الحسابات والدورة المالية", report_html)
            
            if flow_success:
                st.success("🔒 تم ترحيل البيانات إلى Zoho Webhook بنجاح ميكانيكي كامل!")
            else:
                st.error("❌ فشل الإرسال، يرجى التحقق من صحة رابط الـ Webhook الفعال في ملف الإعدادات.")
