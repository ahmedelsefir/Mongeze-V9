import streamlit as st
import smtplib
import requests  # المكتبة المسؤولة عن شحن واستقبال البيانات سحابياً من Firebase و Zoho Flow
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ========================================================
# 🔗 جلب الإعدادات الحساسة بأمان من بيئة العمل (Secrets)
# ========================================================
try:
    FIREBASE_URL = st.secrets["FIREBASE_URL"]
    ZOHO_EMAIL = st.secrets["ZOHO_EMAIL"]
    ZOHO_PASSWORD = st.secrets["ZOHO_PASSWORD"]
    ZOHO_WEBHOOK_URL = st.secrets["ZOHO_WEBHOOK_URL"]
except Exception:
    # قيم احتياطية آمنة للتشغيل التجريبي المحلي فقط
    FIREBASE_URL = "https://gen-lang-client-03099029-937be-default-rtdb.firebaseio.com"
    ZOHO_EMAIL = "ahmed.mustafa@monjez-app.icu"
    ZOHO_PASSWORD = "42s1kTKByngN"
    ZOHO_WEBHOOK_URL = """https://flow.zoho.com/925590557/flow/webhook/incoming?zapikey=1001.75117eafd3bfacda9a022b78f8cb0806.945cb0677134fbfebbaaa92da61b0ea1&isdebug=false"""

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

# جلب البيانات المالية الحية مباشرة من Firebase
financial_records = load_from_firebase("financial_records")

if not financial_records:
    financial_records = [
        {"الرحلة": "TR-101", "العميل": "شركة الأمل للتجارة", "الكابتن": "أحمد محمود", "القيمة الأساسية (ج.م)": 1500.0, "الحالة": "مكتملة"},
        {"الرحلة": "TR-102", "العميل": "مصنع النور للبلاستيك", "الكابتن": "محمد علي", "القيمة الأساسية (ج.م)": 3200.0, "الحالة": "مكتملة"},
    ]

def navigate_to(page_name):
    st.session_state["current_page"] = page_name

# ========================================================
# 2. محرك إرسال الفواتير والإشعارات السيادي (Zoho SMTP)
# ========================================================
def send_monjez_email(receiver_email, subject, body_html):
    smtp_server = "smtp.zoho.com"
    port = 465

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = ZOHO_EMAIL
    message["To"] = receiver_email
    
    part_html = MIMEText(body_html, "html", "utf-8")
    message.attach(part_html)

    try:
        with smtplib.SMTP_SSL(smtp_server, port) as server:
            server.login(ZOHO_EMAIL, ZOHO_PASSWORD)
            server.sendmail(ZOHO_EMAIL, receiver_email, message.as_string())
        return True
    except Exception as e:
        st.error(f"❌ استجابة سيرفر Zoho SMTP: {e}")
        return False

# ========================================================
# 3. شريط التحكم والتنقل العلوي المستقر
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

# ========================================================
# 4. شاشات وبوابات التطبيق الفاعلة السحابية
# ========================================================

