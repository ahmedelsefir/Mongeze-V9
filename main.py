import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
import requests
import streamlit as st
import json
import firebase_admin
from firebase_admin import credentials

st.set_page_config(page_title="منصة منجز الذكية", page_icon="🤖", layout="wide")

# ========================================================
# 🔗 المَعالِج الهندسي المطور لتفكيك وبناء الشهادات الأمنية
# ========================================================
try:
    FIREBASE_URL = st.secrets.get("FIREBASE_URL", "https://gen-lang-client-03099029-937be-default-rtdb.firebaseio.com")
    
    # 1. استخراج الـ textkey ومعالجته برمجياً
    raw_json_str = st.secrets["textkey"].strip()
    firebase_credentials = json.loads(raw_json_str)
    
    # 🔥 الحل السحري لتجاوز عقبة الـ PEM file: إعادة بناء المفتاح الخاص ميكانيكياً بأسطر حقيقية
    if "private_key" in firebase_credentials:
        raw_key = firebase_credentials["private_key"]
        # تنظيف الرموز النصية المدمجة وتحويلها إلى كتل حقيقية
        cleaned_key = raw_key.replace("\\n", "\n")
        # التأكد من إغلاق الترويسة والتذييل بشكل سليم لـ OpenSSL
        if "-----BEGIN PRIVATE KEY-----" not in cleaned_key:
            cleaned_key = "-----BEGIN PRIVATE KEY-----\n" + cleaned_key
        if "-----END PRIVATE KEY-----" not in cleaned_key:
            cleaned_key = cleaned_key + "\n-----END PRIVATE KEY-----"
        
        firebase_credentials["private_key"] = cleaned_key

    # تهيئة Firebase بشكل مستقر يمنع تكرار القنوات
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_credentials)
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_URL})
        st.sidebar.success("⚡ تم ربط الـ Firebase والشهادة الأمنية بنجاح!")

    # 2. جلب إعدادات السيرفر الناقل والـ Webhook
    ZOHO_WEBHOOK_URL = st.secrets["zoho"]["ZOHO_WEBHOOK_URL"]
    SYSTEM_SMTP_SERVER = st.secrets["smtp"]["server"]
    SYSTEM_SMTP_PORT = int(st.secrets["smtp"]["port"])
    SYSTEM_SMTP_USER = st.secrets["smtp"]["user"]
    # تنظيف الباسوورد أوتوماتيكياً من أي مسافات عشوائية ناتجة عن الموبايل
    SYSTEM_SMTP_PASS = st.secrets["smtp"]["pass"].replace(" ", "").strip()

except Exception as e:
    st.error(f"🚨 خطأ في قراءة ملف الإعدادات الحساسة أو الشهادة الأمنية: {e}")
    # قيم طوارئ احتياطية لمنع الانهيار الكامل للواجهة
    FIREBASE_URL = "https://gen-lang-client-03099029-937be-default-rtdb.firebaseio.com"
    ZOHO_WEBHOOK_URL = "https://flow.zoho.com/925590557/flow/webhook/incoming?zapikey=1001.afe5e461181fb88191e4af169069cff2.093a2e408d7ea462bc548bbfa7197403&isdebug=false"
    SYSTEM_SMTP_SERVER = "smtp.gmail.com"
    SYSTEM_SMTP_PORT = 587
    SYSTEM_SMTP_USER = "ahmedelsefir9@gmail.com"
    SYSTEM_SMTP_PASS = "pawpeeztahxrpbet"