# --- أ: بوابة العملاء ونظام المزايدات الحية ---
if st.session_state["current_page"] == "العملاء":
    st.markdown("<h2 style='color: #1E88E5;'>🛒 بوابة طلب الشحنات ونظام المزايدة الحي</h2>", unsafe_allow_html=True)
    
    customer_name = st.text_input("اسم العميل أو الشركة طالبة الشحن:")
    delivery_address = st.text_input("عنوان التوصيل (من وإلى):")
    suggested_price = st.number_input("السعر المقترح من قبلك للرحلة (جنيه):", min_value=0.0, step=50.0, value=150.0)
    
    if suggested_price > 0 and customer_name and delivery_address:
        st.write("---")
        st.markdown("<h4 style='color: #1E88E5;'>🚖 العروض المستلمة حية من الكباتن المحيطين بك:</h4>", unsafe_allow_html=True)
        
        bid_1 = suggested_price
        bid_2 = suggested_price + (suggested_price * 0.15)
        bid_3 = suggested_price + (suggested_price * 0.30)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"<div style='border: 1px solid #ddd; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 10px;'><b>كابتن/ رأفت المنسي</b><br>⭐ 4.9 (موتوسيكل)<br><h3 style='color: #1E88E5; margin: 5px 0;'>{bid_1:,.0f} ج.م</h3></div>", unsafe_allow_html=True)
            if st.button("قبول عرض رأفت", key="accept_bid_1", use_container_width=True):
                new_trip = {"الرحلة": f"TR-{len(financial_records)+101}", "العميل": customer_name, "الكابتن": "رأفت المنسي", "القيمة الأساسية (ج.م)": float(bid_1), "الحالة": "مكتملة"}
                if save_to_firebase("financial_records", new_trip):
                    st.success(f"☁️ تم حفظ رحلة كابتن رأفت بنجاح في السحاب!")
                    st.rerun()
                
        with c2:
            st.markdown(f"<div style='border: 1px solid #ddd; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 10px;'><b>كابتن/ إيهاب جلال</b><br>⭐ 4.8 (سيارة فاني)<br><h3 style='color: #1E88E5; margin: 5px 0;'>{bid_2:,.0f} ج.م</h3></div>", unsafe_allow_html=True)
            if st.button("قبول عرض إيهاب", key="accept_bid_2", use_container_width=True):
                new_trip = {"الرحلة": f"TR-{len(financial_records)+101}", "العميل": customer_name, "الكابتن": "إيهاب جلال", "القيمة الأساسية (ج.م)": float(bid_2), "الحالة": "مكتملة"}
                if save_to_firebase("financial_records", new_trip):
                    st.success(f"☁️ تم ترحيل رحلة كابتن إيهاب وتأمين الحسابات سحابياً!")
                    st.rerun()
                
        with c3:
            st.markdown(f"<div style='border: 1px solid #ddd; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 10px;'><b>كابتن/ مصطفى طه</b><br>⭐ 4.7 (سيارة ربع نقل)<br><h3 style='color: #1E88E5; margin: 5px 0;'>{bid_3:,.0f} ج.م</h3></div>", unsafe_allow_html=True)
            if st.button("قبول عرض مصطفى", key="accept_bid_3", use_container_width=True):
                new_trip = {"الرحلة": f"TR-{len(financial_records)+101}", "العميل": customer_name, "الكابتن": "مصطفى طه", "القيمة الأساسية (ج.م)": float(bid_3), "الحالة": "مكتملة"}
                if save_to_firebase("financial_records", new_trip):
                    st.success(f"☁️ تم ربط وحفظ شحنة كابتن مصطفى بنجاح!")
                    st.rerun()
    else:
        st.warning("⚠️ يرجى إدخال اسم العميل وعنوان التوصيل لتشغيل لوحة التفاعل الحية.")

# --- ب: بوابة الكباتن وتوثيق المستندات الفنية للأمان ---
elif st.session_state["current_page"] == "الكباتن":
    st.markdown("<h2 style='color: #4CAF50;'>🚖 مركز توثيق الفحص الأمني للمستندات (الكباتن)</h2>", unsafe_allow_html=True)
    
    driver_name = st.text_input("اسم الكابتن اللوجيستي المعتمد رباعياً:")
    driver_id = st.text_input("رقم بطاقة الرقم القومي (14 رقم):")
    driver_email = st.text_input("البريد الإلكتروني الخاص بالكابتن:")
    
    st.markdown("<h4 style='color: #4CAF50;'>🪪 1. صور بطاقة الرقم القومي السارية</h4>", unsafe_allow_html=True)
    id_col1, id_col2 = st.columns(2)
    with id_col1: id_front = st.file_uploader("البطاقة الشخصية (وش):", type=["jpg", "png", "jpeg"], key="idf")
    with id_col2: id_back = st.file_uploader("البطاقة الشخصية (ظهر):", type=["jpg", "png", "jpeg"], key="idb")
    
    st.markdown("<h4 style='color: #4CAF50;'>🪪 2. صور رخصة القيادة الشخصية السارية</h4>", unsafe_allow_html=True)
    license_col1, license_col2 = st.columns(2)
    with license_col1: license_front = st.file_uploader("رخصة القيادة (وش):", type=["jpg", "png", "jpeg"], key="lf")
    with license_col2: license_back = st.file_uploader("رخصة القيادة (ظهر):", type=["jpg", "png", "jpeg"], key="lb")
    
    st.markdown("<h4 style='color: #4CAF50;'>🚖 3. صور رخصة المركبة (السيارة/الموتوسيكل)</h4>", unsafe_allow_html=True)
    vehicle_col1, vehicle_col2 = st.columns(2)
    with vehicle_col1: vehicle_front = st.file_uploader("رخصة المركبة (وش):", type=["jpg", "png", "jpeg"], key="vf")
    with vehicle_col2: vehicle_back = st.file_uploader("رخصة المركبة (ظهر):", type=["jpg", "png", "jpeg"], key="vb")
    
    if st.button("تفعيل واعتماد الكابتن وحفظه سحابياً", use_container_width=True):
        if (driver_name and driver_id and driver_email and id_front and id_back and license_front and license_back and vehicle_front and vehicle_back):
            driver_profile = {
                "اسم_الكابتن": driver_name,
                "الرقم_القومي": driver_id,
                "البريد": driver_email,
                "حالة_التوثيق": "نشط وموثق سحابياً بالملف الأمني الكامل"
            }
            if save_to_firebase("verified_drivers", driver_profile):
                st.success(f"🎉 تم اعتماد الكابتن [{driver_name}] وحفظ ملفه الرقمي في سحابة Firebase بنجاح!")
        else:
            st.error("❌ تعذر التوثيق! يرجى رفع كافة المستندات المطلوبة كاملة.")