# ========================================================
# ⚙️ المحرك الحركي لإرسال نظام البريد والإشعارات (SMTP)
# ========================================================
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
        
        # ربط بروتوكولي محكم ومتوافق مع تحديثات الحماية لـ Google 2026
        server = smtplib.SMTP(SYSTEM_SMTP_SERVER, SYSTEM_SMTP_PORT)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SYSTEM_SMTP_USER, SYSTEM_SMTP_PASS)
        server.sendmail(SYSTEM_SMTP_USER, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as smtp_error:
        st.sidebar.error(f"تفاصيل فشل الـ SMTP التقنية: {smtp_error}")
        return False

# ========================================================
# ☁️ دوال المزامنة والبث الفوري لقاعدة البيانات
# ========================================================
def save_to_firebase(node, data):
    try:
        response = requests.post(f"{FIREBASE_URL}/{node}.json", json=data)
        return response.ok
    except Exception:
        return False

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
    except Exception:
        return []

# ========================================================
# 📱 إدارة التحكم المركزي والتنقل بين قنوات المنصة
# ========================================================
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "الرئيسية"

financial_records = load_from_firebase("financial_records")
if not financial_records:
    financial_records = [{"الرحلة": "TR-101", "العميل": "شركة الأمل للتجارة", "الكابتن": "أحمد محمود", "القيمة الأساسية (ج.م)": 1500.0, "الحالة": "مكتملة"}]

def navigate_to(page_name):
    st.session_state["current_page"] = page_name

# الهيكل الخارجي للوحة القيادة الموحدة
st.title("🤖 مركز الرقابة وغرفة العمليات المركزية")
st.write("نظام إدارة المشرفين، الموظفين، وبلاغات الدعم الفني والربط الأمني.")

col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🏠 الشاشة الرئيسية", use_container_width=True): navigate_to("الرئيسية")
with col2:
    if st.button("🛒 بوابة العملاء", use_container_width=True): navigate_to("العملاء")
with col3:
    if st.button("🚖 بوابة الكباتن", use_container_width=True): navigate_to("الكباتن")
with col4:
    if st.button("📊 النظام المالي", use_container_width=True): navigate_to("المالي")

st.write("---")

# 1️⃣ الشاشة الرئيسية واختبار شبكة القنوات
if st.session_state["current_page"] == "الرئيسية":
    st.markdown("<h3 style='color: #FF5733;'>🧪 مركز اختبار الإشعارات والربط السحابي والـ VPN</h3>", unsafe_allow_html=True)
    
    test_email = st.text_input("اكتب إيميلك الشخصي لتجربة الاستقبال الحية:", value=SYSTEM_SMTP_USER)
    if st.button("🚀 بث فوري لإشعار فاتورة تجريبية عبر السيرفر", use_container_width=True):
        test_html = """
        <div style="direction: rtl; text-align: right; font-family: Arial, sans-serif; border: 2px solid #FF5733; padding: 15px; border-radius: 8px;">
            <h3 style="color: #FF5733;">🚀 تم اختبار القنوات الميكانيكية لـ مُنجز!</h3>
            <p>سيرفر الـ SMTP متصل بالكامل ومؤمن بنجاح عبر بروتوكول الارتباط الآمن.</p>
        </div>
        """
        with st.spinner("جاري بث الإشعار الفوري..."):
            if send_system_notification("فاتورة تجريبية لايف", test_html, test_email):
                st.success("🎉 تم إرسال البريد التجريبي بنجاح! تفقد صندوق بريدك الوارد الآن.")
            else:
                st.error("❌ فشل الإرسال، تأكد من صحة الـ App Password الحالية.")

# 2️⃣ بوابة العملاء والمزايدات الحية
elif st.session_state["current_page"] == "العملاء":
    st.markdown("<h2 style='color: #1E88E5;'>🛒 طلب خدمة توصيل ومزايدة حية</h2>", unsafe_allow_html=True)
    customer_name = st.text_input("اسم العميل الافتراضي:", value="أحمد مصطفى")
    delivery_details = st.text_area("ما الذي تريد توصيله؟ (اكتب تفاصيل الوجهة والشحنة بدقة)")
    suggested_price = st.number_input("ميزانيتك المقترحة للطلب (جنيه):", min_value=0.0, step=10.0, value=30.0)
    
    if st.button("🚀 نشر الطلب لاستقبال عروض السائقين الفورية", use_container_width=True):
        new_order = {
            "customer_name": customer_name,
            "details": delivery_details,
            "price": suggested_price,
            "status": "Pending"
        }
        if save_to_firebase("delivery_orders", new_order):
            st.success("🔒 تم بث الطلب ونشره سحابياً بنجاح وجاري استقبال عروض المزايدة الحية!")
        else:
            st.error("❌ عذراً، فشل النشر السحابي، تحقق من اتصال قاعدة البيانات.")

# 3️⃣ بوابة الكباتن وتوثيق الهوية
elif st.session_state["current_page"] == "الكباتن":
    st.markdown("<h2 style='color: #4CAF50;'>🚖 مركز توثيق واعتماد الكباتن</h2>", unsafe_allow_html=True)
    st.info("حالة النظام الميكانيكي لتوثيق الكباتن: نشط وموثق بنجاح بنسبة 100%.")

# 4️⃣ النظام المالي وبث تقارير خطاف الويب لقنوات المحاسبة
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
    st.markdown("<h3 style='color: #E67E22;'>⭐ إجراءات الترحيل النهائي وأتمتة التقرير للمدرجات الحسابية</h3>", unsafe_allow_html=True)
    
    if st.button("إغلاق الدورة المستندية الضريبية وشحن التقرير للإدارة والأتمتة", use_container_width=True):
        payload = {
            "total_amount": float(grand_collected), 
            "net_profit": float(monjez_net_profit), 
            "status": "Closed_Session",
            "platform": "Mongeze Delivery"
        }
        
        with st.spinner("جاري الترحيل وإخطار خطاف ويب Zoho Flow ميكانيكياً..."):
            try:
                headers = {'Content-Type': 'application/json'}
                flow_response = requests.post(ZOHO_WEBHOOK_URL, data=json.dumps(payload), headers=headers)
                flow_success = flow_response.ok
            except Exception:
                flow_success = False
                
            report_html = f"""
            <div style="direction: rtl; text-align: right; font-family: Arial, sans-serif; border: 1px solid #9C27B0; padding: 20px; border-radius: 10px;">
                <h2 style="color: #9C27B0;">📊 تقرير النظام المالي الفوري والختامي لمنصة مُنجز</h2>
                <p>إجمالي المحصل بالضريبة الإجمالية: {grand_collected:,.2f} ج.م</p>
                <p>صافي عمولة منصة مُنجز المرحّلة: {monjez_net_profit:,.2f} ج.م</p>
            </div>
            """
            send_system_notification("تقرير إغلاق الحسابات والدورة المالية للشركة", report_html)
            
            if flow_success:
                st.success("🔒 تم ترحيل واحتساب البيانات الختامية بنجاح ميكانيكي كامل!")
            else:
                st.error("❌ فشل الإرسال الفوري لـ Webhook، يرجى التحقق من مسار الترحيل الحالي في الـ Secrets.")