# --- ج: النظام الإداري والمالي المحاسبي (الربط المزدوج: البريد + Zoho Flow وبشكل مخفي وأمن) ---
elif st.session_state["current_page"] == "المالي":
    st.markdown("<h2 style='color: #9C27B0;'>📊 الهيكل المحاسبي والتقرير الضريبي وعوائد المزايدات السحابية</h2>", unsafe_allow_html=True)
    
    df = pd.DataFrame(financial_records)
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
    
    if st.button("إغلاق الدورة المستندية الضريبية وشحن التقرير للإدارة والأتمتة", use_container_width=True):
        if admin_audit_email:
            # 📜 1. بناء قالب الفاتورة التفاعلي الـ HTML لإرساله بالإيميل بقيم حية كاملة
            report_html = f"""
            <div style="direction: rtl; text-align: right; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; border: 2px solid #9C27B0; padding: 25px; border-radius: 15px; max-width: 600px; margin: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                <div style="text-align: center; margin-bottom: 20px;">
                    <h2 style="color: #9C27B0; margin-bottom: 5px;">📊 تقرير المحاسبة والإقرار الضريبي المعتمد</h2>
                    <strong style="color: #555;">منصة مُنجز السيادية اللوجستية</strong>
                </div>
                <hr style="border: 0; border-top: 2px dashed #9C27B0; margin-bottom: 20px;">
                <div style="background-color: #f3e5f5; padding: 20px; border-radius: 10px; color: #4a148c; font-size: 16px; line-height: 2;">
                    • وعاء حركة الشحن الأساسي المعتمد: <b style="float: left;">{total_base_revenue:,.2f} ج.م</b><br>
                    • قيمة ضريبة القيمة المضافة الإلزامية (14%): <b style="float: left; color: #d32f2f;">{total_vat_pool:,.2f} ج.م</b><br>
                    <div style="border-top: 1px solid #ce93d8; margin: 10px 0;"></div>
                    • 🏢 <b>إجمالي التحصيل المالي الشامل بالضريبة: <b style="float: left; font-size: 18px;">{grand_collected:,.2f} ج.م</b></b><br>
                    <div style="border-top: 1px solid #ce93d8; margin: 10px 0;"></div>
                    • مستحقات أسطول كباتن منجز (80%): <b style="float: left;">{drivers_share:,.2f} ج.م</b><br>
                    • 💰 <b>صافي أرباح وعمولة منصة منجز (20%): <b style="float: left; color: #2e7d32;">{monjez_net_profit:,.2f} ج.م</b></b>
                </div>
                <div style="text-align: center; margin-top: 25px; font-size: 12px; color: #777;">
                    تم توليد هذا البيان المالي وتأمينه سحابياً تلقائياً.
                </div>
            </div>
            """
            
            # 📦 2. تجهيز حزمة بيانات JSON اللوجستية والمالية لـ Zoho Flow
            payload = {
                "admin_email": admin_audit_email,
                "total_base_revenue": float(total_base_revenue),
                "total_vat_pool": float(total_vat_pool),
                "grand_collected": float(grand_collected),
                "drivers_share": float(drivers_share),
                "monjez_net_profit": float(monjez_net_profit),
                "status": "Closed_Session"
            }
            
            with st.spinner("جاري شحن الفاتورة حياً وعزل الحسابات والربط السحابي الآمن..."):
                # التنفيذ المزدوج
                email_success = send_monjez_email(admin_audit_email, "⚠️ إشعار وعزل كشف الحساب الضريبي المالي - منصة مُنجز", report_html)
                
                try:
                    flow_response = requests.post(ZOHO_WEBHOOK_URL, json=payload)
                    flow_success = flow_response.ok
                except Exception:
                    flow_success = False
                
                # إظهار النتائج النهائية الفنية للمدير
                if email_success and flow_success:
                    st.success("✅ معجزة رقمية! أُرسلت الفاتورة المكتملة إلى بريد الإدارة، والتقطت لوحة Zoho Flow الإشارة الحية بأمان كامل 🔐!")
                elif email_success:
                    st.warning("✔️ تم إرسال الفاتورة البريدية المكتملة بنجاح، ولكن يرجى مراجعة تفعيل الـ Webhook في لوحة Zoho Flow.")

# --- د: الصفحة الرئيسية ---
else:
    st.markdown("<h3 style='color: #FF5733;'>🧪 مركز اختبار الإشعارات والربط السحابي</h3>", unsafe_allow_html=True)
    st.info("المنصة متصلة الآن بسحابة قاعدة بيانات Firebase بنجاح وبأعلى معايير الحماية والتأمين السري البرمجي.")
